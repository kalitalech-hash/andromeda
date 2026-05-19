#!/usr/bin/env python3
"""
Andromeda keyword scraper for psychotherapy / clinical psychology journals. v0.5

Purpose
-------
Collect article metadata and author/publisher keywords into two audit-friendly CSV layers:

    <prefix>_articles.csv
    <prefix>_keywords_long.csv
    <prefix>_scrape_log.csv

Strategy
--------
1. Query Crossref by ISSN and publication-date range to obtain DOI-level article metadata.
2. Visit DOI landing pages politely and parse keywords from HTML metadata / JSON-LD.
3. Keep all provenance fields and keyword extraction source labels for later QA.

Important
---------
This script does not bypass paywalls, does not download PDFs by default, and should be run with
a real contact email in --mailto. Some publishers expose keywords inconsistently. Treat missing
keywords as a QA finding, not as evidence that an article had no keywords.

Example
-------
python andromeda_keyword_scraper_v05.py \
  --mailto your.email@university.edu \
  --from-year 2005 --to-year 2025 \
  --journal all \
  --outdir data_psychotherapy_journals/raw \
  --delay 1.5

Install
-------
pip install requests beautifulsoup4 pandas lxml tqdm
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import sys
import time
import unicodedata
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import quote, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


CROSSREF_API = "https://api.crossref.org/works"


JOURNALS: Dict[str, Dict[str, Any]] = {
    "psychotherapy_research": {
        "title": "Psychotherapy Research",
        "issns": ["1050-3307", "1468-4381"],
        "publisher_family": "taylor_francis",
    },
    "journal_consulting_clinical_psychology": {
        "title": "Journal of Consulting and Clinical Psychology",
        "issns": ["0022-006X", "1939-2117"],
        "publisher_family": "apa",
    },
    "psychotherapy": {
        "title": "Psychotherapy",
        "issns": ["0033-3204", "1939-1536"],
        "publisher_family": "apa",
    },
    "behaviour_research_and_therapy": {
        "title": "Behaviour Research and Therapy",
        "issns": ["0005-7967", "1873-622X"],
        "publisher_family": "elsevier",
    },
    "cognitive_behaviour_therapy": {
        "title": "Cognitive Behaviour Therapy",
        "issns": ["1650-6073", "1651-2316"],
        "publisher_family": "taylor_francis",
    },
    "journal_psychotherapy_integration": {
        "title": "Journal of Psychotherapy Integration",
        "issns": ["1053-0479", "1573-3696"],
        "publisher_family": "apa",
    },
    "clinical_psychology_psychotherapy": {
        "title": "Clinical Psychology & Psychotherapy",
        "issns": ["1063-3995", "1099-0879"],
        "publisher_family": "wiley",
    },
    "psychology_psychotherapy_tprp": {
        "title": "Psychology and Psychotherapy: Theory, Research and Practice",
        "issns": ["1476-0835", "2044-8341"],
        "publisher_family": "wiley",
    },
    "counselling_psychotherapy_research": {
        "title": "Counselling and Psychotherapy Research",
        "issns": ["1473-3145", "1746-1405"],
        "publisher_family": "wiley",
    },
    "arts_in_psychotherapy": {
        "title": "The Arts in Psychotherapy",
        "issns": ["0197-4556", "1873-5878"],
        "publisher_family": "elsevier",
    },
}


KEYWORD_META_NAMES = [
    # Generic / common bibliographic meta tags
    "citation_keywords",
    "citation_keyword",
    "keywords",
    "keyword",
    "dc.subject",
    "dc.Subject",
    "dcterms.subject",
    "prism.keywords",
    "article:tag",
    # Publisher variants observed across journal platforms
    "dc.Keywords",
    "DC.Subject",
    "WT.cg_s",
    "parsely-tags",
]


ARTICLE_TYPES_ALLOWED_DEFAULT = {
    "journal-article",
    "posted-content",
}


@dataclass
class ScrapeLog:
    journal_key: str
    journal_title: str
    doi: str
    url: str
    status: str
    http_status: Optional[int] = None
    keyword_count: int = 0
    keyword_source: str = ""
    error: str = ""


def normalize_space(text: str) -> str:
    text = html.unescape(text or "")
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def safe_join(values: Sequence[Any], sep: str = "; ") -> str:
    return sep.join(normalize_space(str(v)) for v in values if v is not None and str(v).strip())


def first_date_part(item: Dict[str, Any]) -> Tuple[Optional[int], str]:
    """
    Return (year, YYYY-MM-DD-ish string) from Crossref date-parts.
    Prefer published-print, then published-online, then published.
    """
    for key in ("published-print", "published-online", "published", "issued", "created"):
        dp = item.get(key, {}).get("date-parts")
        if dp and dp[0]:
            parts = [str(x) for x in dp[0]]
            year = int(parts[0]) if parts and parts[0].isdigit() else None
            return year, "-".join(parts)
    return None, ""


def crossref_query(
    session: requests.Session,
    issn: str,
    mailto: str,
    from_year: Optional[int],
    to_year: Optional[int],
    rows: int = 100,
    max_records: Optional[int] = None,
    delay: float = 1.0,
    use_select: bool = False,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Crossref query for a single ISSN.

    v0.5 change
    -----------
    The previous cursor loop could stop after one page on some Crossref responses,
    which produced the suspicious 2 x 100 = 200 records per journal pattern.
    This version uses explicit offset pagination by default. For this corpus
    the per-ISSN result sets are well below Crossref's practical 10k offset ceiling.

    Returns:
        (items, diagnostics)
    """
    filters = [f"issn:{issn}", "type:journal-article"]
    if from_year:
        filters.append(f"from-pub-date:{from_year}-01-01")
    if to_year:
        filters.append(f"until-pub-date:{to_year}-12-31")

    page_rows = min(max(int(rows), 1), 1000)

    base_params = {
        "filter": ",".join(filters),
        "rows": page_rows,
        "offset": 0,
        "mailto": mailto,
        "sort": "published",
        "order": "asc",
    }

    # Safe selectable fields only. Do not include Crossref fields unless verified.
    if use_select:
        base_params["select"] = ",".join([
            "DOI", "URL", "ISSN", "container-title", "title", "author",
            "published", "published-print", "published-online", "issued",
            "volume", "issue", "page", "type", "subject",
            "abstract", "publisher", "created"
        ])

    all_items: List[Dict[str, Any]] = []
    seen_doi = set()
    diagnostics: Dict[str, Any] = {
        "issn": issn,
        "request_filter": base_params["filter"],
        "rows": page_rows,
        "http_status_first": None,
        "crossref_total_results": None,
        "pages_fetched": 0,
        "items_seen": 0,
        "items_kept": 0,
        "used_select": use_select,
        "pagination": "offset",
        "last_offset": 0,
        "error": "",
    }

    offset = 0
    total_results = None

    while True:
        params = dict(base_params)
        params["offset"] = offset

        try:
            r = session_get_with_retries(session, CROSSREF_API, params=params, timeout=(10, 25), retries=5, backoff=2.0)
            if diagnostics["http_status_first"] is None:
                diagnostics["http_status_first"] = r.status_code
            r.raise_for_status()
            payload = r.json()
        except requests.HTTPError as e:
            # If select was requested and Crossref rejects it, retry without select.
            if use_select and base_params.get("select"):
                diagnostics["error"] = (
                    f"select_query_failed_retrying_without_select: "
                    f"{type(e).__name__}: {e}; body={getattr(e.response, 'text', '')[:500]}"
                )
                base_params.pop("select", None)
                use_select = False
                diagnostics["used_select"] = False
                offset = 0
                all_items = []
                seen_doi = set()
                total_results = None
                continue
            diagnostics["error"] = f"{type(e).__name__}: {e}; body={getattr(e.response, 'text', '')[:1000]}"
            raise RuntimeError(diagnostics["error"]) from e
        except Exception as e:
            diagnostics["error"] = f"{type(e).__name__}: {e}"
            raise

        msg = payload.get("message", {})
        if total_results is None:
            total_results = msg.get("total-results")
            diagnostics["crossref_total_results"] = total_results

        items = msg.get("items", [])
        diagnostics["pages_fetched"] += 1
        diagnostics["items_seen"] += len(items)
        diagnostics["last_offset"] = offset

        if not items:
            break

        before = len(all_items)
        for item in items:
            doi = (item.get("DOI") or "").lower().strip()
            key = doi or normalize_space(item.get("URL", "")) or json.dumps(item, sort_keys=True)[:200]
            if key and key not in seen_doi:
                all_items.append(item)
                seen_doi.add(key)
                if max_records and len(all_items) >= max_records:
                    diagnostics["items_kept"] = len(all_items)
                    return all_items, diagnostics

        # Stop when Crossref returned a short page or we have reached the reported total.
        offset += page_rows
        if len(items) < page_rows:
            break
        if isinstance(total_results, int) and offset >= total_results:
            break

        # Safety: Crossref offset pagination has a practical 10k ceiling.
        # This corpus should not approach it per ISSN; if it does, split by year.
        if offset >= 10000:
            diagnostics["error"] = "offset_reached_10000_split_query_by_year_recommended"
            break

        # If a page produced no new records, continue only once more would likely be wasteful.
        # This is a duplicate-heavy ISSN response rather than a useful new page.
        if len(all_items) == before and diagnostics["pages_fetched"] > 1:
            # Do not break immediately on first duplicate-heavy page; but avoid endless loops.
            pass

        time.sleep(delay)

    diagnostics["items_kept"] = len(all_items)
    return all_items, diagnostics

