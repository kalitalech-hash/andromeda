#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4b_journal_vs_global_semantic_change.py

Andromeda Nowicka v0.5-pre
Journal-vs-global semantic change analysis for psychoanalytic_core.

Purpose
-------
4a computed semantic change indices globally, by journal, by period, and by
journal × period. 4b asks a more critical methodological question:

    Is the observed semantic change a corpus-wide historical shift,
    or is it driven mainly by journal composition and journal-specific cultures?

This script compares journal-period trajectories with global period trends and
creates diagnostic tables for:

- journal deviations from global period profile,
- within-journal temporal change,
- direction consistency across journals,
- journal-period distinctiveness,
- possible composition-driven effects,
- relational / drive-conflict / narrative-reframing trajectories by journal.

It does not make final causal claims. It prepares evidence for later
journal-balanced and robustness analyses.

Inputs
------
From 4a:
    ../data/title_abstract/semantic_change/psychoanalytic_core_semantic_change_indices_by_period.csv
    ../data/title_abstract/semantic_change/psychoanalytic_core_semantic_change_indices_by_journal.csv
    ../data/title_abstract/semantic_change/psychoanalytic_core_semantic_change_indices_by_journal_period.csv
    ../data/title_abstract/semantic_change/psychoanalytic_core_semantic_change_journal_vs_global_period.csv

Refined family-by-journal-period table:
    ../data/title_abstract/semantic_refined/psychoanalytic_core_semantic_family_by_journal_period_refined.csv

Outputs
-------
../data/title_abstract/semantic_change_journal_global/
    psychoanalytic_core_journal_vs_global_index_deviations.csv
    psychoanalytic_core_within_journal_temporal_change.csv
    psychoanalytic_core_direction_consistency_by_index.csv
    psychoanalytic_core_journal_period_distinctiveness_ranked.csv
    psychoanalytic_core_journal_contribution_diagnostics.csv
    psychoanalytic_core_journal_trajectory_summary.csv
    psychoanalytic_core_global_vs_journal_semantic_change_summary.json

Run
---
Put this file in:

    data_psychoanalytic_core/scripts/

Run:

    cd data_psychoanalytic_core/scripts
    python 4b_journal_vs_global_semantic_change.py
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

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
        "semantic_refined_root": title_root / "semantic_refined",
        "out_root": title_root / "semantic_change_journal_global",
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


def infer_available_indices(df: pd.DataFrame) -> List[str]:
    return [c for c in CORE_INDICES if c in df.columns]


def make_deviations(jp: pd.DataFrame, period: pd.DataFrame) -> pd.DataFrame:
    """
    Compare journal-period index values with global period values.
    """
    indices = infer_available_indices(jp)
    if jp.empty or period.empty or not indices:
        return pd.DataFrame()

    global_period = period[["period"] + indices].copy()
    global_period = global_period.rename(columns={c: f"global_{c}" for c in indices})

    out = jp[["journal_key", "period"] + indices].merge(global_period, on="period", how="left")

    for idx in indices:
        out[f"delta_from_global_{idx}"] = (
            num(out, idx) - num(out, f"global_{idx}")
        ).round(4)

    # Compact signed and absolute distinctiveness summaries.
    focus_delta_cols = [f"delta_from_global_{idx}" for idx in FOCUS_INDICES if f"delta_from_global_{idx}" in out.columns]
    if focus_delta_cols:
        out["mean_abs_focus_deviation"] = (
            out[focus_delta_cols].apply(pd.to_numeric, errors="coerce").abs().mean(axis=1)
        ).round(4)
        out["mean_signed_focus_deviation"] = (
            out[focus_delta_cols].apply(pd.to_numeric, errors="coerce").mean(axis=1)
        ).round(4)
    else:
        out["mean_abs_focus_deviation"] = 0.0
        out["mean_signed_focus_deviation"] = 0.0

    return add_sort(out)


def first_last_change(g: pd.DataFrame, index: str) -> Tuple[str, str, float, float, float, int]:
    gg = g.copy()
    gg["_period_order"] = gg["period"].map(PERIOD_ORDER).fillna(999).astype(int)
    gg = gg.sort_values("_period_order")
    if gg.empty:
        return "", "", 0.0, 0.0, 0.0, 0
    first = gg.iloc[0]
    last = gg.iloc[-1]
    first_val = float(pd.to_numeric(pd.Series([first.get(index, 0)]), errors="coerce").fillna(0).iloc[0])
    last_val = float(pd.to_numeric(pd.Series([last.get(index, 0)]), errors="coerce").fillna(0).iloc[0])
    return (
        str(first.get("period", "")),
        str(last.get("period", "")),
        round(first_val, 4),
        round(last_val, 4),
        round(last_val - first_val, 4),
        int(len(gg)),
    )


