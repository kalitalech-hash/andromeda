#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1a_pep_japa_probe.py

Clean local wrapper for JAPA reconnaissance using the existing PEP probe v12.

Placement
---------
Put this file in:

    data_psychoanalytic_core/scripts/

next to:

    1a_pep_metadata_probe_v12.py

Run from that same scripts directory:

    python 1a_pep_japa_probe.py --control
    python 1a_pep_japa_probe.py --sample

or simply:

    python 1a_pep_japa_probe.py

Why this wrapper uses absolute paths
------------------------------------
The v12 probe internally calls:

    raw_path.relative_to(PROJECT_ROOT)

On Windows this fails if --out-dir is passed as a relative path such as
"..\\data\\raw_pep_metadata\\japa_probe".

Therefore this wrapper resolves all output paths to absolute paths inside
data_psychoanalytic_core before passing them to v12. The outputs still land in
the standard repo locations, but v12 receives paths compatible with PROJECT_ROOT.

No PDF download. No full-text mirroring. No separate PEP API client.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SCRIPT_NAME = "1a_pep_metadata_probe_v12.py"
DEFAULT_YEARS = [1953, 1970, 1990, 2005, 2020]


def get_paths() -> dict[str, Path]:
    scripts_dir = Path(__file__).resolve().parent
    project_root = scripts_dir.parent

    return {
        "scripts_dir": scripts_dir,
        "project_root": project_root,
        "probe_script": scripts_dir / SCRIPT_NAME,
        "source_recon": project_root / "data" / "source_recon",
        "logs": project_root / "data" / "logs",
        "raw_japa": project_root / "data" / "raw_pep_metadata" / "japa_probe",
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
    for key in ["source_recon", "logs", "raw_japa"]:
        paths[key].mkdir(parents=True, exist_ok=True)


def build_base_cmd(args: argparse.Namespace, paths: dict[str, Path]) -> list[str]:
    return [
        sys.executable,
        str(paths["probe_script"]),
        "--journal", "japa",
        "--limit", str(args.limit),
        "--delay", str(args.delay),
        "--timeout", str(args.timeout),
        "--flat-csv", str(paths["source_recon"] / "japa_pep_metadata_probe_results.csv"),
        "--keywords-long-csv", str(paths["source_recon"] / "japa_pep_keywords_probe_long.csv"),
        "--log", str(paths["logs"] / "japa_pep_metadata_probe_log.csv"),
        "--out-dir", str(paths["raw_japa"]),
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
        description="Absolute-path JAPA wrapper for 1a_pep_metadata_probe_v12.py."
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--control",
        action="store_true",
        help="Run exact control probe for APA.068.0583A.",
    )
    mode.add_argument(
        "--sample",
        action="store_true",
        help="Run year-sample probe. This is also the default.",
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

    cmd = build_base_cmd(args, paths)

    if not args.no_diagnose:
        cmd.append("--diagnose")

    if args.append_flat_csv:
        cmd.append("--append-flat-csv")

    if args.control:
        cmd += [
            "--year", "2020",
            "--facetquery", "art_id:APA.068.0583A",
        ]
    else:
        for year in args.years:
            cmd += ["--year", str(year)]

    return run_cmd(cmd, dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
