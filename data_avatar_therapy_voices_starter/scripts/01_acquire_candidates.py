#!/usr/bin/env python3
"""Andromeda v0.5 | Stage 01 v0.4.1: API-key-enabled, resumable OpenAlex acquisition.

Uses explicit HITL approved-source manifest; never guesses approvals from malformed CSV.
Uses OPENALEX_API_KEY as a bearer token (never in URLs or logs).
One atomic JSON checkpoint per successful API page; CSV/JSON summaries are rebuilt
from checkpoints. No PDF or full-text acquisition.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import random
import re
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

URL = "https://api.openalex.org/works"
FIELDS = ["article_id", "article_url", "source", "journal", "year", "doi", "title", "abstract", "publication_type", "language", "source_collection", "rights_note", "acquisition_date", "openalex_id", "matched_search_query", "source_openalex_id"]
LOG_FIELDS = ["timestamp", "journal", "source_openalex_id", "query", "page", "url", "http_status", "extraction_status", "records", "error", "user_agent"]
SID = re.compile(r"^S\d+$")


def utcnow():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def json_atomic(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + ".tmp")
    with temp.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.flush()
        os.fsync(f.fileno())
    temp.replace(path)


def csv_atomic(path: Path, rows, fields):
    temp = path.with_name(path.name + ".tmp")
    with temp.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    temp.replace(path)


def source_id(value):
    value = str(value or "").strip().rstrip("/").split("/")[-1]
    if not SID.fullmatch(value):
        raise ValueError(f"Nieprawidłowe ID OpenAlex: {value!r}")
    return value


def normalized_name(name):
    return re.sub(r"[^a-z0-9]", "", str(name).casefold())


def validate_approved_sources(config, audit_path):
    """Validate every approved journal against raw discovery CSV, without inferring booleans.

    Original CSV has unescaped ISSN commas. Column H is not a reliable semantic
    approval column across rows. Manifest supplies human-confirmed IDs explicitly.
    """
    approved = config["approved_sources"]
    if len({j["name"] for j in approved}) != len(approved):
        raise ValueError("Powtarzające się nazwy w approved_sources")
    if len({source_id(j["openalex_source_id"]) for j in approved}) != len(approved):
        raise ValueError("Powtarzające się identyfikatory OpenAlex")
    with Path(audit_path).open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if not rows or rows[0][:3] != ["requested_journal", "candidate_name", "openalex_source_id"]:
        raise ValueError("Nieoczekiwany format source_candidates.csv")
    candidates = []
    for line, row in enumerate(rows[1:], 2):
        if len(row) < 3:
            continue
        try:
            sid = source_id(row[2])
        except ValueError:
            continue
        candidates.append({"line": line, "requested": row[0].strip(), "candidate": row[1].strip(), "sid": sid, "raw_cells": row})
    for j in approved:
        sid = source_id(j["openalex_source_id"])
        matches = [r for r in candidates if r["sid"] == sid and r["requested"] == j["name"]]
        if len(matches) != 1:
            raise ValueError(f"ID {sid} czasopisma {j['name']} nie ma jednoznacznego dopasowania w CSV")
        if normalized_name(matches[0]["candidate"]) != normalized_name(j["candidate_name"]):
            raise ValueError(f"Niezgodna nazwa kandydata dla {sid}")
    return approved, candidates


def restore_abstract(index):
    if not isinstance(index, dict):
        return ""
    positions = []
    for word, offsets in index.items():
        for n in offsets:
            positions.append((int(n), word))
    return " ".join(word for _, word in sorted(positions))


def unpack_works(items, journal, query, sid, acquired):
    records = []
    for w in items:
        actual = (((w.get("primary_location") or {}).get("source") or {}).get("id") or "").rstrip("/").split("/")[-1]
        if actual != sid:
            continue
        oid = w.get("id") or ""
        if not oid:
            continue
        records.append({
            "article_id": oid, "article_url": w.get("doi") or oid,
            "source": "OpenAlex", "journal": journal,
            "year": w.get("publication_year") or "", "doi": w.get("doi") or "",
            "title": w.get("display_name") or "",
            "abstract": restore_abstract(w.get("abstract_inverted_index")),
            "publication_type": w.get("type") or "", "language": w.get("language") or "",
            "source_collection": "journal_scoped_openalex_search",
            "rights_note": "OpenAlex metadata; confirm abstract reuse rights before redistribution",
            "acquisition_date": acquired[:10], "openalex_id": oid,
            "matched_search_query": query, "source_openalex_id": sid,
        })
    return records


def config_fingerprint(config, mode, sample_size):
    essential = {k: config[k] for k in ("approved_sources", "from_date", "to_date", "search_queries", "max_pages_per_query", "per_page")}
    essential.update({"mode": mode, "sample_size": sample_size})
    return hashlib.sha256(json.dumps(essential, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def aggregate(run_dir, cfg, approved, mode, fingerprint, status, problems=None):
    checkpoints = sorted((run_dir / "checkpoints").glob("*.json"))
    combined, page_logs = {}, []
    for path in checkpoints:
        page = json.loads(path.read_text(encoding="utf-8"))
        page_logs.append(page["log"])
        for r in page["records"]:
            oid = r["openalex_id"]
            if oid not in combined:
                combined[oid] = dict(r)
            else:
                q = r["matched_search_query"]
                prior = combined[oid]["matched_search_query"].split(" ; ")
                if q not in prior:
                    combined[oid]["matched_search_query"] += " ; " + q
    rows = list(combined.values())
    csv_atomic(run_dir / "raw_candidates.csv", rows, FIELDS)
    csv_atomic(run_dir / "acquisition_log.csv", page_logs, LOG_FIELDS)
    summary = {
        "schema_version": "0.4", "mode": mode, "status": status,
        "complete_search": status == "completed" and mode == "full",
        "complete_configured_scope": status == "completed",  # full mode still has per-query page cap
        "full_search_exhaustive": False,
        "page_limit_per_query": cfg["max_pages_per_query"] if mode == "full" else 1,
        "approved_journals": [{"journal": j["name"], "openalex_source_id": source_id(j["openalex_source_id"])} for j in approved],
        "unique_candidates": len(rows), "saved_pages": len(checkpoints),
        "records_by_journal": {j["name"]: sum(r["journal"] == j["name"] for r in rows) for j in approved},
        "fingerprint": fingerprint, "last_updated_utc": utcnow(),
        "problems": problems or [],
        "note": "Candidate retrieval only; indexing is not restricted to abstract/title. QA and human relevance screening required. No automated interpretation of malformed CSV approval cells.",
    }
    json_atomic(run_dir / "acquisition_summary.json", summary)
    return summary


def safe_rate_limit_detail(response):
    """Extract documented diagnostics only; never preserve arbitrary server text."""
    reason = None
    try:
        body = response.json()
        if isinstance(body, dict):
            candidate = body.get("reason")
            if isinstance(candidate, str) and re.fullmatch(r"[a-z0-9_\-]{1,64}", candidate):
                reason = candidate
    except (ValueError, TypeError, AttributeError):
        pass
    raw_retry = response.headers.get("Retry-After", "")
    retry = raw_retry if re.fullmatch(r"[0-9]{1,8}", str(raw_retry)) else None
    return reason, retry


def request_page(session, sid, journal, query, page, per_page, cfg, email, ua):
    params = {
        "filter": f"primary_location.source.id:{sid},from_publication_date:{cfg['from_date']},to_publication_date:{cfg['to_date']}",
        "search": query, "per-page": per_page, "page": page, "mailto": email,
    }
    stamp = utcnow()
    # Deliberately log the canonical endpoint, never response.url or auth details.
    entry = {"timestamp": stamp, "journal": journal, "source_openalex_id": sid,
             "query": query, "page": page, "url": URL, "http_status": "",
             "extraction_status": "", "records": 0, "error": "", "user_agent": ua}
    try:
        response = session.get(URL, params=params, timeout=(10, 40))
        entry["http_status"] = response.status_code
        if response.status_code == 429:
            reason, retry_after = safe_rate_limit_detail(response)
            entry["rate_limit_reason"] = reason or "unspecified"
            entry["retry_after_seconds"] = retry_after
            message = f"OpenAlex HTTP 429; reason={entry['rate_limit_reason']}"
            if retry_after:
                message += f"; Retry-After={retry_after}s"
            message += "; przerwano bez ponawiania; spróbuj ponownie zgodnie z zaleceniami API"
            raise RuntimeError(message)
        if response.status_code in (401, 403) or response.status_code >= 500:
            raise RuntimeError(f"API zatrzymało pobieranie: HTTP {response.status_code}; bez automatycznych prób")
        if response.status_code >= 400:
            raise RuntimeError(f"API zwróciło HTTP {response.status_code}; bez automatycznych prób")
        data = response.json()
        items = data.get("results")
        if not isinstance(items, list):
            raise ValueError("Odpowiedź OpenAlex bez listy results")
        records = unpack_works(items, journal, query, sid, stamp)
        entry["extraction_status"] = "OK"
        entry["records"] = len(records)
        return {"log": entry, "records": records, "returned_count": len(items), "meta_count": (data.get("meta") or {}).get("count")}
    except requests.RequestException as exc:
        # Requests exception text may include sensitive URLs; do not log it.
        message = f"Błąd komunikacji OpenAlex ({type(exc).__name__}); szczegóły nie są zapisywane"
        entry["extraction_status"] = "HALTED_ERROR"
        entry["error"] = message
        raise AcquisitionError(message, entry) from None
    except Exception as exc:
        entry["extraction_status"] = "HALTED_ERROR"
        entry["error"] = str(exc)
        raise AcquisitionError(str(exc), entry) from None


class AcquisitionError(Exception):
    def __init__(self, message, entry):
        super().__init__(message)
        self.entry = entry


def run(args):
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    approved, candidates = validate_approved_sources(cfg, args.source_audit)
    if args.require_all_five and len(approved) != 5:
        raise ValueError("Oczekiwano 5 zatwierdzonych czasopism")
    print(f"[AUDYT] zatwierdzonych: {len(approved)}, kandydatów w CSV: {len(candidates)}", flush=True)
    for j in approved:
        print(f"    + {j['name']}: {source_id(j['openalex_source_id'])}", flush=True)
    if args.audit_only:
        return 0
    email = args.contact_email or os.getenv("ANDROMEDA_CONTACT_EMAIL", "")
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email) or "example" in email.lower():
        raise ValueError("Podaj realny --contact-email lub ANDROMEDA_CONTACT_EMAIL")
    if args.sample_size < 1 or args.sample_size > 100:
        raise ValueError("--sample-size wymaga wartości 1..100")
    lower = float(cfg["minimum_delay_seconds"])
    upper = float(cfg["maximum_delay_seconds"])
    if lower < 3 or upper < lower:
        raise ValueError("Zgodnie z robots.md opóźnienie musi wynosić co najmniej 3 sekundy")
    mode = "full" if args.full else "sample"
    fp = config_fingerprint(cfg, mode, args.sample_size)
    run_dir = Path(args.output_dir) / ("avatar01_full_v04" if args.full else "avatar01_sample_v04")
    run_dir.mkdir(parents=True, exist_ok=True)
    state = run_dir / "run_manifest.json"
    if state.exists():
        prior = json.loads(state.read_text(encoding="utf-8"))
        if prior["fingerprint"] != fp:
            raise ValueError(f"Zmieniła się konfiguracja. Dla nowego przebiegu wybierz inny --output-dir; istniejącego {run_dir} nie nadpisuję")
        print("[RESUME] zgodny manifest; wznawiam od brakujących stron", flush=True)
    else:
        json_atomic(state, {"fingerprint": fp, "created_utc": utcnow(), "config": cfg,
                            "mode": mode, "sample_size": args.sample_size, "audit_path": str(args.source_audit),
                            "audit_sha256": hashlib.sha256(Path(args.source_audit).read_bytes()).hexdigest()})
        (run_dir / "source_audit_snapshot.csv").write_bytes(Path(args.source_audit).read_bytes())
    api_key = os.getenv("OPENALEX_API_KEY", "").strip()
    if not api_key:
        raise ValueError("Brak OPENALEX_API_KEY w bieżącej sesji PowerShell; bez klucza nie uruchamiam nowego przebiegu")
    if re.search(r"\s", api_key):
        raise ValueError("OPENALEX_API_KEY zawiera białe znaki — sprawdź sposób ustawienia (nie wypisuję wartości)")
    ua = f"AndromedaNowickaBibliometricBot/0.5 (metadata-only bibliometric research; contact: {email}; no PDF mirroring; polite delay)"
    session = requests.Session()
    # Authorization header avoids exposing credentials via response.url, query logs and checkpoints.
    session.headers.update({"User-Agent": ua, "From": email, "Accept": "application/json", "Authorization": f"Bearer {api_key}"})
    print("[AUTH] OPENALEX_API_KEY dostępny; uwierzytelnianie Bearer (wartość ukryta)", flush=True)
    queries = list(dict.fromkeys(cfg["search_queries"]))
    max_pages = int(cfg["max_pages_per_query"]) if args.full else 1
    per_page = min(100, int(cfg["per_page"])) if args.full else args.sample_size
    if max_pages < 1 or per_page < 1:
        raise ValueError("Nieprawidłowa liczba stron lub rekordów")
    total = len(approved) * len(queries) * max_pages
    counter = 0
    last_request = None
    problems = []
    try:
        for jidx, journal in enumerate(approved, 1):
            sid = source_id(journal["openalex_source_id"])
            for qidx, query in enumerate(queries, 1):
                for page in range(1, max_pages + 1):
                    counter += 1
                    key = f"{sid}_q{qidx:02d}_p{page:03d}.json"
                    checkpoint = run_dir / "checkpoints" / key
                    if checkpoint.exists():
                        print(f"[SKIP {counter}/{total}] zapisano: {journal['name']} | {query} | p{page}", flush=True)
                        cached = json.loads(checkpoint.read_text(encoding="utf-8"))
                        if cached.get("returned_count", 0) < per_page:
                            break
                        continue
                    if last_request is not None:
                        seconds = random.uniform(lower, upper)
                        print(f"[PAUSE] {seconds:.1f}s przed kolejnym żądaniem", flush=True)
                        time.sleep(seconds)
                    print(f"[GET {counter}/{total}] journal {jidx}/{len(approved)}, query {qidx}/{len(queries)}, p{page}: {journal['name']} | {query}", flush=True)
                    last_request = utcnow()
                    response = request_page(session, sid, journal["name"], query, page, per_page, cfg, email, ua)
                    json_atomic(checkpoint, response)
                    summary = aggregate(run_dir, cfg, approved, mode, fp, "in_progress")
                    print(f"[OK] +{len(response['records'])} | zapisane strony: {summary['saved_pages']} | unikalne rekordy: {summary['unique_candidates']}", flush=True)
                    if response["returned_count"] < per_page:
                        break
    except KeyboardInterrupt:
        summary = aggregate(run_dir, cfg, approved, mode, fp, "interrupted")
        print(f"\n[CTRL+C] Zachowałam {summary['saved_pages']} stron. Uruchom identyczne polecenie, by wznowić.", file=sys.stderr, flush=True)
        return 130
    except AcquisitionError as exc:
        problems.append(exc.entry)
        json_atomic(run_dir / "last_error.json", exc.entry)
        aggregate(run_dir, cfg, approved, mode, fp, "halted", problems)
        print(f"[HALT] {exc}; wcześniej zapisane strony pozostają na dysku", file=sys.stderr, flush=True)
        return 1
    summary = aggregate(run_dir, cfg, approved, mode, fp, "completed")
    print(f"[DONE] {summary['unique_candidates']} unikalnych rekordów | {run_dir / 'raw_candidates.csv'}", flush=True)
    return 0


def main():
    p = argparse.ArgumentParser(description="Andromeda 01 v0.4.1 | OpenAlex with API key, resumable checkpoints")
    p.add_argument("--config", default="config/corpus.json")
    p.add_argument("--source-audit", default="outputs/source_candidates.csv")
    p.add_argument("--output-dir", default="outputs/raw")
    p.add_argument("--contact-email", default=None)
    p.add_argument("--audit-only", action="store_true")
    p.add_argument("--require-all-five", action="store_true")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--sample", action="store_true", help="Default: one page per journal and query")
    group.add_argument("--full", action="store_true", help="Configured pages per journal and query")
    p.add_argument("--sample-size", type=int, default=5, help="Up to N works per query and journal (default 5)")
    return run(p.parse_args())


if __name__ == "__main__":
    sys.exit(main())
