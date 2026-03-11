# 1_scrape_psychiatria_polska.py
# -*- coding: utf-8 -*-

import csv
import os
import re
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

BASE = "https://www.psychiatriapolska.pl/"
ARCHIVE_URL = urljoin(BASE, "Archiwum")

OUT_DIR = "output"
ARTICLES_CSV = os.path.join(OUT_DIR, "pp_articles.csv")
KEYWORDS_LONG_CSV = os.path.join(OUT_DIR, "pp_keywords_long.csv")
TOPICS_LONG_CSV = os.path.join(OUT_DIR, "pp_topics_long.csv")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/122.0 Safari/537.36"
}

TIMEOUT = 45
SLEEP_BETWEEN = 0.6
MAX_RETRIES = 6

# Jeśli chcesz przyciąć zakres:
MIN_YEAR = 1900
MAX_YEAR = 2100

@dataclass
class Article:
    url: str
    title: str
    year: Optional[int]
    volume: Optional[int]
    issue: Optional[int]
    pages: Optional[str]
    doi: Optional[str]
    article_type: Optional[str]

def ensure_out_dir() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)

def get_soup(session: requests.Session, url: str) -> BeautifulSoup:
    last_err = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = session.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            return BeautifulSoup(r.text, "html.parser")
        except Exception as e:
            last_err = e
            wait = min(2 ** (attempt - 1), 20)
            print(f"[WARN] {url} -> {type(e).__name__}: {e}. Retry in {wait}s (attempt {attempt}/{MAX_RETRIES})")
            time.sleep(wait)
    raise RuntimeError(f"Failed to fetch {url} after {MAX_RETRIES} retries: {last_err}")

def parse_issue_links(soup: BeautifulSoup) -> List[str]:
    """
    Z archiwum wyciąga linki do numerów.
    Na stronie są linki typu:
      - /Numer-6-2025%2C15233
      - /Numer-6-2025,15233
    """
    issue_links: List[str] = []
    pat = re.compile(r"Numer-\d+-\d{4}(%2C|,)\d+")

    for a in soup.select("a[href]"):
        href = a.get("href", "").strip()
        if not href:
            continue
        if pat.search(href):
            issue_links.append(urljoin(BASE, href.lstrip("/")))

    # unikalnie, zachowując kolejność
    seen: Set[str] = set()
    out: List[str] = []
    for u in issue_links:
        if u not in seen:
            seen.add(u)
            out.append(u)

    return out

def parse_year_volume_issue_from_text(text: str) -> Tuple[Optional[int], Optional[int], Optional[int], Optional[str]]:
    """
    Z linii typu: 'Psychiatr Pol 2009;43(6):671-681'
    """
    text = " ".join(text.split())
    m = re.search(r"(\d{4});\s*(\d+)\s*\((\d+)\)\s*:\s*([0-9\-–]+)", text)
    if not m:
        return None, None, None, None
    return int(m.group(1)), int(m.group(2)), int(m.group(3)), m.group(4)

def parse_issue_page(session: requests.Session, issue_url: str) -> List[str]:
    """Z numeru wyciąga linki do stron artykułów (te z .html)."""
    soup = get_soup(session, issue_url)
    urls: List[str] = []
    for a in soup.select("a[href]"):
        href = a.get("href", "").strip()
        if not href:
            continue
        if href.endswith(".html"):
            urls.append(urljoin(BASE, href.lstrip("/")))

    # unikalnie
    seen: Set[str] = set()
    out: List[str] = []
    for u in urls:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out

def extract_keywords(soup: BeautifulSoup) -> List[str]:
    """Wyciąga teksty linków spod nagłówka 'SŁOWA KLUCZOWE' (lub 'KEYWORDS')."""
    text = soup.get_text("\n")
    if "SŁOWA KLUCZOWE" not in text and "KEYWORDS" not in text:
        return []

    header = None
    for tag in soup.find_all(["h1", "h2", "h3", "strong", "div", "p"]):
        if tag.get_text(strip=True).upper() in ["SŁOWA KLUCZOWE", "KEYWORDS"]:
            header = tag
            break

    kws: List[str] = []
    if header:
        parent = header.parent if header.parent else soup
        for a in parent.select("a[href]"):
            t = a.get_text(" ", strip=True)
            if not t:
                continue
            if len(t) > 80:
                continue
            if any(x.lower() in t.lower() for x in ["pdf", "doi", "streszczenie", "abstract", "statystyki"]):
                continue
            kws.append(t)

    # dedupe
    out: List[str] = []
    seen: Set[str] = set()
    for k in kws:
        kk = k.strip()
        if kk and kk not in seen:
            seen.add(kk)
            out.append(kk)
    return out

def extract_topics(soup: BeautifulSoup) -> List[str]:
    """Wyciąga dziedziny spod nagłówka 'DZIEDZINY' (lub 'TOPICS') jeśli występują."""
    txt = soup.get_text("\n")
    if "DZIEDZINY" not in txt and "TOPICS" not in txt:
        return []

    header = None
    for tag in soup.find_all(["h1", "h2", "h3", "strong", "div", "p"]):
        if tag.get_text(strip=True).upper() in ["DZIEDZINY", "TOPICS"]:
            header = tag
            break

    topics: List[str] = []
    if header:
        parent = header.parent if header.parent else soup
        for a in parent.select("a[href]"):
            t = a.get_text(" ", strip=True)
            if not t:
                continue
            if len(t) > 120:
                continue
            if any(x.lower() in t.lower() for x in ["pdf", "doi", "streszczenie", "abstract", "statystyki"]):
                continue
            topics.append(t)

    # dedupe
    out: List[str] = []
    seen: Set[str] = set()
    for t in topics:
        tt = t.strip()
        if tt and tt not in seen:
            seen.add(tt)
            out.append(tt)
    return out

