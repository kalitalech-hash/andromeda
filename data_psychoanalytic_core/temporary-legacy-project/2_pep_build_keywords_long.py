import json
import csv
from pathlib import Path

RAW_DIR = Path("raw_pep")
OUT = Path("pep_articles_from_search.csv")

def main():
    files = sorted(RAW_DIR.glob("search_page_*.json"))
    if not files:
        raise SystemExit("Brak plików w raw_pep/. Najpierw uruchom 1_pep_download_search.py")

    rows = []

    for fp in files:
        data = json.loads(fp.read_text(encoding="utf-8"))
        docs = data.get("documentList", {}).get("responseSet", [])

        for d in docs:
            rows.append({
                "documentID": d.get("documentID", ""),
                "PEPCode": d.get("PEPCode", ""),
                "year": d.get("year", ""),
                "title": d.get("title", ""),
                "authorMast": d.get("authorMast", ""),
                "sourceTitle": d.get("sourceTitle", ""),
                # jeśli API daje keywords:
                "keywords": "; ".join(d.get("keywords", [])) if isinstance(d.get("keywords"), list) else (d.get("keywords") or ""),
                # pomocniczo: ile keywords widzi indeks
                "art_kwds_count": (d.get("stat") or {}).get("art_kwds_count", "")
            })

    with OUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print("OK ->", OUT.resolve(), "rows:", len(rows))

if __name__ == "__main__":
    main()