def crossref_item_to_article(item: Dict[str, Any], journal_key: str, journal_cfg: Dict[str, Any]) -> Dict[str, Any]:
    doi = normalize_space(item.get("DOI", "")).lower()
    year, pub_date = first_date_part(item)
    authors = []
    for a in item.get("author", []) or []:
        given = a.get("given", "")
        family = a.get("family", "")
        literal = a.get("name", "")
        authors.append(normalize_space(f"{given} {family}" if family else literal))

    title = safe_join(item.get("title", []))
    container = safe_join(item.get("container-title", []))
    article_id = doi if doi else normalize_space(item.get("URL", ""))

    return {
        "article_id": article_id,
        "journal_key": journal_key,
        "journal_title_config": journal_cfg["title"],
        "journal_title_crossref": container,
        "publisher_family": journal_cfg.get("publisher_family", ""),
        "article_url": normalize_space(item.get("URL", "")),
        "doi": doi,
        "year": year,
        "publication_date": pub_date,
        "volume": normalize_space(item.get("volume", "")),
        "issue_number": normalize_space(item.get("issue", "")),
        "pages": normalize_space(item.get("page", "")),
        "title": title,
        "authors": safe_join(authors),
        "article_type": normalize_space(item.get("type", "")),
        "crossref_subjects": safe_join(item.get("subject", [])),
        "abstract_text": clean_crossref_abstract(item.get("abstract", "")),
        "n_keywords": 0,
        "keyword_extraction_status": "not_attempted",
        "keyword_source": "",
    }


