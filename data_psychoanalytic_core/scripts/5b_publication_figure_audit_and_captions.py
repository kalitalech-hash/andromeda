#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
5b_publication_figure_audit_and_captions.py

Andromeda Nowicka v0.5-pre
Publication audit, captions, and claims matrix for psychoanalytic_core.

Purpose
-------
5a created first publication-oriented tables and figures. 5b creates the
interpretive bridge between outputs and manuscript writing:

- figure caption sheet
- table caption sheet
- results claims matrix
- figure selection recommendations
- core results narrative draft
- summary JSON

This script does NOT change analytical data and does NOT regenerate figures.
It reads publication outputs and Stage 4 summaries and writes review artifacts.

Outputs
-------
../data/title_abstract/publication_outputs_review/

    publication_figure_caption_sheet.csv
    publication_table_caption_sheet.csv
    publication_results_claims_matrix.csv
    publication_figure_selection_recommendations.csv
    publication_core_results_narrative.md
    publication_outputs_review_summary.json

Run
---
Put this file in:

    data_psychoanalytic_core/scripts/

Run:

    cd data_psychoanalytic_core/scripts
    python 5b_publication_figure_audit_and_captions.py
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Dict, List

import pandas as pd


SCRIPT_VERSION = "v0.1.0"


FIGURE_METADATA = [
    {
        "figure_id": "Figure 1",
        "file_name": "publication_figure_01_relational_vs_drive_by_period.png",
        "short_title": "Relational/intersubjective versus drive/conflict/defense vocabulary by period",
        "caption": (
            "Refined semantic-family coverage by period for drive/conflict/defense and "
            "relational/intersubjective/field vocabularies. The figure visualizes the central "
            "diachronic contrast: a decline in drive/conflict/defense language and a rise in "
            "relational/intersubjective language across the corpus."
        ),
        "primary_claim_ids": "C1 | C2",
        "recommended_role": "main_text_core_result",
        "priority": 1,
        "audit_note": "Use as the main visual anchor for the global semantic transformation.",
    },
    {
        "figure_id": "Figure 2",
        "file_name": "publication_figure_02_narrative_reframing_by_period.png",
        "short_title": "Narrative reframing index by period",
        "caption": (
            "Narrative reframing index by period. The index combines relational, narrative-symbolic, "
            "and social-ethical vocabularies relative to drive/conflict/defense language. It provides "
            "a Schafer-adjacent indicator of changing narrative grammar in psychoanalytic discourse."
        ),
        "primary_claim_ids": "C1 | C5",
        "recommended_role": "main_text_or_supplement",
        "priority": 2,
        "audit_note": "Strong interpretive figure; may need careful explanation of index construction.",
    },
    {
        "figure_id": "Figure 3",
        "file_name": "publication_figure_03_contextualization_by_period.png",
        "short_title": "Contemporary contextualization versus classical metapsychology by period",
        "caption": (
            "Composite indices for contemporary contextualization and classical metapsychology by period. "
            "The figure shows the growth of relational, social-ethical, and trauma-regulatory vocabularies "
            "alongside the decline of the broader classical/metapsychological vocabulary block."
        ),
        "primary_claim_ids": "C1 | C6",
        "recommended_role": "main_text_or_supplement",
        "priority": 3,
        "audit_note": "Good for broader Orange/ethical-contextual framing; may be secondary to Figure 1.",
    },
    {
        "figure_id": "Figure 4",
        "file_name": "publication_figure_04_journal_relational_shift_trajectories.png",
        "short_title": "Journal trajectories of the relational shift index",
        "caption": (
            "Relational shift index by journal and period. The figure shows that journal cultures differ "
            "in level and intensity while moving broadly in the same direction. Psychoanalytic Dialogues "
            "appears as the strongest relational-contextual pole, while IJPA and JAPA provide long-archive "
            "tests of within-journal change."
        ),
        "primary_claim_ids": "C3 | C4 | C7",
        "recommended_role": "main_text_core_result",
        "priority": 2,
        "audit_note": "Important for journal dialects and composition-effect discussion.",
    },
    {
        "figure_id": "Figure 5",
        "file_name": "publication_figure_05_equal_weight_vs_global_relational_shift.png",
        "short_title": "Article-weighted versus equal-journal-weight relational shift trajectory",
        "caption": (
            "Relational shift index by period under article-weighted global aggregation and equal-journal "
            "weighting. The close correspondence between trajectories supports the robustness of the main "
            "semantic-change pattern against simple journal-composition explanations."
        ),
        "primary_claim_ids": "C3 | C8",
        "recommended_role": "main_text_methods_results_bridge",
        "priority": 1,
        "audit_note": "Key robustness figure; likely essential for reviewer confidence.",
    },
    {
        "figure_id": "Figure 6",
        "file_name": "publication_figure_06_initial_vs_refined_family_drop.png",
        "short_title": "Semantic families most affected by marker-strength correction",
        "caption": (
            "Families with the largest percentage-point drop from initial lexical mapping to refined "
            "marker-strength mapping. The figure documents the conservative correction of broad weak "
            "or name-only markers before substantive interpretation."
        ),
        "primary_claim_ids": "C2",
        "recommended_role": "methods_or_supplement",
        "priority": 4,
        "audit_note": "Methodological transparency figure; useful in supplement or methods section.",
    },
]


