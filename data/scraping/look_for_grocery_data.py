# data/scraping/looker_extract_to_csv.py
# Opens the Looker Studio embed, intercepts batchedDataV2 calls,
# saves raw JSON payloads AND parses each into CSV files.
#
# Usage:
#   pip install playwright
#   playwright install chromium
#   python data/scraping/looker_extract_to_csv.py

import asyncio, json, re, hashlib, csv
from pathlib import Path
from playwright.async_api import async_playwright

# --- CONFIG -------------------------------------------------------------------
EMBED_URL = "https://lookerstudio.google.com/embed/reporting/d7fa6200-d2e4-49e8-9f2a-15aa7076b764/page/p_oyhtyp4dtd"

OUT_DIR = Path("data/outputs/looker")
RAW_DIR = OUT_DIR / "raw"
CSV_DIR = OUT_DIR / "csv"
RAW_DIR.mkdir(parents=True, exist_ok=True)
CSV_DIR.mkdir(parents=True, exist_ok=True)

BATCH_RE = re.compile(r"/embed/batchedDataV2", re.I)

# --- HELPERS ------------------------------------------------------------------
def safe_filename(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_\-]+", "_", s).strip("_")[:120] or "table"

def sha8(s: str) -> str:
    return hashlib.sha1(s.encode()).hexdigest()[:8]

def strip_xssi_prefix(s: str) -> str:
    # Some endpoints add a JSON-hijacking prefix: )]}'
    return re.sub(r"^\)\]\}'\s*", "", s)

def column_values(col: dict):
    # Normalize any known Looker/Google column vector to a Python list of values.
    if "stringColumn" in col: return col["stringColumn"].get("values", [])
    if "longColumn"   in col: return col["longColumn"].get("values", [])
    if "doubleColumn" in col: return col["doubleColumn"].get("values", [])
    if "boolColumn"   in col: return col["boolColumn"].get("values", [])
    if "jsonColumn"   in col: return [json.dumps(v, ensure_ascii=False) for v in col["jsonColumn"].get("values", [])]
    # Fallback (e.g., only nullIndex present): return empty, will be padded later
    return []

def pad_columns(cols: list[list]) -> list[list]:
    maxlen = max((len(c) for c in cols), default=0)
    return [c + [""] * (maxlen - len(c)) for c in cols]

def write_csv(table_name: str, headers: list[str], rows: list[list]):
    fn = CSV_DIR / f"{safe_filename(table_name)}.csv"
    with fn.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        if headers:
            w.writerow(headers)
        for r in rows:
            # ensure row is a flat list
            w.writerow([("" if v is None else v) for v in r])
    print(f"[CSV] {fn}  rows={len(rows)}  cols={len(headers)}")

def parse_batched_payload_to_csv(raw_text: str):
    """
    Parse a Looker Studio batchedDataV2 JSON payload and write one CSV per tableDataset.
    Returns number of CSVs written.
    """
    text = strip_xssi_prefix(raw_text)
    try:
        obj = json.loads(text)
    except Exception as e:
        print(f"[WARN] JSON parse error: {e}")
        return 0

    written = 0
    data_responses = obj.get("dataResponse", [])
    for resp_idx, resp in enumerate(data_responses):
        subsets = resp.get("dataSubset", []) or []
        for subset_idx, subset in enumerate(subsets):
            ds = subset.get("dataset", {})
            td = ds.get("tableDataset")
            if not td:
                continue

            # headers
            colinfo = td.get("columnInfo", []) or []
            headers = [ci.get("name", f"col{idx}") for idx, ci in enumerate(colinfo)]

            # columns -> vectors
            cols = td.get("column", []) or []
            vectors = [column_values(c) for c in cols]
            vectors = pad_columns(vectors)

            # rows from column vectors
            rows = list(zip(*vectors))

            # table name heuristic: first colInfo name if present, else a stable fallback
            name = (colinfo[0].get("name") if colinfo else f"table_{resp_idx}_{subset_idx}")
            write_csv(name, headers, rows)
            written += 1

    if written == 0:
        print("[INFO] No tableDataset found in this batch.")
    return written

# --- MAIN ---------------------------------------------------------------------
async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        ctx = await browser.new_context(locale="he-IL")
        page = await ctx.new_page()

        async def on_response(resp):
            url = resp.url
            if not BATCH_RE.search(url):
                return
            try:
                body = await resp.text()  # Playwright handles gzip transparently
            except Exception:
                return

            # Save raw
            raw_name = f"batchedDataV2_{sha8(url + body)}.json"
            raw_path = RAW_DIR / raw_name
            raw_path.write_text(body, encoding="utf-8")
            print(f"[RAW] saved {raw_path}")

            # Parse -> CSV
            parse_batched_payload_to_csv(body)

        page.on("response", on_response)

        print(f"[OPEN] {EMBED_URL}")
        await page.goto(EMBED_URL, wait_until="domcontentloaded", timeout=120_000)

        print("Interact with the report (switch filters/categories). Capturing for ~90s…")
        await page.wait_for_timeout(90_000)

        await ctx.close()
        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())