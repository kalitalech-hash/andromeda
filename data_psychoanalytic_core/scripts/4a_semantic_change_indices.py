#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4a_semantic_change_indices.py

Andromeda Nowicka v0.5-pre
Semantic change indices for psychoanalytic_core.

Purpose
-------
Stage 3 produced a refined semantic-family layer. Stage 4 begins analytical
index construction.

This script does NOT reduce the project to a single "relational shift" story.
Instead, it computes a wider set of interpretable, auditable indices for the
evolution of psychoanalytic discourse:

- relational_shift_index
- drive_conflict_decline / classical dominance signals
- classical_metapsychology_index
- contemporary_contextualization_index
- clinical_severity_continuity_index
- narrative_reframing_index
- journal distinctiveness from global period profile
- global corpus vs journal-specific trajectories

The conceptual frame is intentionally broad:
- Beebe & Lachmann: relational / dyadic systems / co-construction
- Orange: ethical, hermeneutic, contextual widening
- Schafer: changing psychoanalytic narratives about clinical realities
- Andromeda corpus logic: relatively persistent clinical materials may be
  narrated through historically changing conceptual languages.

Inputs
------
Refined semantic family tables:
    ../data/title_abstract/semantic_refined/psychoanalytic_core_semantic_family_counts_refined.csv
    ../data/title_abstract/semantic_refined/psychoanalytic_core_semantic_family_by_journal_refined.csv
    ../data/title_abstract/semantic_refined/psychoanalytic_core_semantic_family_by_period_refined.csv
    ../data/title_abstract/semantic_refined/psychoanalytic_core_semantic_family_by_journal_period_refined.csv

Optional comparison summary:
    ../data/title_abstract/semantic_comparison/psychoanalytic_core_relational_shift_initial_vs_refined.csv

Outputs
-------
../data/title_abstract/semantic_change/
    psychoanalytic_core_semantic_change_family_inputs.csv
    psychoanalytic_core_semantic_change_indices_global.csv
    psychoanalytic_core_semantic_change_indices_by_period.csv
    psychoanalytic_core_semantic_change_indices_by_journal.csv
    psychoanalytic_core_semantic_change_indices_by_journal_period.csv
    psychoanalytic_core_semantic_change_journal_vs_global_period.csv
    psychoanalytic_core_semantic_change_journal_distinctiveness.csv
    psychoanalytic_core_semantic_change_narrative_table.csv
    psychoanalytic_core_semantic_change_summary.json

Run
---
Put this file in:

    data_psychoanalytic_core/scripts/

Run:

    cd data_psychoanalytic_core/scripts
    python 4a_semantic_change_indices.py
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd


SCRIPT_VERSION = "v0.1.0"

