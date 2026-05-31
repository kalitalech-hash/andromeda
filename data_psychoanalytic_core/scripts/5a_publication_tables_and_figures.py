#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
5a_publication_tables_and_figures.py

Andromeda Nowicka v0.5-pre
Publication-oriented tables and first figures for psychoanalytic_core.

Purpose
-------
Create clean, publication-facing tables and first figures from Stage 3–4 outputs.

This script does NOT change the analytical data. It only prepares selected
tables and visualizations for inspection, writing, and later manuscript use.

Core sources:
- refined semantic-family results
- initial-vs-refined comparison
- semantic change indices
- journal-vs-global diagnostics
- journal-balanced robustness checks

Outputs
-------
../data/title_abstract/publication_outputs/

Tables:
    publication_table_01_corpus_semantic_coverage.csv
    publication_table_02_semantic_family_counts_refined.csv
    publication_table_03_semantic_indices_by_period.csv
    publication_table_04_journal_trajectories.csv
    publication_table_05_balanced_direction_consistency.csv
    publication_table_06_initial_vs_refined_impact.csv
    publication_table_07_journal_distinctiveness.csv
    publication_table_08_narrative_table.csv

Figures:
    publication_figure_01_relational_vs_drive_by_period.png
    publication_figure_02_narrative_reframing_by_period.png
    publication_figure_03_contextualization_by_period.png
    publication_figure_04_journal_relational_shift_trajectories.png
    publication_figure_05_equal_weight_vs_global_relational_shift.png
    publication_figure_06_initial_vs_refined_family_drop.png

Summary:
    publication_outputs_summary.json

Run
---
Put this file in:

    data_psychoanalytic_core/scripts/

Run:

    cd data_psychoanalytic_core/scripts
    python 5a_publication_tables_and_figures.py

Notes
-----
- Figures use matplotlib defaults intentionally.
- No seaborn.
- No hard-coded journal colors.
- No interpretive smoothing.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib.pyplot as plt
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

JOURNAL_LABELS = {
    "ijpa": "IJPA",
    "japa": "JAPA",
    "psychoanalytic_dialogues": "Psychoanalytic Dialogues",
    "psychoanalytic_psychology": "Psychoanalytic Psychology",
    "psychoanalytic_psychotherapy": "Psychoanalytic Psychotherapy",
}

FAMILY_LABELS = {
    "drive_conflict_defense": "Drive / conflict / defense",
    "dream_fantasy_unconscious": "Dream / fantasy / unconscious",
    "ego_self_narcissism": "Ego / self / narcissism",
    "object_relations": "Object relations",
    "kleinian_bionian": "Kleinian / Bionian",
    "winnicottian_environment_holding": "Winnicottian / holding",
    "attachment_development_infant": "Attachment / development / infant",
    "transference_countertransference": "Transference / countertransference",
    "technique_interpretation_process": "Technique / interpretation / process",
    "relational_intersubjective_field": "Relational / intersubjective / field",
    "trauma_dissociation_affect_regulation": "Trauma / dissociation / affect regulation",
    "psychosis_borderline_primitive_states": "Psychosis / borderline / primitive states",
    "body_sexuality_gender": "Body / sexuality / gender",
    "language_narrative_symbolization": "Language / narrative / symbolization",
    "culture_race_social_ethics": "Culture / race / social / ethics",
    "empirical_research_measurement": "Empirical research / measurement",
    "history_theory_schools": "History / theory / schools",
}


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
        "semantic_application": title_root / "semantic_application",
        "semantic_refined": title_root / "semantic_refined",
        "semantic_comparison": title_root / "semantic_comparison",
        "semantic_change": title_root / "semantic_change",
        "semantic_change_journal_global": title_root / "semantic_change_journal_global",
        "semantic_change_balanced": title_root / "semantic_change_balanced",
        "publication_outputs": title_root / "publication_outputs",
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