def clean_crossref_abstract(raw: str) -> str:
    if not raw:
        return ""
    soup = BeautifulSoup(raw, "lxml")
    return normalize_space(soup.get_text(" "))


def doi_url(doi: str) -> str:
    return f"https://doi.org/{quote(doi, safe='/')}"


def fetch_landing_page(session: requests.Session, doi: str, fallback_url: str = "", delay: float = 1.0) -> Tuple[str, int, str]:
    """
    Resolve DOI to landing page. Returns (final_url, http_status, text).
    """
    url = doi_url(doi) if doi else fallback_url
    time.sleep(delay)
    r = session_get_with_retries(session, url, timeout=(10, 30), allow_redirects=True, retries=3, backoff=2.0)
    return r.url, r.status_code, r.text


def split_keyword_blob(value: str) -> List[str]:
    """
    Split conservatively. Publisher metadata uses semicolons most often; commas also appear.
    We avoid splitting on slash or hyphen. We split comma only when there are multiple
    comma-separated short phrases.
    """
    value = normalize_space(value)
    if not value:
        return []

    # Remove labels accidentally captured from visible text.
    value = re.sub(r"^(keywords?|key words|author keywords)\s*[:：]\s*", "", value, flags=re.I)

    if ";" in value:
        parts = value.split(";")
    elif "|" in value:
        parts = value.split("|")
    elif re.search(r"\s•\s", value):
        parts = re.split(r"\s•\s", value)
    elif value.count(",") >= 2:
        parts = value.split(",")
    else:
        parts = [value]

    cleaned = []
    for p in parts:
        p = normalize_space(p.strip(" .;,\u2022"))
        if p and len(p) <= 250:
            cleaned.append(p)
    return cleaned


def dedupe_preserve_order(items: Iterable[str]) -> List[str]:
    seen = set()
    out = []
    for x in items:
        key = normalize_space(x).casefold()
        if key and key not in seen:
            out.append(normalize_space(x))
            seen.add(key)
    return out


