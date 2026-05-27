#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
1b_pep_article_detail_probe.py

PEP-Web article-level metadata/detail probe for data_psychoanalytic_core.

Purpose
-------
Given one PEP article id, for example IJP.101.0013A, try a small set of
article-detail endpoint candidates and save raw responses for inspection.

This script is intentionally conservative:
- it does not download PDFs;
- it does not mirror full text;
- it writes raw API responses only for narrowly scoped probe requests;
- it never prints credentials or header values;
- it can search returned payloads for expected article keywords.

Known case
----------
IJP.101.0013A has visible article keywords on the article/PDF first page:

Paradigms, incommensurability, common ground, communication, redescription

The Search API record reports stat.art_kwds_count = 1 but does not expose
the keyword text in the flattened Search API record. This script helps identify
which article-level endpoint, if any, exposes those values.

Credentials
-----------
Put local values in data_psychoanalytic_core/.env.pep, not in this script.

Supported .env names:
PEP_CLIENT_ID=...
PEP_CLIENT_SESSION=...
PEP_X_API_AUTHORIZE=...
PEP_X_PEP_AUTH=...
PEP_ORIGIN=...
PEP_REFERER=...

Optional generic variants:
PEP_AUTH_HEADER=...
PEP_AUTH_BEARER=...
PEP_COOKIE=...
ANDROMEDA_CONTACT_EMAIL=...
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_ENDPOINT = "https://api.pep-web.org/v2/Database/Search/"
DEFAULT_ENV = PROJECT_ROOT / ".env.pep"
DEFAULT_OUT_DIR = PROJECT_ROOT / "data" / "raw_pep_metadata" / "article_detail_probe"
DEFAULT_LOG = PROJECT_ROOT / "data" / "logs" / "pep_article_detail_probe_log.csv"
DEFAULT_SUMMARY = PROJECT_ROOT / "data" / "source_recon" / "pep_article_detail_probe_summary.csv"

USER_AGENT = (
    "AndromedaNowickaBibliometricBot/0.4 "
    "(metadata-only bibliometric research; no PDF mirroring; polite delay)"
)

DEFAULT_EXPECTED_TERMS = [
    "Paradigms",
    "incommensurability",
    "common ground",
    "communication",
    "redescription",
]


