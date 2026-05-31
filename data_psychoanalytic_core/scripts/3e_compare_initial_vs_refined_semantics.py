#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3e_compare_initial_vs_refined_semantics.py

Andromeda Nowicka v0.5-pre
Compare initial vs refined semantic-family application.

Purpose
-------
Compare Stage 3 initial semantic application with the refined marker-strength
application.

The refined layer is more conservative: weak markers alone and name markers
alone do not count as full family hits.

Outputs are written to:

    ../data/title_abstract/semantic_comparison/

Run
---
Put this file in:

    data_psychoanalytic_core/scripts/

Run:

    cd data_psychoanalytic_core/scripts
    python 3e_compare_initial_vs_refined_semantics.py
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Dict

import pandas as pd


SCRIPT_VERSION = "v0.1.0"

SEMANTIC_FAMILY_ORDER = [
    "drive_conflict_defense",
    "dream_fantasy_unconscious",
    "ego_self_narcissism",
    "object_relations",
    "kleinian_bionian",
    "winnicottian_environment_holding",
    "attachment_development_infant",
    "transference_countertransference",
    "technique_interpretation_process",
    "relational_intersubjective_field",
    "trauma_dissociation_affect_regulation",
    "psychosis_borderline_primitive_states",
    "body_sexuality_gender",
    "language_narrative_symbolization",
    "culture_race_social_ethics",
    "empirical_research_measurement",
    "history_theory_schools",
]

RELATIONAL_FAMILY = "relational_intersubjective_field"
CLASSICAL_FAMILY = "drive_conflict_defense"
CULTURE_FAMILY = "culture_race_social_ethics"
TRAUMA_FAMILY = "trauma_dissociation_affect_regulation"


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
    }