def extract_from_meta(soup: BeautifulSoup) -> Tuple[List[str], str]:
    hits = []
    sources = []
    for tag in soup.find_all("meta"):
        name = tag.get("name") or tag.get("property") or tag.get("itemprop") or ""
        if name in KEYWORD_META_NAMES or name.lower() in [n.lower() for n in KEYWORD_META_NAMES]:
            content = tag.get("content") or ""
            parts = split_keyword_blob(content)
            if parts:
                hits.extend(parts)
                sources.append(f"meta:{name}")
    return dedupe_preserve_order(hits), safe_join(sorted(set(sources)))


def extract_from_jsonld(soup: BeautifulSoup) -> Tuple[List[str], str]:
    hits = []
    for script in soup.find_all("script", attrs={"type": re.compile(r"ld\+json", re.I)}):
        raw = script.string or script.get_text() or ""
        if not raw.strip():
            continue
        try:
            data = json.loads(raw)
        except Exception:
            continue

        def walk(obj: Any):
            if isinstance(obj, dict):
                for key in ("keywords", "about"):
                    if key in obj:
                        val = obj[key]
                        if isinstance(val, str):
                            hits.extend(split_keyword_blob(val))
                        elif isinstance(val, list):
                            for v in val:
                                if isinstance(v, str):
                                    hits.extend(split_keyword_blob(v))
                                elif isinstance(v, dict):
                                    name = v.get("name") or v.get("@id")
                                    if name:
                                        hits.extend(split_keyword_blob(str(name)))
                for v in obj.values():
                    walk(v)
            elif isinstance(obj, list):
                for v in obj:
                    walk(v)

        walk(data)

    return dedupe_preserve_order(hits), "jsonld:keywords/about" if hits else ""


def extract_from_visible_sections(soup: BeautifulSoup) -> Tuple[List[str], str]:
    """
    Last-resort parser for visible keyword blocks. Conservative because pages have many unrelated tags.
    """
    candidates: List[str] = []

    # Common publisher containers / labels.
    selectors = [
        "[class*=keyword]", "[id*=keyword]",
        "section", "div", "p",
    ]
    for sel in selectors:
        for elem in soup.select(sel):
            text = normalize_space(elem.get_text(" "))
            if not text or len(text) > 1000:
                continue
            if re.search(r"\b(keywords?|key words|author keywords)\b", text, flags=re.I):
                # Prefer text after label; avoid page-wide blocks.
                m = re.search(r"\b(?:keywords?|key words|author keywords)\b\s*[:：]?\s*(.+)$", text, flags=re.I)
                blob = m.group(1) if m else text
                parts = split_keyword_blob(blob)
                if 1 <= len(parts) <= 30:
                    candidates.extend(parts)

    # Filter out navigation noise.
    bad = re.compile(r"^(abstract|article|references|download|pdf|view|rights|copyright|share|related|recommended)$", re.I)
    candidates = [c for c in candidates if not bad.match(c)]
    return dedupe_preserve_order(candidates), "visible_keyword_section" if candidates else ""


def extract_keywords_from_html(html_text: str) -> Tuple[List[str], str]:
    soup = BeautifulSoup(html_text, "lxml")

    for extractor in (extract_from_meta, extract_from_jsonld, extract_from_visible_sections):
        keywords, source = extractor(soup)
        if keywords:
            return keywords, source

    return [], ""


def build_keyword_rows(article: Dict[str, Any], keywords: Sequence[str], keyword_source: str, landing_url: str) -> List[Dict[str, Any]]:
    rows = []
    for i, kw in enumerate(keywords, start=1):
        rows.append({
            "article_id": article["article_id"],
            "journal_key": article["journal_key"],
            "journal_title": article["journal_title_config"],
            "article_url": article.get("article_url", ""),
            "landing_url": landing_url,
            "doi": article.get("doi", ""),
            "year": article.get("year", ""),
            "volume": article.get("volume", ""),
            "issue_number": article.get("issue_number", ""),
            "title": article.get("title", ""),
            "keyword_order": i,
            "keyword_raw": kw,
            "keyword_url": "",
            "keyword_source": keyword_source,
        })
    return rows


