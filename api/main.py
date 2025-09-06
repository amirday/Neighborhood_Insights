from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os, psycopg, json

app = FastAPI(title="Neighborhood Insights IL")

# CORS for local dev (Next.js on 3000/3001)
frontend_origins = [
    os.getenv("FRONTEND_ORIGIN"),
    os.getenv("FRONTEND_ORIGIN_ALT"),
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]

# For dev, allow all origins to simplify local setups across ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_conn():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST","postgres"),
        port=os.getenv("POSTGRES_PORT","5432"),
        user=os.getenv("POSTGRES_USER","ni"),
        password=os.getenv("POSTGRES_PASSWORD","ni_password"),
        dbname=os.getenv("POSTGRES_DB","ni"),
    )

class ReverseSearchRequest(BaseModel):
    weights: dict
    filters: dict

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/address/search")
def address_search(q: str = Query(..., min_length=3)):
    # TODO: integrate Places (runtime only) or simple LIKE on deals/address
    return {"results": []}

@app.post("/search/reverse")
def reverse_search(req: ReverseSearchRequest):
    # TODO: implement SQL-based scoring pipeline
    return {"features": [], "ranking": []}


@app.get("/regions/geojson")
def regions_geojson(
    bbox: str | None = Query(
        default=None,
        description="Optional bbox as minx,miny,maxx,maxy in EPSG:4326",
    ),
    simplify: float = Query(default=0.0, ge=0.0, description="Simplify tolerance in degrees"),
):
    """Return CBS statistical areas as a GeoJSON FeatureCollection.

    For Day 9/10 this serves as a simple data feed to the frontend map.
    Later we can swap to MVT endpoints for performance.
    """
    env = {
        "host": os.getenv("POSTGRES_HOST", "postgres"),
        "port": os.getenv("POSTGRES_PORT", "5432"),
        "user": os.getenv("POSTGRES_USER", "ni"),
        "password": os.getenv("POSTGRES_PASSWORD", "ni_password"),
        "dbname": os.getenv("POSTGRES_DB", "ni"),
    }
    try:
        with psycopg.connect(**env) as conn:
            with conn.cursor() as cur:
                where_clause = ""
                params: list = []
                if bbox:
                    try:
                        minx, miny, maxx, maxy = [float(x) for x in bbox.split(",")]
                    except ValueError:
                        raise HTTPException(status_code=400, detail="Invalid bbox format")
                    where_clause = "WHERE geom && ST_MakeEnvelope(%s, %s, %s, %s, 4326)"
                    params.extend([minx, miny, maxx, maxy])

                simplify_expr = "geom" if simplify <= 0 else "ST_SimplifyPreserveTopology(geom, %s)"
                if simplify > 0:
                    params.append(simplify)

                sql = f"""
                    WITH feats AS (
                      SELECT 
                        region_id,
                        lamas_code,
                        name_he,
                        ST_AsGeoJSON({simplify_expr}, 6) AS geom_json
                      FROM regions
                      {where_clause}
                    )
                    SELECT json_build_object(
                      'type','FeatureCollection',
                      'features', COALESCE(json_agg(json_build_object(
                          'type','Feature',
                          'id', feats.region_id,
                          'properties', json_build_object(
                              'region_id', feats.region_id,
                              'lamas_code', feats.lamas_code,
                              'name_he', feats.name_he
                          ),
                          'geometry', feats.geom_json::json
                      )), '[]'::json)
                    )
                    FROM feats
                """
                cur.execute(sql, params)
                row = cur.fetchone()
                if not row:
                    return {"type": "FeatureCollection", "features": []}
                payload = row[0]
                # psycopg may return json as dict (adapted) or as string
                if isinstance(payload, str):
                    try:
                        return JSONResponse(content=json.loads(payload))
                    except Exception:
                        # If not valid JSON string, raise a 500 with context
                        raise HTTPException(status_code=500, detail="Invalid JSON payload from database")
                return JSONResponse(content=payload)
    except psycopg.OperationalError as e:
        raise HTTPException(status_code=500, detail=f"Database connection failed: {e}")
