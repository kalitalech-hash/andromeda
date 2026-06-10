#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
6a_resubmit_pp_pd_exclusion_sensitivity.py

Reviewer-facing sensitivity analysis:
- full corpus vs excluding Psychoanalytic Dialogues;
- all periods and post-1990 subset;
- output tables and figures for resubmission to Psychoanalytic Psychology.

Run from data_psychoanalytic_core/scripts:
    python 6a_resubmit_pp_pd_exclusion_sensitivity.py
"""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
from _resubmit_pp_common import paths, read_csv, write_csv, write_json, aggregate_family_period, pivot_indices, first_last, lineplot, now

def main() -> int:
    p=paths()
    refined=p["refined"]
    out=p["out"]/"pd_exclusion_sensitivity"
    out.mkdir(parents=True, exist_ok=True)

    src=refined/"psychoanalytic_core_semantic_family_by_journal_period_refined.csv"
    jp=read_csv(src)
    if jp.empty:
        raise SystemExit(f"Missing input: {src}")

    family_tables=[]
    for scenario, exclude, post in [
        ("full_corpus_all_periods", None, False),
        ("excluding_psychoanalytic_dialogues_all_periods", ["psychoanalytic_dialogues"], False),
        ("full_corpus_post_1990", None, True),
        ("excluding_psychoanalytic_dialogues_post_1990", ["psychoanalytic_dialogues"], True),
    ]:
        family_tables.append(aggregate_family_period(jp, scenario, exclude=exclude, post1990=post))

    family_period=pd.concat(family_tables, ignore_index=True)
    indices=pivot_indices(family_period)
    changes=first_last(indices)

    write_csv(family_period, out/"pp_resubmit_R1_family_coverage_by_period_full_vs_no_PD.csv")
    write_csv(indices, out/"pp_resubmit_R1_indices_by_period_full_vs_no_PD.csv")
    write_csv(changes, out/"pp_resubmit_R1_first_last_changes_full_vs_no_PD.csv")

    # Figure A: core family coverage
    lineplot(
        indices[indices["scenario"].isin(["full_corpus_all_periods","excluding_psychoanalytic_dialogues_all_periods"])],
        out/"fig_R1_full_vs_no_PD_drive_relational.png",
        "Full corpus vs excluding Psychoanalytic Dialogues: drive/conflict and relational coverage",
        ["drive_conflict_defense","relational_intersubjective_field"],
    )
    # Figure B: composite indices
    lineplot(
        indices[indices["scenario"].isin(["full_corpus_all_periods","excluding_psychoanalytic_dialogues_all_periods"])],
        out/"fig_R1_full_vs_no_PD_indices.png",
        "Full corpus vs excluding Psychoanalytic Dialogues: semantic-change indices",
        ["relational_shift_index","contemporary_contextualization_index","narrative_reframing_index"],
    )

    summary={
        "script":"6a_resubmit_pp_pd_exclusion_sensitivity.py",
        "created_at_utc":now(),
        "input":str(src),
        "outputs":{
            "family_coverage":str(out/"pp_resubmit_R1_family_coverage_by_period_full_vs_no_PD.csv"),
            "indices":str(out/"pp_resubmit_R1_indices_by_period_full_vs_no_PD.csv"),
            "changes":str(out/"pp_resubmit_R1_first_last_changes_full_vs_no_PD.csv"),
        },
        "interpretive_use":"Use this table to show whether the main directions persist when Psychoanalytic Dialogues is excluded, and to report post-1990-only sensitivity.",
        "caution":"This is a composition sensitivity analysis, not a causal decomposition of journal effects."
    }
    write_json(summary, out/"pp_resubmit_R1_summary.json")
    print(json.dumps({"status":"ok","out_dir":str(out),"n_rows":len(indices)}, indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
