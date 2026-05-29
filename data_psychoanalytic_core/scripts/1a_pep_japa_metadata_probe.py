#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1a_pep_japa_metadata_probe.py

Andromeda Nowicka v0.4 — PEP-Web metadata reconnaissance probe for JAPA.

Purpose
-------
Small, auditable, metadata-first probe for:
    Journal of the American Psychoanalytic Association (JAPA)
    PEP prefix: APA

The script:
- queries the PEP-Web Search API for selected sample years,
- saves raw JSON responses for audit,
- exports article-level metadata CSV,
- exports keyword-long CSV,
- exports request log CSV,
- writes a small JSON summary,
- optionally checks one control article: APA.068.0583A.

It does NOT download PDFs and does NOT mirror full text.

Expected local file
-------------------
Create a local file not committed to git:

    .env.pep

Example:

    PEP_COOKIE="..."
    PEP_AUTHORIZATION="Bearer ..."
    PEP_FROM="your.email@example.org"

Depending on the current PEP session/API setup, cookie and/or authorization
may be needed. Do not commit .env.pep, cookies, tokens, or session headers.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import os
import re
import sys
import time
import uuid
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests


SCRIPT_VERSION = "v0.1.0"
DEFAULT_ENDPOINT = "https://api.pep-web.org/v2/Database/Search/"
DEFAULT_JOURNAL_KEY = "japa"
DEFAULT_JOURNAL_TITLE = "Journal of the American Psychoanalytic Association"
DEFAULT_PEP_PREFIX = "APA"
DEFAULT_SAMPLE_YEARS = [1953, 1970, 1990, 2005, 2020]
DEFAULT_LIMIT = 20
DEFAULT_DELAY_SECONDS = 5.0

CONTROL_ARTICLE_ID = "APA.068.0583A"
CONTROL_EXPECTED = {
    "year": "2020",
    "volume": "68",
    "pages": "583-613",
    "title_contains": "Consenting and Assenting to Psychoanalytic Work",
    "keywords": {
        "informed consent",
        "framework",
        "ethics",
        "good-enough assenting",
        "professional guidelines",
    },
}


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def load_env_file(path: Path) -> Dict[str, str]:
    """
    Minimal .env parser. Avoids adding python-dotenv dependency.
    Supports:
        KEY=value
        KEY="value"
        KEY='value'
    Ignores blank lines and comments.
    """
    values: Dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def build_headers(env: Dict[str, str]) -> Dict[str, str]:
    contact = env.get("PEP_FROM") or os.environ.get("PEP_FROM") or "CONTACT_EMAIL"
    user_agent = (
        "AndromedaNowickaBibliometricBot/0.4 "
        f"(metadata-only bibliometric research; contact: {contact}; "
        "no PDF mirroring; polite delay)"
    )
    headers = {
        "User-Agent": user_agent,
        "From": contact,
        "Accept": "application/json,text/plain,*/*",
        "Accept-Language": "en-US,en;q=0.9,pl;q=0.8",
    }

    cookie = env.get("PEP_COOKIE") or os.environ.get("PEP_COOKIE")
    authorization = env.get("PEP_AUTHORIZATION") or os.environ.get("PEP_AUTHORIZATION")
    x_api_key = env.get("PEP_API_KEY") or os.environ.get("PEP_API_KEY")

    if cookie:
        headers["Cookie"] = cookie
    if authorization:
        headers["Authorization"] = authorization
    if x_api_key:
        headers["x-api-key"] = x_api_key

    return headers


def ensure_dirs(base_dir: Path) -> Dict[str, Path]:
    dirs = {
        "base": base_dir,
        "raw": base_dir / "raw_json",
        "logs": base_dir / "logs",
        "tables": base_dir / "tables",
        "summary": base_dir / "summary",
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def first_present(record: Dict[str, Any], candidates: Iterable[str]) -> Any:
    for key in candidates:
        if key in record and record[key] not in (None, "", []):
            return record[key]
    return None


def as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(as_text(x) for x in value if as_text(x))
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).strip()


