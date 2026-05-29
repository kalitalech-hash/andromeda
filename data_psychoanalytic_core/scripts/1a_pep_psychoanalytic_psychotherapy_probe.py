#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1a_pep_psychoanalytic_psychotherapy_probe.py

Clean local wrapper for Psychoanalytic Psychotherapy reconnaissance using the existing
PEP probe v12.

Placement
---------
Put this file in:

    data_psychoanalytic_core/scripts/

next to:

    1a_pep_metadata_probe_v12.py

Run from any directory, for example from scripts:

    python 1a_pep_psychoanalytic_psychotherapy_probe.py --sample

or simply:

    python 1a_pep_psychoanalytic_psychotherapy_probe.py

Default behavior
----------------
By default, this wrapper runs the year-sample probe for Psychoanalytic Psychotherapy:

    1987, 1995, 2005, 2015, 2024

It reuses the exact v12 PEP API logic and supplies:
- --journal psychoanalytic_psychotherapy
- explicit facetquery values using confirmed PEP prefix PPTX
- output paths specific to Psychoanalytic Psychotherapy
- safe default options

PEP prefix
----------
Confirmed by user/source recon:

    psychoanalytic_psychotherapy -> PPTX

Generated query pattern in sample mode:

    art_id:PPTX.* AND year:<YEAR>

Why explicit facetquery?
------------------------
If v12 still has a placeholder/wrong mapping for psychoanalytic_psychotherapy,
this wrapper overrides it by passing explicit --facetquery values. This keeps
the v12 request/parse/write logic but avoids editing the v12 JOURNALS mapping.

Control mode
------------
Use --control only when you have a confirmed PEP document_id for Psychoanalytic
Psychotherapy, for example:

    python 1a_pep_psychoanalytic_psychotherapy_probe.py --control --control-id PPTX.xxx.xxxxA

No PDF download. No full-text mirroring. No separate PEP API client.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SCRIPT_NAME = "1a_pep_metadata_probe_v12.py"
JOURNAL_ID = "psychoanalytic_psychotherapy"
OUTPUT_STEM = "psychoanalytic_psychotherapy"
PEP_PREFIX = "PPTX"

DEFAULT_YEARS = [1987, 1995, 2005, 2015, 2024]
DEFAULT_CONTROL_ID = "PPTX.038.0001A"


def get_paths() -> dict[str, Path]:
    scripts_dir = Path(__file__).resolve().parent
    project_root = scripts_dir.parent

    return {
        "scripts_dir": scripts_dir,
        "project_root": project_root,
        "probe_script": scripts_dir / SCRIPT_NAME,
        "source_recon": project_root / "data" / "source_recon",
        "logs": project_root / "data" / "logs",
        "raw_journal": project_root / "data" / "raw_pep_metadata" / f"{OUTPUT_STEM}_probe",
    }


def require_valid_layout(paths: dict[str, Path]) -> None:
    if not paths["probe_script"].exists():
        msg = (
            "\nERROR: Nie widzę 1a_pep_metadata_probe_v12.py obok wrappera.\n\n"
            "Ten plik powinien leżeć w:\n"
            "    data_psychoanalytic_core/scripts/\n\n"
            "Obok niego powinien leżeć:\n"
            "    1a_pep_metadata_probe_v12.py\n"
        )
        print(msg, file=sys.stderr)
        raise SystemExit(2)


def ensure_output_dirs(paths: dict[str, Path]) -> None:
    for key in ["source_recon", "logs", "raw_journal"]:
        paths[key].mkdir(parents=True, exist_ok=True)


def build_base_cmd(args: argparse.Namespace, paths: dict[str, Path]) -> list[str]:
    return [
        sys.executable,
        str(paths["probe_script"]),
        "--journal", JOURNAL_ID,
        "--limit", str(args.limit),
        "--delay", str(args.delay),
        "--timeout", str(args.timeout),
        "--flat-csv", str(paths["source_recon"] / f"{OUTPUT_STEM}_pep_metadata_probe_results.csv"),
        "--keywords-long-csv", str(paths["source_recon"] / f"{OUTPUT_STEM}_pep_keywords_probe_long.csv"),
        "--log", str(paths["logs"] / f"{OUTPUT_STEM}_pep_metadata_probe_log.csv"),
        "--out-dir", str(paths["raw_journal"]),
        "--write-run-csv",
    ]


def run_cmd(cmd: list[str], dry_run: bool = False) -> int:
    print("\nRunning command:\n")
    print(" ".join(f'"{x}"' if " " in x else x for x in cmd))
    print()

    if dry_run:
        return 0

    return subprocess.call(cmd)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Absolute-path Psychoanalytic Psychotherapy wrapper for 1a_pep_metadata_probe_v12.py."
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--control",
        action="store_true",
        help="Run exact control probe for --control-id.",
    )
    mode.add_argument(
        "--sample",
        action="store_true",
        help="Run year-sample probe. This is also the default.",
    )

    parser.add_argument(
        "--control-id",
        default=DEFAULT_CONTROL_ID,
        help=(
            "Known PEP document_id for control mode. "
            "Default is only a placeholder; replace if it returns zero records."
        ),
    )
    parser.add_argument(
        "--control-year",
        type=int,
        default=2024,
        help="Year passed together with --control-id. Used mainly for diagnostics/output naming.",
    )
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=DEFAULT_YEARS,
        help="Sample years for --sample mode.",
    )
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--delay", type=float, default=5.0)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument(
        "--no-diagnose",
        action="store_true",
        help="Do not pass --diagnose to v12.",
    )
    parser.add_argument(
        "--append-flat-csv",
        action="store_true",
        help="Append rows to the existing flat CSV if v12 supports this option.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print command but do not execute.",
    )

    args = parser.parse_args()

    paths = get_paths()
    require_valid_layout(paths)
    ensure_output_dirs(paths)

    base_cmd = build_base_cmd(args, paths)

    if not args.no_diagnose:
        base_cmd.append("--diagnose")

    if args.append_flat_csv:
        base_cmd.append("--append-flat-csv")

    if args.control:
        cmd = base_cmd + [
            "--year", str(args.control_year),
            "--facetquery", f"art_id:{args.control_id}",
        ]
        return run_cmd(cmd, dry_run=args.dry_run)

    # Sample mode:
    # We run v12 once per year because v12 accepts one explicit --facetquery.
    # This avoids relying on the possibly stale placeholder mapping in v12.
    exit_codes: list[int] = []
    for idx, year in enumerate(args.years):
        cmd = base_cmd.copy()
        if idx > 0:
            # Preserve earlier sampled years in the shared flat CSV if v12 supports this flag.
            # If v12 does not support --append-flat-csv, run with --dry-run first and remove this option.
            if "--append-flat-csv" not in cmd:
                cmd.append("--append-flat-csv")
        cmd += [
            "--year", str(year),
            "--facetquery", f"art_id:{PEP_PREFIX}.* AND year:{year}",
        ]
        exit_code = run_cmd(cmd, dry_run=args.dry_run)
        exit_codes.append(exit_code)
        if exit_code != 0:
            return exit_code

    return max(exit_codes) if exit_codes else 0


if __name__ == "__main__":
    raise SystemExit(main())
