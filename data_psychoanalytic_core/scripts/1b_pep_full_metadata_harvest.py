#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1b_pep_full_metadata_harvest.py

Andromeda Nowicka v0.4/v0.5-pre
PEP-Web metadata harvesting orchestrator for data_psychoanalytic_core.

Purpose
-------
Run year-by-year metadata harvesting for the psychoanalytic core journals by
reusing the already tested PEP probe:

    data_psychoanalytic_core/scripts/1a_pep_metadata_probe_v12.py

This script intentionally does NOT implement a new PEP API client. It delegates
requesting, parsing, raw JSON writing, article flattening, and keyword-long
extraction to v12. Its role is orchestration:

- one journal or all journals,
- defined year ranges,
- safe absolute output paths,
- per-year output files,
- skip-existing / resume behavior,
- polite delay,
- no PDF download,
- no full-text mirroring,
- reproducible harvest manifest.

Run location
------------
Put this file in:

    data_psychoanalytic_core/scripts/

next to:

    1a_pep_metadata_probe_v12.py

Recommended first test:

    cd data_psychoanalytic_core/scripts
    python 1b_pep_full_metadata_harvest.py --journal psychoanalytic_dialogues --start-year 1991 --end-year 1992 --limit 500 --dry-run

Then actual small test:

    python 1b_pep_full_metadata_harvest.py --journal psychoanalytic_dialogues --start-year 1991 --end-year 1992 --limit 500

Then a full single-journal run, for example:

    python 1b_pep_full_metadata_harvest.py --journal psychoanalytic_dialogues --start-year 1991 --end-year 2025 --limit 500

Core policy
-----------
Metadata-first only. This script does not request PDFs and does not mirror full
text. It writes metadata outputs and raw JSON responses produced by v12.

Article type policy
-------------------
The main downstream analytical corpus will be ART-only, but this harvest stage
keeps all article types in raw/per-year outputs. ART-only filtering belongs to
the next QA stage so exclusions remain auditable.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional


SCRIPT_VERSION = "v0.1.0"
PROBE_SCRIPT_NAME = "1a_pep_metadata_probe_v12.py"

# Confirmed / currently used PEP prefixes from source reconnaissance.
# The prefix is used only to build explicit facetquery strings. We still pass
# --journal to v12 so its metadata labels remain consistent.
JOURNALS: Dict[str, Dict[str, object]] = {
    "ijpa": {
        "label": "The International Journal of Psychoanalysis",
        "pep_prefix": "IJP",
        "start_year": 1920,
        "end_year": 2025,
    },
    "japa": {
        "label": "Journal of the American Psychoanalytic Association",
        "pep_prefix": "APA",
        "start_year": 1953,
        "end_year": 2025,
    },
    "psychoanalytic_dialogues": {
        "label": "Psychoanalytic Dialogues",
        "pep_prefix": "PD",
        "start_year": 1991,
        "end_year": 2025,
    },
    "psychoanalytic_psychology": {
        "label": "Psychoanalytic Psychology",
        "pep_prefix": "PPSY",
        "start_year": 1984,
        "end_year": 2025,
    },
    "psychoanalytic_psychotherapy": {
        "label": "Psychoanalytic Psychotherapy",
        "pep_prefix": "PPTX",
        "start_year": 1987,
        "end_year": 2025,
    },
}

DEFAULT_ORDER = [
    "psychoanalytic_dialogues",
    "psychoanalytic_psychotherapy",
    "psychoanalytic_psychology",
    "japa",
    "ijpa",
]


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def get_paths() -> Dict[str, Path]:
    scripts_dir = Path(__file__).resolve().parent
    project_root = scripts_dir.parent
    return {
        "scripts_dir": scripts_dir,
        "project_root": project_root,
        "probe_script": scripts_dir / PROBE_SCRIPT_NAME,
        "raw_root": project_root / "data" / "raw_pep_metadata",
        "harvest_root": project_root / "data" / "harvest",
        "logs_root": project_root / "data" / "logs",
        "qa_root": project_root / "data" / "qa",
        "source_recon_root": project_root / "data" / "source_recon",
    }


def require_layout(paths: Dict[str, Path]) -> None:
    if not paths["probe_script"].exists():
        raise SystemExit(
            "\nERROR: Nie znaleziono 1a_pep_metadata_probe_v12.py obok tego skryptu.\n"
            "Umieść 1b_pep_full_metadata_harvest.py w data_psychoanalytic_core/scripts/.\n"
        )