def read_csv_safe(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")


def read_json_safe(path: Path) -> Dict:
    if not path.exists() or path.stat().st_size == 0:
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def write_json(payload: Dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def family_order_value(family: str) -> int:
    try:
        return SEMANTIC_FAMILY_ORDER.index(str(family))
    except ValueError:
        return 999


def numeric(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series([0] * len(df), index=df.index, dtype="float64")
    return pd.to_numeric(df[col], errors="coerce").fillna(0)


def classify_impact(drop: float, retention: float) -> str:
    if drop >= 20 or retention < 50:
        return "high_marker_strength_impact"
    if drop >= 10 or retention < 70:
        return "medium_marker_strength_impact"
    if drop >= 5 or retention < 85:
        return "low_marker_strength_impact"
    return "minimal_marker_strength_impact"


def standardize_initial_counts(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if out.empty:
        return pd.DataFrame(columns=["semantic_family", "n_articles_initial", "pct_articles_initial", "n_family_hits_initial"])
    out["n_articles_initial"] = numeric(out, "n_articles").astype(int)
    out["pct_articles_initial"] = numeric(out, "pct_articles")
    out["n_family_hits_initial"] = numeric(out, "n_family_hits").astype(int)
    return out[["semantic_family", "n_articles_initial", "pct_articles_initial", "n_family_hits_initial"]]


def standardize_refined_counts(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if out.empty:
        return pd.DataFrame(columns=[
            "semantic_family", "n_articles_refined", "pct_articles_refined",
            "n_articles_any_marker", "pct_articles_any_marker",
            "n_weak_only_rows", "n_name_only_rows"
        ])
    out["n_articles_refined"] = numeric(out, "n_articles_refined").astype(int)
    out["pct_articles_refined"] = numeric(out, "pct_articles_refined")
    out["n_articles_any_marker"] = numeric(out, "n_articles_any_marker").astype(int)
    out["pct_articles_any_marker"] = numeric(out, "pct_articles_any_marker")
    out["n_weak_only_rows"] = numeric(out, "n_weak_only_rows").astype(int)
    out["n_name_only_rows"] = numeric(out, "n_name_only_rows").astype(int)
    return out[[
        "semantic_family", "n_articles_refined", "pct_articles_refined",
        "n_articles_any_marker", "pct_articles_any_marker",
        "n_weak_only_rows", "n_name_only_rows"
    ]]


def compare_family_counts(initial: pd.DataFrame, refined: pd.DataFrame) -> pd.DataFrame:
    i = standardize_initial_counts(initial)
    r = standardize_refined_counts(refined)
    out = i.merge(r, on="semantic_family", how="outer").fillna(0)

    int_cols = [
        "n_articles_initial", "n_family_hits_initial",
        "n_articles_refined", "n_articles_any_marker",
        "n_weak_only_rows", "n_name_only_rows"
    ]
    for col in int_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0).astype(int)

    float_cols = ["pct_articles_initial", "pct_articles_refined", "pct_articles_any_marker"]
    for col in float_cols:
        out[col] = pd.to_numeric(out[col], errors="coerce").fillna(0.0)

    out["delta_pct_refined_minus_initial"] = (out["pct_articles_refined"] - out["pct_articles_initial"]).round(4)
    out["absolute_pct_drop"] = (out["pct_articles_initial"] - out["pct_articles_refined"]).round(4)
    out["relative_retention_pct"] = (
        out["pct_articles_refined"] / out["pct_articles_initial"].replace(0, pd.NA) * 100
    ).round(2).fillna(0)
    out["n_articles_removed_by_refinement"] = out["n_articles_initial"] - out["n_articles_refined"]
    out["marker_strength_impact_flag"] = [
        classify_impact(float(d), float(r))
        for d, r in zip(out["absolute_pct_drop"], out["relative_retention_pct"])
    ]
    out["_family_order"] = out["semantic_family"].map(family_order_value)
    return out.sort_values(["_family_order", "semantic_family"]).drop(columns=["_family_order"])


def standardize_group_initial(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    if out.empty:
        return pd.DataFrame(columns=group_cols + [
            "semantic_family", "n_articles_initial", "pct_articles_group_initial", "n_articles_group_initial"
        ])
    out["n_articles_initial"] = numeric(out, "n_articles").astype(int)
    out["pct_articles_group_initial"] = numeric(out, "pct_articles_group")
    out["n_articles_group_initial"] = numeric(out, "n_articles_group").astype(int)
    return out[group_cols + ["semantic_family", "n_articles_initial", "pct_articles_group_initial", "n_articles_group_initial"]]


def standardize_group_refined(df: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    out = df.copy()
    if out.empty:
        return pd.DataFrame(columns=group_cols + [
            "semantic_family", "n_articles_refined", "pct_articles_group_refined", "n_articles_group_refined"
        ])
    out["n_articles_refined"] = numeric(out, "n_articles_refined").astype(int)
    out["pct_articles_group_refined"] = numeric(out, "pct_articles_group_refined")
    out["n_articles_group_refined"] = numeric(out, "n_articles_group").astype(int)
    return out[group_cols + ["semantic_family", "n_articles_refined", "pct_articles_group_refined", "n_articles_group_refined"]]


def compare_group(initial: pd.DataFrame, refined: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    i = standardize_group_initial(initial, group_cols)
    r = standardize_group_refined(refined, group_cols)
    out = i.merge(r, on=group_cols + ["semantic_family"], how="outer").fillna(0)

    out["delta_pct_refined_minus_initial"] = (
        numeric(out, "pct_articles_group_refined") - numeric(out, "pct_articles_group_initial")
    ).round(4)
    out["absolute_pct_drop"] = (
        numeric(out, "pct_articles_group_initial") - numeric(out, "pct_articles_group_refined")
    ).round(4)
    out["relative_retention_pct"] = (
        numeric(out, "pct_articles_group_refined") / numeric(out, "pct_articles_group_initial").replace(0, pd.NA) * 100
    ).round(2).fillna(0)
    out["_family_order"] = out["semantic_family"].map(family_order_value)
    return out.sort_values(group_cols + ["_family_order", "semantic_family"]).drop(columns=["_family_order"])


def impact_ranking(comparison: pd.DataFrame) -> pd.DataFrame:
    if comparison.empty:
        return pd.DataFrame()
    out = comparison.sort_values(["absolute_pct_drop", "n_articles_removed_by_refinement"], ascending=[False, False]).copy()
    out.insert(0, "impact_rank", range(1, len(out) + 1))
    return out


def make_relational_shift_table(by_period_comp: pd.DataFrame) -> pd.DataFrame:
    if by_period_comp.empty:
        return pd.DataFrame()

    rows = []
    for period, g in by_period_comp.groupby("period", dropna=False):
        def val(family: str, col: str) -> float:
            s = g.loc[g["semantic_family"] == family, col]
            if s.empty:
                return 0.0
            return float(pd.to_numeric(s, errors="coerce").fillna(0).iloc[0])

        relational_initial = val(RELATIONAL_FAMILY, "pct_articles_group_initial")
        relational_refined = val(RELATIONAL_FAMILY, "pct_articles_group_refined")
        classical_initial = val(CLASSICAL_FAMILY, "pct_articles_group_initial")
        classical_refined = val(CLASSICAL_FAMILY, "pct_articles_group_refined")
        culture_refined = val(CULTURE_FAMILY, "pct_articles_group_refined")
        trauma_refined = val(TRAUMA_FAMILY, "pct_articles_group_refined")

        rows.append({
            "period": period,
            "relational_initial_pct": round(relational_initial, 4),
            "relational_refined_pct": round(relational_refined, 4),
            "drive_conflict_initial_pct": round(classical_initial, 4),
            "drive_conflict_refined_pct": round(classical_refined, 4),
            "culture_race_social_ethics_refined_pct": round(culture_refined, 4),
            "trauma_dissociation_affect_regulation_refined_pct": round(trauma_refined, 4),
            "relational_minus_drive_conflict_refined": round(relational_refined - classical_refined, 4),
            "relational_to_drive_conflict_ratio_refined": round(relational_refined / classical_refined, 4) if classical_refined else "",
            "contemporary_contextualization_index": round(culture_refined + trauma_refined, 4),
        })

    out = pd.DataFrame(rows)
    period_order = {
        "1920-1945": 1,
        "1946-1969": 2,
        "1970-1989": 3,
        "1990-2009": 4,
        "2010-2025": 5,
    }
    out["_period_order"] = out["period"].map(period_order).fillna(999)
    return out.sort_values(["_period_order", "period"]).drop(columns=["_period_order"])


def top_changes_by_group(comp: pd.DataFrame, group_cols: list[str], n: int = 5) -> pd.DataFrame:
    if comp.empty:
        return pd.DataFrame()
    rows = []
    for _, g in comp.groupby(group_cols, dropna=False):
        rows.append(g.sort_values("absolute_pct_drop", ascending=False).head(n))
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare initial vs refined semantic application.")
    parser.add_argument("--initial-root", default="../data/title_abstract/semantic_application")
    parser.add_argument("--refined-root", default="../data/title_abstract/semantic_refined")
    parser.add_argument("--out-dir", default="../data/title_abstract/semantic_comparison")
    args = parser.parse_args()

    paths = get_paths()

    def resolve(p: str) -> Path:
        path = Path(p)
        if not path.is_absolute():
            path = (paths["scripts_dir"] / path).resolve()
        return path

    initial_root = resolve(args.initial_root)
    refined_root = resolve(args.refined_root)
    out_dir = resolve(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    initial_counts = read_csv_safe(initial_root / "psychoanalytic_core_initial_semantic_family_counts.csv")
    refined_counts = read_csv_safe(refined_root / "psychoanalytic_core_semantic_family_counts_refined.csv")
    initial_by_journal = read_csv_safe(initial_root / "psychoanalytic_core_semantic_family_by_journal.csv")
    refined_by_journal = read_csv_safe(refined_root / "psychoanalytic_core_semantic_family_by_journal_refined.csv")
    initial_by_period = read_csv_safe(initial_root / "psychoanalytic_core_semantic_family_by_period.csv")
    refined_by_period = read_csv_safe(refined_root / "psychoanalytic_core_semantic_family_by_period_refined.csv")
    initial_by_journal_period = read_csv_safe(initial_root / "psychoanalytic_core_semantic_family_by_journal_period.csv")
    refined_by_journal_period = read_csv_safe(refined_root / "psychoanalytic_core_semantic_family_by_journal_period_refined.csv")
    initial_summary = read_json_safe(initial_root / "psychoanalytic_core_semantic_application_summary.json")
    refined_summary = read_json_safe(refined_root / "psychoanalytic_core_semantic_marker_strength_summary.json")

    if initial_counts.empty:
        raise SystemExit(f"ERROR: missing initial counts in {initial_root}")
    if refined_counts.empty:
        raise SystemExit(f"ERROR: missing refined counts in {refined_root}")

    global_comp = compare_family_counts(initial_counts, refined_counts)
    by_journal_comp = compare_group(initial_by_journal, refined_by_journal, ["journal_key"])
    by_period_comp = compare_group(initial_by_period, refined_by_period, ["period"])
    by_journal_period_comp = compare_group(initial_by_journal_period, refined_by_journal_period, ["journal_key", "period"])
    impact = impact_ranking(global_comp)
    relational_shift = make_relational_shift_table(by_period_comp)
    top_journal_changes = top_changes_by_group(by_journal_comp, ["journal_key"], n=5)
    top_period_changes = top_changes_by_group(by_period_comp, ["period"], n=5)

    outputs = {
        "global_comparison": out_dir / "psychoanalytic_core_initial_vs_refined_family_counts.csv",
        "by_journal_comparison": out_dir / "psychoanalytic_core_initial_vs_refined_by_journal.csv",
        "by_period_comparison": out_dir / "psychoanalytic_core_initial_vs_refined_by_period.csv",
        "by_journal_period_comparison": out_dir / "psychoanalytic_core_initial_vs_refined_by_journal_period.csv",
        "impact_ranking": out_dir / "psychoanalytic_core_family_marker_strength_impact_ranking.csv",
        "relational_shift": out_dir / "psychoanalytic_core_relational_shift_initial_vs_refined.csv",
        "top_journal_changes": out_dir / "psychoanalytic_core_top_marker_strength_changes_by_journal.csv",
        "top_period_changes": out_dir / "psychoanalytic_core_top_marker_strength_changes_by_period.csv",
    }

    for key, path in outputs.items():
        df = {
            "global_comparison": global_comp,
            "by_journal_comparison": by_journal_comp,
            "by_period_comparison": by_period_comp,
            "by_journal_period_comparison": by_journal_period_comp,
            "impact_ranking": impact,
            "relational_shift": relational_shift,
            "top_journal_changes": top_journal_changes,
            "top_period_changes": top_period_changes,
        }[key]
        write_csv(df, path)

    n_articles_initial = initial_summary.get("articles", {}).get("n_articles")
    n_any_initial = initial_summary.get("articles", {}).get("n_articles_with_any_semantic_family_hit")
    pct_any_initial = initial_summary.get("articles", {}).get("pct_articles_with_any_semantic_family_hit")
    n_articles_refined = refined_summary.get("articles", {}).get("n_articles")
    n_refined = refined_summary.get("articles", {}).get("n_articles_with_refined_semantic_family_hit")
    pct_refined = refined_summary.get("articles", {}).get("pct_articles_with_refined_semantic_family_hit")
    n_any_marker = refined_summary.get("articles", {}).get("n_articles_with_any_marker_hit")
    pct_any_marker = refined_summary.get("articles", {}).get("pct_articles_with_any_marker_hit")

    largest_drops = []
    if not impact.empty:
        largest_drops = (
            impact[[
                "impact_rank", "semantic_family", "pct_articles_initial", "pct_articles_refined",
                "absolute_pct_drop", "relative_retention_pct", "marker_strength_impact_flag"
            ]]
            .head(10)
            .to_dict(orient="records")
        )

    relational_summary = {}
    if not relational_shift.empty:
        first_period = relational_shift.iloc[0].to_dict()
        last_period = relational_shift.iloc[-1].to_dict()
        relational_summary = {
            "first_period": first_period,
            "last_period": last_period,
            "relational_refined_change_first_to_last": round(
                float(last_period.get("relational_refined_pct", 0) or 0)
                - float(first_period.get("relational_refined_pct", 0) or 0),
                4,
            ),
            "drive_conflict_refined_change_first_to_last": round(
                float(last_period.get("drive_conflict_refined_pct", 0) or 0)
                - float(first_period.get("drive_conflict_refined_pct", 0) or 0),
                4,
            ),
        }

    summary = {
        "script_version": SCRIPT_VERSION,
        "created_at_utc": utc_now_iso(),
        "purpose": "Compare initial and refined semantic-family application after marker-strength correction.",
        "inputs": {
            "initial_root": str(initial_root),
            "refined_root": str(refined_root),
        },
        "coverage": {
            "n_articles_initial": n_articles_initial,
            "n_articles_refined": n_articles_refined,
            "n_articles_with_any_initial_family_hit": n_any_initial,
            "pct_articles_with_any_initial_family_hit": pct_any_initial,
            "n_articles_with_refined_family_hit": n_refined,
            "pct_articles_with_refined_family_hit": pct_refined,
            "n_articles_with_any_marker_hit_after_refinement": n_any_marker,
            "pct_articles_with_any_marker_hit_after_refinement": pct_any_marker,
        },
        "largest_family_drops": largest_drops,
        "relational_shift_summary": relational_summary,
        "outputs": {k: str(v) for k, v in outputs.items()},
        "interpretive_note": (
            "The comparison documents the conservative effect of marker-strength correction. "
            "Families that depended heavily on broad weak markers should drop most. "
            "Signals that persist after refinement are stronger candidates for interpretation."
        ),
    }

    summary_path = out_dir / "psychoanalytic_core_semantic_comparison_summary.json"
    write_json(summary, summary_path)
    summary["outputs"]["summary_json"] = str(summary_path)

    print(json.dumps({
        "status": "ok",
        "script_version": SCRIPT_VERSION,
        "global_family_rows": int(len(global_comp)),
        "journal_family_rows": int(len(by_journal_comp)),
        "period_family_rows": int(len(by_period_comp)),
        "journal_period_family_rows": int(len(by_journal_period_comp)),
        "pct_initial_any_hit": pct_any_initial,
        "pct_refined_hit": pct_refined,
        "largest_drop_family": largest_drops[0]["semantic_family"] if largest_drops else "",
        "largest_drop_pct_points": largest_drops[0]["absolute_pct_drop"] if largest_drops else "",
        "summary_json": str(summary_path),
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