def load_env(path: Path) -> None:
    """Load simple KEY=value pairs from .env without external dependency."""
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def build_headers() -> Dict[str, str]:
    headers: Dict[str, str] = {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, text/plain, */*",
    }

    contact = os.environ.get("ANDROMEDA_CONTACT_EMAIL")
    if contact:
        headers["From"] = contact

    auth_header = os.environ.get("PEP_AUTH_HEADER")
    bearer = os.environ.get("PEP_AUTH_BEARER")
    cookie = os.environ.get("PEP_COOKIE")

    if auth_header:
        headers["Authorization"] = auth_header
    elif bearer:
        headers["Authorization"] = f"Bearer {bearer}"

    if cookie:
        headers["Cookie"] = cookie

    pep_header_map = {
        "PEP_CLIENT_ID": "client-id",
        "PEP_CLIENT_SESSION": "client-session",
        "PEP_X_API_AUTHORIZE": "x-api-authorize",
        "PEP_X_PEP_AUTH": "x-pep-auth",
        "PEP_ORIGIN": "origin",
        "PEP_REFERER": "referer",
    }
    for env_name, header_name in pep_header_map.items():
        value = os.environ.get(env_name)
        if value:
            headers[header_name] = value

    return headers


def safe_header_diagnostics(env_path: Path, headers: Dict[str, str]) -> Dict[str, Any]:
    return {
        "env_path": str(env_path),
        "env_exists": env_path.exists(),
        "has_PEP_CLIENT_ID": bool(os.environ.get("PEP_CLIENT_ID")),
        "has_PEP_CLIENT_SESSION": bool(os.environ.get("PEP_CLIENT_SESSION")),
        "has_PEP_X_API_AUTHORIZE": bool(os.environ.get("PEP_X_API_AUTHORIZE")),
        "has_PEP_X_PEP_AUTH": bool(os.environ.get("PEP_X_PEP_AUTH")),
        "has_PEP_ORIGIN": bool(os.environ.get("PEP_ORIGIN")),
        "has_PEP_REFERER": bool(os.environ.get("PEP_REFERER")),
        "has_PEP_AUTH_HEADER": bool(os.environ.get("PEP_AUTH_HEADER")),
        "has_PEP_AUTH_BEARER": bool(os.environ.get("PEP_AUTH_BEARER")),
        "has_PEP_COOKIE": bool(os.environ.get("PEP_COOKIE")),
        "sends_client_id_header": "client-id" in headers,
        "sends_client_session_header": "client-session" in headers,
        "sends_x_api_authorize_header": "x-api-authorize" in headers,
        "sends_x_pep_auth_header": "x-pep-auth" in headers,
        "sends_origin_header": "origin" in headers,
        "sends_referer_header": "referer" in headers,
        "sends_Authorization_header": "Authorization" in headers,
        "sends_Cookie_header": "Cookie" in headers,
    }


def make_endpoint_candidates(api_base: str, art_id: str) -> List[Dict[str, Any]]:
    """Return conservative endpoint candidates.

    The confirmed baseline is Database/Search with facetquery=art_id:<ID>.
    Other candidates are intentionally exploratory and may return 404/400.
    They are used only in small single-article probe runs.
    """
    api_base = api_base.rstrip("/")
    quoted = quote(art_id, safe="")

    return [
        {
            "candidate": "search_by_art_id",
            "method": "GET",
            "url": api_base + "/",
            "params": {
                "facetquery": f"art_id:{art_id}",
                "formatrequested": "JSON",
                "abstract": "true",
                "limit": "1",
                "offset": "0",
                "synonyms": "false",
            },
        },
        {
            "candidate": "document_by_art_id_path",
            "method": "GET",
            "url": f"{api_base.rsplit('/Database/Search', 1)[0]}/Documents/{quoted}",
            "params": {"formatrequested": "JSON"},
        },
        {
            "candidate": "document_info_by_art_id_path",
            "method": "GET",
            "url": f"{api_base.rsplit('/Database/Search', 1)[0]}/Documents/{quoted}/Info",
            "params": {"formatrequested": "JSON"},
        },
        {
            "candidate": "document_metadata_query",
            "method": "GET",
            "url": f"{api_base.rsplit('/Database/Search', 1)[0]}/Document/Metadata/",
            "params": {"documentID": art_id, "formatrequested": "JSON"},
        },
        {
            "candidate": "document_info_query",
            "method": "GET",
            "url": f"{api_base.rsplit('/Database/Search', 1)[0]}/Document/Info/",
            "params": {"documentID": art_id, "formatrequested": "JSON"},
        },
        {
            "candidate": "document_by_art_id_query",
            "method": "GET",
            "url": f"{api_base.rsplit('/Database/Search', 1)[0]}/Document/",
            "params": {"documentID": art_id, "formatrequested": "JSON"},
        },
    ]


def response_shape(payload: Any, text: str) -> Dict[str, Any]:
    if isinstance(payload, dict):
        out: Dict[str, Any] = {
            "payload_type": "dict",
            "top_level_keys": list(payload.keys())[:40],
        }
        for key in [
            "documentList", "responseSet", "responseInfo", "documents",
            "results", "count", "fullCount", "total", "error", "message",
            "detail", "document", "metadata", "article", "keywords",
            "kwds", "glossary", "documentInfoXML", "documentMetaXML",
        ]:
            val = payload.get(key)
            if isinstance(val, dict):
                out[f"{key}_keys"] = list(val.keys())[:40]
            elif isinstance(val, list):
                out[f"{key}_list_len"] = len(val)
            elif val is not None:
                out[key] = str(val)[:300]
        return out
    if isinstance(payload, list):
        return {"payload_type": "list", "list_len": len(payload)}
    return {"payload_type": "non_json", "text_preview": text[:300]}


def parse_json_or_none(resp: requests.Response) -> Tuple[Optional[Any], str]:
    text = resp.text or ""
    try:
        return resp.json(), text
    except Exception:
        return None, text


def save_payload(path: Path, status_code: int, url: str, params: Dict[str, Any], payload: Any, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "status_code": status_code,
        "url": url,
        "params": params,
        "payload": payload,
        "text": None if payload is not None else text,
    }
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")


def contains_terms(raw_text: str, terms: List[str]) -> Dict[str, bool]:
    low = raw_text.lower()
    return {term: (term.lower() in low) for term in terms}


def detect_possible_keyword_fields(obj: Any, prefix: str = "") -> List[str]:
    """Find field paths whose names suggest keyword/glossary/kwd content."""
    hits: List[str] = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            path = f"{prefix}.{k}" if prefix else str(k)
            lk = str(k).lower()
            if any(token in lk for token in ["keyword", "kwd", "glossary", "term", "art_kwd"]):
                preview = ""
                if isinstance(v, (str, int, float, bool)) or v is None:
                    preview = f" = {str(v)[:150]}"
                elif isinstance(v, list):
                    preview = f" [list len={len(v)}]"
                elif isinstance(v, dict):
                    preview = f" [dict keys={list(v.keys())[:10]}]"
                hits.append(path + preview)
            hits.extend(detect_possible_keyword_fields(v, path))
    elif isinstance(obj, list):
        for idx, item in enumerate(obj[:50]):
            hits.extend(detect_possible_keyword_fields(item, f"{prefix}[{idx}]"))
    return hits


def append_csv(path: Path, row: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(row.keys()))
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="PEP article-detail metadata probe.")
    parser.add_argument("--art-id", required=True, help="PEP article id, e.g. IJP.101.0013A")
    parser.add_argument("--endpoint", default=os.environ.get("PEP_API_ENDPOINT", DEFAULT_ENDPOINT))
    parser.add_argument("--env", default=str(DEFAULT_ENV))
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR))
    parser.add_argument("--log", default=str(DEFAULT_LOG))
    parser.add_argument("--summary-csv", default=str(DEFAULT_SUMMARY))
    parser.add_argument("--delay", type=float, default=3.0)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--diagnose", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--expected-term",
        action="append",
        default=None,
        help="Expected term to search in response. Can be repeated.",
    )
    parser.add_argument(
        "--search-default-terms",
        action="store_true",
        help="Search known IJP.101.0013A expected keywords.",
    )
    args = parser.parse_args(argv)

    env_path = Path(args.env)
    load_env(env_path)
    headers = build_headers()

    if args.diagnose:
        print(json.dumps({"safe_env_header_diagnostics": safe_header_diagnostics(env_path, headers)}, ensure_ascii=False, indent=2))

    terms: List[str] = []
    if args.search_default_terms:
        terms.extend(DEFAULT_EXPECTED_TERMS)
    if args.expected_term:
        terms.extend(args.expected_term)

    out_dir = Path(args.out_dir)
    log_path = Path(args.log)
    summary_csv = Path(args.summary_csv)

    session = requests.Session()
    session.headers.update(headers)

    candidates = make_endpoint_candidates(args.endpoint, args.art_id)

    if args.dry_run:
        print(json.dumps({"art_id": args.art_id, "candidates": candidates}, ensure_ascii=False, indent=2))
        return 0

    for idx, candidate in enumerate(candidates, start=1):
        label = candidate["candidate"]
        url = candidate["url"]
        params = candidate["params"]

        status_code = ""
        error = ""
        payload = None
        text = ""
        try:
            resp = session.get(url, params=params, timeout=args.timeout)
            status_code = resp.status_code
            payload, text = parse_json_or_none(resp)
        except Exception as exc:
            error = repr(exc)

        raw_text = json.dumps(payload, ensure_ascii=False) if payload is not None else text
        term_hits = contains_terms(raw_text, terms) if terms else {}
        possible_fields = detect_possible_keyword_fields(payload) if payload is not None else []

        safe_art_id = re.sub(r"[^A-Za-z0-9_.-]+", "_", args.art_id)
        raw_path = out_dir / f"{safe_art_id}_{idx:02d}_{label}.json"
        save_payload(raw_path, int(status_code) if status_code else 0, url, params, payload, text)

        if args.diagnose:
            print(json.dumps({
                "candidate_diagnostics": {
                    "candidate": label,
                    "status_code": status_code,
                    "url": url,
                    "params": params,
                    "response_shape": response_shape(payload, text),
                    "term_hits": term_hits,
                    "possible_keyword_fields": possible_fields[:40],
                    "raw_path": str(raw_path.relative_to(PROJECT_ROOT)),
                    "error": error,
                }
            }, ensure_ascii=False, indent=2))

        append_csv(log_path, {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "art_id": args.art_id,
            "candidate": label,
            "url": url,
            "params_json": json.dumps(params, ensure_ascii=False),
            "status_code": status_code,
            "raw_path": str(raw_path.relative_to(PROJECT_ROOT)),
            "term_hits_json": json.dumps(term_hits, ensure_ascii=False),
            "possible_keyword_fields_count": len(possible_fields),
            "error": error,
        })

        append_csv(summary_csv, {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "art_id": args.art_id,
            "candidate": label,
            "status_code": status_code,
            "has_payload_json": payload is not None,
            "contains_any_expected_term": any(term_hits.values()) if term_hits else "",
            "term_hits_json": json.dumps(term_hits, ensure_ascii=False),
            "possible_keyword_fields_preview": " | ".join(possible_fields[:10]),
            "raw_path": str(raw_path.relative_to(PROJECT_ROOT)),
            "error": error,
        })

        if idx < len(candidates):
            time.sleep(args.delay)

    print(f"Wrote raw candidate responses to: {out_dir}")
    print(f"Wrote log CSV: {log_path}")
    print(f"Wrote summary CSV: {summary_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
