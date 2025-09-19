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

#TODO: fix the script df_out.drop_duplicates('שם וסמל מוסד')

from __future__ import annotations
import argparse
import os
import time
import re
from itertools import combinations
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


def remove_numbers_from_street(street: str) -> str:
    """Remove all numbers from street address."""
    return re.sub(r'\d+', '', street).strip()


def generate_word_combinations(street: str) -> list[str]:
    """Generate all combinations by removing words from street name.
    Returns combinations sorted by number of words removed (fewer removals first).
    """
    if not street or not street.strip():
        return []

    words = street.strip().split()
    if len(words) <= 1:
        return [street]  # Can't remove words if only one word

    result_combinations = []

    # Try removing 1 word, then 2 words, etc.
    for num_to_remove in range(1, len(words)):
        for indices_to_remove in combinations(range(len(words)), num_to_remove):
            remaining_words = [words[i] for i in range(len(words)) if i not in indices_to_remove]
            if remaining_words:  # Must have at least one word
                result_combinations.append(' '.join(remaining_words))

    return result_combinations


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
                retries: int = 2) -> Tuple[Optional[float], Optional[float], Optional[str], Optional[str]]:
        """
        Returns (lon, lat, error, fixed_address). If success, error=None.
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

        # Build the fixed address string
        address_parts = [p for p in (country, city, street) if p and p.strip()]
        fixed_address = ", ".join(address_parts) if address_parts else None

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
                    return lon, lat, None, fixed_address
                return None, None, "no_result", fixed_address
            except Exception as e:
                last_err = f"exc:{type(e).__name__}"
                time.sleep(min(3.0, 0.5 * (2 ** attempt)))
        return None, None, last_err or "error", fixed_address

    def geocode_with_fallback(self, *, street: Optional[str], city: Optional[str], country: Optional[str],
                             retries: int = 2) -> Tuple[Optional[float], Optional[float], Optional[str], Optional[str]]:
        """
        Geocode with fallback strategies when initial query fails.
        Returns (lon, lat, error, fixed_address). If success, error=None.
        """
        if not street:
            return self.geocode(street=street, city=city, country=country, retries=retries)

        # Try original address first
        lon, lat, err, fixed_addr = self.geocode(street=street, city=city, country=country, retries=retries)
        if err is None:  # Success
            return lon, lat, err, fixed_addr

        # Fallback 1: Remove numbers from street
        street_no_numbers = remove_numbers_from_street(street)
        if street_no_numbers and street_no_numbers != street:
            lon, lat, err, fixed_addr = self.geocode(street=street_no_numbers, city=city, country=country, retries=retries)
            if err is None:  # Success
                return lon, lat, err, fixed_addr

        # Fallback 2: Try word combinations (remove words from street name)
        word_combos = generate_word_combinations(street_no_numbers if street_no_numbers else street)
        for combo_street in word_combos:
            lon, lat, err, fixed_addr = self.geocode(street=combo_street, city=city, country=country, retries=retries)
            if err is None:  # Success
                return lon, lat, err, fixed_addr

        # Fallback 3: Try city only (no street, no country)
        if city:
            lon, lat, err, fixed_addr = self.geocode(street=None, city=city, country=None, retries=retries)
            if err is None:  # Success - found city coordinates but not street
                return lon, lat, "street_not_found", fixed_addr

        # Fallback 4: Try country only (no street, no city)
        if country:
            lon, lat, err, fixed_addr = self.geocode(street=None, city=None, country=country, retries=retries)
            if err is None:  # Success - found country coordinates but not city
                return lon, lat, "city_not_found", fixed_addr

        # All fallbacks failed, return null coordinates
        original_parts = [p for p in (country, city, street) if p and p.strip()]
        original_fixed = ", ".join(original_parts) if original_parts else None
        return None, None, "country_not_found", original_fixed


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
                    default="/Users/amirdaygmail.com/projects/Neighborhood_Insights/data/processed/mosdot_5.csv", 
                    help="Output CSV path (also used as cache on re-runs)")
    ap.add_argument("--sleep", type=float, default=1.1, help="Seconds between requests (>=1.0 for public Nominatim)")
    ap.add_argument("--country", default="ישראל", help="Country appended to the address key")
    ap.add_argument("--checkpoint-every", type=int, default=50, help="Write CSV every N newly geocoded addresses")
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
    else:
        df_out = df_in.copy()
    for c in ["lon", "lat", "geocode_error", "fixed_address"]:
        if c not in df_out.columns:
            df_out[c] = None

    # Build address_key for all rows
    addr_keys = (
        df_out[required_cols]
        .astype(str)
        .apply(lambda r: make_address_key(r["כתובת"], r["יישוב"], args.country), axis=1)
    )
    df_out["__address_key"] = addr_keys


    # Deduplicate within this run to avoid double requests
    client = NominatimClient(min_interval_s=args.sleep)

    total_to_geocode = df_out['lat'].isna().sum()
    pbar = tqdm(total=total_to_geocode, desc="Geocoding", unit="addr")
    df_out = df_out.reset_index(drop=True)
    updates_count = 0
    processed_count = 0

    for idx in df_out.index:
        row = df_out.loc[idx]
        if pd.notna(row.get("lon")) and pd.notna(row.get("lat")):
            continue

        processed_count += 1
        updates_count += 1
        df_out.at[idx, "geocode_error"] = "no_address"
        city = row["יישוב"]
        street = row["כתובת"]

        if not city or not street:
            print(f"Row {idx}: Missing both כתובת and יישוב; skipping.")
            pbar.update(1)
            continue

        # Update progress bar description with current address
        current_address = f"{street}, {city}" if street else city
        pbar.set_description(f"Geocoding: {current_address[:50][::-1]}... ({processed_count}/{total_to_geocode})")

        lon, lat, err, fixed_addr = client.geocode_with_fallback(street=street, city=city, country=args.country)
        if err:
            print(f"Row {idx}: Geocode error '{err}' for '{street[::-1]}, {city[::-1]}'")
            df_out.at[idx, "geocode_error"] = err
            if fixed_addr:
                df_out.at[idx, "fixed_address"] = fixed_addr
            pbar.update(1)
            continue

        sub = df_out["__address_key"] == row["__address_key"]
        df_out.loc[sub, "lon"] = lon
        df_out.loc[sub, "lat"] = lat
        df_out.loc[sub, "fixed_address"] = fixed_addr
        pbar.update(sub.sum())

        if updates_count >= args.checkpoint_every:
            atomic_write_csv(df_out, args.out)
            updates_count = 0

    pbar.close()

    print(f"Done. Wrote CSV cache: {args.out}")

if __name__ == "__main__":
    main()