def make_within_journal_change(jp: pd.DataFrame) -> pd.DataFrame:
    """
    First-to-last observed period change within each journal.
    This avoids pretending that all journals span all periods.
    """
    indices = infer_available_indices(jp)
    if jp.empty or not indices:
        return pd.DataFrame()

    rows = []
    for journal, g in jp.groupby("journal_key", dropna=False):
        row = {"journal_key": journal}
        observed_periods = sorted(
            {str(p) for p in g["period"].astype(str)},
            key=lambda p: PERIOD_ORDER.get(p, 999),
        )
        row["observed_periods"] = " | ".join(observed_periods)
        row["n_observed_periods"] = len(observed_periods)

        for idx in indices:
            first_p, last_p, first_v, last_v, delta, n_periods = first_last_change(g, idx)
            row[f"{idx}_first_period"] = first_p
            row[f"{idx}_last_period"] = last_p
            row[f"{idx}_first"] = first_v
            row[f"{idx}_last"] = last_v
            row[f"{idx}_change"] = delta

        # A compact interpretive flag.
        rel_change = row.get("relational_shift_index_change", 0)
        drive_change = row.get("classical_drive_conflict_index_change", 0)
        narrative_change = row.get("narrative_reframing_index_change", 0)
        context_change = row.get("contemporary_contextualization_index_change", 0)

        flags = []
        if rel_change > 0:
            flags.append("relational_shift_increases")
        elif rel_change < 0:
            flags.append("relational_shift_decreases")

        if drive_change < 0:
            flags.append("drive_conflict_decreases")
        elif drive_change > 0:
            flags.append("drive_conflict_increases")

        if narrative_change > 0:
            flags.append("narrative_reframing_increases")
        if context_change > 0:
            flags.append("contextualization_increases")

        row["trajectory_flags"] = " | ".join(flags)
        rows.append(row)

    out = pd.DataFrame(rows)
    return add_sort(out)