def num(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series([0.0] * len(df), index=df.index)
    return pd.to_numeric(df[col], errors="coerce").fillna(0.0)


def add_period_order(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "period" in out.columns:
        out["_period_order"] = out["period"].map(PERIOD_ORDER).fillna(999).astype(int)
        out = out.sort_values(["_period_order", "period"])
        out = out.drop(columns=["_period_order"])
    return out


def add_journal_order(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "journal_key" in out.columns:
        out["_journal_order"] = out["journal_key"].map(JOURNAL_ORDER).fillna(999).astype(int)
        sort_cols = ["_journal_order", "journal_key"]
        if "period" in out.columns:
            out["_period_order"] = out["period"].map(PERIOD_ORDER).fillna(999).astype(int)
            sort_cols = ["_journal_order", "_period_order", "journal_key", "period"]
        out = out.sort_values(sort_cols)
        out = out.drop(columns=[c for c in ["_journal_order", "_period_order"] if c in out.columns])
    return out


def journal_label(journal_key: str) -> str:
    return JOURNAL_LABELS.get(str(journal_key), str(journal_key))


def family_label(family: str) -> str:
    return FAMILY_LABELS.get(str(family), str(family).replace("_", " "))


def save_figure(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def table_coverage(initial_summary: Dict, refined_summary: Dict, comparison_summary: Dict) -> pd.DataFrame:
    rows = []

    init_articles = initial_summary.get("articles", {})
    ref_articles = refined_summary.get("articles", {})

    rows.append({
        "measure": "Initial semantic application: articles with any family hit",
        "value": init_articles.get("n_articles_with_any_semantic_family_hit", ""),
        "denominator": init_articles.get("n_articles", ""),
        "percent": init_articles.get("pct_articles_with_any_semantic_family_hit", ""),
        "note": "Broad lexical semantic map before marker-strength correction",
    })

    rows.append({
        "measure": "Refined semantic application: articles with refined family hit",
        "value": ref_articles.get("n_articles_with_refined_semantic_family_hit", ""),
        "denominator": ref_articles.get("n_articles", ""),
        "percent": ref_articles.get("pct_articles_with_refined_semantic_family_hit", ""),
        "note": "Weak-only and name-only markers do not count as full family hits",
    })

    rows.append({
        "measure": "Refined semantic application: articles with any marker hit",
        "value": ref_articles.get("n_articles_with_any_marker_hit", ""),
        "denominator": ref_articles.get("n_articles", ""),
        "percent": ref_articles.get("pct_articles_with_any_marker_hit", ""),
        "note": "Any strong, medium, weak, or name marker",
    })

    marker_counts = refined_summary.get("marker_map", {}).get("marker_strength_counts", {})
    for marker, count in marker_counts.items():
        rows.append({
            "measure": f"Semantic map marker-strength count: {marker}",
            "value": count,
            "denominator": "",
            "percent": "",
            "note": "Rows in marker-strength semantic map",
        })

    return pd.DataFrame(rows)


def table_family_counts_refined(family_counts: pd.DataFrame) -> pd.DataFrame:
    if family_counts.empty:
        return pd.DataFrame()
    out = family_counts.copy()
    out["semantic_family_label"] = out["semantic_family"].map(family_label)
    keep = [
        "semantic_family",
        "semantic_family_label",
        "n_articles_refined",
        "pct_articles_refined",
        "n_articles_any_marker",
        "pct_articles_any_marker",
        "n_weak_only_rows",
        "n_name_only_rows",
    ]
    return out[[c for c in keep if c in out.columns]]


def table_indices_by_period(indices: pd.DataFrame) -> pd.DataFrame:
    if indices.empty:
        return pd.DataFrame()
    keep = [
        "period",
        "drive_conflict_defense",
        "relational_intersubjective_field",
        "culture_race_social_ethics",
        "trauma_dissociation_affect_regulation",
        "classical_drive_conflict_index",
        "classical_metapsychology_index",
        "relational_shift_index",
        "contemporary_contextualization_index",
        "narrative_reframing_index",
        "relational_to_drive_conflict_ratio",
        "contemporary_to_classical_ratio",
    ]
    return add_period_order(indices[[c for c in keep if c in indices.columns]].copy())


def table_journal_trajectories(trajectory: pd.DataFrame) -> pd.DataFrame:
    if trajectory.empty:
        return pd.DataFrame()
    out = trajectory.copy()
    out["journal_label"] = out["journal_key"].map(journal_label)
    keep = [
        "journal_key",
        "journal_label",
        "observed_periods",
        "n_observed_periods",
        "relational_shift_index_change",
        "classical_drive_conflict_index_change",
        "classical_metapsychology_index_change",
        "contemporary_contextualization_index_change",
        "narrative_reframing_index_change",
        "research_psychology_index_change",
        "mean_abs_focus_deviation_from_global_period",
        "trajectory_flags",
        "trajectory_interpretive_label",
    ]
    return add_journal_order(out[[c for c in keep if c in out.columns]])


def table_direction_consistency(direction: pd.DataFrame) -> pd.DataFrame:
    if direction.empty:
        return pd.DataFrame()
    focus = [
        "relational_shift_index",
        "classical_drive_conflict_index",
        "classical_metapsychology_index",
        "contemporary_contextualization_index",
        "narrative_reframing_index",
        "social_ethical_turn_index",
        "trauma_affect_regulation_index",
        "research_psychology_index",
    ]
    out = direction[direction["index"].isin(focus)].copy()
    keep = [
        "panel",
        "index",
        "n_journals",
        "n_increase",
        "n_decrease",
        "n_no_change",
        "pct_increase",
        "pct_decrease",
        "dominant_direction",
        "direction_consistency_flag",
    ]
    return out[[c for c in keep if c in out.columns]]


def table_initial_vs_refined_impact(impact: pd.DataFrame) -> pd.DataFrame:
    if impact.empty:
        return pd.DataFrame()
    out = impact.copy()
    out["semantic_family_label"] = out["semantic_family"].map(family_label)
    keep = [
        "impact_rank",
        "semantic_family",
        "semantic_family_label",
        "pct_articles_initial",
        "pct_articles_refined",
        "absolute_pct_drop",
        "relative_retention_pct",
        "n_articles_removed_by_refinement",
        "marker_strength_impact_flag",
    ]
    return out[[c for c in keep if c in out.columns]]


def table_journal_distinctiveness(distinctiveness: pd.DataFrame) -> pd.DataFrame:
    if distinctiveness.empty:
        return pd.DataFrame()
    out = distinctiveness.copy()
    out["journal_label"] = out["journal_key"].map(journal_label)
    keep = [
        "journal_key",
        "journal_label",
        "n_period_cells",
        "mean_distinctiveness_score",
        "max_distinctiveness_score",
    ]
    extra = [c for c in out.columns if c.startswith("mean_abs_delta_from_global_relational_shift_index")]
    keep += extra
    return add_journal_order(out[[c for c in keep if c in out.columns]])


def table_narrative(narrative: pd.DataFrame) -> pd.DataFrame:
    if narrative.empty:
        return pd.DataFrame()
    return add_period_order(narrative.copy())


def figure_relational_vs_drive_by_period(indices: pd.DataFrame, path: Path) -> None:
    df = add_period_order(indices.copy())
    fig, ax = plt.subplots(figsize=(8, 5))
    x = range(len(df))
    ax.plot(x, num(df, "drive_conflict_defense"), marker="o", label="Drive / conflict / defense")
    ax.plot(x, num(df, "relational_intersubjective_field"), marker="o", label="Relational / intersubjective / field")
    ax.set_xticks(list(x))
    ax.set_xticklabels(df["period"].astype(str), rotation=30, ha="right")
    ax.set_ylabel("Articles with refined family hit (%)")
    ax.set_title("Relational/intersubjective vs drive/conflict/defense vocabulary by period")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    save_figure(fig, path)


def figure_narrative_reframing_by_period(indices: pd.DataFrame, path: Path) -> None:
    df = add_period_order(indices.copy())
    fig, ax = plt.subplots(figsize=(8, 5))
    x = range(len(df))
    ax.plot(x, num(df, "narrative_reframing_index"), marker="o")
    ax.axhline(0, linewidth=1)
    ax.set_xticks(list(x))
    ax.set_xticklabels(df["period"].astype(str), rotation=30, ha="right")
    ax.set_ylabel("Index value")
    ax.set_title("Narrative reframing index by period")
    ax.grid(True, axis="y", alpha=0.3)
    save_figure(fig, path)


def figure_contextualization_by_period(indices: pd.DataFrame, path: Path) -> None:
    df = add_period_order(indices.copy())
    fig, ax = plt.subplots(figsize=(8, 5))
    x = range(len(df))
    ax.plot(x, num(df, "contemporary_contextualization_index"), marker="o", label="Contemporary contextualization")
    ax.plot(x, num(df, "classical_metapsychology_index"), marker="o", label="Classical metapsychology")
    ax.set_xticks(list(x))
    ax.set_xticklabels(df["period"].astype(str), rotation=30, ha="right")
    ax.set_ylabel("Composite index value")
    ax.set_title("Contemporary contextualization vs classical metapsychology by period")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    save_figure(fig, path)


def figure_journal_relational_trajectories(jp: pd.DataFrame, path: Path) -> None:
    df = jp.copy()
    df["_period_order"] = df["period"].map(PERIOD_ORDER).fillna(999).astype(int)
    df["_journal_order"] = df["journal_key"].map(JOURNAL_ORDER).fillna(999).astype(int)
    df = df.sort_values(["_journal_order", "_period_order"])

    fig, ax = plt.subplots(figsize=(9, 5))
    for journal, g in df.groupby("journal_key", sort=False):
        g = g.sort_values("_period_order")
        x = [PERIOD_ORDER.get(p, 999) for p in g["period"]]
        ax.plot(x, num(g, "relational_shift_index"), marker="o", label=journal_label(journal))

    xticks = list(PERIOD_ORDER.values())
    ax.set_xticks(xticks)
    ax.set_xticklabels(list(PERIOD_ORDER.keys()), rotation=30, ha="right")
    ax.axhline(0, linewidth=1)
    ax.set_ylabel("Relational shift index")
    ax.set_title("Journal trajectories of relational shift index")
    ax.legend(fontsize="small")
    ax.grid(True, axis="y", alpha=0.3)
    save_figure(fig, path)


def figure_equal_weight_vs_global(global_equal: pd.DataFrame, path: Path) -> None:
    df = add_period_order(global_equal.copy())
    fig, ax = plt.subplots(figsize=(8, 5))
    x = range(len(df))

    if "global_article_weighted_relational_shift_index" in df.columns:
        ax.plot(
            x,
            num(df, "global_article_weighted_relational_shift_index"),
            marker="o",
            label="Article-weighted global",
        )
    if "equal_weight_relational_shift_index" in df.columns:
        ax.plot(
            x,
            num(df, "equal_weight_relational_shift_index"),
            marker="o",
            label="Equal journal weight",
        )

    ax.axhline(0, linewidth=1)
    ax.set_xticks(list(x))
    ax.set_xticklabels(df["period"].astype(str), rotation=30, ha="right")
    ax.set_ylabel("Relational shift index")
    ax.set_title("Relational shift index: article-weighted vs equal-journal-weight")
    ax.legend()
    ax.grid(True, axis="y", alpha=0.3)
    save_figure(fig, path)


def figure_initial_vs_refined_drop(impact: pd.DataFrame, path: Path, top_n: int = 10) -> None:
    if impact.empty:
        return
    df = impact.copy()
    df = df.sort_values("absolute_pct_drop", ascending=False).head(top_n)
    df = df.iloc[::-1]
    labels = [family_label(x) for x in df["semantic_family"]]
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(labels, num(df, "absolute_pct_drop"))
    ax.set_xlabel("Percentage-point drop after marker-strength correction")
    ax.set_title("Families most affected by marker-strength correction")
    ax.grid(True, axis="x", alpha=0.3)
    save_figure(fig, path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create publication-oriented tables and figures.")
    parser.add_argument("--out-dir", default="../data/title_abstract/publication_outputs")
    args = parser.parse_args()

    paths = get_paths()

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = (paths["scripts_dir"] / out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    # Input paths.
    initial_summary_path = paths["semantic_application"] / "psychoanalytic_core_semantic_application_summary.json"
    refined_summary_path = paths["semantic_refined"] / "psychoanalytic_core_semantic_marker_strength_summary.json"
    comparison_summary_path = paths["semantic_comparison"] / "psychoanalytic_core_semantic_comparison_summary.json"

    family_counts_path = paths["semantic_refined"] / "psychoanalytic_core_semantic_family_counts_refined.csv"
    indices_period_path = paths["semantic_change"] / "psychoanalytic_core_semantic_change_indices_by_period.csv"
    indices_journal_path = paths["semantic_change"] / "psychoanalytic_core_semantic_change_indices_by_journal.csv"
    indices_journal_period_path = paths["semantic_change"] / "psychoanalytic_core_semantic_change_indices_by_journal_period.csv"
    narrative_path = paths["semantic_change"] / "psychoanalytic_core_semantic_change_narrative_table.csv"
    distinctiveness_path = paths["semantic_change"] / "psychoanalytic_core_semantic_change_journal_distinctiveness.csv"

    impact_path = paths["semantic_comparison"] / "psychoanalytic_core_family_marker_strength_impact_ranking.csv"
    trajectory_path = paths["semantic_change_journal_global"] / "psychoanalytic_core_journal_trajectory_summary.csv"

    balanced_direction_path = paths["semantic_change_balanced"] / "psychoanalytic_core_balanced_direction_consistency.csv"
    balanced_global_equal_path = paths["semantic_change_balanced"] / "psychoanalytic_core_balanced_global_vs_equal_weight.csv"

    required = [
        family_counts_path,
        indices_period_path,
        indices_journal_period_path,
        impact_path,
        balanced_direction_path,
        balanced_global_equal_path,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise SystemExit(f"ERROR: missing required inputs: {missing}")

    # Read inputs.
    initial_summary = read_json_safe(initial_summary_path)
    refined_summary = read_json_safe(refined_summary_path)
    comparison_summary = read_json_safe(comparison_summary_path)

    family_counts = read_csv_safe(family_counts_path)
    indices_period = read_csv_safe(indices_period_path)
    indices_journal = read_csv_safe(indices_journal_path)
    indices_journal_period = read_csv_safe(indices_journal_period_path)
    narrative = read_csv_safe(narrative_path)
    distinctiveness = read_csv_safe(distinctiveness_path)
    impact = read_csv_safe(impact_path)
    trajectory = read_csv_safe(trajectory_path)
    balanced_direction = read_csv_safe(balanced_direction_path)
    balanced_global_equal = read_csv_safe(balanced_global_equal_path)

    # Tables.
    tables = {
        "table_01_corpus_semantic_coverage": table_coverage(initial_summary, refined_summary, comparison_summary),
        "table_02_semantic_family_counts_refined": table_family_counts_refined(family_counts),
        "table_03_semantic_indices_by_period": table_indices_by_period(indices_period),
        "table_04_journal_trajectories": table_journal_trajectories(trajectory),
        "table_05_balanced_direction_consistency": table_direction_consistency(balanced_direction),
        "table_06_initial_vs_refined_impact": table_initial_vs_refined_impact(impact),
        "table_07_journal_distinctiveness": table_journal_distinctiveness(distinctiveness),
        "table_08_narrative_table": table_narrative(narrative),
    }

    table_paths = {}
    for key, df in tables.items():
        path = out_dir / f"publication_{key}.csv"
        write_csv(df, path)
        table_paths[key] = str(path)

    # Figures.
    figure_paths = {
        "figure_01_relational_vs_drive_by_period": out_dir / "publication_figure_01_relational_vs_drive_by_period.png",
        "figure_02_narrative_reframing_by_period": out_dir / "publication_figure_02_narrative_reframing_by_period.png",
        "figure_03_contextualization_by_period": out_dir / "publication_figure_03_contextualization_by_period.png",
        "figure_04_journal_relational_shift_trajectories": out_dir / "publication_figure_04_journal_relational_shift_trajectories.png",
        "figure_05_equal_weight_vs_global_relational_shift": out_dir / "publication_figure_05_equal_weight_vs_global_relational_shift.png",
        "figure_06_initial_vs_refined_family_drop": out_dir / "publication_figure_06_initial_vs_refined_family_drop.png",
    }

    figure_relational_vs_drive_by_period(indices_period, figure_paths["figure_01_relational_vs_drive_by_period"])
    figure_narrative_reframing_by_period(indices_period, figure_paths["figure_02_narrative_reframing_by_period"])
    figure_contextualization_by_period(indices_period, figure_paths["figure_03_contextualization_by_period"])
    figure_journal_relational_trajectories(indices_journal_period, figure_paths["figure_04_journal_relational_shift_trajectories"])
    figure_equal_weight_vs_global(balanced_global_equal, figure_paths["figure_05_equal_weight_vs_global_relational_shift"])
    figure_initial_vs_refined_drop(impact, figure_paths["figure_06_initial_vs_refined_family_drop"])

    # Compact summary.
    trend_summary = {}
    if not indices_period.empty:
        p = add_period_order(indices_period.copy())
        first = p.iloc[0].to_dict()
        last = p.iloc[-1].to_dict()
        for col in [
            "relational_shift_index",
            "drive_conflict_defense",
            "narrative_reframing_index",
            "contemporary_contextualization_index",
        ]:
            if col in p.columns:
                trend_summary[f"{col}_first_period"] = first.get(col, "")
                trend_summary[f"{col}_last_period"] = last.get(col, "")
                try:
                    trend_summary[f"{col}_change"] = round(float(last.get(col, 0)) - float(first.get(col, 0)), 4)
                except Exception:
                    trend_summary[f"{col}_change"] = ""

    summary = {
        "script_version": SCRIPT_VERSION,
        "created_at_utc": utc_now_iso(),
        "purpose": "Prepare publication-oriented tables and first figures from Stage 3–4 outputs.",
        "inputs": {
            "semantic_application": str(paths["semantic_application"]),
            "semantic_refined": str(paths["semantic_refined"]),
            "semantic_comparison": str(paths["semantic_comparison"]),
            "semantic_change": str(paths["semantic_change"]),
            "semantic_change_journal_global": str(paths["semantic_change_journal_global"]),
            "semantic_change_balanced": str(paths["semantic_change_balanced"]),
        },
        "outputs": {
            "tables": table_paths,
            "figures": {k: str(v) for k, v in figure_paths.items()},
        },
        "trend_summary_from_period_indices": trend_summary,
        "methodological_note": (
            "These are publication-oriented derivative tables and figures. "
            "They do not alter analytical outputs. Figure styling is intentionally simple and should be revised before final submission."
        ),
    }

    summary_path = out_dir / "publication_outputs_summary.json"
    write_json(summary, summary_path)
    summary["outputs"]["summary_json"] = str(summary_path)

    print(json.dumps({
        "status": "ok",
        "script_version": SCRIPT_VERSION,
        "n_tables": len(table_paths),
        "n_figures": len(figure_paths),
        "out_dir": str(out_dir),
        "summary_json": str(summary_path),
        "figure_01": str(figure_paths["figure_01_relational_vs_drive_by_period"]),
        "figure_05": str(figure_paths["figure_05_equal_weight_vs_global_relational_shift"]),
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