def ensure_base_dirs(paths: Dict[str, Path]) -> None:
    for key in ["raw_root", "harvest_root", "logs_root", "qa_root"]:
        paths[key].mkdir(parents=True, exist_ok=True)


def parse_journals(value: str) -> List[str]:
    if value == "all":
        return DEFAULT_ORDER.copy()
    requested = [x.strip() for x in value.split(",") if x.strip()]
    unknown = [x for x in requested if x not in JOURNALS]
    if unknown:
        allowed = ", ".join(["all"] + list(JOURNALS.keys()))
        raise SystemExit(f"ERROR: Unknown journal(s): {unknown}. Allowed: {allowed}")
    return requested


def year_range_for_journal(
    journal: str,
    start_year: Optional[int],
    end_year: Optional[int],
) -> range:
    meta = JOURNALS[journal]
    start = int(start_year if start_year is not None else meta["start_year"])
    end = int(end_year if end_year is not None else meta["end_year"])
    if end < start:
        raise SystemExit(f"ERROR: end-year < start-year for {journal}: {start}-{end}")
    return range(start, end + 1)


def journal_dirs(paths: Dict[str, Path], journal: str) -> Dict[str, Path]:
    dirs = {
        "raw": paths["raw_root"] / journal,
        "articles_by_year": paths["harvest_root"] / "articles_by_year" / journal,
        "keywords_by_year": paths["harvest_root"] / "keywords_by_year" / journal,
        "logs_by_year": paths["logs_root"] / "pep_harvest_by_year" / journal,
    }
    for d in dirs.values():
        d.mkdir(parents=True, exist_ok=True)
    return dirs


def per_year_paths(paths: Dict[str, Path], journal: str, year: int) -> Dict[str, Path]:
    dirs = journal_dirs(paths, journal)
    return {
        "articles_csv": dirs["articles_by_year"] / f"{journal}_{year}_pep_articles_raw.csv",
        "keywords_csv": dirs["keywords_by_year"] / f"{journal}_{year}_pep_keywords_long_raw.csv",
        "log_csv": dirs["logs_by_year"] / f"{journal}_{year}_pep_harvest_log.csv",
        "raw_dir": dirs["raw"] / str(year),
    }


def output_complete(paths_for_year: Dict[str, Path], min_article_bytes: int = 50) -> bool:
    articles_csv = paths_for_year["articles_csv"]
    log_csv = paths_for_year["log_csv"]
    return (
        articles_csv.exists()
        and articles_csv.stat().st_size >= min_article_bytes
        and log_csv.exists()
        and log_csv.stat().st_size > 0
    )


def build_probe_cmd(
    *,
    python_exe: str,
    probe_script: Path,
    journal: str,
    year: int,
    limit: int,
    timeout: float,
    delay_within_probe: float,
    diagnose: bool,
    paths_for_year: Dict[str, Path],
) -> List[str]:
    prefix = str(JOURNALS[journal]["pep_prefix"])
    facetquery = f"art_id:{prefix}.* AND year:{year}"

    cmd = [
        python_exe,
        str(probe_script),
        "--journal", journal,
        "--year", str(year),
        "--facetquery", facetquery,
        "--limit", str(limit),
        "--delay", str(delay_within_probe),
        "--timeout", str(timeout),
        "--flat-csv", str(paths_for_year["articles_csv"]),
        "--keywords-long-csv", str(paths_for_year["keywords_csv"]),
        "--log", str(paths_for_year["log_csv"]),
        "--out-dir", str(paths_for_year["raw_dir"]),
        "--write-run-csv",
    ]

    if diagnose:
        cmd.append("--diagnose")

    return cmd


