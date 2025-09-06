"""
ETL loader for CBS Statistical Areas 2022 into PostGIS `regions`.

Usage:
  poetry run python etl/cbs_regions_loader.py \
    --path data/raw/statistical_areas_2022/statistical_areas_2022.shp

Environment variables for DB connection:
  POSTGRES_HOST (default: localhost)
  POSTGRES_PORT (default: 5432)
  POSTGRES_USER (default: ni)
  POSTGRES_PASSWORD (default: ni_password)
  POSTGRES_DB (default: ni)

Notes:
  - Reprojects geometries to EPSG:4326
  - Upserts on `lamas_code`
  - Computes area in sqkm and inserts/upserts centroid
"""

from __future__ import annotations

import os
import sys
from typing import Optional, Tuple

import geopandas as gpd
from shapely.geometry import MultiPolygon, Polygon
try:
    # Shapely 2.x
    from shapely.validation import make_valid as shapely_make_valid  # type: ignore
except Exception:  # pragma: no cover - optional import fallback
    shapely_make_valid = None  # type: ignore
import psycopg


CANDIDATE_ID_FIELDS = [
    "SA_ID",
    "STAT11",
    "STAT12",
    "STAT_CODE",
    "STAT_AREA",
    "STATISTICA",
    "STAT",
    "OBJECTID",
    "ID",
]

CANDIDATE_NAME_HE_FIELDS = [
    "SHEM_EZOR",
    "SHEM_YISH",
    "SHEM_YISHUV",
    "NAME_HEB",
    "HEB_NAME",
    "NAME",
]

CANDIDATE_MUNI_FIELDS = [
    "MUNI_ID",
    "MUNICODE",
    "MUN_CODE",
    "MUNICIPALI",
]


def _find_first_column(gdf: gpd.GeoDataFrame, candidates: list[str]) -> Optional[str]:
    cols = {c.lower(): c for c in gdf.columns}
    for cand in candidates:
        if cand.lower() in cols:
            return cols[cand.lower()]
    return None


def normalize_geometry(geom) -> MultiPolygon:
    if geom is None or geom.is_empty:
        raise ValueError("Empty geometry")
    if isinstance(geom, Polygon):
        return MultiPolygon([geom])
    if isinstance(geom, MultiPolygon):
        return geom
    # In rare cases other geometry types appear; attempt polygonize
    try:
        return MultiPolygon([Polygon(geom.exterior)])  # type: ignore[attr-defined]
    except Exception:
        raise ValueError(f"Unsupported geometry type: {geom.geom_type}")


def get_db_conn():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        user=os.getenv("POSTGRES_USER", "ni"),
        password=os.getenv("POSTGRES_PASSWORD", "ni_password"),
        dbname=os.getenv("POSTGRES_DB", "ni"),
    )


def load_cbs_statistical_areas(path: str) -> Tuple[int, int]:
    if not os.path.exists(path):
        raise FileNotFoundError(path)

    gdf = gpd.read_file(path)
    if gdf.crs is None:
        # CBS SA 2022 are typically in EPSG:2039 (ITM)
        gdf.set_crs(epsg=2039, inplace=True, allow_override=True)
    gdf = gdf.to_crs(epsg=4326)

    id_col = _find_first_column(gdf, CANDIDATE_ID_FIELDS)
    name_col = _find_first_column(gdf, CANDIDATE_NAME_HE_FIELDS)
    muni_col = _find_first_column(gdf, CANDIDATE_MUNI_FIELDS)

    # Compute area in sqkm using metric CRS
    gdf_area = gdf.to_crs(epsg=3857)
    areas_sqkm = (gdf_area.geometry.area / 1_000_000).round(4)

    inserted = 0
    updated = 0

    with get_db_conn() as conn:
        conn.execute("SET application_name = 'etl_cbs_regions_loader'")
        with conn.cursor() as cur:
            for idx, row in gdf.iterrows():
                raw_id = row.get(id_col) if id_col else None
                lamas_code = str(raw_id) if raw_id is not None else f"SA_{idx:06d}"

                raw_name = row.get(name_col) if name_col else None
                name_he = (
                    str(raw_name)
                    if raw_name is not None and str(raw_name).strip()
                    else f"אזור סטטיסטי {lamas_code}"
                )

                municipality_code = (
                    str(row.get(muni_col)) if muni_col and row.get(muni_col) is not None else None
                )

                # Repair geometry if needed
                raw_geom = row.geometry
                if raw_geom is None or raw_geom.is_empty:
                    # Skip empty features
                    continue
                if shapely_make_valid is not None:
                    try:
                        raw_geom = shapely_make_valid(raw_geom)
                    except Exception:
                        # Fallback to zero-width buffer trick
                        raw_geom = raw_geom.buffer(0)
                else:
                    raw_geom = raw_geom.buffer(0)

                if raw_geom is None or raw_geom.is_empty:
                    # Still empty after repair
                    continue

                geom = normalize_geometry(raw_geom)
                # Final sanity checks (Shapely-side)
                try:
                    if not geom.is_valid or geom.is_empty or geom.area == 0:
                        # Skip problematic features
                        print(f"[WARN] Skipping invalid/empty geometry for SA {lamas_code}")
                        continue
                except Exception:
                    print(f"[WARN] Skipping geometry due to validation error for SA {lamas_code}")
                    continue
                area_sqkm = float(areas_sqkm.iloc[idx])

                # Upsert with existence check for accurate counters
                cur.execute("SELECT 1 FROM regions WHERE lamas_code = %s", (lamas_code,))
                exists = cur.fetchone() is not None
                geom_sql = "ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_GeomFromEWKB(%s)), 3))"
                if exists:
                    cur.execute(
                        f"""
                        UPDATE regions
                        SET name_he = %s,
                            municipality_code = %s,
                            area_sqkm = %s,
                            geom = {geom_sql},
                            updated_at = NOW()
                        WHERE lamas_code = %s
                        """,
                        (
                            name_he,
                            municipality_code,
                            area_sqkm,
                            geom.wkb,
                            lamas_code,
                        ),
                    )
                    updated += 1
                else:
                    cur.execute(
                        f"""
                        INSERT INTO regions (lamas_code, name_he, municipality_code, area_sqkm, geom)
                        VALUES (%s, %s, %s, %s, {geom_sql})
                        """,
                        (
                            lamas_code,
                            name_he,
                            municipality_code,
                            area_sqkm,
                            geom.wkb,
                        ),
                    )
                    inserted += 1

                # Ensure centroid upsert
                cur.execute(
                    """
                    INSERT INTO centroids (region_id, geom)
                    SELECT region_id, ST_PointOnSurface(geom) FROM regions WHERE lamas_code = %s
                    ON CONFLICT (region_id) DO UPDATE
                    SET geom = EXCLUDED.geom
                    """,
                    (lamas_code,),
                )

        conn.commit()

    return inserted, updated


def main(argv: list[str]) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Load CBS Statistical Areas into PostGIS regions")
    parser.add_argument(
        "--path",
        default="data/raw/statistical_areas_2022/statistical_areas_2022.shp",
        help="Path to the CBS statistical areas shapefile",
    )
    args = parser.parse_args(argv)

    inserted, updated = load_cbs_statistical_areas(args.path)
    print(f"Loaded regions: inserted={inserted}, updated={updated}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
