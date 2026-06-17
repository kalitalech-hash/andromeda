#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build a PTPP public members snapshot.

Project: ptpp_publication_contribution_pilot
Agent: Andromeda Nowicka (v0.5)
Purpose: create auditable CSV layers from public PTPP membership-related pages.

Default behavior:
- metadata/list acquisition only;
- no PDF downloads;
- no login/session automation;
- no bypassing bot protection;
- polite requests and explicit user-agent;
- if a page returns anti-bot / verification HTML, stop for that page and log it;
- optional offline mode can parse HTML files manually saved by a human researcher.

Outputs:
- data_raw/ptpp_memberships_snapshot.csv   one row per source-list occurrence
- data_raw/ptpp_members_snapshot.csv       de-duplicated persons, membership categories aggregated
- logs/ptpp_members_acquisition_log.csv    request/parse log
- docs/ptpp_members_snapshot_summary.json  machine-readable summary

Usage examples:
    python scripts/build_ptpp_members_snapshot.py \
        --contact-email your.email@example.org

    python scripts/build_ptpp_members_snapshot.py \
        --contact-email your.email@example.org \
        --include-supervisors

    python scripts/build_ptpp_members_snapshot.py \
        --offline-html-dir data_raw/ptpp_html_pages \
        --no-fetch

If PTPP blocks automated access for a page, do not try to circumvent.
Use --offline-html-dir with HTML files saved manually from a browser, e.g.:
    data_raw/ptpp_html_pages/certified_therapists.html
    data_raw/ptpp_html_pages/extraordinary_members.html
    data_raw/ptpp_html_pages/candidates.html
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import re
import sys
import time
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup


DEFAULT_SOURCES = [
    {
        "source_page_key": "certified_therapists",
        "membership_category": "certified_therapist_ptpp",
        "url": "https://ptpp.pl/certyfikowane-i-terapeutki-i-terapeuci-psychoanalityczne-i-ptpp/",
        "title_markers": [
            "Certyfikowani terapeuci psychoanalityczni PTPP",
            "Certyfikowane i terapeutki i terapeuci psychoanalityczne i PTPP",
            "Certyfikowane terapeutki i certyfikowani terapeuci psychoanalityczni PTPP",
        ],
        "offline_filename": "certified_therapists.html",
        "parse_mode": "name_lines",
    },
    {
        "source_page_key": "extraordinary_members",
        "membership_category": "extraordinary_member_ptpp",
        "url": "https://ptpp.pl/czlonkinie-i-czlonkowie-nadzwyczajne-i-ptpp/",
        "title_markers": [
            "Członkowie nadzwyczajni PTPP",
            "Członkinie i Członkowie nadzwyczajne i PTPP",
        ],
        "offline_filename": "extraordinary_members.html",
        "parse_mode": "name_lines",
    },
    {
        "source_page_key": "candidates",
        "membership_category": "candidate_ptpp",
        "url": "https://ptpp.pl/kandydatki-i-kandydaci-ptpp/",
        "title_markers": [
            "Kandydatki i kandydaci PTPP",
        ],
        "offline_filename": "candidates.html",
        "parse_mode": "name_lines",
    },
]

OPTIONAL_SOURCES = [
    {
        "source_page_key": "supervisors",
        "membership_category": "supervisor_ptpp",
        "url": "https://ptpp.pl/o-nas/superwizorki-i-superwizorzy-ptpp/",
        "title_markers": [
            "Superwizorki i Superwizorzy PTPP",
        ],
        "offline_filename": "supervisors.html",
        "parse_mode": "name_dash_attribute",
    },
]


FOOTER_STOP_MARKERS = [
    "Bądź na bieżąco",
    "Siedziba",
    "Kontakt",
    "Sekretariat",
    "Numer konta",
    "Zarząd PTPP",
    "Komisja Etyki",
    "Polityka prywatności",
    "Ta strona korzysta z ciasteczek",
]

