#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4c_journal_balanced_semantic_change.py

Andromeda Nowicka v0.5-pre
Journal-balanced semantic change robustness checks.

Purpose
-------
4a showed strong semantic change indices. 4b showed that all journals move in
the same broad direction, but it did not fully control for changing corpus
composition.

4c provides stricter robustness checks by comparing semantic change within
balanced or partially balanced journal-period panels.

Core question
-------------
Is the apparent semantic change still visible when we reduce the influence of
journal composition?

This script creates several robustness views:

1. Long-journal panel:
   journals with enough historical depth, especially IJPA and JAPA.

2. Common-period journal panel:
   period windows shared by multiple journals.

3. Paired-period within-journal changes:
   first observed period vs last observed period for each journal.

4. Post-1990 panel:
   comparison of journal trajectories in the contemporary multi-journal era.

5. Equal-journal-weight global trajectories:
   unweighted average across journals within each period, contrasted with
   article-weighted/global period indices.

It does NOT replace the full-corpus result. It documents whether the main
semantic-change narrative survives stricter comparisons.

Inputs
------
From 4a:
    ../data/title_abstract/semantic_change/psychoanalytic_core_semantic_change_indices_by_period.csv
    ../data/title_abstract/semantic_change/psychoanalytic_core_semantic_change_indices_by_journal_period.csv

From 4b:
    ../data/title_abstract/semantic_change_journal_global/psychoanalytic_core_within_journal_temporal_change.csv
    ../data/title_abstract/semantic_change_journal_global/psychoanalytic_core_journal_contribution_diagnostics.csv

From refined semantic layer:
    ../data/title_abstract/semantic_refined/psychoanalytic_core_semantic_family_by_journal_period_refined.csv

Outputs
-------
../data/title_abstract/semantic_change_balanced/
    psychoanalytic_core_balanced_equal_journal_weight_by_period.csv
    psychoanalytic_core_balanced_global_vs_equal_weight.csv
    psychoanalytic_core_balanced_long_journal_panel.csv
    psychoanalytic_core_balanced_common_period_panel.csv
    psychoanalytic_core_balanced_post1990_panel.csv
    psychoanalytic_core_balanced_paired_period_changes.csv
    psychoanalytic_core_balanced_direction_consistency.csv
    psychoanalytic_core_balanced_semantic_change_summary.json

Run
---
Put this file in:

    data_psychoanalytic_core/scripts/

Run:

    cd data_psychoanalytic_core/scripts
    python 4c_journal_balanced_semantic_change.py
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd


SCRIPT_VERSION = "v0.1.0"

PERIOD_ORDER = {
    "1920-1945": 1,
    "1946-1969": 2,
    "1970-1989": 3,
    "1990-2009": 4,
    "2010-2025": 5,
}

JOURNAL_ORDER = {
    "ijpa": 1,
    "japa": 2,
    "psychoanalytic_dialogues": 3,
    "psychoanalytic_psychology": 4,
    "psychoanalytic_psychotherapy": 5,
}

CORE_INDICES = [
    "classical_drive_conflict_index",
    "classical_metapsychology_index",
    "object_relations_tradition_index",
    "relational_shift_index",
    "relational_process_index",
    "contemporary_contextualization_index",
    "social_ethical_turn_index",
    "trauma_affect_regulation_index",
    "clinical_severity_continuity_index",
    "developmental_attachment_index",
    "body_sexuality_gender_index",
    "language_narrative_index",
    "narrative_reframing_index",
    "research_psychology_index",
]

FOCUS_INDICES = [
    "relational_shift_index",
    "classical_drive_conflict_index",
    "classical_metapsychology_index",
    "contemporary_contextualization_index",
    "narrative_reframing_index",
    "social_ethical_turn_index",
    "trauma_affect_regulation_index",
    "research_psychology_index",
]

LONG_PANEL_MIN_PERIODS = 4
COMMON_PERIOD_MIN_JOURNALS = 3
POST1990_PERIODS = {"1990-2009", "2010-2025"}


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def get_paths() -> Dict[str, Path]:
    scripts_dir = Path(__file__).resolve().parent
    project_root = scripts_dir.parent
    title_root = project_root / "data" / "title_abstract"
    return {
        "scripts_dir": scripts_dir,
        "project_root": project_root,
        "title_root": title_root,
        "semantic_change_root": title_root / "semantic_change",
        "semantic_change_journal_global_root": title_root / "semantic_change_journal_global",
        "semantic_refined_root": title_root / "semantic_refined",
        "out_root": title_root / "semantic_change_balanced",
    }


