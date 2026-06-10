#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
6d_run_resubmit_pp_robustness_suite.py

Runs all Psychoanalytic Psychology resubmission robustness scripts.
"""
from __future__ import annotations
import subprocess, sys, json, datetime as dt
from pathlib import Path

SCRIPTS=[
    "6a_resubmit_pp_pd_exclusion_sensitivity.py",
    "6b_resubmit_pp_historical_threshold_relational.py",
    "6c_resubmit_pp_journal_period_composition.py",
]

def main() -> int:
    here=Path(__file__).resolve().parent
    results=[]
    for script in SCRIPTS:
        path=here/script
        print(f"\n=== Running {script} ===")
        proc=subprocess.run([sys.executable, str(path)], cwd=str(here), text=True, capture_output=True)
        print(proc.stdout)
        if proc.stderr:
            print(proc.stderr, file=sys.stderr)
        results.append({"script":script,"returncode":proc.returncode})
        if proc.returncode!=0:
            print(json.dumps({"status":"failed","script":script,"returncode":proc.returncode}, indent=2))
            return proc.returncode
    out=here.parent/"data"/"title_abstract"/"resubmit_pp"/"pp_resubmit_robustness_suite_summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "created_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),
        "status":"ok",
        "scripts":results
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status":"ok","summary":str(out)}, indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
