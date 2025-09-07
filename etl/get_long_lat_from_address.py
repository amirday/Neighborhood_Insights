#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Geocode an XLSX with Hebrew columns: 'כתובת' (street) and 'יישוב' (city) using public Nominatim.
- Input:  .xlsx with any columns (must include 'כתובת' and 'יישוב')
- Output: .csv with ALL original columns + 'lon','lat','geocode_error'
- CACHE:  The output CSV *is* the cache. Re-runs only geocode rows missing lon/lat.

Usage:
  python geocode_xlsx_to_csv_cache.py \
    --in addresses.xlsx \
    --out geocoded.csv \
    --sleep 1.1 \
    --country "Israel" \
    --checkpoint-every 250

Notes:
- Respects public Nominatim usage (>=1 req/sec). Do not bulk 35k on the public server.
- Safe to stop/re-run: it resumes from the existing CSV.
"""

from __future__ import annotations
import argparse
import os
import time
import re
from typing import Dict, Optional, Tuple

import pandas as pd
import requests
from tqdm import tqdm


# ----------------------------
# Helpers
# ----------------------------

def normalize_space(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").strip())


def make_address_key(address: Optional[str], city: Optional[str], country: Optional[str]) -> Optional[str]:
    parts = [normalize_space(x).lower() for x in (address, city, country) if x and normalize_space(x)]
    return " | ".join(parts) if parts else None


# ----------------------------
# Nominatim client
# ----------------------------

class NominatimClient:
    def __init__(self, min_interval_s: float = 1.1,
                 user_agent: str = "neighborhood-insights-il/etl (+https://example.org)"):
        self.session = requests.Session()
        self.min_interval_s = max(1.0, float(min_interval_s))
        self.user_agent = user_agent
        self._last_ts = 0.0

    def _pace(self):
        now = time.monotonic()
        delta = now - self._last_ts
        if delta < self.min_interval_s:
            time.sleep(self.min_interval_s - delta)

    def geocode(self, *, street: Optional[str], city: Optional[str], country: Optional[str],
                retries: int = 2) -> Tuple[Optional[float], Optional[float], Optional[str]]:
        """
        Returns (lon, lat, error). If success, error=None.
        """
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "format": "json",
            "limit": 1,
            "addressdetails": 0,
            "extratags": 0,
            "namedetails": 0,
            "countrycodes": "il",
        }
        if street:
            params["street"] = street
        if city:
            params["city"] = city
        if not street and not city:
            q_parts = [p for p in (street, city, country) if p]
            if q_parts:
                params["q"] = ", ".join(q_parts)

        headers = {
            "User-Agent": self.user_agent,
            "Accept-Language": "he,en;q=0.8",
            "Accept": "application/json",
        }

        last_err = None
        for attempt in range(retries + 1):
            try:
                self._pace()
                resp = self.session.get(url, params=params, headers=headers, timeout=20)
                self._last_ts = time.monotonic()
                if resp.status_code in (429, 502, 503, 504) or 500 <= resp.status_code < 600:
                    last_err = f"http_{resp.status_code}"
                    time.sleep(min(3.0, 0.5 * (2 ** attempt)))
                    continue
                data = resp.json()
                if data:
                    lat = float(data[0]["lat"])
                    lon = float(data[0]["lon"])
                    return lon, lat, None
                return None, None, "no_result"
            except Exception as e:
                last_err = f"exc:{type(e).__name__}"
                time.sleep(min(3.0, 0.5 * (2 ** attempt)))
        return None, None, last_err or "error"


# ----------------------------
# Core
# ----------------------------

def atomic_write_csv(df: pd.DataFrame, path: str):
    tmp = f"{path}.tmp"
    # UTF-8 with BOM helps Excel users see Hebrew correctly
    df.to_csv(tmp, index=False, encoding="utf-8-sig")
    os.replace(tmp, path)


def main():
    ap = argparse.ArgumentParser(description="Geocode XLSX (כתובת, יישוב) to CSV with lon/lat, using CSV as cache.")
    ap.add_argument("--in", dest="inp", 
                    default='/Users/amirdaygmail.com/projects/Neighborhood_Insights/data/raw/mosdot_2025.xlsx', 
                    help="Input XLSX file path")
    ap.add_argument("--sheet", default='Sheet1', help="Optional sheet name (defaults to first)")
    ap.add_argument("--out",  
                    default="/Users/amirdaygmail.com/projects/Neighborhood_Insights/data/processed/mosdot.csv", 
                    help="Output CSV path (also used as cache on re-runs)")
    ap.add_argument("--sleep", type=float, default=1.1, help="Seconds between requests (>=1.0 for public Nominatim)")
    ap.add_argument("--country", default="Israel", help="Country appended to the address key")
    ap.add_argument("--checkpoint-every", type=int, default=25, help="Write CSV every N newly geocoded addresses")
    ap.add_argument("--max-rows", type=int, default=None, help="Optional limit on number of input rows to process")
    args = ap.parse_args()

    required_cols = ["כתובת", "יישוב"]

    # Load input XLSX
    df_in = pd.read_excel(args.inp, sheet_name=args.sheet)
    missing = [c for c in required_cols if c not in df_in.columns]
    if missing:
        raise SystemExit(f"Missing required columns in XLSX: {missing}. Found: {list(df_in.columns)}")

    if args.max_rows:
        df_in = df_in.head(args.max_rows)

    # If cache CSV exists, load it; ensure all columns from input exist
    if os.path.exists(args.out):
        df_out = pd.read_csv(args.out, dtype=str, encoding="utf-8-sig")
        # Preserve dtypes but we’ll coerce lon/lat later
        # Make sure all input columns exist in df_out; if not, align/merge
        for col in df_in.columns:
            if col not in df_out.columns:
                df_out[col] = df_in[col]
        # Also ensure any extra cols in cache remain
        # Align row count: merge by a stable key if available; otherwise fallback to position
        # Best effort: If 'כתובת'+'יישוב' exists, merge on them
        if all(c in df_out.columns for c in required_cols):
            # merge to keep existing lon/lat
            df_out = pd.merge(
                df_in,
                df_out[[*required_cols, "lon", "lat", "geocode_error"]] if all(
                    c in df_out.columns for c in ["lon", "lat", "geocode_error"]
                ) else df_out[required_cols],
                on=required_cols,
                how="left",
            )
        else:
            # Fallback: take input and keep lon/lat if present by position (not recommended)
            for c in ["lon", "lat", "geocode_error"]:
                if c not in df_out.columns:
                    df_out[c] = None
            # Overwrite non-key columns from input; keep existing lon/lat columns
            for col in df_in.columns:
                df_out[col] = df_in[col]
    else:
        df_out = df_in.copy()
        for c in ["lon", "lat", "geocode_error"]:
            if c not in df_out.columns:
                df_out[c] = None

    # Build address_key for all rows
    addr_keys = (
        df_out[required_cols]
        .astype(str)
        .apply(lambda r: make_address_key(r["כתובת"], r["יישוב"], args.country), axis=1)
    )
    df_out["__address_key"] = addr_keys

    # Prepare list of unique address keys to geocode (missing lon/lat only)
    df_missing = df_out[(df_out["lon"].isna()) | (df_out["lat"].isna())].copy()
    # Drop rows without an address_key
    df_missing = df_missing[df_missing["__address_key"].notna()]

    # Unique keys not yet resolved in this CSV
    pending_keys = df_missing["__address_key"].dropna().unique().tolist()

    # Deduplicate within this run to avoid double requests
    client = NominatimClient(min_interval_s=args.sleep)
    fresh: Dict[str, Tuple[Optional[float], Optional[float], Optional[str]]] = {}

    if pending_keys:
        # Map address_key back to (כתובת, יישוב) by first occurrence
        key_to_parts: Dict[str, Tuple[str, str]] = {}
        for _, row in df_out.loc[df_out["__address_key"].isin(pending_keys), required_cols + ["__address_key"]].drop_duplicates("__address_key").iterrows():
            key_to_parts[row["__address_key"]] = (row["כתובת"], row["יישוב"])

        pbar = tqdm(pending_keys, desc="Geocoding (CSV cache)", unit="addr")
        since_last_checkpoint = 0
        for k in pbar:
            if k in fresh:
                continue
            street, city = key_to_parts.get(k, (None, None))
            lon, lat, err = client.geocode(street=street, city=city, country=args.country)
            fresh[k] = (lon, lat, err)
            since_last_checkpoint += 1

            # Periodic checkpoint: write results into df_out and flush CSV
            if since_last_checkpoint >= max(25, args.checkpoint_every):
                # Apply fresh to df_out
                sub = df_out["__address_key"].isin(list(fresh.keys()))
                df_out.loc[sub, "lon"] = df_out.loc[sub, "__address_key"].map(lambda kk: fresh[kk][0])
                df_out.loc[sub, "lat"] = df_out.loc[sub, "__address_key"].map(lambda kk: fresh[kk][1])
                df_out.loc[sub, "geocode_error"] = df_out.loc[sub, "__address_key"].map(lambda kk: fresh[kk][2])
                atomic_write_csv(df_out, args.out)
                fresh.clear()
                since_last_checkpoint = 0

        # Final flush
        if fresh:
            sub = df_out["__address_key"].isin(list(fresh.keys()))
            df_out.loc[sub, "lon"] = df_out.loc[sub, "__address_key"].map(lambda kk: fresh[kk][0])
            df_out.loc[sub, "lat"] = df_out.loc[sub, "__address_key"].map(lambda kk: fresh[kk][1])
            df_out.loc[sub, "geocode_error"] = df_out.loc[sub, "__address_key"].map(lambda kk: fresh[kk][2])
            atomic_write_csv(df_out, args.out)
            fresh.clear()
    else:
        # Nothing to geocode; still ensure file exists
        atomic_write_csv(df_out, args.out)

    # Clean up: optional — drop helper key
    # (Leave it if you want re-runs to be even faster and diffable.)
    # df_out.drop(columns=["__address_key"], inplace=True, errors="ignore")
    # atomic_write_csv(df_out, args.out)

    print(f"Done. Wrote CSV cache: {args.out}")

if __name__ == "__main__":
    main()