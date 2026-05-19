#!/usr/bin/env python3
"""
Andromeda universal Crossref + landing-page metadata scraper.

Purpose
-------
This is a model scraper for bibliometric projects. It builds an article-level
corpus from Crossref DOI metadata and, optionally, visits DOI landing pages
to extract publicly exposed metadata such as author keywords.

It is intentionally conservative:
- it does not bypass paywalls;
- it does not scrape PDFs by default;
- it uses polite delays, explicit User-Agent, retries and logs;
- it preserves raw bibliographic metadata separately from later QA layers.

Expected input
--------------
A CSV file with at least:

    journal_key,journal_title,issn

Multiple ISSNs for the same journal can be represented as multiple rows.

Expected outputs
----------------
For each journal_key:

    <journal_key>_articles.csv
    <journal_key>_keywords_long.csv
    <journal_key>_scrape_log.csv
    <journal_key>_scrape_summary.json

Recommended next step
---------------------
Run the relevant QA/deduplication script before any interpretation.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


CROSSREF_API = "https://api.crossref.org/works"


@dataclass
class JournalConfig:
    journal_key: str
    journal_title: str
    issns: List[str]


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "journal"


def stable_article_id(doi: Optional[str], title: str, year: Optional[int], journal_key: str) -> str:
    if doi:
        return "doi:" + doi.lower().strip()
    raw = f"{journal_key}|{year or ''}|{title}".lower().strip()
    return "hash:" + hashlib.sha1(raw.encode("utf-8", errors="ignore")).hexdigest()[:20]


def load_journals(path: Path) -> List[JournalConfig]:
    rows: Dict[str, Dict[str, Any]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        required = {"journal_key", "journal_title", "issn"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"Missing required columns in journal config: {sorted(missing)}")
        for row in reader:
            key = row["journal_key"].strip() or slugify(row["journal_title"])
            rows.setdefault(key, {"journal_title": row["journal_title"].strip(), "issns": []})
            issn = row["issn"].strip()
            if issn and issn not in rows[key]["issns"]:
                rows[key]["issns"].append(issn)
    return [JournalConfig(k, v["journal_title"], v["issns"]) for k, v in rows.items()]


def make_session(mailto: str, user_agent_prefix: str = "AndromedaBibliometricScraper/0.2") -> requests.Session:
    s = requests.Session()
    ua = f"{user_agent_prefix} (mailto:{mailto})"
    s.headers.update({
        "User-Agent": ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json;q=0.8,*/*;q=0.7",
    })
    return s


def get_with_retries(
    session: requests.Session,
    url: str,
    *,
    params: Optional[dict] = None,
    timeout: Tuple[int, int] = (10, 30),
    tries: int = 4,
    delay: float = 1.0,
) -> requests.Response:
    last_exc: Optional[Exception] = None
    for attempt in range(1, tries + 1):
        try:
            r = session.get(url, params=params, timeout=timeout, allow_redirects=True)
            if r.status_code in {429, 500, 502, 503, 504} and attempt < tries:
                time.sleep(delay * attempt)
                continue
            return r
        except requests.RequestException as exc:
            last_exc = exc
            if attempt < tries:
                time.sleep(delay * attempt)
                continue
            raise
    if last_exc:
        raise last_exc
    raise RuntimeError("Unreachable retry state")


def extract_year(item: dict) -> Optional[int]:
    for field in ["published-print", "published-online", "published", "issued", "created"]:
        parts = item.get(field, {}).get("date-parts")
        if parts and parts[0]:
            try:
                return int(parts[0][0])
            except Exception:
                pass
    return None


def first(value: Any) -> Optional[str]:
    if isinstance(value, list) and value:
        return str(value[0])
    if value is None:
        return None
    return str(value)


def authors_to_string(item: dict) -> str:
    authors = []
    for a in item.get("author", []) or []:
        given = a.get("given", "")
        family = a.get("family", "")
        name = " ".join([given, family]).strip()
        if name:
            authors.append(name)
    return "; ".join(authors)


def crossref_query(
    session: requests.Session,
    *,
    issn: str,
    from_year: int,
    to_year: int,
    rows: int,
    max_records_per_issn: Optional[int],
    delay: float,
    mailto: str,
) -> Tuple[List[dict], List[dict]]:
    """Offset pagination. Suitable for journal-year corpora below Crossref's 10k offset limit per ISSN."""
    items: List[dict] = []
    logs: List[dict] = []
    offset = 0
    total_results: Optional[int] = None

    while True:
        if max_records_per_issn is not None and len(items) >= max_records_per_issn:
            break

        current_rows = rows
        if max_records_per_issn is not None:
            current_rows = min(rows, max_records_per_issn - len(items))
            if current_rows <= 0:
                break

        params = {
            "filter": f"issn:{issn},from-pub-date:{from_year}-01-01,until-pub-date:{to_year}-12-31,type:journal-article",
            "rows": current_rows,
            "offset": offset,
            "mailto": mailto,
            "sort": "published",
            "order": "asc",
        }

        try:
            r = get_with_retries(session, CROSSREF_API, params=params, timeout=(10, 25), tries=5, delay=delay)
            status = r.status_code
            if status != 200:
                logs.append({"event": "crossref_http_error", "issn": issn, "offset": offset, "status": status, "message": r.text[:500]})
                break
            data = r.json().get("message", {})
            if total_results is None:
                total_results = data.get("total-results")
            batch = data.get("items", []) or []
            logs.append({"event": "crossref_page_ok", "issn": issn, "offset": offset, "status": status, "n_items": len(batch), "total_results": total_results})
            if not batch:
                break
            items.extend(batch)
            offset += len(batch)
            if len(batch) < current_rows:
                break
            if offset >= 10000:
                logs.append({"event": "crossref_offset_limit_reached", "issn": issn, "offset": offset, "message": "Consider year-sliced querying for very large sources."})
                break
            time.sleep(delay)
        except Exception as exc:
            logs.append({"event": "crossref_exception", "issn": issn, "offset": offset, "message": repr(exc)})
            break

    return items, logs