TABLE_METADATA = [
    {
        "table_id": "Table 1",
        "file_name": "publication_table_01_corpus_semantic_coverage.csv",
        "short_title": "Semantic coverage and marker-strength counts",
        "caption": (
            "Coverage of the initial and refined semantic applications, with marker-strength counts. "
            "This table documents the move from broad lexical coverage to the conservative refined model."
        ),
        "primary_claim_ids": "C2",
        "recommended_role": "methods",
        "priority": 1,
    },
    {
        "table_id": "Table 2",
        "file_name": "publication_table_02_semantic_family_counts_refined.csv",
        "short_title": "Refined semantic-family coverage",
        "caption": (
            "Global refined coverage for each semantic family, including any-marker coverage and weak/name-only rows."
        ),
        "primary_claim_ids": "C1 | C2",
        "recommended_role": "results_or_supplement",
        "priority": 2,
    },
    {
        "table_id": "Table 3",
        "file_name": "publication_table_03_semantic_indices_by_period.csv",
        "short_title": "Semantic change indices by period",
        "caption": (
            "Core semantic families and composite semantic-change indices by period. This is the primary "
            "period-level numerical table supporting the global historical argument."
        ),
        "primary_claim_ids": "C1 | C5 | C6",
        "recommended_role": "main_text_core_result",
        "priority": 1,
    },
    {
        "table_id": "Table 4",
        "file_name": "publication_table_04_journal_trajectories.csv",
        "short_title": "Journal-level semantic trajectories",
        "caption": (
            "Within-journal changes in core indices and journal-level trajectory labels. The table supports "
            "the claim that the transformation is visible within journals while retaining journal-specific dialects."
        ),
        "primary_claim_ids": "C3 | C4 | C7",
        "recommended_role": "main_text_core_result",
        "priority": 1,
    },
    {
        "table_id": "Table 5",
        "file_name": "publication_table_05_balanced_direction_consistency.csv",
        "short_title": "Direction consistency under balanced panels",
        "caption": (
            "Direction of change across journals in all-available, long-journal, common-period, and post-1990 panels. "
            "The table summarizes the robustness of the major semantic trends under partially balanced conditions."
        ),
        "primary_claim_ids": "C3 | C8",
        "recommended_role": "main_text_or_supplement",
        "priority": 1,
    },
    {
        "table_id": "Table 6",
        "file_name": "publication_table_06_initial_vs_refined_impact.csv",
        "short_title": "Initial versus refined marker-strength impact",
        "caption": (
            "Families most affected by marker-strength correction. This table documents which families were most "
            "dependent on broad weak or name-only markers."
        ),
        "primary_claim_ids": "C2",
        "recommended_role": "methods_or_supplement",
        "priority": 2,
    },
    {
        "table_id": "Table 7",
        "file_name": "publication_table_07_journal_distinctiveness.csv",
        "short_title": "Journal distinctiveness",
        "caption": (
            "Journal-level distinctiveness from global period profiles. This table supports interpretation of journals "
            "as distinct psychoanalytic discourse dialects."
        ),
        "primary_claim_ids": "C4 | C7",
        "recommended_role": "results_or_supplement",
        "priority": 3,
    },
    {
        "table_id": "Table 8",
        "file_name": "publication_table_08_narrative_table.csv",
        "short_title": "Period-level narrative interpretation table",
        "caption": (
            "Selected period-level indices with interpretive labels. This table provides a compact bridge from indices "
            "to narrative periodization."
        ),
        "primary_claim_ids": "C1 | C5 | C6",
        "recommended_role": "discussion_or_supplement",
        "priority": 3,
    },
]


