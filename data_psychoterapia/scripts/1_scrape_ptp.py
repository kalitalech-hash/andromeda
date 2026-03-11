import csv
import json
import os
import random
import re
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ----------------------------
# Ustawienia
# ----------------------------
BASE = "https://www.psychoterapiaptp.pl"
ARCHIVE_URL = urljoin(BASE, "/Archiwum")

HEADERS = {
    "User-Agent": "PTP-Keywords-Research/1.1 (personal research; contact: you@example.com)"
}

SLEEP_SEC = 0.8          # przerwa między requestami (plus losowy jitter)
TIMEOUT = 90             # dłużej niż default, bo serwer czasem zamula
MAX_RETRIES = 6          # retry na handshake/timeouty
OUTPUT_DIR = Path("output")

RAW_CSV = OUTPUT_DIR / "raw_articles.csv"
LONG_CSV = OUTPUT_DIR / "keywords_long.csv"
FAILED_JSON = OUTPUT_DIR / "failed_urls.json"

# ----------------------------
# Sesja HTTP z retry
# ----------------------------
_session = requests.Session()
_retry = Retry(
    total=MAX_RETRIES,
    connect=MAX_RETRIES,
    read=MAX_RETRIES,
    backoff_factor=1.2,  # 1.2s, 2.4s, 4.8s...
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
    raise_on_status=False,
)
_adapter = HTTPAdapter(max_retries=_retry, pool_connections=20, pool_maxsize=20)
_session.mount("https://", _adapter)
_session.mount("http://", _adapter)


@dataclass(frozen=True)
class ArticleMeta:
    issue_label: str  # np. "4/2005 vol. 135"
    year: int | None
    item_type: str    # ARTICLE / EDITORIAL MATERIAL itd.
    title: str
    url: str


def polite_sleep():
    time.sleep(SLEEP_SEC + random.random() * 0.4)


def get_soup(url: str) -> BeautifulSoup:
    last_exc = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            r = _session.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            polite_sleep()
            return BeautifulSoup(r.text, "lxml")
        except Exception as e:
            last_exc = e
            wait = min(30, 2 ** attempt)  # 2,4,8,16,30...
            print(f"[WARN] Problem z {url} (próba {attempt}/{MAX_RETRIES}): {type(e).__name__} — czekam {wait}s")
            time.sleep(wait)
    raise last_exc


def extract_issue_urls() -> list[str]:
    soup = get_soup(ARCHIVE_URL)
    issue_urls = set()
    for a in soup.select("a[href]"):
        href = a.get("href", "")
        if "Numer-" in href or "Issue-" in href:
            issue_urls.add(urljoin(BASE, href))
    return sorted(issue_urls)


def extract_issue_label_and_year(text: str) -> tuple[str, int | None]:
    # wzorzec typu: "4/2005 vol. 135"
    m = re.search(r"\b(\d\/\d{4}\s+vol\.\s*\d+)\b", text)
    label = m.group(1) if m else ""
    ym = re.search(r"/(\d{4})\b", label)
    year = int(ym.group(1)) if ym else None
    return label, year


def parse_issue(issue_url: str) -> list[ArticleMeta]:
    soup = get_soup(issue_url)
    full_text = soup.get_text(" ", strip=True)
    issue_label, year = extract_issue_label_and_year(full_text)

    allowed_types = {
        "ARTICLE",
        "EDITORIAL MATERIAL",
        "BOOK REVIEW",
        "LETTER TO THE EDITOR",
        "REPORT",
        "CASE REPORT",
        "UNKNOWN",
    }

    metas: list[ArticleMeta] = []
    current_type = "UNKNOWN"

    # Heurystyka: na stronach numerów są nagłówki sekcji i linki do pozycji.
    for el in soup.find_all(["h2", "h3", "strong", "b", "a"]):
        t = el.get_text(" ", strip=True).strip()
        if not t:
            continue

        up = t.upper()
        if up in allowed_types:
            current_type = up
            continue

        if el.name == "a" and el.get("href"):
            href = el["href"]
            title = t

            if len(title) < 6:
                continue
            if "PDF" in up or "POBIERZ" in up:
                continue

            url = urljoin(BASE, href)
            if not url.startswith(BASE):
                continue

            # Strony artykułów zwykle mają ".html" albo strukturę z "%2C"
            if not (url.endswith(".html") or "%2C" in url):
                continue

            metas.append(ArticleMeta(
                issue_label=issue_label,
                year=year,
                item_type=current_type,
                title=title,
                url=url
            ))

    uniq = {m.url: m for m in metas}
    return list(uniq.values())