NON_NAME_EXACT = {
    "Home",
    "O nas",
    "Przejdź do treści",
    "Image",
    "Polskie Towarzystwo Psychoterapii Psychoanalitycznej",
    "Imię i nazwisko – Obszar specjalizacji w superwizji",
    "Imię i nazwisko - Obszar specjalizacji w superwizji",
}

ANTI_BOT_PATTERNS = [
    "please wait while your request is being verified",
    "checking your browser",
    "cf-browser-verification",
    "captcha",
    "access denied",
    "just a moment",
]


@dataclass
class AcquisitionLogRow:
    timestamp_utc: str
    source_page_key: str
    url: str
    action: str
    status_code: str = ""
    content_type: str = ""
    response_size: str = ""
    success: str = ""
    message: str = ""


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def normalize_space(s: str) -> str:
    s = html.unescape(s)
    s = s.replace("\xa0", " ")
    s = re.sub(r"[ \t\r\f\v]+", " ", s)
    s = re.sub(r"\n+", "\n", s)
    return s.strip()


def normalize_dashes(s: str) -> str:
    # Preserve hyphens inside surnames, normalize dash separators.
    return (
        s.replace("—", "–")
         .replace("−", "–")
         .replace(" - ", " – ")
         .replace("–", "–")
    )


def strip_accents_for_key(s: str) -> str:
    nkfd = unicodedata.normalize("NFKD", s)
    return "".join(ch for ch in nkfd if not unicodedata.combining(ch))


