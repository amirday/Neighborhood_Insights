import requests
import pandas as pd

BASE = "https://services5.arcgis.com/dlrDjz89gx9qyfev/arcgis/rest/services/HMO_Services2/FeatureServer/6/query"

params = {
    "where": "1=1",
    "outFields": "*",
    "f": "json",
    "resultOffset": 0,
    "resultRecordCount": 2000,
    "returnGeometry": "false"
}

rows = []
while True:
    print(f"Fetching offset {params['resultOffset']}")
    r = requests.get(BASE, params=params)
    r.raise_for_status()
    data = r.json()
    feats = data.get("features", [])
    if not feats:
        break
    for f in feats:
        rows.append(f["attributes"])
    params["resultOffset"] += params["resultRecordCount"]

df = pd.DataFrame(rows)
df.to_csv("hmo_services_layer.csv", index=False)
print(f"Saved {len(df)} rows")