SEMANTIC_FAMILIES = [
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

# Composite index definitions.
# Values are simple sums/differences of refined family coverage percentages.
INDEX_DEFINITIONS = {
    "classical_drive_conflict_index": {
        "positive": ["drive_conflict_defense"],
        "negative": [],
        "note": "Narrow index of drive/conflict/defense vocabulary."
    },
    "classical_metapsychology_index": {
        "positive": [
            "drive_conflict_defense",
            "dream_fantasy_unconscious",
            "transference_countertransference",
            "technique_interpretation_process",
        ],
        "negative": [],
        "note": "Broad classical/technical/metapsychological vocabulary block."
    },
    "object_relations_tradition_index": {
        "positive": [
            "object_relations",
            "kleinian_bionian",
            "winnicottian_environment_holding",
        ],
        "negative": [],
        "note": "Object-relational/Kleinian/Bionian/Winnicottian tradition block."
    },
    "relational_shift_index": {
        "positive": ["relational_intersubjective_field"],
        "negative": ["drive_conflict_defense"],
        "note": "Relational/intersubjective coverage minus drive/conflict/defense coverage."
    },
    "relational_process_index": {
        "positive": [
            "relational_intersubjective_field",
            "transference_countertransference",
            "technique_interpretation_process",
        ],
        "negative": [],
        "note": "Clinical relation/process language, including transference and technique."
    },
    "contemporary_contextualization_index": {
        "positive": [
            "relational_intersubjective_field",
            "culture_race_social_ethics",
            "trauma_dissociation_affect_regulation",
        ],
        "negative": [],
        "note": "Relational plus social/ethical/contextual plus trauma/affect/regulation expansion."
    },
    "social_ethical_turn_index": {
        "positive": ["culture_race_social_ethics"],
        "negative": [],
        "note": "Culture/race/social/ethics vocabulary."
    },
    "trauma_affect_regulation_index": {
        "positive": ["trauma_dissociation_affect_regulation"],
        "negative": [],
        "note": "Trauma/dissociation/affect/regulation vocabulary."
    },
    "clinical_severity_continuity_index": {
        "positive": [
            "psychosis_borderline_primitive_states",
            "trauma_dissociation_affect_regulation",
            "attachment_development_infant",
        ],
        "negative": [],
        "note": "Clinical-severity and early-development vocabulary; proxy for persistent clinical materials."
    },
    "developmental_attachment_index": {
        "positive": ["attachment_development_infant"],
        "negative": [],
        "note": "Attachment/development/infant vocabulary."
    },
    "body_sexuality_gender_index": {
        "positive": ["body_sexuality_gender"],
        "negative": [],
        "note": "Body/sexuality/gender vocabulary."
    },
    "language_narrative_index": {
        "positive": ["language_narrative_symbolization"],
        "negative": [],
        "note": "Language/narrative/symbolization vocabulary; Schafer-adjacent narrative dimension."
    },
    "narrative_reframing_index": {
        "positive": [
            "relational_intersubjective_field",
            "language_narrative_symbolization",
            "culture_race_social_ethics",
        ],
        "negative": ["drive_conflict_defense"],
        "note": "Relational + narrative + contextual language minus drive/conflict/defense."
    },
    "research_psychology_index": {
        "positive": ["empirical_research_measurement"],
        "negative": [],
        "note": "Empirical/research/measurement vocabulary."
    },
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
        "semantic_refined_root": title_root / "semantic_refined",
        "semantic_comparison_root": title_root / "semantic_comparison",
        "out_root": title_root / "semantic_change",
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


def standardize_global(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if out.empty:
        return pd.DataFrame(columns=["scope", "semantic_family", "pct"])
    out["scope"] = "global"
    out["pct"] = num(out, "pct_articles_refined")
    out["n_articles"] = num(out, "n_articles_refined").astype(int)
    return out[["scope", "semantic_family", "pct", "n_articles"]]


def standardize_group(df: pd.DataFrame, group_cols: List[str]) -> pd.DataFrame:
    out = df.copy()
    if out.empty:
        return pd.DataFrame(columns=group_cols + ["semantic_family", "pct", "n_articles", "n_articles_group"])
    out["pct"] = num(out, "pct_articles_group_refined")
    out["n_articles"] = num(out, "n_articles_refined").astype(int)
    out["n_articles_group"] = num(out, "n_articles_group").astype(int)
    return out[group_cols + ["semantic_family", "pct", "n_articles", "n_articles_group"]]


def pivot_families(df: pd.DataFrame, index_cols: List[str]) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=index_cols + SEMANTIC_FAMILIES)
    p = (
        df.pivot_table(
            index=index_cols,
            columns="semantic_family",
            values="pct",
            aggfunc="first",
            fill_value=0.0,
        )
        .reset_index()
    )
    p.columns.name = None
    for fam in SEMANTIC_FAMILIES:
        if fam not in p.columns:
            p[fam] = 0.0
    return p[index_cols + SEMANTIC_FAMILIES]


def add_indices(wide: pd.DataFrame) -> pd.DataFrame:
    out = wide.copy()
    for index_name, spec in INDEX_DEFINITIONS.items():
        value = pd.Series([0.0] * len(out), index=out.index)
        for fam in spec["positive"]:
            value = value + num(out, fam)
        for fam in spec["negative"]:
            value = value - num(out, fam)
        out[index_name] = value.round(4)

    # Additional ratios and differences.
    drive = num(out, "drive_conflict_defense")
    relational = num(out, "relational_intersubjective_field")
    culture = num(out, "culture_race_social_ethics")
    trauma = num(out, "trauma_dissociation_affect_regulation")
    classical = num(out, "classical_metapsychology_index")
    contemporary = num(out, "contemporary_contextualization_index")

    out["relational_to_drive_conflict_ratio"] = (
        relational / drive.replace(0, pd.NA)
    ).round(4).fillna("")
    out["contemporary_to_classical_ratio"] = (
        contemporary / classical.replace(0, pd.NA)
    ).round(4).fillna("")
    out["contextualization_minus_classical_metapsychology"] = (
        contemporary - classical
    ).round(4)
    out["culture_plus_trauma_index"] = (culture + trauma).round(4)
    return out


def add_period_journal_order(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "period" in out.columns:
        out["_period_order"] = out["period"].map(PERIOD_ORDER).fillna(999).astype(int)
    if "journal_key" in out.columns:
        out["_journal_order"] = out["journal_key"].map(JOURNAL_ORDER).fillna(999).astype(int)
    sort_cols = [c for c in ["_journal_order", "_period_order", "journal_key", "period"] if c in out.columns]
    if sort_cols:
        out = out.sort_values(sort_cols)
    return out.drop(columns=[c for c in ["_journal_order", "_period_order"] if c in out.columns])


def make_family_inputs(
    global_counts: pd.DataFrame,
    by_period: pd.DataFrame,
    by_journal: pd.DataFrame,
    by_journal_period: pd.DataFrame,
) -> pd.DataFrame:
    frames = []

    if not global_counts.empty:
        g = standardize_global(global_counts)
        g["level"] = "global"
        g["journal_key"] = ""
        g["period"] = ""
        frames.append(g[["level", "journal_key", "period", "semantic_family", "pct", "n_articles"]])

    if not by_period.empty:
        p = standardize_group(by_period, ["period"])
        p["level"] = "period"
        p["journal_key"] = ""
        frames.append(p[["level", "journal_key", "period", "semantic_family", "pct", "n_articles"]])

    if not by_journal.empty:
        j = standardize_group(by_journal, ["journal_key"])
        j["level"] = "journal"
        j["period"] = ""
        frames.append(j[["level", "journal_key", "period", "semantic_family", "pct", "n_articles"]])

    if not by_journal_period.empty:
        jp = standardize_group(by_journal_period, ["journal_key", "period"])
        jp["level"] = "journal_period"
        frames.append(jp[["level", "journal_key", "period", "semantic_family", "pct", "n_articles"]])

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def make_indices_by_period(by_period: pd.DataFrame) -> pd.DataFrame:
    std = standardize_group(by_period, ["period"])
    wide = pivot_families(std, ["period"])
    out = add_indices(wide)
    return add_period_journal_order(out)


def make_indices_by_journal(by_journal: pd.DataFrame) -> pd.DataFrame:
    std = standardize_group(by_journal, ["journal_key"])
    wide = pivot_families(std, ["journal_key"])
    out = add_indices(wide)
    return add_period_journal_order(out)


def make_indices_by_journal_period(by_journal_period: pd.DataFrame) -> pd.DataFrame:
    std = standardize_group(by_journal_period, ["journal_key", "period"])
    wide = pivot_families(std, ["journal_key", "period"])
    out = add_indices(wide)
    return add_period_journal_order(out)


def make_indices_global(global_counts: pd.DataFrame) -> pd.DataFrame:
    std = standardize_global(global_counts)
    wide = pivot_families(std, ["scope"])
    return add_indices(wide)


def make_journal_vs_global_period(jp_indices: pd.DataFrame, period_indices: pd.DataFrame) -> pd.DataFrame:
    if jp_indices.empty or period_indices.empty:
        return pd.DataFrame()

    index_cols = list(INDEX_DEFINITIONS.keys()) + [
        "relational_to_drive_conflict_ratio",
        "contemporary_to_classical_ratio",
        "contextualization_minus_classical_metapsychology",
        "culture_plus_trauma_index",
    ]

    global_period = period_indices[["period"] + [c for c in index_cols if c in period_indices.columns]].copy()
    renamed = {c: f"global_{c}" for c in global_period.columns if c != "period"}
    global_period = global_period.rename(columns=renamed)

    out = jp_indices.merge(global_period, on="period", how="left")

    for c in index_cols:
        if c in jp_indices.columns and f"global_{c}" in out.columns:
            local = pd.to_numeric(out[c], errors="coerce")
            glob = pd.to_numeric(out[f"global_{c}"], errors="coerce")
            out[f"delta_from_global_{c}"] = (local - glob).round(4)

    # A compact distinctiveness score: mean absolute deviation from global period
    # across selected core indices.
    core_delta_cols = [
        "delta_from_global_relational_shift_index",
        "delta_from_global_classical_drive_conflict_index",
        "delta_from_global_contemporary_contextualization_index",
        "delta_from_global_narrative_reframing_index",
        "delta_from_global_research_psychology_index",
    ]
    existing = [c for c in core_delta_cols if c in out.columns]
    if existing:
        out["journal_period_distinctiveness_score"] = (
            out[existing].apply(pd.to_numeric, errors="coerce").abs().mean(axis=1)
        ).round(4)
    else:
        out["journal_period_distinctiveness_score"] = 0.0

    return add_period_journal_order(out)


def make_journal_distinctiveness(journal_vs_global: pd.DataFrame) -> pd.DataFrame:
    if journal_vs_global.empty:
        return pd.DataFrame()

    delta_cols = [c for c in journal_vs_global.columns if c.startswith("delta_from_global_")]
    rows = []
    for journal, g in journal_vs_global.groupby("journal_key", dropna=False):
        row = {"journal_key": journal}
        row["n_period_cells"] = int(g["period"].nunique())
        row["mean_distinctiveness_score"] = round(float(g["journal_period_distinctiveness_score"].mean()), 4)
        row["max_distinctiveness_score"] = round(float(g["journal_period_distinctiveness_score"].max()), 4)
        for c in delta_cols:
            vals = pd.to_numeric(g[c], errors="coerce").fillna(0)
            row[f"mean_abs_{c}"] = round(float(vals.abs().mean()), 4)
            row[f"mean_signed_{c}"] = round(float(vals.mean()), 4)
        rows.append(row)

    out = pd.DataFrame(rows)
    out["_journal_order"] = out["journal_key"].map(JOURNAL_ORDER).fillna(999).astype(int)
    return out.sort_values(["_journal_order", "journal_key"]).drop(columns=["_journal_order"])


def make_narrative_table(period_indices: pd.DataFrame) -> pd.DataFrame:
    if period_indices.empty:
        return pd.DataFrame()

    keep = [
        "period",
        "drive_conflict_defense",
        "relational_intersubjective_field",
        "culture_race_social_ethics",
        "trauma_dissociation_affect_regulation",
        "dream_fantasy_unconscious",
        "classical_drive_conflict_index",
        "classical_metapsychology_index",
        "relational_shift_index",
        "contemporary_contextualization_index",
        "narrative_reframing_index",
        "relational_to_drive_conflict_ratio",
        "contemporary_to_classical_ratio",
    ]
    out = period_indices[[c for c in keep if c in period_indices.columns]].copy()

    labels = []
    for _, r in out.iterrows():
        period = str(r.get("period", ""))
        rel = float(r.get("relational_intersubjective_field", 0) or 0)
        drive = float(r.get("drive_conflict_defense", 0) or 0)
        context = float(r.get("contemporary_contextualization_index", 0) or 0)
        culture = float(r.get("culture_race_social_ethics", 0) or 0)

        if period in {"1920-1945", "1946-1969", "1970-1989"} and drive > rel:
            labels.append("classical_drive_conflict_dominance")
        elif rel > drive and culture >= 10:
            labels.append("relational_contextual_narrative")
        elif rel > drive:
            labels.append("relational_process_narrative")
        elif context >= 60:
            labels.append("mixed_contemporary_expansion")
        else:
            labels.append("mixed_transitional_profile")

    out["interpretive_label"] = labels
    return add_period_journal_order(out)


def trend_summary(period_indices: pd.DataFrame) -> Dict[str, object]:
    if period_indices.empty:
        return {}

    p = add_period_journal_order(period_indices)
    first = p.iloc[0].to_dict()
    last = p.iloc[-1].to_dict()

    def change(col: str) -> float:
        return round(float(last.get(col, 0) or 0) - float(first.get(col, 0) or 0), 4)

    return {
        "first_period": first.get("period", ""),
        "last_period": last.get("period", ""),
        "relational_shift_index_change": change("relational_shift_index"),
        "drive_conflict_defense_change": change("drive_conflict_defense"),
        "relational_intersubjective_field_change": change("relational_intersubjective_field"),
        "culture_race_social_ethics_change": change("culture_race_social_ethics"),
        "trauma_dissociation_affect_regulation_change": change("trauma_dissociation_affect_regulation"),
        "narrative_reframing_index_change": change("narrative_reframing_index"),
        "contemporary_contextualization_index_change": change("contemporary_contextualization_index"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compute semantic change indices.")
    parser.add_argument("--semantic-refined-root", default="../data/title_abstract/semantic_refined")
    parser.add_argument("--semantic-comparison-root", default="../data/title_abstract/semantic_comparison")
    parser.add_argument("--out-dir", default="../data/title_abstract/semantic_change")
    args = parser.parse_args()

    paths = get_paths()

    def resolve(p: str) -> Path:
        path = Path(p)
        if not path.is_absolute():
            path = (paths["scripts_dir"] / path).resolve()
        return path

    refined_root = resolve(args.semantic_refined_root)
    comparison_root = resolve(args.semantic_comparison_root)
    out_dir = resolve(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    global_counts = read_csv_safe(refined_root / "psychoanalytic_core_semantic_family_counts_refined.csv")
    by_journal = read_csv_safe(refined_root / "psychoanalytic_core_semantic_family_by_journal_refined.csv")
    by_period = read_csv_safe(refined_root / "psychoanalytic_core_semantic_family_by_period_refined.csv")
    by_journal_period = read_csv_safe(refined_root / "psychoanalytic_core_semantic_family_by_journal_period_refined.csv")

    if global_counts.empty:
        raise SystemExit(f"ERROR: missing global refined family counts in {refined_root}")
    if by_period.empty:
        raise SystemExit(f"ERROR: missing refined family-by-period table in {refined_root}")
    if by_journal.empty:
        raise SystemExit(f"ERROR: missing refined family-by-journal table in {refined_root}")
    if by_journal_period.empty:
        raise SystemExit(f"ERROR: missing refined family-by-journal-period table in {refined_root}")

    family_inputs = make_family_inputs(global_counts, by_period, by_journal, by_journal_period)
    indices_global = make_indices_global(global_counts)
    indices_by_period = make_indices_by_period(by_period)
    indices_by_journal = make_indices_by_journal(by_journal)
    indices_by_journal_period = make_indices_by_journal_period(by_journal_period)
    journal_vs_global = make_journal_vs_global_period(indices_by_journal_period, indices_by_period)
    journal_distinctiveness = make_journal_distinctiveness(journal_vs_global)
    narrative_table = make_narrative_table(indices_by_period)

    outputs = {
        "family_inputs": out_dir / "psychoanalytic_core_semantic_change_family_inputs.csv",
        "indices_global": out_dir / "psychoanalytic_core_semantic_change_indices_global.csv",
        "indices_by_period": out_dir / "psychoanalytic_core_semantic_change_indices_by_period.csv",
        "indices_by_journal": out_dir / "psychoanalytic_core_semantic_change_indices_by_journal.csv",
        "indices_by_journal_period": out_dir / "psychoanalytic_core_semantic_change_indices_by_journal_period.csv",
        "journal_vs_global_period": out_dir / "psychoanalytic_core_semantic_change_journal_vs_global_period.csv",
        "journal_distinctiveness": out_dir / "psychoanalytic_core_semantic_change_journal_distinctiveness.csv",
        "narrative_table": out_dir / "psychoanalytic_core_semantic_change_narrative_table.csv",
    }

    write_csv(family_inputs, outputs["family_inputs"])
    write_csv(indices_global, outputs["indices_global"])
    write_csv(indices_by_period, outputs["indices_by_period"])
    write_csv(indices_by_journal, outputs["indices_by_journal"])
    write_csv(indices_by_journal_period, outputs["indices_by_journal_period"])
    write_csv(journal_vs_global, outputs["journal_vs_global_period"])
    write_csv(journal_distinctiveness, outputs["journal_distinctiveness"])
    write_csv(narrative_table, outputs["narrative_table"])

    trend = trend_summary(indices_by_period)

    most_distinctive_journals = []
    if not journal_distinctiveness.empty:
        most_distinctive_journals = (
            journal_distinctiveness
            .sort_values("mean_distinctiveness_score", ascending=False)
            .head(5)
            .to_dict(orient="records")
        )

    period_records = indices_by_period.to_dict(orient="records") if not indices_by_period.empty else []

    summary = {
        "script_version": SCRIPT_VERSION,
        "created_at_utc": utc_now_iso(),
        "purpose": "Compute semantic change indices for global corpus, journals, periods, and journal-period cells.",
        "interpretive_frame": {
            "not_only_relational_shift": True,
            "axes": [
                "drive_conflict_decline",
                "relational_intersubjective_shift",
                "contemporary_contextualization",
                "clinical_severity_continuity",
                "language_narrative_reframing",
                "journal_vs_global_dynamics",
            ],
            "theoretical_anchors": [
                "Beebe_Lachmann_relational_dyadic_systems",
                "Orange_ethics_hermeneutics_context",
                "Schafer_narrative_reframing",
            ],
        },
        "inputs": {
            "semantic_refined_root": str(refined_root),
            "semantic_comparison_root": str(comparison_root),
        },
        "index_definitions": INDEX_DEFINITIONS,
        "outputs": {k: str(v) for k, v in outputs.items()},
        "trend_summary_global_by_period": trend,
        "most_distinctive_journals": most_distinctive_journals,
        "period_index_records": period_records,
        "methodological_note": (
            "Indices are simple arithmetic composites of refined semantic-family coverage percentages. "
            "They are exploratory indicators, not final psychometric scales. "
            "They should be used to guide interpretation and later robustness checks."
        ),
    }

    summary_path = out_dir / "psychoanalytic_core_semantic_change_summary.json"
    write_json(summary, summary_path)
    summary["outputs"]["summary_json"] = str(summary_path)

    print(json.dumps({
        "status": "ok",
        "script_version": SCRIPT_VERSION,
        "n_period_rows": int(len(indices_by_period)),
        "n_journal_rows": int(len(indices_by_journal)),
        "n_journal_period_rows": int(len(indices_by_journal_period)),
        "relational_shift_index_change": trend.get("relational_shift_index_change"),
        "drive_conflict_defense_change": trend.get("drive_conflict_defense_change"),
        "narrative_reframing_index_change": trend.get("narrative_reframing_index_change"),
        "summary_json": str(summary_path),
        "narrative_table": str(outputs["narrative_table"]),
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
