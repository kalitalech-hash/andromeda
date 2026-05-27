#!/usr/bin/env python3
"""
1a_pep_metadata_probe.py

Andromeda Nowicka v0.4 — psychoanalytic_core
PEP-Web metadata probe script.

Purpose
-------
This script performs a small, auditable metadata probe against the PEP-Web API
for selected psychoanalytic journals and selected years. It is intentionally
NOT a full harvester.

Default behavior:
- metadata-first,
- no PDF downloads,
- no full-text mirroring,
- no credentials stored in code,
- raw JSON responses saved for audit,
- flattened probe CSV written for methodological review.

Credentials
-----------
Put credentials or authorization values in a local .env file that is NOT
committed to Git. See .env.pep.example.

The script supports three common patterns:

1. Bearer token:
   PEP_AUTH_BEARER=...

2. Raw Authorization header:
   PEP_AUTH_HEADER=...

3. Cookie/session header copied from an allowed authenticated session:
   PEP_COOKIE=...

Use only access methods permitted by your PEP-Web access terms.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

try:
    import requests
except ImportError as exc:
    raise SystemExit(
        "Missing dependency: requests. Install with: pip install requests"
    ) from exc


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_ENDPOINT = "https://api.pep-web.org/v2/Database/Search/"
DEFAULT_OUT_DIR = PROJECT_ROOT / "data" / "raw_pep_metadata" / "probe"
DEFAULT_LOG_PATH = PROJECT_ROOT / "data" / "logs" / "pep_metadata_probe_log.csv"
DEFAULT_FLAT_CSV = PROJECT_ROOT / "data" / "source_recon" / "psychoanalytic_core_metadata_probe_results.csv"

USER_AGENT = (
    "AndromedaNowickaBibliometricBot/0.4 "
    "(metadata-only bibliometric research; no PDF mirroring; polite delay)"
)

# Conservative candidate PEP codes. These should be verified during source recon.
# Leave unknown codes blank rather than guessing silently.
JOURNALS = {
    "ijpa": {
        "label": "The International Journal of Psychoanalysis",
        "pep_code_candidates": ["IJP"],
        "probe_years": [1920, 1950, 1970, 1990, 2005, 2020],
    },
    "japa": {
        "label": "Journal of the American Psychoanalytic Association",
        "pep_code_candidates": ["APA"],
        "probe_years": [1953, 1970, 1990, 2005, 2020],
    },
    "psychoanalytic_psychology": {
        "label": "Psychoanalytic Psychology",
        "pep_code_candidates": ["PPSY"],
        "probe_years": [1984, 1990, 2005, 2020],
    },
    "psychoanalytic_dialogues": {
        "label": "Psychoanalytic Dialogues",
        "pep_code_candidates": ["PD"],
        "probe_years": [1991, 2005, 2020],
    },
    "psychoanalytic_psychotherapy": {
        "label": "Psychoanalytic Psychotherapy",
        "pep_code_candidates": [],
        "probe_years": [1990, 2005, 2020],
    },
}


def load_dotenv(path: Path) -> None:
    """Minimal .env loader; avoids adding python-dotenv as a hard dependency."""
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def build_headers() -> Dict[str, str]:
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/plain, */*",
    }

    # Optional contact email for transparent research crawling.
    contact = os.environ.get("ANDROMEDA_CONTACT_EMAIL")
    if contact:
        headers["From"] = contact

    # Authorization variants. Prefer the most explicit one.
    auth_header = os.environ.get("PEP_AUTH_HEADER")
    bearer = os.environ.get("PEP_AUTH_BEARER")
    cookie = os.environ.get("PEP_COOKIE")

    if auth_header:
        headers["Authorization"] = auth_header
    elif bearer:
        headers["Authorization"] = f"Bearer {bearer}"

    if cookie:
        headers["Cookie"] = cookie

    return headers


def safe_filename(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9._-]+", "_", value)
    return value.strip("_") or "unknown"


def iter_probe_jobs(
    selected_journals: Optional[List[str]] = None,
    selected_years: Optional[List[int]] = None,
) -> Iterable[Dict[str, Any]]:
    journal_ids = selected_journals or list(JOURNALS.keys())
    for journal_id in journal_ids:
        if journal_id not in JOURNALS:
            raise ValueError(f"Unknown journal_id: {journal_id}")

        cfg = JOURNALS[journal_id]
        years = selected_years or cfg["probe_years"]

        # If code is unknown, run a title-based query. This is less precise,
        # but useful during source reconnaissance.
        codes = cfg["pep_code_candidates"] or [None]

        for year in years:
            for pep_code in codes:
                yield {
                    "journal_id": journal_id,
                    "journal_label": cfg["label"],
                    "pep_code_candidate": pep_code,
                    "year": year,
                }


def make_params(job: Dict[str, Any], limit: int, offset: int = 0) -> Dict[str, Any]:
    """
    Build a conservative PEP Search API query.

    The legacy scripts used facetquery + formatrequested=JSON + limit/offset.
    We preserve that structure, but keep it small and explicit.
    """
    year = job["year"]
    pep_code = job.get("pep_code_candidate")

    # Facet syntax may require adjustment after first live test.
    # We deliberately keep this visible and logged.
    if pep_code:
        facetquery = f'PEPCode:("{pep_code}") AND year:("{year}")'
    else:
        # Fallback: title/source-title query. Useful only for recon.
        journal_label = job["journal_label"].replace('"', '\\"')
        facetquery = f'sourceTitle:("{journal_label}") AND year:("{year}")'

    return {
        "facetquery": facetquery,
        "formatrequested": "JSON",
        "abstract": "true",
        "limit": str(limit),
        "offset": str(offset),
        "synonyms": "false",
    }


def request_json(
    session: requests.Session,
    endpoint: str,
    params: Dict[str, Any],
    timeout: int,
) -> Tuple[int, Dict[str, str], Any, str]:
    response = session.get(endpoint, params=params, timeout=timeout)
    text = response.text
    try:
        payload = response.json()
    except Exception:
        payload = None
    return response.status_code, dict(response.headers), payload, text


def extract_document_list(payload: Any) -> List[Dict[str, Any]]:
    """
    Extract document records from known PEP Search API shapes.
    The legacy scripts used documentList.responseSet.
    """
    if not isinstance(payload, dict):
        return []

    candidates = [
        ("documentList", "responseSet"),
        ("documentList", "documents"),
        ("responseSet",),
        ("documents",),
        ("results",),
    ]

    for path in candidates:
        node = payload
        ok = True
        for key in path:
            if isinstance(node, dict) and key in node:
                node = node[key]
            else:
                ok = False
                break
        if ok and isinstance(node, list):
            return [x for x in node if isinstance(x, dict)]

    return []


def get_nested(d: Dict[str, Any], keys: List[str]) -> Any:
    for key in keys:
        if key in d and d[key] not in (None, ""):
            return d[key]
    return None


def normalize_keywords(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        out = []
        for item in value:
            if isinstance(item, str):
                out.append(item.strip())
            elif isinstance(item, dict):
                label = get_nested(item, ["keyword", "label", "name", "text", "value"])
                if label:
                    out.append(str(label).strip())
        return [x for x in out if x]
    if isinstance(value, str):
        # PEP variants may use semicolons, commas, or pipe-like separators.
        parts = re.split(r"\s*;\s*|\s*\|\s*", value)
        return [p.strip() for p in parts if p.strip()]
    return []


def flatten_record(job: Dict[str, Any], record: Dict[str, Any], source_file: str) -> Dict[str, Any]:
    keywords_raw = (
        get_nested(record, ["keywords", "kwds", "art_kwds", "keywordList"])
        or get_nested(record.get("stat", {}) if isinstance(record.get("stat"), dict) else {}, ["art_kwds"])
    )
    keywords = normalize_keywords(keywords_raw)

    return {
        "journal_id": job["journal_id"],
        "journal_label": job["journal_label"],
        "pep_code_candidate": job.get("pep_code_candidate") or "",
        "probe_year": job["year"],
        "document_id": get_nested(record, ["documentID", "documentId", "id", "articleID"]) or "",
        "pep_code_record": get_nested(record, ["PEPCode", "pepCode", "sourceCode"]) or "",
        "year_record": get_nested(record, ["year", "pubYear", "publicationYear"]) or "",
        "title": get_nested(record, ["title", "articleTitle"]) or "",
        "authors": get_nested(record, ["authorMast", "authors", "author", "creator"]) or "",
        "source_title": get_nested(record, ["sourceTitle", "journalTitle", "publicationTitle"]) or "",
        "volume": get_nested(record, ["volume", "vol"]) or "",
        "issue": get_nested(record, ["issue", "issueNo"]) or "",
        "pages": get_nested(record, ["pages", "pageRange"]) or "",
        "doi": get_nested(record, ["doi", "DOI"]) or "",
        "has_abstract": bool(get_nested(record, ["abstract", "abstractText", "abs"])),
        "has_keywords": bool(keywords),
        "n_keywords": len(keywords),
        "keywords_joined": "; ".join(keywords),
        "article_type": get_nested(record, ["articleType", "documentType", "type"]) or "",
        "source_file": source_file,
    }


def append_log(log_path: Path, row: Dict[str, Any]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    exists = log_path.exists()
    with log_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def write_flat_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        # Write header anyway for auditability.
        fieldnames = [
            "journal_id", "journal_label", "pep_code_candidate", "probe_year",
            "document_id", "pep_code_record", "year_record", "title", "authors",
            "source_title", "volume", "issue", "pages", "doi", "has_abstract",
            "has_keywords", "n_keywords", "keywords_joined", "article_type", "source_file",
        ]
    else:
        fieldnames = list(rows[0].keys())

    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="PEP-Web metadata probe for psychoanalytic_core.")
    parser.add_argument("--endpoint", default=os.environ.get("PEP_API_ENDPOINT", DEFAULT_ENDPOINT))
    parser.add_argument("--env", default=str(PROJECT_ROOT / ".env.pep"))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--log", default=str(DEFAULT_LOG_PATH))
    parser.add_argument("--flat-csv", default=str(DEFAULT_FLAT_CSV))
    parser.add_argument("--journal", action="append", help="Journal ID to probe; repeatable.")
    parser.add_argument("--year", action="append", type=int, help="Year to probe; repeatable.")
    parser.add_argument("--limit", type=int, default=25)
    parser.add_argument("--delay", type=float, default=3.0)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--dry-run", action="store_true", help="Print planned requests without calling API.")
    args = parser.parse_args(argv)

    load_dotenv(Path(args.env))

    out_dir = Path(args.out_dir)
    log_path = Path(args.log)
    flat_csv = Path(args.flat_csv)
    out_dir.mkdir(parents=True, exist_ok=True)

    headers = build_headers()
    session = requests.Session()
    session.headers.update(headers)

    all_rows: List[Dict[str, Any]] = []
    jobs = list(iter_probe_jobs(args.journal, args.year))

    for idx, job in enumerate(jobs, start=1):
        params = make_params(job, limit=args.limit, offset=0)
        timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
        file_stub = safe_filename(
            f"{job['journal_id']}_{job.get('pep_code_candidate') or 'titlequery'}_{job['year']}"
        )
        raw_path = out_dir / f"{file_stub}.json"

        if args.dry_run:
            print(json.dumps({
                "endpoint": args.endpoint,
                "params": params,
                "raw_path": str(raw_path),
            }, ensure_ascii=False, indent=2))
            continue

        status_code = None
        error = ""
        n_records = 0

        try:
            status_code, response_headers, payload, text = request_json(
                session=session,
                endpoint=args.endpoint,
                params=params,
                timeout=args.timeout,
            )

            raw_record = {
                "timestamp_utc": timestamp,
                "endpoint": args.endpoint,
                "params": params,
                "status_code": status_code,
                "response_headers_subset": {
                    "content-type": response_headers.get("content-type", ""),
                    "content-length": response_headers.get("content-length", ""),
                },
                "payload": payload if payload is not None else text[:2000],
            }
            raw_path.write_text(json.dumps(raw_record, ensure_ascii=False, indent=2), encoding="utf-8")

            docs = extract_document_list(payload)
            n_records = len(docs)

            for record in docs:
                all_rows.append(flatten_record(job, record, source_file=str(raw_path.relative_to(PROJECT_ROOT))))

        except Exception as exc:
            error = repr(exc)

        append_log(log_path, {
            "timestamp_utc": timestamp,
            "journal_id": job["journal_id"],
            "pep_code_candidate": job.get("pep_code_candidate") or "",
            "probe_year": job["year"],
            "endpoint": args.endpoint,
            "params_json": json.dumps(params, ensure_ascii=False),
            "status_code": status_code if status_code is not None else "",
            "n_records": n_records,
            "raw_path": str(raw_path.relative_to(PROJECT_ROOT)),
            "error": error,
        })

        if idx < len(jobs):
            time.sleep(args.delay)

    if not args.dry_run:
        write_flat_csv(flat_csv, all_rows)
        print(f"Wrote flattened probe CSV: {flat_csv}")
        print(f"Wrote log CSV: {log_path}")
        print(f"Raw JSON directory: {out_dir}")
        print(f"Flattened records: {len(all_rows)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
