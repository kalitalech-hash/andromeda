#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
1a_pep_metadata_probe_v10.py

Clean consolidated PEP-Web Search API metadata probe for data_psychoanalytic_core.

This version intentionally replaces the patched v7/v8/v9 line.

Confirmed live findings:
- PEP Search API endpoint:
  https://api.pep-web.org/v2/Database/Search/
- PEPCode is returned in records but is NOT searchable in facetquery.
- Journal filtering works through article id prefix:
  art_id:IJP.*
- Year filtering works:
  year:2020
- One-article query works:
  art_id:IJP.101.0013A
- Article keywords may be present in documentInfoXML:
  <artkwds><impx type="KEYWORD">...</impx></artkwds>
- Fallback keyword source may be abstract HTML:
  <div class="artkwds">...</div>

No PDF download. No full-text mirroring. Metadata-first probe only.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import os
import re
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENDPOINT = "https://api.pep-web.org/v2/Database/Search/"
DEFAULT_ENV = PROJECT_ROOT / ".env.pep"
DEFAULT_OUT_DIR = PROJECT_ROOT / "data" / "raw_pep_metadata" / "probe"
DEFAULT_LOG = PROJECT_ROOT / "data" / "logs" / "pep_metadata_probe_log.csv"
DEFAULT_FLAT_CSV = PROJECT_ROOT / "data" / "source_recon" / "psychoanalytic_core_metadata_probe_results.csv"

USER_AGENT = (
    "AndromedaNowickaBibliometricBot/0.4 "
    "(metadata-only bibliometric research; no PDF mirroring; polite delay)"
)

JOURNALS: Dict[str, Dict[str, str]] = {
    "ijpa": {
        "journal_label": "International Journal of Psychoanalysis",
        "pep_code": "IJP",
    },
    "japa": {
        "journal_label": "Journal of the American Psychoanalytic Association",
        "pep_code": "APA",
    },
    "psychoanalytic_dialogues": {
        "journal_label": "Psychoanalytic Dialogues",
        "pep_code": "PD",
    },
    # These two codes are placeholders until confirmed by source recon.
    "psychoanalytic_psychology": {
        "journal_label": "Psychoanalytic Psychology",
        "pep_code": "PPSY",
    },
    "psychoanalytic_psychotherapy": {
        "journal_label": "Psychoanalytic Psychotherapy",
        "pep_code": "",
    },
}