def article_from_crossref(item: dict, journal_key: str, journal_title: str, issn: str) -> dict:
    title = first(item.get("title")) or ""
    doi = item.get("DOI")
    year = extract_year(item)
    article_url = item.get("URL")
    article_id = stable_article_id(doi, title, year, journal_key)
    return {
        "article_id": article_id,
        "journal_key": journal_key,
        "journal_title": journal_title,
        "issn_query": issn,
        "article_url": article_url,
        "year": year,
        "title": title,
        "authors": authors_to_string(item),
        "doi": doi,
        "publisher": item.get("publisher"),
        "container_title": first(item.get("container-title")),
        "volume": first(item.get("volume")),
        "issue_number": first(item.get("issue")),
        "pages": first(item.get("page")),
        "article_type": item.get("type"),
        "abstract_text": item.get("abstract"),
        "crossref_score": item.get("score"),
        "source": "crossref",
    }


def split_keywords(value: str) -> List[str]:
    if not value:
        return []
    value = re.sub(r"\s+", " ", value).strip()
    parts = re.split(r"\s*;\s*|\s*\|\s*", value)
    if len(parts) == 1 and "," in value and len(value) < 300:
        parts = [p.strip() for p in value.split(",")]
    return [p.strip(" .;,:") for p in parts if p.strip(" .;,:")]


