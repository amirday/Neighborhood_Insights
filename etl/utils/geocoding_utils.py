#!/usr/bin/env python3
"""
Geocoding utilities for ETL processing.
"""

import re
import time
from itertools import combinations
from typing import Dict, Optional, Tuple

import requests


def normalize_space(s: str) -> str:
    """Normalize whitespace in a string."""
    return re.sub(r"\s+", " ", (s or "").strip())


def make_address_key(address: Optional[str], city: Optional[str], country: Optional[str]) -> Optional[str]:
    """Create a normalized address key for caching and deduplication."""
    parts = [normalize_space(x).lower() for x in (address, city, country) if x and normalize_space(x)]
    return " | ".join(parts) if parts else None


def remove_numbers_from_street(street: str) -> str:
    """Remove all numbers from street address."""
    return re.sub(r'\d+', '', street).strip()


def generate_word_combinations(street: str) -> list[str]:
    """
    Generate all combinations by removing words from street name.
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


class NominatimClient:
    """
    Nominatim geocoding client with rate limiting and fallback strategies.
    """

    def __init__(self, min_interval_s: float = 1.1,
                 user_agent: str = "neighborhood-insights-il/etl (+https://example.org)"):
        self.session = requests.Session()
        self.min_interval_s = max(1.0, float(min_interval_s))
        self.user_agent = user_agent
        self._last_ts = 0.0

    def _pace(self):
        """Ensure minimum interval between requests."""
        now = time.monotonic()
        delta = now - self._last_ts
        if delta < self.min_interval_s:
            time.sleep(self.min_interval_s - delta)

    def geocode(self, *, street: Optional[str], city: Optional[str], country: Optional[str],
                retries: int = 2) -> Tuple[Optional[float], Optional[float], Optional[str], Optional[str]]:
        """
        Geocode an address using Nominatim.

        Returns:
            Tuple of (lon, lat, error, fixed_address). If success, error=None.
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

        Returns:
            Tuple of (lon, lat, error, fixed_address). If success, error=None.
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