def person_key(name: str) -> str:
    s = normalize_space(normalize_dashes(name)).lower()
    s = s.replace("’", "'").replace("`", "'")
    s = strip_accents_for_key(s)
    s = re.sub(r"[^a-z0-9' -]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def stable_person_id(normalized_key: str) -> str:
    h = hashlib.sha1(normalized_key.encode("utf-8")).hexdigest()[:12]
    return f"ptpp_person_{h}"


def looks_like_antibot(text: str) -> bool:
    low = text.lower()
    return any(p in low for p in ANTI_BOT_PATTERNS)


def fetch_url(url: str, contact_email: str, delay_seconds: float, timeout: int) -> Tuple[Optional[str], AcquisitionLogRow]:
    ua = (
        "AndromedaNowickaBibliometricBot/0.5 "
        f"(metadata-only bibliometric research; contact: {contact_email}; "
        "no PDF mirroring; polite delay)"
    )
    headers = {
        "User-Agent": ua,
        "From": contact_email,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pl,en;q=0.8",
    }
    time.sleep(delay_seconds)
    ts = utc_now()
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        text = resp.text or ""
        ct = resp.headers.get("content-type", "")
        log = AcquisitionLogRow(
            timestamp_utc=ts,
            source_page_key="",
            url=url,
            action="fetch",
            status_code=str(resp.status_code),
            content_type=ct,
            response_size=str(len(text.encode("utf-8"))),
            success=str(resp.ok and not looks_like_antibot(text)),
            message="ok" if resp.ok else f"http_status_{resp.status_code}",
        )
        if looks_like_antibot(text):
            log.success = "False"
            log.message = "anti_bot_or_verification_page_detected; stop and use offline HTML if needed"
            return None, log
        if not resp.ok:
            return None, log
        return text, log
    except Exception as e:
        return None, AcquisitionLogRow(
            timestamp_utc=ts,
            source_page_key="",
            url=url,
            action="fetch",
            success="False",
            message=f"{type(e).__name__}: {e}",
        )


def read_offline_html(offline_dir: Path, filename: str) -> Tuple[Optional[str], str]:
    path = offline_dir / filename
    if not path.exists():
        return None, f"offline_file_not_found: {path}"
    return path.read_text(encoding="utf-8", errors="replace"), f"offline_file_read: {path}"


def soup_to_lines(raw_html: str) -> List[str]:
    soup = BeautifulSoup(raw_html, "lxml")
    # Remove elements unlikely to contain membership content.
    for tag in soup(["script", "style", "noscript", "svg", "form"]):
        tag.decompose()
    text = soup.get_text("\n")
    lines = []
    for line in text.splitlines():
        line = normalize_space(normalize_dashes(line))
        if line:
            lines.append(line)
    return lines


def find_content_window(lines: List[str], title_markers: List[str]) -> Tuple[List[str], str]:
    """Return lines after the best title marker and before footer."""
    start_idx = None
    marker_used = ""
    normalized_lines = [person_key(x) for x in lines]
    normalized_markers = [person_key(x) for x in title_markers]

    for i, line_key in enumerate(normalized_lines):
        for marker, marker_key in zip(title_markers, normalized_markers):
            if marker_key and (line_key == marker_key or marker_key in line_key):
                start_idx = i + 1
                marker_used = marker
                break
        if start_idx is not None:
            break

    if start_idx is None:
        # Fallback: find first line that resembles a Polish name after navigation.
        start_idx = 0
        marker_used = "fallback_start_0"

    end_idx = len(lines)
    for j in range(start_idx, len(lines)):
        if any(stop.lower() in lines[j].lower() for stop in FOOTER_STOP_MARKERS):
            end_idx = j
            break

    return lines[start_idx:end_idx], marker_used


def is_probable_name_line(line: str) -> bool:
    if not line or line in NON_NAME_EXACT:
        return False
    if len(line) < 5 or len(line) > 120:
        return False
    if "@" in line or "http" in line.lower() or "www." in line.lower():
        return False
    if re.search(r"\d", line):
        return False
    if line.startswith("#") or line.startswith("*"):
        return False
    # Exclude typical navigation/footer fragments.
    nav_words = [
        "Terapia", "Szkolenia", "Wydarzenia", "Sekcje", "Regiony", "Oddziały",
        "Koła", "Znajdź terapeutę", "Dołącz do nas", "Rodzaje członkostwa",
        "Konferencje", "Czytelnia", "Open Lectures", "SORGA",
    ]
    if line in nav_words:
        return False
    # Names should normally have at least two tokens.
    tokens = line.split()
    if len(tokens) < 2:
        return False
    # Keep Polish surnames with internal dashes and apostrophes.
    # Require at least one uppercase initial; avoids generic text.
    if not any(ch.isupper() for ch in line):
        return False
    return True


def parse_name_and_attribute(line: str, parse_mode: str) -> Tuple[str, str]:
    """Return (name_raw, source_attribute)."""
    source_attribute = ""
    name = line

    if parse_mode == "name_dash_attribute":
        # Supervision page: "Name – adults; children ..."
        parts = re.split(r"\s+–\s+", line, maxsplit=1)
        if len(parts) == 2:
            name, source_attribute = parts[0].strip(), parts[1].strip()
    # Remove parenthetical locality from name but preserve in attribute.
    m = re.search(r"\(([^)]+)\)", name)
    if m:
        source_attribute = (source_attribute + "; " if source_attribute else "") + f"parenthetical_note={m.group(1)}"
        name = re.sub(r"\s*\([^)]+\)\s*", " ", name).strip()

    return normalize_space(name), normalize_space(source_attribute)


def guess_surname_given_names(name_raw: str) -> Tuple[str, str]:
    """
    PTPP list is typically surname-first: "Kowalska Anna Maria".
    This heuristic is intentionally conservative and preserves name_raw as source of truth.
    """
    parts = name_raw.split()
    if len(parts) < 2:
        return name_raw, ""
    # Treat all tokens except final one as surname_guess by default.
    # If 3+ tokens and the last two look like given names, this is not knowable automatically.
    # We choose surname-first minimal rule: first token(s) before last token = surname_guess.
    surname_guess = " ".join(parts[:-1])
    given_names_guess = parts[-1]
    return surname_guess, given_names_guess


def build_records_for_source(source: Dict, raw_html: str, snapshot_date_utc: str) -> Tuple[List[Dict], Dict]:
    lines = soup_to_lines(raw_html)
    window, marker = find_content_window(lines, source["title_markers"])
    records = []
    rejected_lines = []

    for idx, line in enumerate(window, start=1):
        if not is_probable_name_line(line):
            rejected_lines.append(line)
            continue
        name_raw, source_attribute = parse_name_and_attribute(line, source["parse_mode"])
        if not is_probable_name_line(name_raw):
            rejected_lines.append(line)
            continue

        normalized_key = person_key(name_raw)
        surname_guess, given_names_guess = guess_surname_given_names(name_raw)

        records.append({
            "source_page_key": source["source_page_key"],
            "membership_category": source["membership_category"],
            "source_url": source["url"],
            "snapshot_date_utc": snapshot_date_utc,
            "row_index_in_source": len(records) + 1,
            "name_raw": name_raw,
            "full_name_ptpp_order": name_raw,
            "surname_guess": surname_guess,
            "given_names_guess": given_names_guess,
            "normalized_person_key": normalized_key,
            "source_attribute": source_attribute,
            "extraction_method": f"html_text_window:{marker}",
            "review_flag": "",
        })

    summary = {
        "source_page_key": source["source_page_key"],
        "membership_category": source["membership_category"],
        "url": source["url"],
        "title_marker_used": marker,
        "lines_in_content_window": len(window),
        "records_extracted": len(records),
        "rejected_line_count": len(rejected_lines),
        "rejected_line_examples": rejected_lines[:20],
    }
    return records, summary


def write_csv(path: Path, rows: List[Dict], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def aggregate_persons(membership_rows: List[Dict]) -> List[Dict]:
    by_key: Dict[str, List[Dict]] = {}
    for row in membership_rows:
        by_key.setdefault(row["normalized_person_key"], []).append(row)

    persons = []
    for key, rows in sorted(by_key.items(), key=lambda kv: kv[0]):
        # Prefer the longest raw name as canonical; keeps double names better.
        canonical = sorted({r["name_raw"] for r in rows}, key=lambda s: (-len(s), s))[0]
        surname_guess, given_names_guess = guess_surname_given_names(canonical)
        categories = sorted({r["membership_category"] for r in rows})
        page_keys = sorted({r["source_page_key"] for r in rows})
        urls = sorted({r["source_url"] for r in rows})
        attrs = sorted({r["source_attribute"] for r in rows if r.get("source_attribute")})
        persons.append({
            "person_id": stable_person_id(key),
            "full_name_canonical_ptpp_order": canonical,
            "surname_guess": surname_guess,
            "given_names_guess": given_names_guess,
            "normalized_person_key": key,
            "membership_categories": ";".join(categories),
            "source_page_keys": ";".join(page_keys),
            "source_urls": ";".join(urls),
            "source_attributes": ";".join(attrs),
            "membership_occurrence_count": len(rows),
            "duplicate_name_flag": "yes" if len(rows) > 1 else "",
            "snapshot_date_utc": rows[0]["snapshot_date_utc"],
            "disambiguation_status": "not_started",
            "manual_review_flag": "",
        })
    return persons


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--contact-email", default="CONTACT_EMAIL", help="Real contact email for From/User-Agent headers.")
    parser.add_argument("--output-dir", default=".", help="Project root output directory.")
    parser.add_argument("--delay-seconds", type=float, default=5.0, help="Delay before each HTTP request.")
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--no-fetch", action="store_true", help="Do not request web pages; use offline HTML only.")
    parser.add_argument("--offline-html-dir", default="", help="Directory with manually saved source HTML files.")
    parser.add_argument("--include-supervisors", action="store_true", help="Also parse public supervisors page as an additional role layer.")
    parser.add_argument("--save-source-html", action="store_true", help="Save fetched HTML into data_raw/ptpp_html_pages.")
    args = parser.parse_args(argv)

    project = Path(args.output_dir)
    data_raw = project / "data_raw"
    logs_dir = project / "logs"
    docs_dir = project / "docs"
    html_dir = data_raw / "ptpp_html_pages"
    data_raw.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    docs_dir.mkdir(parents=True, exist_ok=True)
    if args.save_source_html:
        html_dir.mkdir(parents=True, exist_ok=True)

    if args.contact_email == "CONTACT_EMAIL" and not args.no_fetch:
        print("ERROR: replace CONTACT_EMAIL using --contact-email before fetching.", file=sys.stderr)
        return 2

    sources = list(DEFAULT_SOURCES)
    if args.include_supervisors:
        sources.extend(OPTIONAL_SOURCES)

    snapshot_date_utc = utc_now()
    all_membership_rows: List[Dict] = []
    acquisition_logs: List[AcquisitionLogRow] = []
    parse_summaries: List[Dict] = []
    offline_dir = Path(args.offline_html_dir) if args.offline_html_dir else None

    for source in sources:
        raw_html = None

        if offline_dir:
            raw_html, msg = read_offline_html(offline_dir, source["offline_filename"])
            acquisition_logs.append(AcquisitionLogRow(
                timestamp_utc=utc_now(),
                source_page_key=source["source_page_key"],
                url=source["url"],
                action="read_offline_html",
                success=str(raw_html is not None),
                message=msg,
            ))

        if raw_html is None and not args.no_fetch:
            raw_html, logrow = fetch_url(source["url"], args.contact_email, args.delay_seconds, args.timeout)
            logrow.source_page_key = source["source_page_key"]
            acquisition_logs.append(logrow)
            if raw_html and args.save_source_html:
                out_html = html_dir / source["offline_filename"]
                out_html.write_text(raw_html, encoding="utf-8")

        if raw_html is None:
            parse_summaries.append({
                "source_page_key": source["source_page_key"],
                "url": source["url"],
                "records_extracted": 0,
                "status": "not_parsed_no_html",
            })
            continue

        if looks_like_antibot(raw_html):
            parse_summaries.append({
                "source_page_key": source["source_page_key"],
                "url": source["url"],
                "records_extracted": 0,
                "status": "not_parsed_antibot_detected",
            })
            continue

        records, summary = build_records_for_source(source, raw_html, snapshot_date_utc)
        summary["status"] = "parsed"
        parse_summaries.append(summary)
        all_membership_rows.extend(records)

    membership_fields = [
        "source_page_key", "membership_category", "source_url", "snapshot_date_utc",
        "row_index_in_source", "name_raw", "full_name_ptpp_order",
        "surname_guess", "given_names_guess", "normalized_person_key",
        "source_attribute", "extraction_method", "review_flag",
    ]
    person_fields = [
        "person_id", "full_name_canonical_ptpp_order", "surname_guess", "given_names_guess",
        "normalized_person_key", "membership_categories", "source_page_keys", "source_urls",
        "source_attributes", "membership_occurrence_count", "duplicate_name_flag",
        "snapshot_date_utc", "disambiguation_status", "manual_review_flag",
    ]
    log_fields = list(AcquisitionLogRow.__dataclass_fields__.keys())

    memberships_path = data_raw / "ptpp_memberships_snapshot.csv"
    persons_path = data_raw / "ptpp_members_snapshot.csv"
    log_path = logs_dir / "ptpp_members_acquisition_log.csv"
    summary_path = docs_dir / "ptpp_members_snapshot_summary.json"

    write_csv(memberships_path, all_membership_rows, membership_fields)
    persons = aggregate_persons(all_membership_rows)
    write_csv(persons_path, persons, person_fields)
    write_csv(log_path, [r.__dict__ for r in acquisition_logs], log_fields)

    summary = {
        "project": "ptpp_publication_contribution_pilot",
        "created_at_utc": snapshot_date_utc,
        "sources_requested": sources,
        "parse_summaries": parse_summaries,
        "membership_occurrences": len(all_membership_rows),
        "deduplicated_persons": len(persons),
        "outputs": {
            "memberships_csv": str(memberships_path),
            "persons_csv": str(persons_path),
            "acquisition_log_csv": str(log_path),
        },
        "methodological_note": (
            "The table is a public-list snapshot. It should not be interpreted as a complete "
            "or official registry beyond the source pages and acquisition date. Membership-linked "
            "publication analysis requires later author disambiguation and manual audit."
        ),
    }
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps({
        "membership_occurrences": len(all_membership_rows),
        "deduplicated_persons": len(persons),
        "memberships_csv": str(memberships_path),
        "persons_csv": str(persons_path),
        "log_csv": str(log_path),
        "summary_json": str(summary_path),
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