def extract_keywords_from_html(html: str) -> Tuple[List[Tuple[str, str]], Dict[str, Any]]:
    """Return list of (keyword, source) and simple diagnostics."""
    soup = BeautifulSoup(html, "lxml")
    found: List[Tuple[str, str]] = []
    diag: Dict[str, Any] = {
        "has_meta_citation_keywords": False,
        "has_meta_dc_subject": False,
        "has_jsonld_keywords": False,
        "has_visible_keyword_signal": False,
    }

    meta_names = [
        ("citation_keywords", "meta:citation_keywords"),
        ("dc.subject", "meta:dc.subject"),
        ("DC.Subject", "meta:dc.subject"),
        ("keywords", "meta:keywords"),
        ("news_keywords", "meta:news_keywords"),
    ]
    for name, source in meta_names:
        for tag in soup.find_all("meta", attrs={"name": name}):
            content = tag.get("content", "")
            if content:
                if "citation_keywords" in name:
                    diag["has_meta_citation_keywords"] = True
                if "subject" in name.lower():
                    diag["has_meta_dc_subject"] = True
                for kw in split_keywords(content):
                    found.append((kw, source))

    # JSON-LD keywords/about
    import json as _json
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        try:
            data = _json.loads(script.string or "")
        except Exception:
            continue
        objs = data if isinstance(data, list) else [data]
        for obj in objs:
            if not isinstance(obj, dict):
                continue
            for key in ["keywords", "about"]:
                val = obj.get(key)
                if not val:
                    continue
                diag["has_jsonld_keywords"] = True
                if isinstance(val, str):
                    for kw in split_keywords(val):
                        found.append((kw, f"jsonld:{key}"))
                elif isinstance(val, list):
                    for entry in val:
                        if isinstance(entry, str):
                            found.append((entry.strip(), f"jsonld:{key}"))
                        elif isinstance(entry, dict):
                            name = entry.get("name")
                            if name:
                                found.append((str(name).strip(), f"jsonld:{key}.name"))

    # Conservative visible keyword block search
    keywordish = soup.find_all(attrs={"class": re.compile("keyword|subject|tag", re.I)})
    keywordish += soup.find_all(attrs={"id": re.compile("keyword|subject|tag", re.I)})
    for node in keywordish[:20]:
        text = node.get_text(" ", strip=True)
        if text and len(text) < 500:
            diag["has_visible_keyword_signal"] = True
            cleaned = re.sub(r"^(keywords?|subjects?|tags?)\s*[:\-]\s*", "", text, flags=re.I)
            for kw in split_keywords(cleaned):
                if len(kw) > 1 and not re.match(r"^(keywords?|subjects?|tags?)$", kw, re.I):
                    found.append((kw, "visible_keyword_block"))

    # Deduplicate while preserving source
    seen = set()
    out = []
    for kw, source in found:
        key = (kw.lower(), source)
        if key not in seen:
            seen.add(key)
            out.append((kw, source))
    return out, diag


def scrape_landing_page(
    session: requests.Session,
    url: Optional[str],
    delay: float,
) -> Tuple[List[Tuple[str, str]], Dict[str, Any]]:
    if not url:
        return [], {"landing_status": "missing_url"}
    try:
        r = get_with_retries(session, url, timeout=(10, 30), tries=3, delay=delay)
        diag = {"landing_status": r.status_code, "landing_final_url": r.url, "content_type": r.headers.get("Content-Type", "")}
        if r.status_code != 200 or "html" not in diag["content_type"].lower():
            return [], diag
        keywords, html_diag = extract_keywords_from_html(r.text)
        diag.update(html_diag)
        return keywords, diag
    except Exception as exc:
        return [], {"landing_status": "exception", "message": repr(exc)}