def parse_article_keywords(article_url: str) -> list[str]:
    soup = get_soup(article_url)

    keywords = []
    for a in soup.select("a[href]"):
        href = a.get("href", "")
        txt = a.get_text(" ", strip=True)
        if not txt:
            continue
        # Na stronach artykułów keywords są linkami do stron "Slowo-kluczowe-..." lub "Keyword-..."
        if "Slowo-kluczowe" in href or "Keyword-" in href:
            keywords.append(txt)

    # dedup zachowując kolejność
    out = []
    seen = set()
    for k in keywords:
        if k not in seen:
            out.append(k)
            seen.add(k)
    return out


def load_done_urls(long_csv_path: Path) -> set[str]:
    """
    Wczytuje już przetworzone artykuły z keywords_long.csv,
    żeby dało się wznawiać bez dublowania.
    """
    done = set()
    if not long_csv_path.exists():
        return done

    try:
        with open(long_csv_path, "r", encoding="utf-8", newline="") as f:
            r = csv.DictReader(f)
            for row in r:
                u = (row.get("url") or "").strip()
                if u:
                    done.add(u)
    except Exception as e:
        print(f"[WARN] Nie udało się wczytać istniejącego {long_csv_path}: {e}")
    return done


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    issue_urls = extract_issue_urls()
    print(f"Znaleziono numerów: {len(issue_urls)}")

    # 1) Zbierz metadane artykułów
    all_articles: list[ArticleMeta] = []
    for i, issue_url in enumerate(issue_urls, start=1):
        try:
            metas = parse_issue(issue_url)
            all_articles.extend(metas)
        except Exception as e:
            print(f"[ERROR] Nie udało się sparsować numeru: {issue_url} ({type(e).__name__}) — pomijam")
        if i % 10 == 0:
            print(f"  przetworzono numery: {i}/{len(issue_urls)}  (pozycji: {len(all_articles)})")

    # 2) Zapisz raw (nadpisuje)
    with open(RAW_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["year", "issue_label", "item_type", "title", "url"])
        w.writeheader()
        for a in all_articles:
            w.writerow({
                "year": a.year,
                "issue_label": a.issue_label,
                "item_type": a.item_type,
                "title": a.title,
                "url": a.url
            })

    print(f"Zapisano listę pozycji: {RAW_CSV}")

    # 3) Wznawianie: wczytaj już zrobione URL-e
    done_urls = load_done_urls(LONG_CSV)
    if done_urls:
        print(f"Wykryto już przetworzone artykuły: {len(done_urls)} — będę je pomijać (resume).")

    # 4) Zapis long (append, ale bez dublowania)
    file_exists = LONG_CSV.exists()
    failed = []

    with open(LONG_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["year", "issue_label", "item_type", "title", "url", "keyword"])
        if not file_exists:
            w.writeheader()

        total = len(all_articles)
        processed = 0
        skipped = 0

        for idx, a in enumerate(all_articles, start=1):
            if a.url in done_urls:
                skipped += 1
                continue

            try:
                kws = parse_article_keywords(a.url)
            except Exception as e:
                print(f"[ERROR] Nie udało się pobrać keywords: {a.url} ({type(e).__name__}) — pomijam")
                failed.append({
                    "url": a.url,
                    "title": a.title,
                    "issue": a.issue_label,
                    "error": repr(e),
                })
                continue

            # nawet jeśli nie ma keywords, zapisujemy "pusty" fakt? Tu: nie zapisujemy pustych.
            for kw in kws:
                w.writerow({
                    "year": a.year,
                    "issue_label": a.issue_label,
                    "item_type": a.item_type,
                    "title": a.title,
                    "url": a.url,
                    "keyword": kw
                })

            done_urls.add(a.url)
            processed += 1

            if idx % 50 == 0:
                print(f"  artykuły: {idx}/{total} | nowe: {processed} | pominięte(resume): {skipped} | błędy: {len(failed)}")

    with open(FAILED_JSON, "w", encoding="utf-8") as f:
        json.dump(failed, f, ensure_ascii=False, indent=2)

    print("\n✅ Gotowe (scrape keywords).")
    print(f" - {RAW_CSV}")
    print(f" - {LONG_CSV}")
    print(f" - {FAILED_JSON} (nieudane URL-e: {len(failed)})")

    if failed:
        print("\nWskazówka: uruchom ten skrypt jeszcze raz — często dozbiera brakujące połączenia.")


if __name__ == "__main__":
    main()