CLAIMS = [
    {
        "claim_id": "C1",
        "claim_text": (
            "The psychoanalytic_core corpus shows a century-scale semantic transformation from "
            "drive/conflict/defense-centered discourse toward relational, contextual, trauma-regulatory, "
            "social-ethical, and narrative-reframing vocabularies."
        ),
        "primary_evidence": "Figure 1; Table 3",
        "supporting_evidence": "Figure 2; Figure 3; Table 8",
        "strength": "strong",
        "caveat": "Title-and-abstract evidence; not direct evidence of clinical practice change.",
        "manuscript_section": "Results I: Global semantic transformation",
    },
    {
        "claim_id": "C2",
        "claim_text": (
            "The main semantic pattern survives conservative marker-strength correction, reducing the risk "
            "that results are driven by broad weak terms or name-only markers."
        ),
        "primary_evidence": "Table 1; Figure 6",
        "supporting_evidence": "Table 6; Stage 3e comparison outputs",
        "strength": "strong",
        "caveat": "Marker-strength model remains rule-based and provisional.",
        "manuscript_section": "Methods; Sensitivity analysis",
    },
    {
        "claim_id": "C3",
        "claim_text": (
            "The transformation is visible within journal trajectories and is not reducible to simple journal-composition effects."
        ),
        "primary_evidence": "Figure 5; Table 5",
        "supporting_evidence": "Table 4; 4b and 4c summaries",
        "strength": "strong",
        "caveat": "Balanced diagnostics reduce but do not fully eliminate all composition concerns.",
        "manuscript_section": "Results II: Journal/global robustness",
    },
    {
        "claim_id": "C4",
        "claim_text": (
            "Psychoanalytic Dialogues intensifies and condenses the relational-contextual transformation but does not create it alone."
        ),
        "primary_evidence": "Figure 4; Table 4",
        "supporting_evidence": "Table 7; journal-vs-global deviation outputs",
        "strength": "moderate_to_strong",
        "caveat": "Journal start dates and period coverage remain uneven.",
        "manuscript_section": "Results II: Journal dialects",
    },
    {
        "claim_id": "C5",
        "claim_text": (
            "The narrative_reframing_index suggests a change in the narrative grammar through which psychoanalytic clinical reality is described."
        ),
        "primary_evidence": "Figure 2; Table 3",
        "supporting_evidence": "Table 8",
        "strength": "moderate_to_strong",
        "caveat": "The index is interpretive and composite; it requires careful theoretical framing.",
        "manuscript_section": "Results and Discussion",
    },
    {
        "claim_id": "C6",
        "claim_text": (
            "The contemporary corpus shows a strong contextualization pattern, combining relational, social-ethical, and trauma-regulatory vocabularies."
        ),
        "primary_evidence": "Figure 3; Table 3",
        "supporting_evidence": "Table 8",
        "strength": "strong",
        "caveat": "Composite index should be interpreted as exploratory, not as a validated scale.",
        "manuscript_section": "Results I; Discussion",
    },
    {
        "claim_id": "C7",
        "claim_text": (
            "Journals function as distinct psychoanalytic discourse dialects, shaping the tempo, intensity, and vocabulary of the broader transformation."
        ),
        "primary_evidence": "Table 4; Table 7",
        "supporting_evidence": "Figure 4",
        "strength": "moderate_to_strong",
        "caveat": "Distinctiveness is based on selected semantic indices; further cluster/network analysis may refine this claim.",
        "manuscript_section": "Results II; Discussion",
    },
    {
        "claim_id": "C8",
        "claim_text": (
            "Equal-journal-weight and balanced-panel checks preserve the main directions of semantic change."
        ),
        "primary_evidence": "Figure 5; Table 5",
        "supporting_evidence": "4c balanced robustness summary",
        "strength": "strong",
        "caveat": "This is a robustness diagnostic rather than a full causal decomposition.",
        "manuscript_section": "Robustness checks",
    },
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
        "publication_outputs": title_root / "publication_outputs",
        "semantic_change": title_root / "semantic_change",
        "semantic_change_balanced": title_root / "semantic_change_balanced",
        "review_outputs": title_root / "publication_outputs_review",
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


def write_text(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def file_exists_flag(root: Path, file_name: str) -> bool:
    return (root / file_name).exists()


def add_file_status(df: pd.DataFrame, root: Path) -> pd.DataFrame:
    out = df.copy()
    out["file_exists"] = out["file_name"].apply(lambda x: file_exists_flag(root, x))
    out["relative_path"] = out["file_name"].apply(lambda x: str(root / x))
    return out


def make_figure_recommendations(figures: pd.DataFrame) -> pd.DataFrame:
    if figures.empty:
        return pd.DataFrame()
    out = figures.copy()
    role_order = {
        "main_text_core_result": 1,
        "main_text_methods_results_bridge": 2,
        "main_text_or_supplement": 3,
        "methods_or_supplement": 4,
    }
    out["_role_order"] = out["recommended_role"].map(role_order).fillna(99).astype(int)
    out = out.sort_values(["priority", "_role_order", "figure_id"]).drop(columns=["_role_order"])
    out["selection_recommendation"] = out.apply(
        lambda r: (
            "include_main_text"
            if r["recommended_role"] in {"main_text_core_result", "main_text_methods_results_bridge"}
            else "consider_supplement_or_methods"
            if r["recommended_role"] in {"methods_or_supplement", "main_text_or_supplement"}
            else "review"
        ),
        axis=1,
    )
    return out


def build_core_results_narrative(pub_summary: Dict, balanced_summary: Dict) -> str:
    trend = pub_summary.get("trend_summary_from_period_indices", {})
    coverage = pub_summary.get("outputs", {})

    rel_change = trend.get("relational_shift_index_change", "")
    drive_change = trend.get("drive_conflict_defense_change", "")
    narrative_change = trend.get("narrative_reframing_index_change", "")
    contextual_change = trend.get("contemporary_contextualization_index_change", "")

    balanced = balanced_summary.get("key_conclusions", {})
    eq = balanced.get("equal_weight_first_to_last", {})
    eq_rel = eq.get("relational_shift_change_equal_weight", "")
    eq_drive = eq.get("drive_conflict_change_equal_weight", "")
    eq_narr = eq.get("narrative_reframing_change_equal_weight", "")

    text = f"""# Core results narrative draft

**Status:** working results narrative generated by `5b_publication_figure_audit_and_captions.py`  
**Use:** manuscript planning only; requires human revision.

## Main result

The refined title-and-abstract semantic layer indicates a substantial diachronic transformation in the psychoanalytic journal corpus. The most compact expression of this transformation is the movement from drive/conflict/defense-centered discourse toward relational, contextual, trauma-regulatory, social-ethical, and narrative-reframing vocabularies.

Across the full period range, the key period-level changes are:

```text
relational_shift_index_change: {rel_change}
drive_conflict_defense_change: {drive_change}
narrative_reframing_index_change: {narrative_change}
contemporary_contextualization_index_change: {contextual_change}
```

These results support the interpretation that the corpus does not merely show a rise in relational language. It shows a broader change in the narrative grammar of psychoanalytic discourse.

## Marker-strength correction

The main interpretive layer is the refined semantic model, not the initial broad lexical model. Stage 3 QA showed that some families were inflated by broad weak terms or name-only markers. The marker-strength model therefore treated weak-only and name-only hits conservatively. The purpose was not to remove psychoanalytically meaningful words, but to prevent them from carrying too much interpretive weight when they appeared alone.

This correction supports a central methodological claim: the major trends are not simply artifacts of overbroad lexical matching.

## Journal and corpus dynamics

The field-level transformation is visible globally, but journals differ in how they carry it. Psychoanalytic Dialogues appears as the strongest relational-contextual pole, yet it does not produce the shift alone. Long-archive journals such as IJPA and JAPA also show movement in the same broad direction.

The journal-level results suggest that psychoanalytic journals function as distinct discourse dialects: they participate in the same historical transformation, but with different intensity, timing, and vocabulary.

## Balanced robustness checks

Balanced and partially balanced analyses support the robustness of the main result. In the equal-journal-weight trajectory, the key changes were:

```text
relational_shift_change_equal_weight: {eq_rel}
drive_conflict_change_equal_weight: {eq_drive}
narrative_reframing_change_equal_weight: {eq_narr}
```

The similarity between article-weighted and equal-journal-weight trajectories suggests that the result is not reducible to the changing composition of the corpus. Journal composition matters, but it does not fully explain the observed semantic transformation.

## Theoretical interpretation

The empirical pattern is consistent with a broad theoretical frame involving:

```text
Beebe and Lachmann: relational and dyadic-systems transformation
Orange: ethical, contextual, and hermeneutic expansion
Schafer: changing psychoanalytic narratives
Pluralism/common-ground literature: useful fictions, regional dialects, and redescriptions
```

The corpus does not prove how clinical practice changed. It provides title-and-abstract-level evidence for how psychoanalytic authors and journals publicly redescribed their clinical and theoretical world over time.

## Recommended manuscript claim

A cautious central claim is:

> In a century-scale corpus of psychoanalytic journal articles, refined title-and-abstract semantic mapping shows a robust transformation from drive/conflict/defense-centered discourse toward relational, contextual, trauma-regulatory, social-ethical, and narrative-reframing vocabularies. This transformation is visible globally, within journal trajectories, and under partially balanced journal-composition checks, while remaining shaped by distinct journal cultures.

"""
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description="Create publication audit, captions, and claims matrix.")
    parser.add_argument("--publication-root", default="../data/title_abstract/publication_outputs")
    parser.add_argument("--balanced-root", default="../data/title_abstract/semantic_change_balanced")
    parser.add_argument("--out-dir", default="../data/title_abstract/publication_outputs_review")
    args = parser.parse_args()

    paths = get_paths()

    def resolve(p: str) -> Path:
        path = Path(p)
        if not path.is_absolute():
            path = (paths["scripts_dir"] / path).resolve()
        return path

    publication_root = resolve(args.publication_root)
    balanced_root = resolve(args.balanced_root)
    out_dir = resolve(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not publication_root.exists():
        raise SystemExit(f"ERROR: publication output directory not found: {publication_root}")

    pub_summary = read_json_safe(publication_root / "publication_outputs_summary.json")
    balanced_summary = read_json_safe(balanced_root / "psychoanalytic_core_balanced_semantic_change_summary.json")

    figures = add_file_status(pd.DataFrame(FIGURE_METADATA), publication_root)
    tables = add_file_status(pd.DataFrame(TABLE_METADATA), publication_root)
    claims = pd.DataFrame(CLAIMS)
    recommendations = make_figure_recommendations(figures)
    narrative = build_core_results_narrative(pub_summary, balanced_summary)

    outputs = {
        "figure_caption_sheet": out_dir / "publication_figure_caption_sheet.csv",
        "table_caption_sheet": out_dir / "publication_table_caption_sheet.csv",
        "results_claims_matrix": out_dir / "publication_results_claims_matrix.csv",
        "figure_selection_recommendations": out_dir / "publication_figure_selection_recommendations.csv",
        "core_results_narrative": out_dir / "publication_core_results_narrative.md",
    }

    write_csv(figures, outputs["figure_caption_sheet"])
    write_csv(tables, outputs["table_caption_sheet"])
    write_csv(claims, outputs["results_claims_matrix"])
    write_csv(recommendations, outputs["figure_selection_recommendations"])
    write_text(narrative, outputs["core_results_narrative"])

    missing_figures = figures.loc[~figures["file_exists"], "file_name"].tolist()
    missing_tables = tables.loc[~tables["file_exists"], "file_name"].tolist()

    summary = {
        "script_version": SCRIPT_VERSION,
        "created_at_utc": utc_now_iso(),
        "purpose": "Create caption sheets, claims matrix, figure recommendations, and core results narrative draft.",
        "inputs": {
            "publication_root": str(publication_root),
            "balanced_root": str(balanced_root),
        },
        "outputs": {k: str(v) for k, v in outputs.items()},
        "counts": {
            "n_figures_documented": int(len(figures)),
            "n_tables_documented": int(len(tables)),
            "n_claims": int(len(claims)),
            "n_missing_figures": int(len(missing_figures)),
            "n_missing_tables": int(len(missing_tables)),
        },
        "missing_figures": missing_figures,
        "missing_tables": missing_tables,
        "recommended_main_text_figures": (
            recommendations.loc[
                recommendations["selection_recommendation"] == "include_main_text",
                ["figure_id", "file_name", "short_title", "primary_claim_ids"],
            ].to_dict(orient="records")
            if not recommendations.empty else []
        ),
        "methodological_note": (
            "This review layer links figures and tables to claims. It should be treated as manuscript planning, "
            "not as final text. Captions and claims require human scholarly revision before submission."
        ),
    }

    summary_path = out_dir / "publication_outputs_review_summary.json"
    write_json(summary, summary_path)
    summary["outputs"]["summary_json"] = str(summary_path)

    print(json.dumps({
        "status": "ok",
        "script_version": SCRIPT_VERSION,
        "n_figures_documented": summary["counts"]["n_figures_documented"],
        "n_tables_documented": summary["counts"]["n_tables_documented"],
        "n_claims": summary["counts"]["n_claims"],
        "n_missing_figures": summary["counts"]["n_missing_figures"],
        "n_missing_tables": summary["counts"]["n_missing_tables"],
        "summary_json": str(summary_path),
        "claims_matrix": str(outputs["results_claims_matrix"]),
        "narrative": str(outputs["core_results_narrative"]),
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
