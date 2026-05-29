#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1a_pep_japa_probe_wrapper.py

Thin wrapper around the already working Andromeda PEP probe:

    data_psychoanalytic_core/scripts/1a_pep_metadata_probe_v12.py

Purpose:
- reuse the exact IJPA-tested API access pattern, headers, params and metadata parser,
- run it for JAPA by selecting --journal japa,
- rely on the existing JOURNALS mapping where japa -> APA,
- avoid introducing a second, divergent PEP client.

No PDF download. No full-text mirroring.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="JAPA wrapper for the existing PEP metadata probe v12.")
    parser.add_argument(
        "--script",
        default="data_psychoanalytic_core/scripts/1a_pep_metadata_probe_v12.py",
        help="Path to the existing IJPA-tested PEP probe script.",
    )
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=[1953, 1970, 1990, 2005, 2020],
        help="Sample years for JAPA reconnaissance.",
    )
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--delay", type=float, default=5.0)
    parser.add_argument("--timeout", type=float, default=30.0)
    parser.add_argument("--diagnose", action="store_true")
    parser.add_argument(
        "--control",
        action="store_true",
        help="Run exact control query for APA.068.0583A instead of year samples.",
    )
    parser.add_argument(
        "--append-flat-csv",
        action="store_true",
        help="Append to existing CSV instead of overwriting.",
    )
    args = parser.parse_args()

    script_path = Path(args.script)
    if not script_path.exists():
        print(f"ERROR: script not found: {script_path}", file=sys.stderr)
        return 2

    base_cmd = [
        sys.executable,
        str(script_path),
        "--journal",
        "japa",
        "--limit",
        str(args.limit),
        "--delay",
        str(args.delay),
        "--timeout",
        str(args.timeout),
        "--flat-csv",
        "data_psychoanalytic_core/data/source_recon/japa_pep_metadata_probe_results.csv",
        "--keywords-long-csv",
        "data_psychoanalytic_core/data/source_recon/japa_pep_keywords_probe_long.csv",
        "--log",
        "data_psychoanalytic_core/data/logs/japa_pep_metadata_probe_log.csv",
        "--out-dir",
        "data_psychoanalytic_core/data/raw_pep_metadata/japa_probe",
        "--write-run-csv",
    ]

    if args.diagnose:
        base_cmd.append("--diagnose")
    if args.append_flat_csv:
        base_cmd.append("--append-flat-csv")

    if args.control:
        cmd = base_cmd + [
            "--year",
            "2020",
            "--facetquery",
            "art_id:APA.068.0583A",
        ]
    else:
        cmd = base_cmd[:]
        for year in args.years:
            cmd += ["--year", str(year)]

    print("Running:")
    print(" ".join(cmd))
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