def load_env_file(path: Path) -> None:
    """Load KEY=value lines from .env.pep. Does not print values."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def build_headers() -> Dict[str, str]:
    """Build request headers from .env.pep without hardcoded secrets."""
    headers: Dict[str, str] = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/plain, */*",
    }

    contact = os.environ.get("ANDROMEDA_CONTACT_EMAIL")
    if contact:
        headers["From"] = contact

    # Generic variants, usually not needed for PEP-Web but kept for compatibility.
    auth_header = os.environ.get("PEP_AUTH_HEADER")
    bearer = os.environ.get("PEP_AUTH_BEARER")
    cookie = os.environ.get("PEP_COOKIE")

    if auth_header:
        headers["Authorization"] = auth_header
    elif bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    if cookie:
        headers["Cookie"] = cookie

    # PEP-Web browser/API-specific headers.
    pep_map = {
        "PEP_CLIENT_ID": "client-id",
        "PEP_CLIENT_SESSION": "client-session",
        "PEP_X_API_AUTHORIZE": "x-api-authorize",
        "PEP_X_PEP_AUTH": "x-pep-auth",
        "PEP_ORIGIN": "origin",
        "PEP_REFERER": "referer",
    }
    for env_name, header_name in pep_map.items():
        value = os.environ.get(env_name)
        if value:
            headers[header_name] = value

    return headers


def safe_env_header_diagnostics(env_path: Path, headers: Dict[str, str]) -> Dict[str, Any]:
    """Non-sensitive diagnostics. Never print header values."""
    return {
        "env_path": str(env_path),
        "env_exists": env_path.exists(),
        "has_PEP_AUTH_HEADER": bool(os.environ.get("PEP_AUTH_HEADER")),
        "has_PEP_AUTH_BEARER": bool(os.environ.get("PEP_AUTH_BEARER")),
        "has_PEP_COOKIE": bool(os.environ.get("PEP_COOKIE")),
        "has_PEP_CLIENT_ID": bool(os.environ.get("PEP_CLIENT_ID")),
        "has_PEP_CLIENT_SESSION": bool(os.environ.get("PEP_CLIENT_SESSION")),
        "has_PEP_X_API_AUTHORIZE": bool(os.environ.get("PEP_X_API_AUTHORIZE")),
        "has_PEP_X_PEP_AUTH": bool(os.environ.get("PEP_X_PEP_AUTH")),
        "has_PEP_ORIGIN": bool(os.environ.get("PEP_ORIGIN")),
        "has_PEP_REFERER": bool(os.environ.get("PEP_REFERER")),
        "sends_Authorization_header": "Authorization" in headers,
        "sends_Cookie_header": "Cookie" in headers,
        "sends_client_id_header": "client-id" in headers,
        "sends_client_session_header": "client-session" in headers,
        "sends_x_api_authorize_header": "x-api-authorize" in headers,
        "sends_x_pep_auth_header": "x-pep-auth" in headers,
        "sends_origin_header": "origin" in headers,
        "sends_referer_header": "referer" in headers,
        "has_ANDROMEDA_CONTACT_EMAIL": bool(os.environ.get("ANDROMEDA_CONTACT_EMAIL")),
    }


def make_jobs(journal_ids: Optional[List[str]], years: Optional[List[int]]) -> List[Dict[str, Any]]:
    journal_ids = journal_ids or list(JOURNALS.keys())
    years = years or [None]

    jobs: List[Dict[str, Any]] = []
    for journal_id in journal_ids:
        if journal_id not in JOURNALS:
            raise ValueError(f"Unknown journal_id: {journal_id}. Known: {', '.join(JOURNALS)}")
        meta = JOURNALS[journal_id]
        for year in years:
            jobs.append({
                "journal_id": journal_id,
                "journal_label": meta["journal_label"],
                "pep_code_candidate": meta.get("pep_code", ""),
                "year": year,
            })
    return jobs


def make_params(job: Dict[str, Any], limit: int, offset: int = 0) -> Dict[str, str]:
    pep_code = job.get("pep_code_candidate") or ""
    year = job.get("year")

    clauses: List[str] = []
    if pep_code:
        clauses.append(f"art_id:{pep_code}.*")
    if year:
        clauses.append(f"year:{year}")

    facetquery = " AND ".join(clauses) if clauses else "*:*"

    return {
        "facetquery": facetquery,
        "formatrequested": "JSON",
        "abstract": "true",
        "limit": str(limit),
        "offset": str(offset),
        "synonyms": "false",
    }


def request_json(session: requests.Session, endpoint: str, params: Dict[str, str], timeout: float) -> Tuple[int, Dict[str, str], Any, str]:
    response = session.get(endpoint, params=params, timeout=timeout)
    text = response.text or ""
    try:
        payload = response.json()
    except Exception:
        payload = None
    return response.status_code, dict(response.headers), payload, text


def payload_shape(payload: Any) -> Dict[str, Any]:
    if isinstance(payload, dict):
        out: Dict[str, Any] = {
            "payload_type": "dict",
            "top_level_keys": list(payload.keys())[:40],
        }
        for key in [
            "documentList", "responseInfo", "responseSet", "documents",
            "results", "count", "fullCount", "total", "error", "message", "detail",
        ]:
            value = payload.get(key)
            if isinstance(value, dict):
                out[f"{key}_keys"] = list(value.keys())[:40]
            elif isinstance(value, list):
                out[f"{key}_list_len"] = len(value)
            elif value is not None:
                out[key] = str(value)[:300]
        return out
    if isinstance(payload, list):
        return {"payload_type": "list", "list_len": len(payload)}
    return {"payload_type": "non_json_or_empty"}


def extract_document_list(payload: Any) -> List[Dict[str, Any]]:
    """Extract document records from known PEP Search API response shapes."""
    if not isinstance(payload, dict):
        return []

    document_list = payload.get("documentList")
    if isinstance(document_list, dict):
        response_set = document_list.get("responseSet")
        if isinstance(response_set, list):
            return [x for x in response_set if isinstance(x, dict)]
        if isinstance(response_set, dict):
            for key in ["document", "documents", "results", "items"]:
                value = response_set.get(key)
                if isinstance(value, list):
                    return [x for x in value if isinstance(x, dict)]

    for key in ["responseSet", "documents", "results", "items"]:
        value = payload.get(key)
        if isinstance(value, list):
            return [x for x in value if isinstance(x, dict)]

    return []


def get_nested(record: Dict[str, Any], keys: List[str]) -> Any:
    for key in keys:
        if key in record and record[key] not in (None, ""):
            return record[key]
    return None


def strip_tags(value: str) -> str:
    if not value:
        return ""
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def normalize_keyword(value: str) -> str:
    value = html.unescape(value or "")
    value = strip_tags(value)
    value = value.strip(" \t\r\n;,.")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def split_keyword_line(value: str) -> List[str]:
    if not value:
        return []
    value = strip_tags(value)
    parts = re.split(r"\s*;\s*|\s*,\s*", value)
    return [kw for kw in (normalize_keyword(p) for p in parts) if kw]


def unique_preserve_order(values: List[str]) -> List[str]:
    seen = set()
    out: List[str] = []
    for value in values:
        key = value.casefold()
        if value and key not in seen:
            out.append(value)
            seen.add(key)
    return out


def extract_keywords_from_document_info_xml(xml_text: str) -> List[str]:
    if not xml_text:
        return []
    keywords: List[str] = []

    try:
        root = ET.fromstring(xml_text)
        for elem in root.findall(".//artkwds//impx"):
            if (elem.attrib.get("type") or "").upper() == "KEYWORD":
                kw = normalize_keyword("".join(elem.itertext()))
                if kw:
                    keywords.append(kw)
        if not keywords:
            for elem in root.findall(".//artkwds//*"):
                kw = normalize_keyword("".join(elem.itertext()))
                if kw:
                    keywords.append(kw)
    except Exception:
        for match in re.finditer(
            r'<impx[^>]*type=["\']KEYWORD["\'][^>]*>(.*?)</impx>',
            xml_text,
            flags=re.IGNORECASE | re.DOTALL,
        ):
            kw = normalize_keyword(match.group(1))
            if kw:
                keywords.append(kw)

    return unique_preserve_order(keywords)


def extract_keywords_from_abstract_html(abstract_html: str) -> List[str]:
    if not abstract_html:
        return []
    hits: List[str] = []
    for match in re.finditer(
        r'<div[^>]+class=["\'][^"\']*\bartkwds\b[^"\']*["\'][^>]*>(.*?)</div>',
        abstract_html,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        hits.extend(split_keyword_line(match.group(1)))
    return unique_preserve_order(hits)


def extract_article_keywords(record: Dict[str, Any]) -> Tuple[List[str], str]:
    for field in ["keywords", "kwds", "art_kwds", "keywordList"]:
        value = record.get(field)
        if isinstance(value, list):
            kws = unique_preserve_order([normalize_keyword(str(v)) for v in value if normalize_keyword(str(v))])
            if kws:
                return kws, field
        if isinstance(value, str):
            kws = split_keyword_line(value)
            if kws:
                return kws, field

    xml_text = record.get("documentInfoXML") or record.get("documentMetaXML") or ""
    if isinstance(xml_text, str):
        kws = extract_keywords_from_document_info_xml(xml_text)
        if kws:
            return kws, "documentInfoXML/artkwds"

    abstract_html = record.get("abstract") or ""
    if isinstance(abstract_html, str):
        kws = extract_keywords_from_abstract_html(abstract_html)
        if kws:
            return kws, "abstract_html/div.artkwds"

    return [], ""


def flatten_record(job: Dict[str, Any], record: Dict[str, Any], source_file: str) -> Dict[str, Any]:
    keywords, keyword_source = extract_article_keywords(record)
    abstract_value = get_nested(record, ["abstract", "abstractText", "abs"])

    return {
        "journal_id": job["journal_id"],
        "journal_label": job["journal_label"],
        "pep_code_candidate": job.get("pep_code_candidate") or "",
        "probe_year": job["year"] if job["year"] is not None else "",
        "document_id": get_nested(record, ["documentID", "id", "art_id"]) or "",
        "pep_code_record": get_nested(record, ["PEPCode", "pepCode"]) or "",
        "year_record": get_nested(record, ["year", "pubYear", "publicationYear"]) or "",
        "title": get_nested(record, ["title", "articleTitle"]) or "",
        "authors": get_nested(record, ["authorMast", "authors", "author", "creator"]) or "",
        "source_title": get_nested(record, ["sourceTitle", "journalTitle", "publicationTitle"]) or "",
        "volume": get_nested(record, ["volume", "vol"]) or "",
        "issue": get_nested(record, ["issue", "issueNo"]) or "",
        "pages": get_nested(record, ["pages", "pageRange"]) or "",
        "doi": get_nested(record, ["doi", "DOI"]) or "",
        "article_type": get_nested(record, ["articleType", "documentType", "type"]) or "",
        "has_abstract": bool(abstract_value),
        "has_keywords": bool(keywords),
        "n_keywords": len(keywords),
        "keywords_joined": "; ".join(keywords),
        "keyword_source": keyword_source,
        "art_kwds_count": get_nested(record, ["stat", "art_kwds_count"]) or "",
        "source_file": source_file,
    }


def write_flat_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "journal_id", "journal_label", "pep_code_candidate", "probe_year",
        "document_id", "pep_code_record", "year_record", "title", "authors",
        "source_title", "volume", "issue", "pages", "doi", "article_type",
        "has_abstract", "has_keywords", "n_keywords", "keywords_joined",
        "keyword_source", "art_kwds_count", "source_file",
    ]
    if rows:
        for key in rows[0].keys():
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def append_flat_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    fieldnames = list(rows[0].keys())
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerows(rows)


def append_log_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists() and path.stat().st_size > 0
    fieldnames = list(rows[0].keys())
    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not exists:
            writer.writeheader()
        writer.writerows(rows)


def safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="PEP-Web metadata probe for psychoanalytic_core.")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--env", default=str(DEFAULT_ENV))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--log", default=str(DEFAULT_LOG))
    parser.add_argument("--flat-csv", default=str(DEFAULT_FLAT_CSV))
    parser.add_argument("--journal", action="append", help="Journal id, e.g. ijpa. Can be repeated.")
    parser.add_argument("--year", action="append", type=int, help="Year, e.g. 2020. Can be repeated.")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--delay", type=float, default=3.0)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--diagnose", action="store_true")
    parser.add_argument("--facetquery", help="Override generated facetquery, e.g. art_id:IJP.101.0013A")
    parser.add_argument("--append-flat-csv", action="store_true")
    parser.add_argument("--write-run-csv", action="store_true")
    args = parser.parse_args(argv)

    env_path = Path(args.env)
    load_env_file(env_path)

    headers = build_headers()
    if args.diagnose:
        print(json.dumps(
            {"safe_env_header_diagnostics": safe_env_header_diagnostics(env_path, headers)},
            ensure_ascii=False,
            indent=2,
        ))

    jobs = make_jobs(args.journal, args.year)
    out_dir = Path(args.out_dir)
    log_path = Path(args.log)
    flat_csv = Path(args.flat_csv)

    session = requests.Session()
    session.headers.update(headers)

    all_rows: List[Dict[str, Any]] = []
    log_rows: List[Dict[str, Any]] = []

    for idx, job in enumerate(jobs, start=1):
        params = make_params(job, limit=args.limit, offset=0)
        if args.facetquery:
            params["facetquery"] = args.facetquery

        pep_part = job.get("pep_code_candidate") or "nopep"
        year_part = str(job["year"]) if job["year"] is not None else "allyears"
        raw_name = f"{job['journal_id']}_{safe_filename(pep_part)}_{safe_filename(year_part)}.json"
        if args.facetquery:
            raw_name = f"{job['journal_id']}_{safe_filename(pep_part)}_{safe_filename(year_part)}_{safe_filename(args.facetquery)[:80]}.json"
        raw_path = out_dir / raw_name

        if args.dry_run:
            print(json.dumps({
                "endpoint": args.endpoint,
                "params": params,
                "raw_path": str(raw_path),
            }, ensure_ascii=False, indent=2))
            continue

        error = ""
        status_code = 0
        response_headers: Dict[str, str] = {}
        payload: Any = None
        text = ""

        try:
            status_code, response_headers, payload, text = request_json(
                session=session,
                endpoint=args.endpoint,
                params=params,
                timeout=args.timeout,
            )
        except Exception as exc:
            error = repr(exc)

        if args.diagnose:
            print(json.dumps({
                "request_diagnostics": {
                    "journal_id": job["journal_id"],
                    "pep_code_candidate": job.get("pep_code_candidate") or "",
                    "year": job["year"],
                    "status_code": status_code,
                    "params": params,
                    "payload_shape": payload_shape(payload),
                    "error": error,
                }
            }, ensure_ascii=False, indent=2))

        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_record = {
            "endpoint": args.endpoint,
            "params": params,
            "status_code": status_code,
            "response_headers_subset": {
                "content-type": response_headers.get("content-type", ""),
                "content-length": response_headers.get("content-length", ""),
            },
            "payload": payload,
            "text": None if payload is not None else text,
            "error": error,
        }
        raw_path.write_text(json.dumps(raw_record, ensure_ascii=False, indent=2), encoding="utf-8")

        records = extract_document_list(payload)
        for record in records:
            all_rows.append(flatten_record(job, record, source_file=str(raw_path.relative_to(PROJECT_ROOT))))

        log_rows.append({
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "journal_id": job["journal_id"],
            "probe_year": job["year"] if job["year"] is not None else "",
            "endpoint": args.endpoint,
            "params_json": json.dumps(params, ensure_ascii=False),
            "status_code": status_code,
            "n_records": len(records),
            "raw_path": str(raw_path.relative_to(PROJECT_ROOT)),
            "error": error,
        })

        if idx < len(jobs):
            time.sleep(args.delay)

    if not args.dry_run:
        if args.append_flat_csv:
            append_flat_csv(flat_csv, all_rows)
            print(f"Appended flattened probe CSV: {flat_csv}")
        else:
            write_flat_csv(flat_csv, all_rows)
            print(f"Wrote flattened probe CSV: {flat_csv}")

        if args.write_run_csv and all_rows:
            run_dir = PROJECT_ROOT / "data" / "source_recon" / "probe_runs"
            run_dir.mkdir(parents=True, exist_ok=True)
            journal_part = safe_filename("_".join(args.journal or ["all_journals"]))
            year_part = safe_filename("_".join(str(y) for y in (args.year or ["all_years"])))
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            run_csv = run_dir / f"pep_probe_{journal_part}_{year_part}_{stamp}.csv"
            write_flat_csv(run_csv, all_rows)
            print(f"Wrote per-run probe CSV: {run_csv}")

        append_log_csv(log_path, log_rows)
        print(f"Wrote log CSV: {log_path}")
        print(f"Raw JSON directory: {out_dir}")
        print(f"Flattened records: {len(all_rows)}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