def read_csv_safe(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def write_json(payload: Dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def num(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series([0.0] * len(df), index=df.index)
    return pd.to_numeric(df[col], errors="coerce").fillna(0.0)


def add_sort(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "journal_key" in out.columns:
        out["_journal_order"] = out["journal_key"].map(JOURNAL_ORDER).fillna(999).astype(int)
    if "period" in out.columns:
        out["_period_order"] = out["period"].map(PERIOD_ORDER).fillna(999).astype(int)
    sort_cols = [c for c in ["_journal_order", "_period_order", "journal_key", "period"] if c in out.columns]
    if sort_cols:
        out = out.sort_values(sort_cols)
    return out.drop(columns=[c for c in ["_journal_order", "_period_order"] if c in out.columns])


def infer_indices(df: pd.DataFrame) -> List[str]:
    return [c for c in CORE_INDICES if c in df.columns]


def get_cell_sizes(refined_jp_family: pd.DataFrame) -> pd.DataFrame:
    if refined_jp_family.empty or "n_articles_group" not in refined_jp_family.columns:
        return pd.DataFrame(columns=["journal_key", "period", "n_articles_group"])
    out = refined_jp_family[["journal_key", "period", "n_articles_group"]].drop_duplicates().copy()
    out["n_articles_group"] = pd.to_numeric(out["n_articles_group"], errors="coerce").fillna(0).astype(int)
    return add_sort(out)


def attach_cell_sizes(jp: pd.DataFrame, cell_sizes: pd.DataFrame) -> pd.DataFrame:
    out = jp.copy()
    if not cell_sizes.empty:
        out = out.merge(cell_sizes, on=["journal_key", "period"], how="left")
    if "n_articles_group" not in out.columns:
        out["n_articles_group"] = 0
    out["n_articles_group"] = pd.to_numeric(out["n_articles_group"], errors="coerce").fillna(0).astype(int)
    return out


def equal_journal_weight_by_period(jp: pd.DataFrame) -> pd.DataFrame:
    indices = infer_indices(jp)
    if jp.empty or not indices:
        return pd.DataFrame()

    rows = []
    for period, g in jp.groupby("period", dropna=False):
        row = {
            "period": period,
            "n_journals_available": int(g["journal_key"].nunique()),
            "journals_available": " | ".join(sorted(g["journal_key"].astype(str), key=lambda x: JOURNAL_ORDER.get(x, 999))),
        }
        for idx in indices:
            row[f"equal_weight_{idx}"] = round(float(pd.to_numeric(g[idx], errors="coerce").fillna(0).mean()), 4)
            row[f"journal_sd_{idx}"] = round(float(pd.to_numeric(g[idx], errors="coerce").fillna(0).std(ddof=0)), 4)
        rows.append(row)

    return add_sort(pd.DataFrame(rows))


def global_vs_equal_weight(global_period: pd.DataFrame, equal_weight: pd.DataFrame) -> pd.DataFrame:
    if global_period.empty or equal_weight.empty:
        return pd.DataFrame()

    indices = infer_indices(global_period)
    g = global_period[["period"] + indices].copy()
    g = g.rename(columns={idx: f"global_article_weighted_{idx}" for idx in indices})

    out = equal_weight.merge(g, on="period", how="left")

    for idx in indices:
        ew = f"equal_weight_{idx}"
        gw = f"global_article_weighted_{idx}"
        if ew in out.columns and gw in out.columns:
            out[f"equal_minus_global_{idx}"] = (
                pd.to_numeric(out[ew], errors="coerce").fillna(0)
                - pd.to_numeric(out[gw], errors="coerce").fillna(0)
            ).round(4)

    return add_sort(out)


def journals_with_min_periods(jp: pd.DataFrame, min_periods: int) -> List[str]:
    if jp.empty:
        return []
    counts = jp.groupby("journal_key")["period"].nunique()
    return sorted(counts[counts >= min_periods].index.astype(str), key=lambda x: JOURNAL_ORDER.get(x, 999))


def make_long_journal_panel(jp: pd.DataFrame, min_periods: int = LONG_PANEL_MIN_PERIODS) -> pd.DataFrame:
    long_journals = journals_with_min_periods(jp, min_periods)
    out = jp[jp["journal_key"].isin(long_journals)].copy()
    out["panel_type"] = f"long_journal_panel_min_{min_periods}_periods"
    return add_sort(out)


def make_common_period_panel(jp: pd.DataFrame, min_journals: int = COMMON_PERIOD_MIN_JOURNALS) -> pd.DataFrame:
    if jp.empty:
        return pd.DataFrame()
    counts = jp.groupby("period")["journal_key"].nunique()
    common_periods = sorted(counts[counts >= min_journals].index.astype(str), key=lambda x: PERIOD_ORDER.get(x, 999))
    out = jp[jp["period"].isin(common_periods)].copy()
    out["panel_type"] = f"common_period_panel_min_{min_journals}_journals"
    out["n_journals_in_period"] = out["period"].map(counts).astype(int)
    return add_sort(out)


def make_post1990_panel(jp: pd.DataFrame) -> pd.DataFrame:
    out = jp[jp["period"].isin(POST1990_PERIODS)].copy()
    out["panel_type"] = "post1990_multi_journal_panel"
    return add_sort(out)


def first_last_change_for_panel(panel: pd.DataFrame, panel_name: str) -> pd.DataFrame:
    indices = infer_indices(panel)
    if panel.empty or not indices:
        return pd.DataFrame()

    rows = []
    for journal, g in panel.groupby("journal_key", dropna=False):
        gg = g.copy()
        gg["_period_order"] = gg["period"].map(PERIOD_ORDER).fillna(999).astype(int)
        gg = gg.sort_values("_period_order")
        if len(gg) < 2:
            continue
        first = gg.iloc[0]
        last = gg.iloc[-1]

        row = {
            "panel": panel_name,
            "journal_key": journal,
            "first_period": first["period"],
            "last_period": last["period"],
            "n_periods_compared": int(len(gg)),
        }

        for idx in indices:
            first_v = float(pd.to_numeric(pd.Series([first.get(idx, 0)]), errors="coerce").fillna(0).iloc[0])
            last_v = float(pd.to_numeric(pd.Series([last.get(idx, 0)]), errors="coerce").fillna(0).iloc[0])
            row[f"{idx}_first"] = round(first_v, 4)
            row[f"{idx}_last"] = round(last_v, 4)
            row[f"{idx}_change"] = round(last_v - first_v, 4)

        rows.append(row)

    return add_sort(pd.DataFrame(rows))


def make_paired_period_changes(
    jp: pd.DataFrame,
    long_panel: pd.DataFrame,
    common_panel: pd.DataFrame,
    post1990_panel: pd.DataFrame,
) -> pd.DataFrame:
    frames = []
    panels = [
        ("all_available_per_journal", jp),
        ("long_journal_panel", long_panel),
        ("common_period_panel", common_panel),
        ("post1990_panel", post1990_panel),
    ]
    for name, panel in panels:
        part = first_last_change_for_panel(panel, name)
        if not part.empty:
            frames.append(part)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def make_direction_consistency(paired: pd.DataFrame) -> pd.DataFrame:
    if paired.empty:
        return pd.DataFrame()

    rows = []
    for panel, gpanel in paired.groupby("panel", dropna=False):
        for idx in CORE_INDICES:
            col = f"{idx}_change"
            if col not in gpanel.columns:
                continue
            vals = pd.to_numeric(gpanel[col], errors="coerce").fillna(0)
            n = int(len(vals))
            n_pos = int((vals > 0).sum())
            n_neg = int((vals < 0).sum())
            n_zero = int((vals == 0).sum())

            if n_pos > n_neg:
                dominant = "increase"
            elif n_neg > n_pos:
                dominant = "decrease"
            else:
                dominant = "mixed_or_tied"

            rows.append({
                "panel": panel,
                "index": idx,
                "n_journals": n,
                "n_increase": n_pos,
                "n_decrease": n_neg,
                "n_no_change": n_zero,
                "pct_increase": round(n_pos / max(n, 1) * 100, 2),
                "pct_decrease": round(n_neg / max(n, 1) * 100, 2),
                "dominant_direction": dominant,
                "direction_consistency_flag": (
                    "high_consistency" if max(n_pos, n_neg) >= max(1, n - 1)
                    else "moderate_consistency" if max(n_pos, n_neg) >= 3
                    else "low_consistency"
                ),
            })
    return pd.DataFrame(rows)


def summarize_panel(panel: pd.DataFrame, name: str) -> Dict[str, object]:
    if panel.empty:
        return {
            "panel": name,
            "n_rows": 0,
            "journals": [],
            "periods": [],
        }
    return {
        "panel": name,
        "n_rows": int(len(panel)),
        "n_journals": int(panel["journal_key"].nunique()),
        "n_periods": int(panel["period"].nunique()),
        "journals": sorted(panel["journal_key"].astype(str).unique(), key=lambda x: JOURNAL_ORDER.get(x, 999)),
        "periods": sorted(panel["period"].astype(str).unique(), key=lambda x: PERIOD_ORDER.get(x, 999)),
    }


def make_key_conclusions(direction: pd.DataFrame, paired: pd.DataFrame, global_vs_equal: pd.DataFrame) -> Dict[str, object]:
    conclusions: Dict[str, object] = {}

    def direction_for(panel: str, idx: str) -> Dict[str, object]:
        if direction.empty:
            return {}
        row = direction[(direction["panel"] == panel) & (direction["index"] == idx)]
        return row.iloc[0].to_dict() if not row.empty else {}

    for panel in ["all_available_per_journal", "long_journal_panel", "common_period_panel", "post1990_panel"]:
        conclusions[f"{panel}_relational_shift"] = direction_for(panel, "relational_shift_index")
        conclusions[f"{panel}_drive_conflict"] = direction_for(panel, "classical_drive_conflict_index")
        conclusions[f"{panel}_narrative_reframing"] = direction_for(panel, "narrative_reframing_index")
        conclusions[f"{panel}_contextualization"] = direction_for(panel, "contemporary_contextualization_index")

    # Equal-weight vs global: does equal weighting preserve direction across periods?
    if not global_vs_equal.empty and "equal_weight_relational_shift_index" in global_vs_equal.columns:
        ew = global_vs_equal.copy()
        ew["_period_order"] = ew["period"].map(PERIOD_ORDER).fillna(999).astype(int)
        ew = ew.sort_values("_period_order")
        first = ew.iloc[0]
        last = ew.iloc[-1]
        conclusions["equal_weight_first_to_last"] = {
            "first_period": first.get("period", ""),
            "last_period": last.get("period", ""),
            "relational_shift_change_equal_weight": round(
                float(first_last_num(last, "equal_weight_relational_shift_index"))
                - float(first_last_num(first, "equal_weight_relational_shift_index")),
                4,
            ),
            "drive_conflict_change_equal_weight": round(
                float(first_last_num(last, "equal_weight_classical_drive_conflict_index"))
                - float(first_last_num(first, "equal_weight_classical_drive_conflict_index")),
                4,
            ),
            "narrative_reframing_change_equal_weight": round(
                float(first_last_num(last, "equal_weight_narrative_reframing_index"))
                - float(first_last_num(first, "equal_weight_narrative_reframing_index")),
                4,
            ),
        }

    return conclusions


def first_last_num(row: pd.Series, col: str) -> float:
    return float(pd.to_numeric(pd.Series([row.get(col, 0)]), errors="coerce").fillna(0).iloc[0])


def main() -> int:
    parser = argparse.ArgumentParser(description="Journal-balanced semantic change robustness checks.")
    parser.add_argument("--semantic-change-root", default="../data/title_abstract/semantic_change")
    parser.add_argument("--semantic-change-journal-global-root", default="../data/title_abstract/semantic_change_journal_global")
    parser.add_argument("--semantic-refined-root", default="../data/title_abstract/semantic_refined")
    parser.add_argument("--out-dir", default="../data/title_abstract/semantic_change_balanced")
    parser.add_argument("--long-panel-min-periods", type=int, default=LONG_PANEL_MIN_PERIODS)
    parser.add_argument("--common-period-min-journals", type=int, default=COMMON_PERIOD_MIN_JOURNALS)
    args = parser.parse_args()

    paths = get_paths()

    def resolve(p: str) -> Path:
        path = Path(p)
        if not path.is_absolute():
            path = (paths["scripts_dir"] / path).resolve()
        return path

    change_root = resolve(args.semantic_change_root)
    journal_global_root = resolve(args.semantic_change_journal_global_root)
    refined_root = resolve(args.semantic_refined_root)
    out_dir = resolve(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    indices_by_period = read_csv_safe(change_root / "psychoanalytic_core_semantic_change_indices_by_period.csv")
    indices_by_journal_period = read_csv_safe(change_root / "psychoanalytic_core_semantic_change_indices_by_journal_period.csv")
    within_journal = read_csv_safe(journal_global_root / "psychoanalytic_core_within_journal_temporal_change.csv")
    contribution = read_csv_safe(journal_global_root / "psychoanalytic_core_journal_contribution_diagnostics.csv")
    refined_jp_family = read_csv_safe(refined_root / "psychoanalytic_core_semantic_family_by_journal_period_refined.csv")

    if indices_by_period.empty:
        raise SystemExit(f"ERROR: missing indices_by_period in {change_root}")
    if indices_by_journal_period.empty:
        raise SystemExit(f"ERROR: missing indices_by_journal_period in {change_root}")

    cell_sizes = get_cell_sizes(refined_jp_family)
    jp = attach_cell_sizes(indices_by_journal_period, cell_sizes)

    equal_weight = equal_journal_weight_by_period(jp)
    global_equal = global_vs_equal_weight(indices_by_period, equal_weight)

    long_panel = make_long_journal_panel(jp, min_periods=args.long_panel_min_periods)
    common_panel = make_common_period_panel(jp, min_journals=args.common_period_min_journals)
    post1990_panel = make_post1990_panel(jp)

    paired = make_paired_period_changes(jp, long_panel, common_panel, post1990_panel)
    direction = make_direction_consistency(paired)

    outputs = {
        "equal_journal_weight_by_period": out_dir / "psychoanalytic_core_balanced_equal_journal_weight_by_period.csv",
        "global_vs_equal_weight": out_dir / "psychoanalytic_core_balanced_global_vs_equal_weight.csv",
        "long_journal_panel": out_dir / "psychoanalytic_core_balanced_long_journal_panel.csv",
        "common_period_panel": out_dir / "psychoanalytic_core_balanced_common_period_panel.csv",
        "post1990_panel": out_dir / "psychoanalytic_core_balanced_post1990_panel.csv",
        "paired_period_changes": out_dir / "psychoanalytic_core_balanced_paired_period_changes.csv",
        "direction_consistency": out_dir / "psychoanalytic_core_balanced_direction_consistency.csv",
    }

    write_csv(equal_weight, outputs["equal_journal_weight_by_period"])
    write_csv(global_equal, outputs["global_vs_equal_weight"])
    write_csv(long_panel, outputs["long_journal_panel"])
    write_csv(common_panel, outputs["common_period_panel"])
    write_csv(post1990_panel, outputs["post1990_panel"])
    write_csv(paired, outputs["paired_period_changes"])
    write_csv(direction, outputs["direction_consistency"])

    panels = [
        summarize_panel(jp, "all_available_per_journal"),
        summarize_panel(long_panel, "long_journal_panel"),
        summarize_panel(common_panel, "common_period_panel"),
        summarize_panel(post1990_panel, "post1990_panel"),
    ]

    conclusions = make_key_conclusions(direction, paired, global_equal)

    summary = {
        "script_version": SCRIPT_VERSION,
        "created_at_utc": utc_now_iso(),
        "purpose": "Journal-balanced robustness checks for semantic change indices.",
        "inputs": {
            "semantic_change_root": str(change_root),
            "semantic_change_journal_global_root": str(journal_global_root),
            "semantic_refined_root": str(refined_root),
        },
        "parameters": {
            "long_panel_min_periods": args.long_panel_min_periods,
            "common_period_min_journals": args.common_period_min_journals,
            "post1990_periods": sorted(POST1990_PERIODS, key=lambda x: PERIOD_ORDER.get(x, 999)),
        },
        "panels": panels,
        "counts": {
            "n_journal_period_rows": int(len(jp)),
            "n_equal_weight_period_rows": int(len(equal_weight)),
            "n_long_panel_rows": int(len(long_panel)),
            "n_common_panel_rows": int(len(common_panel)),
            "n_post1990_panel_rows": int(len(post1990_panel)),
            "n_paired_change_rows": int(len(paired)),
            "n_direction_rows": int(len(direction)),
        },
        "key_conclusions": conclusions,
        "outputs": {k: str(v) for k, v in outputs.items()},
        "methodological_note": (
            "These are robustness diagnostics, not final causal decomposition. "
            "Equal-journal weighting and within-journal paired changes reduce but do not eliminate "
            "composition effects. Results should be interpreted together with the full-corpus and "
            "journal-vs-global analyses."
        ),
    }

    summary_path = out_dir / "psychoanalytic_core_balanced_semantic_change_summary.json"
    write_json(summary, summary_path)
    summary["outputs"]["summary_json"] = str(summary_path)

    rel_all = conclusions.get("all_available_per_journal_relational_shift", {})
    drive_all = conclusions.get("all_available_per_journal_drive_conflict", {})
    rel_long = conclusions.get("long_journal_panel_relational_shift", {})

    print(json.dumps({
        "status": "ok",
        "script_version": SCRIPT_VERSION,
        "n_journal_period_rows": int(len(jp)),
        "n_long_panel_rows": int(len(long_panel)),
        "n_common_panel_rows": int(len(common_panel)),
        "n_post1990_panel_rows": int(len(post1990_panel)),
        "all_available_relational_direction": rel_all.get("dominant_direction", ""),
        "all_available_drive_conflict_direction": drive_all.get("dominant_direction", ""),
        "long_panel_relational_direction": rel_long.get("dominant_direction", ""),
        "summary_json": str(summary_path),
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