def make_direction_consistency(within: pd.DataFrame) -> pd.DataFrame:
    """
    Count how many journals show positive/negative/no change for each index.
    """
    if within.empty:
        return pd.DataFrame()

    rows = []
    for idx in CORE_INDICES:
        col = f"{idx}_change"
        if col not in within.columns:
            continue

        vals = pd.to_numeric(within[col], errors="coerce").fillna(0)
        n_pos = int((vals > 0).sum())
        n_neg = int((vals < 0).sum())
        n_zero = int((vals == 0).sum())
        n = int(len(vals))

        if n_pos > n_neg:
            dominant = "increase"
        elif n_neg > n_pos:
            dominant = "decrease"
        else:
            dominant = "mixed_or_tied"

        rows.append({
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


def make_distinctiveness_ranked(deviations: pd.DataFrame) -> pd.DataFrame:
    if deviations.empty:
        return pd.DataFrame()
    out = deviations.copy()
    out = out.sort_values("mean_abs_focus_deviation", ascending=False)
    out.insert(0, "distinctiveness_rank", range(1, len(out) + 1))
    return out


def make_contribution_diagnostics(
    by_journal_period_family: pd.DataFrame,
    jp_indices: pd.DataFrame,
) -> pd.DataFrame:
    """
    Estimate journal-period cell size and pair it with key index levels.

    This does not compute exact causal contribution to the global trend, but it
    flags cells that combine high article volume with high index intensity.
    """
    if by_journal_period_family.empty or jp_indices.empty:
        return pd.DataFrame()

    if "n_articles_group" not in by_journal_period_family.columns:
        return pd.DataFrame()

    cell_sizes = (
        by_journal_period_family[["journal_key", "period", "n_articles_group"]]
        .drop_duplicates()
        .copy()
    )
    cell_sizes["n_articles_group"] = pd.to_numeric(cell_sizes["n_articles_group"], errors="coerce").fillna(0).astype(int)

    out = cell_sizes.merge(
        jp_indices,
        on=["journal_key", "period"],
        how="left",
    )

    total_by_period = (
        cell_sizes.groupby("period", dropna=False)
        .agg(n_articles_period_total=("n_articles_group", "sum"))
        .reset_index()
    )
    out = out.merge(total_by_period, on="period", how="left")
    out["cell_article_share_of_period_pct"] = (
        out["n_articles_group"] / out["n_articles_period_total"].replace(0, pd.NA) * 100
    ).round(4).fillna(0)

    for idx in [
        "relational_shift_index",
        "classical_drive_conflict_index",
        "contemporary_contextualization_index",
        "narrative_reframing_index",
        "research_psychology_index",
    ]:
        if idx in out.columns:
            out[f"{idx}_weighted_cell_signal"] = (
                pd.to_numeric(out[idx], errors="coerce").fillna(0)
                * out["cell_article_share_of_period_pct"] / 100
            ).round(4)

    return add_sort(out)


def make_trajectory_summary(within: pd.DataFrame, deviations: pd.DataFrame, distinctiveness: pd.DataFrame) -> pd.DataFrame:
    if within.empty:
        return pd.DataFrame()

    rows = []
    for _, r in within.iterrows():
        journal = r["journal_key"]
        d = deviations[deviations["journal_key"] == journal].copy()
        mean_dev = float(d["mean_abs_focus_deviation"].mean()) if not d.empty else 0.0
        max_dev = float(d["mean_abs_focus_deviation"].max()) if not d.empty else 0.0

        rows.append({
            "journal_key": journal,
            "observed_periods": r.get("observed_periods", ""),
            "n_observed_periods": r.get("n_observed_periods", ""),
            "relational_shift_index_change": r.get("relational_shift_index_change", ""),
            "classical_drive_conflict_index_change": r.get("classical_drive_conflict_index_change", ""),
            "classical_metapsychology_index_change": r.get("classical_metapsychology_index_change", ""),
            "contemporary_contextualization_index_change": r.get("contemporary_contextualization_index_change", ""),
            "narrative_reframing_index_change": r.get("narrative_reframing_index_change", ""),
            "research_psychology_index_change": r.get("research_psychology_index_change", ""),
            "mean_abs_focus_deviation_from_global_period": round(mean_dev, 4),
            "max_abs_focus_deviation_from_global_period": round(max_dev, 4),
            "trajectory_flags": r.get("trajectory_flags", ""),
        })

    out = pd.DataFrame(rows)

    # Add rough narrative interpretation.
    labels = []
    for _, r in out.iterrows():
        rel = float(pd.to_numeric(pd.Series([r.get("relational_shift_index_change", 0)]), errors="coerce").fillna(0).iloc[0])
        drive = float(pd.to_numeric(pd.Series([r.get("classical_drive_conflict_index_change", 0)]), errors="coerce").fillna(0).iloc[0])
        dev = float(pd.to_numeric(pd.Series([r.get("mean_abs_focus_deviation_from_global_period", 0)]), errors="coerce").fillna(0).iloc[0])
        context = float(pd.to_numeric(pd.Series([r.get("contemporary_contextualization_index_change", 0)]), errors="coerce").fillna(0).iloc[0])

        if dev >= 20 and rel > 0:
            labels.append("distinct_relational_or_contextual_trajectory")
        elif rel > 0 and drive < 0:
            labels.append("within_journal_relational_shift")
        elif drive < 0 and context > 0:
            labels.append("within_journal_classical_decline_contextual_rise")
        elif dev >= 20:
            labels.append("distinct_non_global_trajectory")
        else:
            labels.append("mixed_or_limited_temporal_signal")

    out["trajectory_interpretive_label"] = labels
    return add_sort(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Journal-vs-global semantic change diagnostics.")
    parser.add_argument("--semantic-change-root", default="../data/title_abstract/semantic_change")
    parser.add_argument("--semantic-refined-root", default="../data/title_abstract/semantic_refined")
    parser.add_argument("--out-dir", default="../data/title_abstract/semantic_change_journal_global")
    args = parser.parse_args()

    paths = get_paths()

    def resolve(p: str) -> Path:
        path = Path(p)
        if not path.is_absolute():
            path = (paths["scripts_dir"] / path).resolve()
        return path

    change_root = resolve(args.semantic_change_root)
    refined_root = resolve(args.semantic_refined_root)
    out_dir = resolve(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    indices_by_period = read_csv_safe(change_root / "psychoanalytic_core_semantic_change_indices_by_period.csv")
    indices_by_journal = read_csv_safe(change_root / "psychoanalytic_core_semantic_change_indices_by_journal.csv")
    indices_by_journal_period = read_csv_safe(change_root / "psychoanalytic_core_semantic_change_indices_by_journal_period.csv")
    precomputed_journal_vs_global = read_csv_safe(change_root / "psychoanalytic_core_semantic_change_journal_vs_global_period.csv")
    refined_jp_family = read_csv_safe(refined_root / "psychoanalytic_core_semantic_family_by_journal_period_refined.csv")

    if indices_by_period.empty:
        raise SystemExit(f"ERROR: missing indices_by_period in {change_root}")
    if indices_by_journal_period.empty:
        raise SystemExit(f"ERROR: missing indices_by_journal_period in {change_root}")

    deviations = make_deviations(indices_by_journal_period, indices_by_period)
    within = make_within_journal_change(indices_by_journal_period)
    direction = make_direction_consistency(within)
    distinctiveness = make_distinctiveness_ranked(deviations)
    contribution = make_contribution_diagnostics(refined_jp_family, indices_by_journal_period)
    trajectory = make_trajectory_summary(within, deviations, distinctiveness)

    outputs = {
        "deviations": out_dir / "psychoanalytic_core_journal_vs_global_index_deviations.csv",
        "within_journal_temporal_change": out_dir / "psychoanalytic_core_within_journal_temporal_change.csv",
        "direction_consistency": out_dir / "psychoanalytic_core_direction_consistency_by_index.csv",
        "distinctiveness_ranked": out_dir / "psychoanalytic_core_journal_period_distinctiveness_ranked.csv",
        "contribution_diagnostics": out_dir / "psychoanalytic_core_journal_contribution_diagnostics.csv",
        "trajectory_summary": out_dir / "psychoanalytic_core_journal_trajectory_summary.csv",
    }

    write_csv(deviations, outputs["deviations"])
    write_csv(within, outputs["within_journal_temporal_change"])
    write_csv(direction, outputs["direction_consistency"])
    write_csv(distinctiveness, outputs["distinctiveness_ranked"])
    write_csv(contribution, outputs["contribution_diagnostics"])
    write_csv(trajectory, outputs["trajectory_summary"])

    # Summary snippets.
    direction_focus = (
        direction[direction["index"].isin(FOCUS_INDICES)].to_dict(orient="records")
        if not direction.empty else []
    )

    top_distinctive_cells = (
        distinctiveness.head(10).to_dict(orient="records")
        if not distinctiveness.empty else []
    )

    trajectory_records = (
        trajectory.to_dict(orient="records")
        if not trajectory.empty else []
    )

    # Conservative conclusion flags.
    rel_row = direction[direction["index"] == "relational_shift_index"] if not direction.empty else pd.DataFrame()
    drive_row = direction[direction["index"] == "classical_drive_conflict_index"] if not direction.empty else pd.DataFrame()

    relational_direction = rel_row.iloc[0].to_dict() if not rel_row.empty else {}
    drive_direction = drive_row.iloc[0].to_dict() if not drive_row.empty else {}

    summary = {
        "script_version": SCRIPT_VERSION,
        "created_at_utc": utc_now_iso(),
        "purpose": "Diagnose global-vs-journal dynamics of semantic change indices.",
        "inputs": {
            "semantic_change_root": str(change_root),
            "semantic_refined_root": str(refined_root),
        },
        "outputs": {k: str(v) for k, v in outputs.items()},
        "counts": {
            "n_journal_period_rows": int(len(indices_by_journal_period)),
            "n_deviation_rows": int(len(deviations)),
            "n_within_journal_rows": int(len(within)),
            "n_direction_rows": int(len(direction)),
            "n_distinctiveness_rows": int(len(distinctiveness)),
            "n_contribution_rows": int(len(contribution)),
        },
        "direction_consistency_focus": direction_focus,
        "relational_shift_direction": relational_direction,
        "drive_conflict_direction": drive_direction,
        "top_distinctive_journal_period_cells": top_distinctive_cells,
        "journal_trajectory_summary": trajectory_records,
        "methodological_note": (
            "This script does not prove whether global change is independent of journal composition. "
            "It identifies where journal-specific trajectories align with or diverge from the global trend. "
            "A stricter next step should construct journal-balanced comparisons."
        ),
    }

    summary_path = out_dir / "psychoanalytic_core_global_vs_journal_semantic_change_summary.json"
    write_json(summary, summary_path)
    summary["outputs"]["summary_json"] = str(summary_path)

    print(json.dumps({
        "status": "ok",
        "script_version": SCRIPT_VERSION,
        "n_journal_period_rows": summary["counts"]["n_journal_period_rows"],
        "n_deviation_rows": summary["counts"]["n_deviation_rows"],
        "n_within_journal_rows": summary["counts"]["n_within_journal_rows"],
        "n_direction_rows": summary["counts"]["n_direction_rows"],
        "relational_direction": relational_direction.get("dominant_direction", ""),
        "drive_conflict_direction": drive_direction.get("dominant_direction", ""),
        "summary_json": str(summary_path),
        "trajectory_summary": str(outputs["trajectory_summary"]),
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
