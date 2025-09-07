#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GovMap WFS → Pandas/GeoPandas with proper paging.

- Warms up cookies (to avoid HTML/Cesium responses).
- Uses browser-like headers + X-Requested-With.
- Supports WFS 2.0.0 (count/startIndex) and 1.1.0 (maxFeatures + vendor startIndex).
- Paginates until all features are fetched.
- Tries both bases (www + open) and both workspaces (govmap/opendata).
- Returns full GeoDataFrames and Pandas DataFrames per layer.

Requirements:
    pip install requests pandas geopandas shapely tqdm
"""

from __future__ import annotations
import io, time, argparse
from typing import Dict, List, Tuple
import requests, pandas as pd, geopandas as gpd
from tqdm import tqdm

# Known useful layers (edit to taste)
FALLBACK_LAYERS = [
    "govmap:layer_kids_g",        # Kindergartens
    "govmap:layer_school",        # Schools
    "govmap:layer_bus_stops",     # Bus stops
    "govmap:layer_clinics",       # Clinics
    "govmap:layer_train_statoins" # Train stations (typo in source)
]

WFS_BASES = [
    "https://www.govmap.gov.il/geoserver/wfs",
    "https://open.govmap.gov.il/geoserver/opendata/wfs",
]

TIMEOUT = 120
RETRIES = 3
PAGE = 5000          # try big pages to reduce round trips
SLEEP_BETWEEN = 0.25 # politeness

def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 15_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome Safari",
        "Accept": "application/json,text/plain,*/*",
        "Origin": "https://www.govmap.gov.il",
        "Referer": "https://www.govmap.gov.il/",
        "X-Requested-With": "XMLHttpRequest",
    })
    try:
        s.get("https://www.govmap.gov.il/", timeout=TIMEOUT)  # warm cookies
    except Exception:
        pass
    return s

def is_geojson_bytes(b: bytes) -> bool:
    t = b.strip()
    return t.startswith(b"{") and b'"FeatureCollection"' in t

def looks_like_html(b: bytes) -> bool:
    t = b.strip()[:200].lower()
    return t.startswith(b"<!doctype html") or t.startswith(b"<html") or b"cesium.js" in t

def post(s: requests.Session, url: str, data: dict) -> bytes:
    # Retries with small backoff
    last = None
    for i in range(RETRIES):
        try:
            r = s.post(url, data=data, timeout=TIMEOUT, allow_redirects=True)
            if r.status_code != 200:
                raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")
            body = r.content
            if looks_like_html(body):
                raise RuntimeError("Got HTML app shell (blocked)")
            return body
        except Exception as e:
            last = e
            time.sleep(0.6 * (i + 1))
    raise RuntimeError(str(last) if last else "POST failed")

def get_hits_wfs20(s: requests.Session, base: str, typename: str) -> int | None:
    """
    WFS 2.0.0: resultType=hits returns numberMatched in XML/JSON.
    We ask JSON (GeoServer returns an OGC Features-esque JSON hits response).
    """
    params = {
        "service": "WFS", "version": "2.0.0", "request": "GetFeature",
        "typeNames": typename, "resultType": "hits", "outputFormat": "application/json"
    }
    try:
        r = s.get(base, params=params, timeout=TIMEOUT)
        if r.status_code != 200:
            return None
        js = r.json()
        nm = js.get("numberMatched") or js.get("totalFeatures")  # GeoServer varies
        return int(nm) if nm is not None else None
    except Exception:
        return None

def get_page_wfs20(s: requests.Session, base: str, typename: str, start: int, count: int) -> bytes:
    data = {
        "service": "WFS", "version": "2.0.0", "request": "GetFeature",
        "typeNames": typename, "outputFormat": "application/json",
        "srsName": "EPSG:4326", "startIndex": start, "count": count,
    }
    return post(s, base, data)

def get_page_wfs11(s: requests.Session, base: str, typename: str, start: int, count: int) -> bytes:
    """
    WFS 1.1.0 doesn't define paging standardly, but GeoServer supports vendor param 'startIndex'.
    """
    data = {
        "service": "WFS", "version": "1.1.0", "request": "GetFeature",
        "typeName": typename, "outputFormat": "application/json",
        "srsName": "EPSG:4326", "maxFeatures": count, "startIndex": start,
    }
    return post(s, base, data)

def fetch_all_geojson(s: requests.Session, base: str, typename: str) -> List[bytes]:
    """
    Try WFS 2.0.0 paging first; if blocked, try 1.1.0 with vendor 'startIndex'.
    Returns list of GeoJSON-chunk bytes to concatenate later.
    """
    chunks: List[bytes] = []

    # --- Path A: 2.0.0 with hits + paging ---
    total = get_hits_wfs20(s, base, typename)
    if total and total > 0:
        for start in tqdm(range(0, total, PAGE), desc=f"{typename} (WFS 2.0.0)", leave=False):
            b = get_page_wfs20(s, base, typename, start, min(PAGE, total - start))
            if not is_geojson_bytes(b):
                raise RuntimeError(f"Unexpected body at {start} (2.0.0)")
            chunks.append(b)
            time.sleep(0.1)
        return chunks

    # --- Path B: 1.1.0 with paging (GeoServer vendor param) ---
    # We don't know count; loop until empty page
    start = 0
    while True:
        b = get_page_wfs11(s, base, typename, start, PAGE)
        if not is_geojson_bytes(b):
            # If the very first call returns non-geojson, bail to next strategy
            if start == 0:
                break
            raise RuntimeError(f"Unexpected body at startIndex={start} (1.1.0)")
        # parse and see how many features we got
        js = pd.read_json(io.BytesIO(b))
        # quick count without fully materializing
        f_count = len(js.get("features", [])) if isinstance(js, dict) else None
        if f_count is None:
            # geopandas will read; use that to count
            gdf = gpd.read_file(io.BytesIO(b))
            f_count = len(gdf)
        if f_count == 0:
            break
        chunks.append(b)
        start += PAGE
        time.sleep(0.1)

    if chunks:
        return chunks

    # Nothing worked
    raise RuntimeError("WFS paging failed (both 2.0.0 and 1.1.0 paths)")

def coalesce_geojson_chunks(chunks: List[bytes]) -> gpd.GeoDataFrame:
    """
    Merge multiple GeoJSON FeatureCollections into one GeoDataFrame.
    """
    frames = []
    for b in chunks:
        frames.append(gpd.read_file(io.BytesIO(b)))
    if not frames:
        return gpd.GeoDataFrame(geometry=[], crs="EPSG:4326")
    gdf = pd.concat(frames, ignore_index=True)
    if isinstance(gdf, gpd.GeoDataFrame) and (gdf.crs is None or gdf.crs.to_epsg() != 4326):
        try:
            gdf = gdf.to_crs(4326)
        except Exception:
            pass
    return gdf

def fetch_typename_all(s: requests.Session, typename: str) -> gpd.GeoDataFrame:
    """
    Try all base URLs and both workspaces automatically, with paging.
    """
    candidates: List[Tuple[str, str]] = []
    for base in WFS_BASES:
        candidates.append((base, typename))
    if ":" in typename:
        ws, name = typename.split(":", 1)
        other = "opendata" if ws.lower() != "opendata" else "govmap"
        for base in WFS_BASES:
            candidates.append((base, f"{other}:{name}"))

    errs = []
    for base, tn in candidates:
        try:
            chunks = fetch_all_geojson(s, base, tn)
            gdf = coalesce_geojson_chunks(chunks)
            if not gdf.empty:
                return gdf
        except Exception as e:
            errs.append(f"{base} {tn}: {e}")
            continue
    raise RuntimeError(" ; ".join(errs))

def to_plain_df(gdf: gpd.GeoDataFrame) -> pd.DataFrame:
    df = pd.DataFrame(gdf.drop(columns=[c for c in gdf.columns if c == "geometry"]))
    return df.reset_index(drop=True)

def load_layers(layers: List[str]) -> Dict[str, Dict[str, object]]:
    s = make_session()
    out: Dict[str, Dict[str, object]] = {}
    failures: Dict[str, str] = {}

    for tn in layers:
        print(f"\nFetching {tn} …")
        try:
            gdf = fetch_typename_all(s, tn)
            df = to_plain_df(gdf)
            print(f"  -> {len(gdf)} features")
            out[tn] = {"geodata": gdf.reset_index(drop=True), "data": df}
        except Exception as e:
            print(f"  !! Failed: {e}")
            failures[tn] = str(e)
        time.sleep(SLEEP_BETWEEN)

    print("\nSummary:")
    for tn, b in out.items():
        print(f"  {tn}: {len(b['geodata'])} features")
    if failures:
        print("\nFailed layers:")
        for tn, msg in failures.items():
            print(f"  {tn}: {msg}")
    return out

def main():
    ap = argparse.ArgumentParser(description="GovMap WFS → DataFrames (paged)")
    ap.add_argument("--layers", nargs="*", default=FALLBACK_LAYERS, help="TypeNames to fetch")
    args = ap.parse_args()
    load_layers(args.layers)

if __name__ == "__main__":
    main()