def make_session(mailto: str, user_agent_prefix: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": f"{user_agent_prefix}/0.5 (mailto:{mailto}; bibliometric keyword extraction; https://github.com/kalitalech-hash/andromeda)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    return s



def session_get_with_retries(
    session: requests.Session,
    url: str,
    *,
    params: Optional[Dict[str, Any]] = None,
    timeout: Tuple[int, int] = (10, 25),
    allow_redirects: bool = True,
    retries: int = 4,
    backoff: float = 2.0,
) -> requests.Response:
    """
    Robust GET wrapper for long bibliometric runs.

    Uses a separate connect/read timeout. This prevents the shell from appearing
    to hang indefinitely while requests waits for a slow response body.
    """
    last_exc: Optional[BaseException] = None
    for attempt in range(1, retries + 1):
        try:
            response = session.get(
                url,
                params=params,
                timeout=timeout,
                allow_redirects=allow_redirects,
            )
            return response
        except (
            requests.exceptions.ReadTimeout,
            requests.exceptions.ConnectTimeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.ChunkedEncodingError,
        ) as exc:
            last_exc = exc
            if attempt >= retries:
                break
            time.sleep(backoff * attempt)
    raise RuntimeError(f"GET failed after {retries} attempts for {url}: {type(last_exc).__name__}: {last_exc}") from last_exc


def scrape_journal(
    journal_key: str,
    journal_cfg: Dict[str, Any],
    args: argparse.Namespace,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[ScrapeLog]]:
    session = make_session(args.mailto, args.user_agent_prefix)
    articles_by_id: Dict[str, Dict[str, Any]] = {}
    logs: List[ScrapeLog] = []
    keyword_rows: List[Dict[str, Any]] = []

    for issn in journal_cfg["issns"]:
        try:
            items, diag = crossref_query(
                session=session,
                issn=issn,
                mailto=args.mailto,
                from_year=args.from_year,
                to_year=args.to_year,
                rows=args.rows,
                max_records=args.max_records_per_issn,
                delay=args.delay,
                use_select=args.crossref_use_select,
            )
            logs.append(ScrapeLog(
                journal_key=journal_key,
                journal_title=journal_cfg["title"],
                doi="",
                url=f"crossref:issn:{issn}",
                status="crossref_query_ok",
                http_status=diag.get("http_status_first"),
                keyword_count=int(diag.get("items_kept") or 0),
                keyword_source=f"total_results={diag.get('crossref_total_results')}; pages={diag.get('pages_fetched')}; seen={diag.get('items_seen')}; filter={diag.get('request_filter')}",
            ))
        except Exception as e:
            logs.append(ScrapeLog(
                journal_key=journal_key,
                journal_title=journal_cfg["title"],
                doi="",
                url="",
                status="crossref_query_error",
                error=f"{type(e).__name__}: {e}",
            ))
            continue

        for item in items:
            article = crossref_item_to_article(item, journal_key, journal_cfg)
            if not article.get("doi"):
                continue
            # Crossref can return the same DOI for print and online ISSN.
            articles_by_id.setdefault(article["article_id"], article)

    articles = list(articles_by_id.values())

    for article in tqdm(articles, desc=f"{journal_key}: landing pages", unit="article"):
        doi = article.get("doi", "")
        fallback_url = article.get("article_url", "")
        final_url = fallback_url
        status_code = None
        try:
            final_url, status_code, text = fetch_landing_page(session, doi, fallback_url, delay=args.delay)
            keywords, source = extract_keywords_from_html(text)

            # Fallback: Crossref subject terms are not author keywords, so keep them only if requested.
            if not keywords and args.use_crossref_subjects_as_fallback and article.get("crossref_subjects"):
                keywords = [x.strip() for x in article["crossref_subjects"].split(";") if x.strip()]
                source = "crossref_subject_fallback_not_author_keywords"

            article["article_url"] = final_url or fallback_url
            article["n_keywords"] = len(keywords)
            article["keyword_extraction_status"] = "ok" if keywords else "no_keywords_found"
            article["keyword_source"] = source
            keyword_rows.extend(build_keyword_rows(article, keywords, source, final_url))

            logs.append(ScrapeLog(
                journal_key=journal_key,
                journal_title=journal_cfg["title"],
                doi=doi,
                url=final_url,
                status=article["keyword_extraction_status"],
                http_status=status_code,
                keyword_count=len(keywords),
                keyword_source=source,
            ))
        except Exception as e:
            article["keyword_extraction_status"] = "landing_page_error"
            logs.append(ScrapeLog(
                journal_key=journal_key,
                journal_title=journal_cfg["title"],
                doi=doi,
                url=final_url or fallback_url,
                status="landing_page_error",
                http_status=status_code,
                error=f"{type(e).__name__}: {e}",
            ))

    return articles, keyword_rows, logs


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    pd.DataFrame(rows).to_csv(path, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_MINIMAL)


def write_summary(path: Path, articles: List[Dict[str, Any]], keyword_rows: List[Dict[str, Any]], logs: List[ScrapeLog]) -> None:
    df_a = pd.DataFrame(articles)
    df_k = pd.DataFrame(keyword_rows)
    df_l = pd.DataFrame([asdict(x) for x in logs])

    summary = {
        "n_article_rows": int(len(df_a)),
        "n_unique_article_ids": int(df_a["article_id"].nunique()) if not df_a.empty else 0,
        "n_keyword_rows": int(len(df_k)),
        "n_unique_keyword_raw": int(df_k["keyword_raw"].nunique()) if not df_k.empty else 0,
        "year_min": int(df_a["year"].min()) if not df_a.empty and df_a["year"].notna().any() else None,
        "year_max": int(df_a["year"].max()) if not df_a.empty and df_a["year"].notna().any() else None,
        "keyword_extraction_status_counts": df_a["keyword_extraction_status"].value_counts(dropna=False).to_dict() if not df_a.empty else {},
        "keyword_source_counts": df_a["keyword_source"].value_counts(dropna=False).to_dict() if not df_a.empty else {},
        "log_status_counts": df_l["status"].value_counts(dropna=False).to_dict() if not df_l.empty else {},
    }
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Scrape author/publisher keywords from a psychotherapy journal corpus.")
    p.add_argument("--mailto", required=True, help="Contact email for Crossref polite pool and User-Agent.")
    p.add_argument("--journal", default="all", help="Journal key or 'all'. Use --list-journals to inspect keys.")
    p.add_argument("--from-year", type=int, default=None)
    p.add_argument("--to-year", type=int, default=None)
    p.add_argument("--outdir", default="data_psychotherapy_journals/raw")
    p.add_argument("--prefix", default="psychotherapy_journals")
    p.add_argument("--delay", type=float, default=1.5, help="Delay between HTTP requests in seconds.")
    p.add_argument("--rows", type=int, default=100, help="Crossref page size.")
    p.add_argument("--max-records-per-issn", type=int, default=None, help="Debug limit.")
    p.add_argument("--user-agent-prefix", default="AndromedaNowickaKeywordScraper")
    p.add_argument("--use-crossref-subjects-as-fallback", action="store_true",
                   help="Use Crossref subject categories when no author keywords are found. Marked as fallback, not author keywords.")
    p.add_argument("--crossref-use-select", action="store_true",
                   help="Use Crossref select parameter. Default off because invalid select fields can zero out collection.")
    p.add_argument("--list-journals", action="store_true")
    return p.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)
    if args.list_journals:
        for key, cfg in JOURNALS.items():
            print(f"{key}\t{cfg['title']}\t{';'.join(cfg['issns'])}\t{cfg.get('publisher_family','')}")
        return 0

    selected = list(JOURNALS.keys()) if args.journal == "all" else [args.journal]
    unknown = [j for j in selected if j not in JOURNALS]
    if unknown:
        print(f"Unknown journal key(s): {unknown}. Run --list-journals.", file=sys.stderr)
        return 2

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    all_articles: List[Dict[str, Any]] = []
    all_keywords: List[Dict[str, Any]] = []
    all_logs: List[ScrapeLog] = []

    for journal_key in selected:
        cfg = JOURNALS[journal_key]
        articles, keywords, logs = scrape_journal(journal_key, cfg, args)
        all_articles.extend(articles)
        all_keywords.extend(keywords)
        all_logs.extend(logs)

        safe_key = re.sub(r"[^a-z0-9_]+", "_", journal_key.lower())
        write_csv(outdir / f"{safe_key}_articles.csv", articles)
        write_csv(outdir / f"{safe_key}_keywords_long.csv", keywords)
        write_csv(outdir / f"{safe_key}_scrape_log.csv", [asdict(x) for x in logs])
        write_summary(outdir / f"{safe_key}_scrape_summary.json", articles, keywords, logs)

    # Combined corpus layer.
    write_csv(outdir / f"{args.prefix}_articles.csv", all_articles)
    write_csv(outdir / f"{args.prefix}_keywords_long.csv", all_keywords)
    write_csv(outdir / f"{args.prefix}_scrape_log.csv", [asdict(x) for x in all_logs])
    write_summary(outdir / f"{args.prefix}_scrape_summary.json", all_articles, all_keywords, all_logs)

    print(f"Done. Articles: {len(all_articles)}; keyword rows: {len(all_keywords)}; logs: {len(all_logs)}")
    print(f"Output: {outdir.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
