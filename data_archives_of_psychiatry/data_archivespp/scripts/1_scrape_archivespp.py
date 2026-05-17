#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Scraper metadanych i słów kluczowych dla czasopisma:
Archives of Psychiatry and Psychotherapy
https://www.archivespp.pl/

Etap 1 pipeline'u bibliometrycznego:
    strona archiwum -> strony numerów -> strony artykułów -> articles.csv + keywords_long.csv

Domyślne wyjścia:
    ../data/app_articles.csv
    ../data/app_keywords_long.csv
    ../data/app_issues.csv
    ../data/app_scrape_log.csv

Uruchomienie:
    python 1_scrape_archivespp.py

Przykłady:
    python 1_scrape_archivespp.py --start-year 2005 --end-year 2025
    python 1_scrape_archivespp.py --include-online-first
    python 1_scrape_archivespp.py --sleep 0.75 --timeout 30
"""

from __future__ import annotations

import argparse
import csv
import logging
import re
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import urljoin, urlparse, unquote

import requests
from bs4 import BeautifulSoup


BASE_URL = "https://www.archivespp.pl/"
ARCHIVE_URL = urljoin(BASE_URL, "Archive")
ONLINE_FIRST_URL = urljoin(BASE_URL, "Online-first/")


@dataclass
class IssueRecord:
    issue_url: str
    issue_label: str
    year: Optional[int]
    volume: Optional[str]
    issue_number: Optional[str]
    issue_id: Optional[str]
    source: str = "archive"


@dataclass
class ArticleRecord:
    article_id: str
    article_url: str
    source_issue_url: str
    source_issue_label: str
    source: str
    year: Optional[int]
    volume: Optional[str]
    issue_number: Optional[str]
    title: str
    authors: str
    citation: str
    pages: str
    doi: str
    pdf_url: str
    publication_date: str
    online_publication_date: str
    submission_date: str
    acceptance_date: str
    article_type: str
    topics: str
    abstract_text: str
    n_keywords: int


@dataclass
class KeywordRecord:
    article_id: str
    article_url: str
    year: Optional[int]
    volume: Optional[str]
    issue_number: Optional[str]
    title: str
    keyword_order: int
    keyword_raw: str
    keyword_url: str


def setup_logging(log_path: Path) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_path, encoding="utf-8"),
        ],
    )


def fetch(session: requests.Session, url: str, timeout: int, sleep: float) -> BeautifulSoup:
    logging.info("GET %s", url)
    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    if sleep > 0:
        time.sleep(sleep)
    return BeautifulSoup(response.text, "html.parser")


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = re.sub(r"\s+", " ", value.replace("\xa0", " ")).strip()
    return value


def text_lines(soup: BeautifulSoup) -> list[str]:
    return [clean_text(x) for x in soup.get_text("\n").splitlines() if clean_text(x)]


def absolute_url(href: str) -> str:
    return urljoin(BASE_URL, href)


def parse_issue_label(label: str) -> tuple[Optional[int], Optional[str], Optional[str]]:
    """
    Obsługiwane przykłady:
        1/2026 vol. 28
        1-2/2007 vol. 9
        4/2025 vol. 27
    """
    label = clean_text(label)
    year = None
    volume = None
    issue_number = None

    m_year = re.search(r"\b(19|20)\d{2}\b", label)
    if m_year:
        year = int(m_year.group(0))

    m_issue = re.search(r"^([0-9]+(?:-[0-9]+)?)/", label)
    if m_issue:
        issue_number = m_issue.group(1)

    m_volume = re.search(r"vol\.\s*([0-9A-Za-z\-]+)", label, flags=re.I)
    if m_volume:
        volume = m_volume.group(1)

    return year, volume, issue_number


def parse_id_from_url(url: str) -> str:
    decoded = unquote(url)
    # Article example: /Some-title%2C211034%2C0%2C2.html
    # Issue example:   /Issue-4-2025%2C15499
    m_article = re.search(r",(\d+),0,2\.html$", decoded)
    if m_article:
        return m_article.group(1)

    m_issue = re.search(r",(\d+)$", decoded)
    if m_issue:
        return m_issue.group(1)

    m_any = re.search(r",(\d+)", decoded)
    if m_any:
        return m_any.group(1)

    return ""


def is_internal_archivespp_url(url: str) -> bool:
    parsed = urlparse(url)
    return parsed.netloc in {"www.archivespp.pl", "archivespp.pl"}


def is_issue_url(url: str) -> bool:
    decoded = unquote(url)
    return is_internal_archivespp_url(url) and "/Issue-" in decoded


def is_article_url(url: str) -> bool:
    decoded = unquote(url)
    if not is_internal_archivespp_url(url):
        return False
    if not decoded.endswith(".html"):
        return False
    # Typowy wzorzec strony artykułu Bentus/Journals System.
    return bool(re.search(r",\d+,0,2\.html$", decoded))


def extract_issues(
    soup: BeautifulSoup,
    start_year: Optional[int],
    end_year: Optional[int],
) -> list[IssueRecord]:
    seen: set[str] = set()
    issues: list[IssueRecord] = []

    for a in soup.find_all("a", href=True):
        href = absolute_url(a["href"])
        label = clean_text(a.get_text(" "))
        if not label or not is_issue_url(href):
            continue

        year, volume, issue_number = parse_issue_label(label)

        if start_year is not None and year is not None and year < start_year:
            continue
        if end_year is not None and year is not None and year > end_year:
            continue

        if href in seen:
            continue
        seen.add(href)

        issues.append(
            IssueRecord(
                issue_url=href,
                issue_label=label,
                year=year,
                volume=volume,
                issue_number=issue_number,
                issue_id=parse_id_from_url(href),
                source="archive",
            )
        )

    # Sortowanie chronologiczne: rosnąco po roku i numerze, z obsługą numerów 1-2.
    def sort_key(issue: IssueRecord):
        issue_sort = 999
        if issue.issue_number:
            try:
                issue_sort = int(issue.issue_number.split("-")[0])
            except ValueError:
                pass
        return (issue.year or 9999, issue_sort)

    return sorted(issues, key=sort_key)


def extract_article_urls_from_issue(soup: BeautifulSoup) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()

    for a in soup.find_all("a", href=True):
        href = absolute_url(a["href"])
        if not is_article_url(href):
            continue
        if href in seen:
            continue
        seen.add(href)
        urls.append(href)

    return urls


def meta_values(soup: BeautifulSoup, name: str) -> list[str]:
    values = []
    for tag in soup.find_all("meta"):
        key = tag.get("name") or tag.get("property") or ""
        if key.lower() == name.lower():
            content = clean_text(tag.get("content"))
            if content:
                values.append(content)
    return values


def first_meta(soup: BeautifulSoup, names: Iterable[str]) -> str:
    for name in names:
        vals = meta_values(soup, name)
        if vals:
            return vals[0]
    return ""


def get_title(soup: BeautifulSoup) -> str:
    # Najpierw metadane cytowań, potem h1, potem <title>.
    title = first_meta(soup, ["citation_title", "og:title", "DC.Title"])
    if title:
        return title

    h1 = soup.find("h1")
    if h1:
        title = clean_text(h1.get_text(" "))
        if title:
            return title

    if soup.title and soup.title.string:
        title = clean_text(soup.title.string)
        title = re.sub(r"\s*-\s*Archives of Psychiatry and Psychotherapy\s*$", "", title)
        return title

    return ""


def extract_between_headings(lines: list[str], start: str, stops: Iterable[str]) -> list[str]:
    start_norm = start.upper()
    stop_norms = {s.upper() for s in stops}

    start_index = None
    for i, line in enumerate(lines):
        if line.upper() == start_norm:
            start_index = i + 1
            break

    if start_index is None:
        return []

    out = []
    for line in lines[start_index:]:
        if line.upper() in stop_norms:
            break
        out.append(line)
    return out


def extract_keywords(soup: BeautifulSoup) -> list[tuple[str, str]]:
    """
    Pobiera keywordy z bloku KEYWORDS.
    Strategia 1: linki występujące po nagłówku KEYWORDS do następnego nagłówka.
    Strategia 2: fallback liniowy z tekstu strony.
    """
    lines = text_lines(soup)
    raw_keywords = extract_between_headings(lines, "KEYWORDS", ["TOPICS", "ABSTRACT", "Submit your paper"])

    # Jeśli BeautifulSoup rozdzielił linki na osobne linie, to ten fallback już wystarczy.
    fallback = []
    for kw in raw_keywords:
        kw = clean_text(kw)
        if kw and kw.upper() not in {"TOPICS", "ABSTRACT"}:
            fallback.append((kw, ""))

    # Próba odzyskania URL-i keywordów przez przejście od tekstu "KEYWORDS" w drzewie.
    keyword_pairs: list[tuple[str, str]] = []
    marker = soup.find(string=lambda s: isinstance(s, str) and clean_text(s).upper() == "KEYWORDS")
    if marker:
        # Przechodzimy po elementach następujących po markerze, aż napotkamy TOPICS/ABSTRACT.
        for node in marker.find_all_next():
            node_text = clean_text(node.get_text(" ") if hasattr(node, "get_text") else str(node))
            if node_text.upper() in {"TOPICS", "ABSTRACT"}:
                break
            if getattr(node, "name", None) == "a":
                kw = clean_text(node.get_text(" "))
                href = absolute_url(node.get("href", ""))
                if kw and not kw.lower().startswith("article"):
                    keyword_pairs.append((kw, href))

    # Usunięcie duplikatów z zachowaniem kolejności.
    deduped = []
    seen = set()
    for kw, href in keyword_pairs or fallback:
        key = (kw, href)
        if kw and key not in seen:
            seen.add(key)
            deduped.append((kw, href))

    return deduped


def extract_topics(soup: BeautifulSoup) -> str:
    lines = text_lines(soup)
    topics = extract_between_headings(lines, "TOPICS", ["ABSTRACT", "Submit your paper"])
    topics = [re.sub(r"^\*\s*", "", t).strip() for t in topics]
    return " | ".join([t for t in topics if t])


def extract_abstract(soup: BeautifulSoup) -> str:
    lines = text_lines(soup)
    abstract_lines = extract_between_headings(
        lines,
        "ABSTRACT",
        ["Submit your paper", "Share", "RELATED ARTICLE", "Indexes"],
    )
    return " ".join(abstract_lines)


def extract_dates(lines: list[str]) -> dict[str, str]:
    labels = {
        "Submission date:": "submission_date",
        "Acceptance date:": "acceptance_date",
        "Online publication date:": "online_publication_date",
        "Publication date:": "publication_date",
    }
    out = {v: "" for v in labels.values()}
    for line in lines:
        for prefix, field in labels.items():
            if line.startswith(prefix):
                out[field] = clean_text(line.replace(prefix, "", 1))
    return out


def extract_citation_parts(soup: BeautifulSoup, fallback_year: Optional[int]) -> tuple[str, str, Optional[int], str, str]:
    lines = text_lines(soup)
    citation = ""
    for line in lines:
        if line.startswith("Arch Psych Psych "):
            citation = line
            break

    year = fallback_year
    volume = ""
    issue_number = ""
    pages = ""

    # Arch Psych Psych 2026;28(1):7-21
    m = re.search(r"Arch Psych Psych\s+(\d{4});\s*([^(:]+)(?:\(([^)]+)\))?(?::([0-9A-Za-z\-–]+))?", citation)
    if m:
        year = int(m.group(1))
        volume = clean_text(m.group(2))
        issue_number = clean_text(m.group(3) or "")
        pages = clean_text(m.group(4) or "")

    return citation, pages, year, volume, issue_number


def extract_pdf_url(soup: BeautifulSoup) -> str:
    for a in soup.find_all("a", href=True):
        txt = clean_text(a.get_text(" ")).lower()
        href = absolute_url(a["href"])
        if "article" in txt and "pdf" in txt:
            return href
        if href.lower().endswith(".pdf"):
            return href
    return ""


def infer_article_type(title: str, citation: str) -> str:
    title_norm = title.strip().lower()
    if title_norm == "editorial" or title_norm.startswith("editorial"):
        return "editorial"
    if "book review" in title_norm:
        return "book review"
    if "case report" in title_norm or "case analysis" in title_norm:
        return "case report/review"
    # Domyślnie nie przesądzamy typu; historycznie strona issue czasem ma etykietę ARTICLE.
    return ""


def parse_article(
    session: requests.Session,
    url: str,
    issue: IssueRecord,
    timeout: int,
    sleep: float,
) -> tuple[ArticleRecord, list[KeywordRecord]]:
    soup = fetch(session, url, timeout=timeout, sleep=sleep)
    lines = text_lines(soup)

    article_id = parse_id_from_url(url)
    title = get_title(soup)
    authors = " | ".join(meta_values(soup, "citation_author"))

    # Fallback dla autorów, gdy metatagi nie wystąpią:
    if not authors:
        try:
            title_index = lines.index(title)
            after_title = lines[title_index + 1 :]
            stop_words = {"More details Hide details", "Submission date:", "Arch Psych Psych"}
            author_candidates = []
            for line in after_title:
                if any(line.startswith(stop) for stop in stop_words):
                    break
                if line in {",", "1", "2", "3", "4", "5"}:
                    continue
                if len(line) > 1:
                    author_candidates.append(line)
            authors = " | ".join(author_candidates)
        except ValueError:
            authors = ""

    doi = first_meta(soup, ["citation_doi"])
    if not doi:
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "doi.org/" in href:
                doi = href.split("doi.org/", 1)[-1]
                break

    citation, pages, parsed_year, parsed_volume, parsed_issue_number = extract_citation_parts(soup, issue.year)
    dates = extract_dates(lines)
    pdf_url = first_meta(soup, ["citation_pdf_url"]) or extract_pdf_url(soup)
    topics = extract_topics(soup)
    abstract_text = extract_abstract(soup)
    keywords = extract_keywords(soup)

    year = parsed_year or issue.year
    volume = parsed_volume or issue.volume or ""
    issue_number = parsed_issue_number or issue.issue_number or ""

    article = ArticleRecord(
        article_id=article_id,
        article_url=url,
        source_issue_url=issue.issue_url,
        source_issue_label=issue.issue_label,
        source=issue.source,
        year=year,
        volume=volume,
        issue_number=issue_number,
        title=title,
        authors=authors,
        citation=citation,
        pages=pages,
        doi=doi,
        pdf_url=pdf_url,
        publication_date=dates["publication_date"],
        online_publication_date=dates["online_publication_date"],
        submission_date=dates["submission_date"],
        acceptance_date=dates["acceptance_date"],
        article_type=infer_article_type(title, citation),
        topics=topics,
        abstract_text=abstract_text,
        n_keywords=len(keywords),
    )

    keyword_records = [
        KeywordRecord(
            article_id=article_id,
            article_url=url,
            year=year,
            volume=volume,
            issue_number=issue_number,
            title=title,
            keyword_order=i,
            keyword_raw=kw,
            keyword_url=kw_url,
        )
        for i, (kw, kw_url) in enumerate(keywords, start=1)
    ]

    return article, keyword_records


def write_csv(path: Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape Archives of Psychiatry and Psychotherapy metadata and keywords.")
    parser.add_argument("--base-url", default=BASE_URL)
    parser.add_argument("--start-year", type=int, default=None)
    parser.add_argument("--end-year", type=int, default=None)
    parser.add_argument("--include-online-first", action="store_true")
    parser.add_argument("--sleep", type=float, default=0.5, help="Delay after each request, in seconds.")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--outdir", default=str(Path(__file__).resolve().parents[1] / "data"))
    parser.add_argument("--user-agent", default="AndromedaNowicka/0.2 bibliometric research scraper; contact: repository maintainer")
    args = parser.parse_args()

    outdir = Path(args.outdir)
    setup_logging(outdir / "app_scrape_log.csv")

    session = requests.Session()
    session.headers.update({"User-Agent": args.user_agent})

    logging.info("Pobieram archiwum: %s", ARCHIVE_URL)
    archive_soup = fetch(session, ARCHIVE_URL, timeout=args.timeout, sleep=args.sleep)
    issues = extract_issues(archive_soup, start_year=args.start_year, end_year=args.end_year)

    if args.include_online_first:
        issues.append(
            IssueRecord(
                issue_url=ONLINE_FIRST_URL,
                issue_label="Online first",
                year=None,
                volume=None,
                issue_number=None,
                issue_id=None,
                source="online_first",
            )
        )

    logging.info("Liczba numerów do przetworzenia: %s", len(issues))

    articles: list[ArticleRecord] = []
    keywords_long: list[KeywordRecord] = []

    for issue in issues:
        try:
            issue_soup = fetch(session, issue.issue_url, timeout=args.timeout, sleep=args.sleep)
            article_urls = extract_article_urls_from_issue(issue_soup)
            logging.info("%s: znaleziono %s stron artykułów", issue.issue_label, len(article_urls))

            for article_url in article_urls:
                try:
                    article, keyword_records = parse_article(
                        session=session,
                        url=article_url,
                        issue=issue,
                        timeout=args.timeout,
                        sleep=args.sleep,
                    )
                    articles.append(article)
                    keywords_long.extend(keyword_records)
                    logging.info(
                        "OK article_id=%s year=%s n_keywords=%s title=%s",
                        article.article_id,
                        article.year,
                        article.n_keywords,
                        article.title[:80],
                    )
                except Exception as exc:  # noqa: BLE001
                    logging.exception("Błąd parsowania artykułu %s: %s", article_url, exc)
        except Exception as exc:  # noqa: BLE001
            logging.exception("Błąd parsowania numeru %s: %s", issue.issue_url, exc)

    issue_rows = [asdict(x) for x in issues]
    article_rows = [asdict(x) for x in articles]
    keyword_rows = [asdict(x) for x in keywords_long]

    write_csv(outdir / "app_issues.csv", issue_rows, list(IssueRecord.__dataclass_fields__.keys()))
    write_csv(outdir / "app_articles.csv", article_rows, list(ArticleRecord.__dataclass_fields__.keys()))
    write_csv(outdir / "app_keywords_long.csv", keyword_rows, list(KeywordRecord.__dataclass_fields__.keys()))

    logging.info("Zapisano: %s", outdir / "app_issues.csv")
    logging.info("Zapisano: %s", outdir / "app_articles.csv")
    logging.info("Zapisano: %s", outdir / "app_keywords_long.csv")
    logging.info("Artykuły: %s; rekordy keyword-long: %s", len(article_rows), len(keyword_rows))


if __name__ == "__main__":
    main()
