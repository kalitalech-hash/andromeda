#!/usr/bin/env python3
"""
Crossref candidate search for PTPP publication pilot.

Usage:
    python scripts/search_crossref_candidates.py --members data_raw/ptpp_members_snapshot.csv --out data_intermediate/publication_candidates.csv --mailto your.email@example.org

This script searches Crossref by author name. It does not make final person-publication attributions.
Manual disambiguation is required before records are moved to final tables.
"""

import argparse
import csv
import datetime as dt
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

USER_AGENT = "AndromedaNowickaBibliometricBot/0.5 (metadata-only bibliometric research; no PDF mirroring; polite delay)"

def request_json(url, mailto):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT + f"; mailto:{mailto}",
            "Accept": "application/json"
        }
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def search_author(first_name, last_name, rows, mailto):
    author_query = f"{first_name} {last_name}".strip()
    params = {
        "query.author": author_query,
        "rows": str(rows),
        "mailto": mailto
    }
    url = "https://api.crossref.org/works?" + urllib.parse.urlencode(params)
    return request_json(url, mailto), url

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--members", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mailto", required=True)
    ap.add_argument("--rows", type=int, default=20)
    ap.add_argument("--delay", type=float, default=3.0)
    args = ap.parse_args()

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "candidate_id","source_database","source_query","title","year","journal_or_book",
        "publication_type","doi","url","authors_raw","abstract","keywords","language",
        "retrieved_at","raw_record_path"
    ]

    with open(args.members, encoding="utf-8", newline="") as f, open(out_path, "w", encoding="utf-8", newline="") as out:
        reader = csv.DictReader(f)
        writer = csv.DictWriter(out, fieldnames=fields)
        writer.writeheader()
        n = 0
        for row in reader:
            first = row.get("first_name", "")
            last = row.get("last_name", "")
            if not first or not last:
                continue
            data, query_url = search_author(first, last, args.rows, args.mailto)
            items = data.get("message", {}).get("items", [])
            for item in items:
                n += 1
                title = " ".join(item.get("title", []) or [])
                year_parts = item.get("issued", {}).get("date-parts", [[]])
                year = year_parts[0][0] if year_parts and year_parts[0] else ""
                authors = []
                for a in item.get("author", []) or []:
                    authors.append(" ".join(filter(None, [a.get("given",""), a.get("family","")])))
                writer.writerow({
                    "candidate_id": f"crossref_{n:06d}",
                    "source_database": "Crossref",
                    "source_query": query_url,
                    "title": title,
                    "year": year,
                    "journal_or_book": " | ".join(item.get("container-title", []) or []),
                    "publication_type": item.get("type",""),
                    "doi": item.get("DOI",""),
                    "url": item.get("URL",""),
                    "authors_raw": "; ".join(authors),
                    "abstract": item.get("abstract",""),
                    "keywords": "; ".join(item.get("subject", []) or []),
                    "language": item.get("language",""),
                    "retrieved_at": dt.datetime.utcnow().isoformat() + "Z",
                    "raw_record_path": ""
                })
            time.sleep(args.delay)

if __name__ == "__main__":
    main()