def clean_text(value: Any) -> str:
    text = as_text(value)
    if not text:
        return ""
    text = html.unescape(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_keyword(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<[^>]+>", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip(" \t\r\n;,.:")


def maybe_parse_json_response(resp: requests.Response) -> Any:
    try:
        return resp.json()
    except Exception:
        return {
            "_non_json_response": True,
            "status_code": resp.status_code,
            "text_preview": resp.text[:2000],
        }


def find_records(payload: Any) -> List[Dict[str, Any]]:
    """
    PEP API response shapes may vary. This recursively finds plausible article records.
    It prefers lists of dicts containing article-like keys.
    """
    article_keys = {
        "art_id", "articleID", "documentID", "document_id", "pepCode",
        "title", "articleTitle", "source_title", "sourceTitle", "year",
    }

    candidates: List[List[Dict[str, Any]]] = []

    def walk(obj: Any) -> None:
        if isinstance(obj, list):
            dicts = [x for x in obj if isinstance(x, dict)]
            if dicts:
                score = sum(len(article_keys.intersection(d.keys())) for d in dicts[:10])
                if score > 0:
                    candidates.append(dicts)
            for item in obj[:5]:
                walk(item)
        elif isinstance(obj, dict):
            for value in obj.values():
                walk(value)

    walk(payload)

    if not candidates:
        return []

    # Choose the list with the best article-key density and length.
    candidates.sort(
        key=lambda lst: (
            sum(len(article_keys.intersection(d.keys())) for d in lst[:20]),
            len(lst),
        ),
        reverse=True,
    )
    return candidates[0]


def extract_document_info_xml(record: Dict[str, Any]) -> str:
    value = first_present(
        record,
        [
            "documentInfoXML",
            "document_info_xml",
            "documentInfoXml",
            "documentInfo",
            "frontMatterXML",
            "front_matter_xml",
        ],
    )
    return as_text(value)


def extract_keywords_from_xml(xml_text: str) -> List[str]:
    """
    Extracts keywords from PEP documentInfoXML/front matter if present.

    Known useful pattern from IJPA/JAPA recon:
        artkwds / impx type="KEYWORD"

    This parser is intentionally forgiving.
    """
    if not xml_text:
        return []

    # Sometimes XML is embedded as escaped text.
    xml_text = html.unescape(xml_text).strip()
    if not xml_text:
        return []

    keywords: List[str] = []

    # Regex fallback first: robust to namespace/broken XML.
    for match in re.finditer(
        r"<impx\b[^>]*type=[\"']KEYWORD[\"'][^>]*>(.*?)</impx>",
        xml_text,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        kw = normalize_keyword(match.group(1))
        if kw:
            keywords.append(kw)

    if keywords:
        return dedupe_preserve_order(keywords)

    # XML parse fallback.
    try:
        root = ET.fromstring(xml_text)
    except Exception:
        return []

    for elem in root.iter():
        tag = elem.tag.split("}")[-1].lower()
        attrib_type = (elem.attrib.get("type") or elem.attrib.get("Type") or "").lower()
        if tag == "impx" and attrib_type == "keyword":
            kw = normalize_keyword("".join(elem.itertext()))
            if kw:
                keywords.append(kw)

    return dedupe_preserve_order(keywords)


def extract_keywords_from_html(value: Any) -> List[str]:
    """
    Fallback for PEP records where abstract/front matter includes HTML.
    Looks for div.artkwds and simple keyword-like separators.
    """
    text = as_text(value)
    if not text:
        return []
    text = html.unescape(text)

    blocks = re.findall(
        r"<div[^>]+class=[\"'][^\"']*artkwds[^\"']*[\"'][^>]*>(.*?)</div>",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    keywords: List[str] = []
    for block in blocks:
        block_text = clean_text(block)
        # Remove common labels.
        block_text = re.sub(r"^(keywords?|key words?)\s*[:：]\s*", "", block_text, flags=re.I)
        parts = re.split(r"\s*[,;]\s*", block_text)
        for part in parts:
            kw = normalize_keyword(part)
            if kw:
                keywords.append(kw)

    return dedupe_preserve_order(keywords)


def dedupe_preserve_order(values: Iterable[str]) -> List[str]:
    seen = set()
    out = []
    for value in values:
        key = value.casefold()
        if value and key not in seen:
            seen.add(key)
            out.append(value)
    return out


def extract_keywords(record: Dict[str, Any]) -> Tuple[List[str], str]:
    direct = first_present(record, ["keywords", "keyword", "keyWords", "kwds", "terms"])
    if direct:
        if isinstance(direct, list):
            kws = [normalize_keyword(as_text(x)) for x in direct]
        else:
            kws = [normalize_keyword(x) for x in re.split(r"\s*[,;]\s*", as_text(direct))]
        kws = dedupe_preserve_order([x for x in kws if x])
        if kws:
            return kws, "direct_field"

    xml_text = extract_document_info_xml(record)
    kws = extract_keywords_from_xml(xml_text)
    if kws:
        return kws, "documentInfoXML_artkwds"

    abstract_like = first_present(record, ["abstract", "abstractHTML", "abstract_text", "summary"])
    kws = extract_keywords_from_html(abstract_like)
    if kws:
        return kws, "abstract_html_artkwds"

    return [], "not_found"


def extract_abstract(record: Dict[str, Any]) -> str:
    value = first_present(record, ["abstractText", "abstract_text", "abstract", "summary"])
    if not value:
        return ""
    text = as_text(value)

    # Remove keyword block if embedded in HTML.
    text = re.sub(
        r"<div[^>]+class=[\"'][^\"']*artkwds[^\"']*[\"'][^>]*>.*?</div>",
        " ",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    return clean_text(text)


def extract_article_row(
    record: Dict[str, Any],
    *,
    journal_key: str,
    journal_title: str,
    pep_prefix: str,
    query_year: Optional[int],
    run_id: str,
) -> Tuple[Dict[str, Any], List[str], str]:
    document_id = as_text(
        first_present(
            record,
            ["art_id", "document_id", "documentID", "articleID", "article_id", "pepCode", "id"],
        )
    )

    title = clean_text(first_present(record, ["title", "articleTitle", "article_title", "art_title"]))
    authors = clean_text(first_present(record, ["authors", "author", "authorList", "author_names"]))
    year = as_text(first_present(record, ["year", "year_record", "publicationYear", "pubYear"]))
    volume = as_text(first_present(record, ["volume", "vol"]))
    issue_number = as_text(first_present(record, ["issue", "issue_number", "issueNumber"]))
    pages = clean_text(first_present(record, ["pages", "pageRange", "page_range"]))
    doi = clean_text(first_present(record, ["doi", "DOI"]))
    source_title = clean_text(first_present(record, ["source_title", "sourceTitle", "journal", "journalTitle"]))
    article_type = clean_text(first_present(record, ["article_type", "articleType", "documentType", "type"]))
    url = clean_text(first_present(record, ["url", "article_url", "documentUrl", "link"]))

    abstract_text = extract_abstract(record)
    keywords, keyword_source = extract_keywords(record)

    row = {
        "run_id": run_id,
        "journal_key": journal_key,
        "journal_title": journal_title,
        "pep_prefix": pep_prefix,
        "query_year": query_year,
        "article_id": document_id,
        "article_url": url,
        "year": year,
        "volume": volume,
        "issue_number": issue_number,
        "title": title,
        "authors": authors,
        "source_title": source_title,
        "pages": pages,
        "doi": doi,
        "article_type": article_type,
        "abstract_available": bool(abstract_text),
        "abstract_text": abstract_text,
        "n_keywords": len(keywords),
        "keyword_extraction_source": keyword_source,
        "raw_record_keys": ";".join(sorted(record.keys())),
    }
    return row, keywords, keyword_source


def build_search_payload(pep_prefix: str, year: Optional[int], limit: int, offset: int = 0) -> Dict[str, Any]:
    # Confirmed pattern from prior recon: art_id:IJP.* AND year:2020.
    # For JAPA/APA we use art_id:APA.*.
    facetquery = f"art_id:{pep_prefix}.*"
    if year is not None:
        facetquery += f" AND year:{year}"

    # PEP API versions may accept different parameter names; this payload keeps
    # the known facetquery explicit and includes conservative paging hints.
    return {
        "facetquery": facetquery,
        "limit": limit,
        "offset": offset,
        "from": offset,
        "size": limit,
        "sort": "year asc",
    }


def request_search(
    session: requests.Session,
    endpoint: str,
    payload: Dict[str, Any],
    timeout: int = 60,
) -> requests.Response:
    # POST is the likely mode for the PEP search endpoint.
    resp = session.post(endpoint, json=payload, timeout=timeout)
    if resp.status_code in {400, 405}:
        # Fallback to GET for endpoint variants.
        resp = session.get(endpoint, params=payload, timeout=timeout)
    return resp


def write_csv(path: Path, rows: List[Dict[str, Any]], fieldnames: List[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT)
    parser.add_argument("--journal-key", default=DEFAULT_JOURNAL_KEY)
    parser.add_argument("--journal-title", default=DEFAULT_JOURNAL_TITLE)
    parser.add_argument("--pep-prefix", default=DEFAULT_PEP_PREFIX)
    parser.add_argument("--years", nargs="+", type=int, default=DEFAULT_SAMPLE_YEARS)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--delay", type=float, default=DEFAULT_DELAY_SECONDS)
    parser.add_argument("--env-file", default=".env.pep")
    parser.add_argument(
        "--out-dir",
        default="data_psychoanalytic_core/data/source_recon/japa_probe",
    )
    parser.add_argument(
        "--control-article-id",
        default=CONTROL_ARTICLE_ID,
        help="Optional control article ID to query separately; use empty string to skip.",
    )
    args = parser.parse_args()

    run_id = f"pep_{args.journal_key}_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    dirs = ensure_dirs(Path(args.out_dir))

    env = load_env_file(Path(args.env_file))
    headers = build_headers(env)

    session = requests.Session()
    session.headers.update(headers)

    article_rows: List[Dict[str, Any]] = []
    keyword_rows: List[Dict[str, Any]] = []
    log_rows: List[Dict[str, Any]] = []

    def process_query(label: str, year: Optional[int], extra_payload: Optional[Dict[str, Any]] = None) -> None:
        payload = build_search_payload(args.pep_prefix, year, args.limit)
        if extra_payload:
            payload.update(extra_payload)

        started = utc_now_iso()
        status_code = None
        error = ""
        n_records = 0
        raw_path = dirs["raw"] / f"{safe_filename(label)}.json"

        try:
            resp = request_search(session, args.endpoint, payload)
            status_code = resp.status_code
            parsed = maybe_parse_json_response(resp)
            raw_path.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")

            if status_code >= 400:
                error = f"HTTP {status_code}"
                records = []
            else:
                records = find_records(parsed)
                n_records = len(records)

            for idx, record in enumerate(records, start=1):
                article_row, keywords, keyword_source = extract_article_row(
                    record,
                    journal_key=args.journal_key,
                    journal_title=args.journal_title,
                    pep_prefix=args.pep_prefix,
                    query_year=year,
                    run_id=run_id,
                )
                article_row["query_label"] = label
                article_row["record_order_in_query"] = idx
                article_rows.append(article_row)

                for k_idx, kw in enumerate(keywords, start=1):
                    keyword_rows.append(
                        {
                            "run_id": run_id,
                            "journal_key": args.journal_key,
                            "pep_prefix": args.pep_prefix,
                            "query_year": year,
                            "query_label": label,
                            "article_id": article_row["article_id"],
                            "article_url": article_row["article_url"],
                            "year": article_row["year"],
                            "volume": article_row["volume"],
                            "issue_number": article_row["issue_number"],
                            "title": article_row["title"],
                            "keyword_order": k_idx,
                            "keyword_raw": kw,
                            "keyword_extraction_source": keyword_source,
                        }
                    )

        except Exception as exc:
            error = repr(exc)

        finished = utc_now_iso()
        log_rows.append(
            {
                "run_id": run_id,
                "script_version": SCRIPT_VERSION,
                "query_label": label,
                "query_year": year,
                "endpoint": args.endpoint,
                "payload_json": json.dumps(payload, ensure_ascii=False, sort_keys=True),
                "started_at_utc": started,
                "finished_at_utc": finished,
                "status_code": status_code,
                "n_records_detected": n_records,
                "raw_json_path": str(raw_path),
                "error": error,
                "user_agent": headers.get("User-Agent", ""),
                "pdfs_downloaded": False,
                "full_text_mirrored": False,
            }
        )

    for year in args.years:
        label = f"{args.journal_key}_{args.pep_prefix}_{year}_limit{args.limit}"
        process_query(label=label, year=year)
        time.sleep(args.delay)

    if args.control_article_id:
        # Exact article probe. The API may or may not support exact art_id in facetquery;
        # we keep it as an auditable raw test.
        label = f"{args.journal_key}_control_{args.control_article_id}"
        process_query(
            label=label,
            year=None,
            extra_payload={
                "facetquery": f"art_id:{args.control_article_id}",
                "limit": 5,
                "size": 5,
            },
        )

    article_fieldnames = [
        "run_id", "query_label", "record_order_in_query",
        "journal_key", "journal_title", "pep_prefix", "query_year",
        "article_id", "article_url", "year", "volume", "issue_number",
        "title", "authors", "source_title", "pages", "doi", "article_type",
        "abstract_available", "abstract_text", "n_keywords",
        "keyword_extraction_source", "raw_record_keys",
    ]
    keyword_fieldnames = [
        "run_id", "journal_key", "pep_prefix", "query_year", "query_label",
        "article_id", "article_url", "year", "volume", "issue_number", "title",
        "keyword_order", "keyword_raw", "keyword_extraction_source",
    ]
    log_fieldnames = [
        "run_id", "script_version", "query_label", "query_year", "endpoint",
        "payload_json", "started_at_utc", "finished_at_utc", "status_code",
        "n_records_detected", "raw_json_path", "error", "user_agent",
        "pdfs_downloaded", "full_text_mirrored",
    ]

    articles_csv = dirs["tables"] / f"{args.journal_key}_pep_metadata_probe_articles.csv"
    keywords_csv = dirs["tables"] / f"{args.journal_key}_pep_metadata_probe_keywords_long.csv"
    log_csv = dirs["logs"] / f"{args.journal_key}_pep_metadata_probe_log.csv"
    summary_json = dirs["summary"] / f"{args.journal_key}_pep_metadata_probe_summary.json"

    write_csv(articles_csv, article_rows, article_fieldnames)
    write_csv(keywords_csv, keyword_rows, keyword_fieldnames)
    write_csv(log_csv, log_rows, log_fieldnames)

    unique_article_ids = {r["article_id"] for r in article_rows if r.get("article_id")}
    control_rows = [r for r in article_rows if r.get("article_id") == args.control_article_id]
    control_keywords = {
        r["keyword_raw"].casefold()
        for r in keyword_rows
        if r.get("article_id") == args.control_article_id and r.get("keyword_raw")
    }

    summary = {
        "run_id": run_id,
        "script_version": SCRIPT_VERSION,
        "journal_key": args.journal_key,
        "journal_title": args.journal_title,
        "pep_prefix": args.pep_prefix,
        "years": args.years,
        "limit_per_year": args.limit,
        "n_article_rows": len(article_rows),
        "n_unique_article_ids": len(unique_article_ids),
        "n_keyword_rows": len(keyword_rows),
        "n_articles_with_abstract": sum(1 for r in article_rows if r.get("abstract_available")),
        "n_articles_with_keywords": sum(1 for r in article_rows if int(r.get("n_keywords") or 0) > 0),
        "outputs": {
            "articles_csv": str(articles_csv),
            "keywords_csv": str(keywords_csv),
            "log_csv": str(log_csv),
            "summary_json": str(summary_json),
            "raw_json_dir": str(dirs["raw"]),
        },
        "control_article": {
            "article_id": args.control_article_id,
            "found": bool(control_rows),
            "n_rows": len(control_rows),
            "expected_keywords": sorted(CONTROL_EXPECTED["keywords"]),
            "observed_keywords": sorted(control_keywords),
            "missing_expected_keywords": sorted(CONTROL_EXPECTED["keywords"] - control_keywords),
        },
        "policy_flags": {
            "metadata_first": True,
            "pdfs_downloaded": False,
            "full_text_mirrored": False,
            "credentials_written_to_outputs": False,
        },
        "created_at_utc": utc_now_iso(),
    }
    summary_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