def write_csv(path: Path, rows: List[dict], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def scrape_journal(
    session: requests.Session,
    cfg: JournalConfig,
    *,
    from_year: int,
    to_year: int,
    rows: int,
    max_records_per_issn: Optional[int],
    fetch_landing_pages: bool,
    delay: float,
    mailto: str,
) -> Tuple[List[dict], List[dict], List[dict]]:
    article_rows: List[dict] = []
    keyword_rows: List[dict] = []
    logs: List[dict] = []

    for issn in cfg.issns:
        items, crossref_logs = crossref_query(
            session,
            issn=issn,
            from_year=from_year,
            to_year=to_year,
            rows=rows,
            max_records_per_issn=max_records_per_issn,
            delay=delay,
            mailto=mailto,
        )
        logs.extend([{**x, "journal_key": cfg.journal_key} for x in crossref_logs])
        for item in items:
            article_rows.append(article_from_crossref(item, cfg.journal_key, cfg.journal_title, issn))

    # Deduplicate before landing-page visits
    dedup: Dict[str, dict] = {}
    for row in article_rows:
        dedup.setdefault(row["article_id"], row)
    article_rows = list(dedup.values())

    if fetch_landing_pages:
        for row in tqdm(article_rows, desc=f"{cfg.journal_key}: landing pages", unit="article"):
            kws, diag = scrape_landing_page(session, row.get("article_url"), delay=delay)
            logs.append({"event": "landing_page_checked", "journal_key": cfg.journal_key, "article_id": row["article_id"], **diag})
            row["n_keywords"] = len(kws)
            for i, (kw, source) in enumerate(kws, start=1):
                keyword_rows.append({
                    "article_id": row["article_id"],
                    "article_url": row.get("article_url"),
                    "journal_key": row["journal_key"],
                    "year": row.get("year"),
                    "title": row.get("title"),
                    "keyword_order": i,
                    "keyword_raw": kw,
                    "keyword_source": source,
                })
            time.sleep(delay)
    else:
        for row in article_rows:
            row["n_keywords"] = 0

    return article_rows, keyword_rows, logs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--journal-config", required=True, help="CSV with journal_key,journal_title,issn")
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--mailto", required=True)
    ap.add_argument("--from-year", type=int, required=True)
    ap.add_argument("--to-year", type=int, required=True)
    ap.add_argument("--journal", default="all", help="journal_key or all")
    ap.add_argument("--rows", type=int, default=100)
    ap.add_argument("--max-records-per-issn", type=int, default=None)
    ap.add_argument("--delay", type=float, default=1.0)
    ap.add_argument("--skip-landing-pages", action="store_true")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    journals = load_journals(Path(args.journal_config))
    if args.journal != "all":
        journals = [j for j in journals if j.journal_key == args.journal]
        if not journals:
            raise ValueError(f"No journal with key: {args.journal}")

    session = make_session(args.mailto)

    all_articles: List[dict] = []
    all_keywords: List[dict] = []
    all_logs: List[dict] = []

    for cfg in journals:
        articles, keywords, logs = scrape_journal(
            session,
            cfg,
            from_year=args.from_year,
            to_year=args.to_year,
            rows=args.rows,
            max_records_per_issn=args.max_records_per_issn,
            fetch_landing_pages=not args.skip_landing_pages,
            delay=args.delay,
            mailto=args.mailto,
        )
        prefix = slugify(cfg.journal_key)
        write_csv(outdir / f"{prefix}_articles.csv", articles, list(articles[0].keys()) if articles else [
            "article_id","journal_key","journal_title","issn_query","article_url","year","title","authors","doi"
        ])
        write_csv(outdir / f"{prefix}_keywords_long.csv", keywords, [
            "article_id","article_url","journal_key","year","title","keyword_order","keyword_raw","keyword_source"
        ])
        write_csv(outdir / f"{prefix}_scrape_log.csv", logs, sorted(set().union(*(r.keys() for r in logs))) if logs else ["event"])
        summary = {
            "journal_key": cfg.journal_key,
            "journal_title": cfg.journal_title,
            "issns": cfg.issns,
            "n_articles": len(articles),
            "n_keyword_rows": len(keywords),
            "n_articles_with_keywords": len({r["article_id"] for r in keywords}) if keywords else 0,
            "year_min": min([r["year"] for r in articles if r.get("year") is not None], default=None),
            "year_max": max([r["year"] for r in articles if r.get("year") is not None], default=None),
        }
        (outdir / f"{prefix}_scrape_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        all_articles.extend(articles)
        all_keywords.extend(keywords)
        all_logs.extend(logs)

    write_csv(outdir / "combined_articles.csv", all_articles, list(all_articles[0].keys()) if all_articles else ["article_id"])
    write_csv(outdir / "combined_keywords_long.csv", all_keywords, [
        "article_id","article_url","journal_key","year","title","keyword_order","keyword_raw","keyword_source"
    ])
    write_csv(outdir / "combined_scrape_log.csv", all_logs, sorted(set().union(*(r.keys() for r in all_logs))) if all_logs else ["event"])

    print(f"Done. Articles: {len(all_articles)}; keyword rows: {len(all_keywords)}; logs: {len(all_logs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