def parse_article_page(session: requests.Session, url: str) -> Tuple[Article, List[str], List[str]]:
    soup = get_soup(session, url)

    h = soup.find(["h1", "h2"])
    title = h.get_text(" ", strip=True) if h else (soup.title.get_text(" ", strip=True) if soup.title else url)

    article_type = None
    for key in ["REVIEW", "ARTICLE", "CASE REPORT", "EDITORIAL", "LETTER"]:
        if re.search(rf"\b{re.escape(key)}\b", soup.get_text("\n")):
            article_type = key
            break

    doi = None
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        if "doi.org/" in href:
            m = re.search(r"(https?://doi\.org/\S+)", href)
            doi = m.group(1) if m else href
            break

    year = volume = issue = None
    pages = None
    text_lines = [ln.strip() for ln in soup.get_text("\n").split("\n") if ln.strip()]
    for ln in text_lines:
        if ln.startswith("Psychiatr Pol") and ";" in ln and "(" in ln and ":" in ln:
            y, v, i, p = parse_year_volume_issue_from_text(ln)
            year, volume, issue, pages = y, v, i, p
            break

    keywords = extract_keywords(soup)
    topics = extract_topics(soup)

    art = Article(
        url=url,
        title=title,
        year=year,
        volume=volume,
        issue=issue,
        pages=pages,
        doi=doi,
        article_type=article_type,
    )
    return art, keywords, topics

def write_csvs(articles: List[Article], kw_long: List[Dict], topics_long: List[Dict]) -> None:
    ensure_out_dir()

    with open(ARTICLES_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["url", "title", "year", "volume", "issue", "pages", "doi", "article_type"],
        )
        w.writeheader()
        for a in articles:
            w.writerow({
                "url": a.url,
                "title": a.title,
                "year": a.year,
                "volume": a.volume,
                "issue": a.issue,
                "pages": a.pages,
                "doi": a.doi,
                "article_type": a.article_type,
            })

    with open(KEYWORDS_LONG_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["url", "year", "volume", "issue", "doi", "keyword_raw"],
        )
        w.writeheader()
        for row in kw_long:
            w.writerow(row)

    with open(TOPICS_LONG_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["url", "year", "volume", "issue", "doi", "topic_raw"],
        )
        w.writeheader()
        for row in topics_long:
            w.writerow(row)

def main() -> None:
    ensure_out_dir()
    session = requests.Session()

    print(f"[INFO] Fetch archive: {ARCHIVE_URL}")
    archive_soup = get_soup(session, ARCHIVE_URL)

    issue_links = parse_issue_links(archive_soup)
    print(f"[INFO] Found issues: {len(issue_links)}")
    print("[INFO] Sample issue links:", issue_links[:10])

    all_article_urls: List[str] = []
    for idx, issue_url in enumerate(issue_links, 1):
        print(f"[INFO] Issue {idx}/{len(issue_links)}: {issue_url}")
        try:
            urls = parse_issue_page(session, issue_url)
            all_article_urls.extend(urls)
        except Exception as e:
            print(f"[WARN] Failed issue page: {issue_url} -> {e}")
        time.sleep(SLEEP_BETWEEN)

    # dedupe
    seen: Set[str] = set()
    article_urls: List[str] = []
    for u in all_article_urls:
        if u not in seen:
            seen.add(u)
            article_urls.append(u)

    print(f"[INFO] Unique article pages: {len(article_urls)}")

    articles: List[Article] = []
    kw_long: List[Dict] = []
    topics_long: List[Dict] = []

    for idx, url in enumerate(article_urls, 1):
        print(f"[INFO] Article {idx}/{len(article_urls)}")
        try:
            art, kws, topics = parse_article_page(session, url)

            if art.year is not None and (art.year < MIN_YEAR or art.year > MAX_YEAR):
                continue

            articles.append(art)

            for k in kws:
                kw_long.append({
                    "url": art.url,
                    "year": art.year,
                    "volume": art.volume,
                    "issue": art.issue,
                    "doi": art.doi,
                    "keyword_raw": k,
                })

            for t in topics:
                topics_long.append({
                    "url": art.url,
                    "year": art.year,
                    "volume": art.volume,
                    "issue": art.issue,
                    "doi": art.doi,
                    "topic_raw": t,
                })

        except Exception as e:
            print(f"[WARN] Failed article: {url} -> {e}")

        time.sleep(SLEEP_BETWEEN)

    print(f"[INFO] Parsed articles: {len(articles)}")
    print(f"[INFO] Keyword rows: {len(kw_long)}")
    print(f"[INFO] Topic rows: {len(topics_long)}")

    write_csvs(articles, kw_long, topics_long)
    print(f"[DONE] Wrote:\n- {ARTICLES_CSV}\n- {KEYWORDS_LONG_CSV}\n- {TOPICS_LONG_CSV}")

if __name__ == "__main__":
    main()