def read_csv_rows(path: Path) -> List[Dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def append_manifest_row(path: Path, row: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "run_id",
        "script_version",
        "timestamp_utc",
        "journal",
        "journal_label",
        "pep_prefix",
        "year",
        "status",
        "exit_code",
        "n_article_rows",
        "n_keyword_rows",
        "articles_csv",
        "keywords_csv",
        "log_csv",
        "raw_dir",
        "command",
        "note",
    ]
    exists = path.exists()
    with path.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def write_json(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def run_one_year(
    *,
    args: argparse.Namespace,
    paths: Dict[str, Path],
    run_id: str,
    journal: str,
    year: int,
    manifest_csv: Path,
) -> Dict[str, object]:
    py = sys.executable
    year_paths = per_year_paths(paths, journal, year)

    if args.skip_existing and output_complete(year_paths):
        article_rows = read_csv_rows(year_paths["articles_csv"])
        keyword_rows = read_csv_rows(year_paths["keywords_csv"])
        row = {
            "run_id": run_id,
            "script_version": SCRIPT_VERSION,
            "timestamp_utc": utc_now_iso(),
            "journal": journal,
            "journal_label": JOURNALS[journal]["label"],
            "pep_prefix": JOURNALS[journal]["pep_prefix"],
            "year": year,
            "status": "skipped_existing",
            "exit_code": 0,
            "n_article_rows": len(article_rows),
            "n_keyword_rows": len(keyword_rows),
            "articles_csv": str(year_paths["articles_csv"]),
            "keywords_csv": str(year_paths["keywords_csv"]),
            "log_csv": str(year_paths["log_csv"]),
            "raw_dir": str(year_paths["raw_dir"]),
            "command": "",
            "note": "Existing per-year outputs detected.",
        }
        append_manifest_row(manifest_csv, row)
        return row

    cmd = build_probe_cmd(
        python_exe=py,
        probe_script=paths["probe_script"],
        journal=journal,
        year=year,
        limit=args.limit,
        timeout=args.timeout,
        delay_within_probe=args.probe_delay,
        diagnose=not args.no_diagnose,
        paths_for_year=year_paths,
    )

    print("\n=== Harvest job ===")
    print(f"journal: {journal}")
    print(f"year: {year}")
    print("command:")
    print(" ".join(f'"{x}"' if " " in x else x for x in cmd))

    if args.dry_run:
        exit_code = 0
        status = "dry_run"
    else:
        exit_code = subprocess.call(cmd)
        status = "ok" if exit_code == 0 else "error"

    article_rows = read_csv_rows(year_paths["articles_csv"])
    keyword_rows = read_csv_rows(year_paths["keywords_csv"])

    row = {
        "run_id": run_id,
        "script_version": SCRIPT_VERSION,
        "timestamp_utc": utc_now_iso(),
        "journal": journal,
        "journal_label": JOURNALS[journal]["label"],
        "pep_prefix": JOURNALS[journal]["pep_prefix"],
        "year": year,
        "status": status,
        "exit_code": exit_code,
        "n_article_rows": len(article_rows),
        "n_keyword_rows": len(keyword_rows),
        "articles_csv": str(year_paths["articles_csv"]),
        "keywords_csv": str(year_paths["keywords_csv"]),
        "log_csv": str(year_paths["log_csv"]),
        "raw_dir": str(year_paths["raw_dir"]),
        "command": " ".join(cmd),
        "note": "",
    }
    append_manifest_row(manifest_csv, row)
    return row


def summarize_run(
    *,
    run_id: str,
    rows: List[Dict[str, object]],
    paths: Dict[str, Path],
    selected_journals: List[str],
    args: argparse.Namespace,
) -> Dict[str, object]:
    by_journal: Dict[str, Dict[str, int]] = {}
    for row in rows:
        journal = str(row["journal"])
        by_journal.setdefault(
            journal,
            {
                "years_attempted": 0,
                "years_ok": 0,
                "years_skipped": 0,
                "years_error": 0,
                "article_rows": 0,
                "keyword_rows": 0,
            },
        )
        item = by_journal[journal]
        item["years_attempted"] += 1
        status = str(row["status"])
        if status == "ok":
            item["years_ok"] += 1
        elif status == "skipped_existing":
            item["years_skipped"] += 1
        elif status == "error":
            item["years_error"] += 1
        item["article_rows"] += int(row.get("n_article_rows") or 0)
        item["keyword_rows"] += int(row.get("n_keyword_rows") or 0)

    summary = {
        "run_id": run_id,
        "script_version": SCRIPT_VERSION,
        "created_at_utc": utc_now_iso(),
        "selected_journals": selected_journals,
        "args": {
            "journal": args.journal,
            "start_year": args.start_year,
            "end_year": args.end_year,
            "limit": args.limit,
            "timeout": args.timeout,
            "probe_delay": args.probe_delay,
            "between_year_delay": args.between_year_delay,
            "skip_existing": args.skip_existing,
            "dry_run": args.dry_run,
        },
        "policy_flags": {
            "metadata_first": True,
            "pdfs_downloaded": False,
            "full_text_mirrored": False,
            "keeps_all_article_types_at_harvest_stage": True,
            "downstream_main_corpus_rule": "article_type == 'ART'",
        },
        "by_journal": by_journal,
        "total_year_jobs": len(rows),
        "total_article_rows": sum(int(r.get("n_article_rows") or 0) for r in rows),
        "total_keyword_rows": sum(int(r.get("n_keyword_rows") or 0) for r in rows),
    }
    out = paths["qa_root"] / f"pep_full_metadata_harvest_summary_{run_id}.json"
    write_json(out, summary)
    summary["summary_json"] = str(out)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Year-by-year PEP metadata harvest orchestrator for psychoanalytic_core."
    )
    parser.add_argument(
        "--journal",
        default="psychoanalytic_dialogues",
        help=(
            "Journal key, comma-separated journal keys, or 'all'. "
            f"Known: {', '.join(JOURNALS.keys())}"
        ),
    )
    parser.add_argument("--start-year", type=int, default=None)
    parser.add_argument("--end-year", type=int, default=None)
    parser.add_argument(
        "--limit",
        type=int,
        default=500,
        help="Per-year PEP result limit. Use a high enough value for full year coverage.",
    )
    parser.add_argument("--timeout", type=float, default=60.0)
    parser.add_argument(
        "--probe-delay",
        type=float,
        default=0.0,
        help="Delay passed into v12. Usually 0 because this orchestrator runs one request per process.",
    )
    parser.add_argument(
        "--between-year-delay",
        type=float,
        default=5.0,
        help="Polite delay between year jobs.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        default=True,
        help="Skip year if per-year article CSV and log already exist. Default: true.",
    )
    parser.add_argument(
        "--overwrite",
        dest="skip_existing",
        action="store_false",
        help="Overwrite/re-run existing year outputs.",
    )
    parser.add_argument(
        "--no-diagnose",
        action="store_true",
        help="Do not pass --diagnose to v12.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned commands and write manifest rows without executing v12.",
    )
    parser.add_argument(
        "--stop-on-error",
        action="store_true",
        default=True,
        help="Stop at first failed year job. Default: true.",
    )
    parser.add_argument(
        "--continue-on-error",
        dest="stop_on_error",
        action="store_false",
        help="Continue to later years even if one year fails.",
    )

    args = parser.parse_args()

    paths = get_paths()
    require_layout(paths)
    ensure_base_dirs(paths)

    selected_journals = parse_journals(args.journal)
    run_id = dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    manifest_csv = paths["logs_root"] / f"pep_full_metadata_harvest_manifest_{run_id}.csv"

    all_rows: List[Dict[str, object]] = []

    print("Andromeda PEP full metadata harvest")
    print(f"run_id: {run_id}")
    print(f"journals: {', '.join(selected_journals)}")
    print(f"manifest: {manifest_csv}")

    for journal in selected_journals:
        years = list(year_range_for_journal(journal, args.start_year, args.end_year))
        print(f"\n--- Journal: {journal} ({JOURNALS[journal]['pep_prefix']}) ---")
        print(f"years: {years[0]}-{years[-1]} ({len(years)} jobs)")

        for idx, year in enumerate(years):
            row = run_one_year(
                args=args,
                paths=paths,
                run_id=run_id,
                journal=journal,
                year=year,
                manifest_csv=manifest_csv,
            )
            all_rows.append(row)

            if row["status"] == "error" and args.stop_on_error:
                summary = summarize_run(
                    run_id=run_id,
                    rows=all_rows,
                    paths=paths,
                    selected_journals=selected_journals,
                    args=args,
                )
                print(json.dumps(summary, ensure_ascii=False, indent=2))
                return int(row["exit_code"] or 1)

            if not args.dry_run and idx < len(years) - 1:
                time.sleep(args.between_year_delay)

    summary = summarize_run(
        run_id=run_id,
        rows=all_rows,
        paths=paths,
        selected_journals=selected_journals,
        args=args,
    )
    print("\nHarvest summary:")
    print(json.dumps(summary, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
