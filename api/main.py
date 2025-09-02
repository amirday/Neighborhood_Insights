from fastapi import FastAPI, Query
from pydantic import BaseModel
import os, psycopg
app = FastAPI(title="Neighborhood Insights IL")

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