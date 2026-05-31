#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
5d_semantic_family_content_tables.py

Andromeda Nowicka v0.5-pre
Publication-facing semantic family content tables.

Purpose
-------
Create publication-oriented tables that show what the semantic families contain.

This script answers a reader/reviewer question:

    "What is inside these semantic families?"

It prepares compact and auditable tables using:
- refined semantic map with marker strength,
- semantic QA top terms by family,
- refined global family coverage.

It does NOT change semantic mappings and does NOT reinterpret the corpus.
It only prepares presentation layers.

Inputs
------
From Stage 3 refined semantic layer:
    ../data/title_abstract/semantic_refined/psychoanalytic_core_semantic_map_marker_strength.csv
    ../data/title_abstract/semantic_refined/psychoanalytic_core_semantic_family_counts_refined.csv
    ../data/title_abstract/semantic_refined/psychoanalytic_core_marker_strength_by_family.csv

From Stage 3 QA:
    ../data/title_abstract/semantic_QA/psychoanalytic_core_semantic_QA_top_terms_by_family.csv
    ../data/title_abstract/semantic_QA/psychoanalytic_core_semantic_QA_family_term_concentration.csv
    ../data/title_abstract/semantic_QA/psychoanalytic_core_semantic_QA_high_risk_terms.csv

Outputs
-------
../data/title_abstract/publication_outputs/

    publication_table_09_semantic_family_definitions_and_top_terms.csv
    publication_table_10_semantic_family_marker_strength_examples.csv
    publication_table_11_semantic_family_top_terms_long.csv
    publication_table_12_semantic_family_high_risk_terms.csv
    publication_table_13_semantic_family_content_audit_summary.csv
    publication_figure_07_semantic_family_content_heatmap.png
    publication_figure_08_marker_strength_by_family.png

Also updates:
    publication_outputs_summary_5d.json

Run
---
Put this file in:

    data_psychoanalytic_core/scripts/

Run:

    cd data_psychoanalytic_core/scripts
    python 5d_semantic_family_content_tables.py

Notes
-----
- Figures use matplotlib defaults intentionally.
- No seaborn.
- No hard-coded colors.
- Tables are meant for manuscript/supplement inspection.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Dict, List, Iterable

import matplotlib.pyplot as plt
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

FAMILY_DEFINITIONS = {
    "drive_conflict_defense": (
        "Vocabulary of drive theory, psychic conflict, defense, resistance, aggression, libido, "
        "and related classical metapsychological conflict formulations."
    ),
    "dream_fantasy_unconscious": (
        "Vocabulary of dreams, fantasy, unconscious processes, phantasy, wish, symbol, and related "
        "imaginative or unconscious formations."
    ),
    "ego_self_narcissism": (
        "Vocabulary of ego, self, identity, subjectivity, narcissism, selfhood, and related self-structural concepts."
    ),
    "object_relations": (
        "Vocabulary of objects, internal/external object relations, splitting, projective identification, "
        "and object-relational organization."
    ),
    "kleinian_bionian": (
        "Specific Kleinian and Bionian vocabulary, including projective identification, positions, container/contained, "
        "alpha function, beta elements, and related terms."
    ),
    "winnicottian_environment_holding": (
        "Vocabulary associated with Winnicottian holding, environment, transitionality, potential space, play, "
        "and facilitating conditions."
    ),
    "attachment_development_infant": (
        "Vocabulary of infant research, child development, attachment, early development, caregiver relations, "
        "and developmental contexts."
    ),
    "transference_countertransference": (
        "Vocabulary of transference, countertransference, enactment, analytic relationship as transferential field, "
        "and related clinical process concepts."
    ),
    "technique_interpretation_process": (
        "Vocabulary of analytic technique, interpretation, setting, frame, process, working through, free association, "
        "therapeutic action, and clinical procedure."
    ),
    "relational_intersubjective_field": (
        "Vocabulary of relational, intersubjective, interpersonal, mutual, dialogic, field, recognition, and co-constructed processes."
    ),
    "trauma_dissociation_affect_regulation": (
        "Vocabulary of trauma, dissociation, affect, emotion, regulation, anxiety, traumatic states, and affective processing."
    ),
    "psychosis_borderline_primitive_states": (
        "Vocabulary of psychosis, borderline states, primitive mental states, severe pathology, and related clinical configurations."
    ),
    "body_sexuality_gender": (
        "Vocabulary of body, sexuality, gender, sex, embodiment, and related bodily/sexual/gendered experience."
    ),
    "language_narrative_symbolization": (
        "Vocabulary of language, narrative, meaning, symbolization, metaphor, representation, and interpretive redescription."
    ),
    "culture_race_social_ethics": (
        "Vocabulary of culture, race, racism, society, politics, ethics, responsibility, violence, war, and social context."
    ),
    "empirical_research_measurement": (
        "Vocabulary of empirical research, measurement, evidence, methodology, studies, data, outcomes, and assessment."
    ),
    "history_theory_schools": (
        "Vocabulary of psychoanalytic history, schools, theoretical traditions, authors, and named lineages."
    ),
}

PUBLICATION_FAMILY_GROUPS = {
    "drive_conflict_defense": "Classical / metapsychological",
    "dream_fantasy_unconscious": "Classical / metapsychological",
    "ego_self_narcissism": "Self / structure",
    "object_relations": "Object-relational traditions",
    "kleinian_bionian": "Object-relational traditions",
    "winnicottian_environment_holding": "Object-relational traditions",
    "attachment_development_infant": "Developmental / attachment",
    "transference_countertransference": "Clinical process / technique",
    "technique_interpretation_process": "Clinical process / technique",
    "relational_intersubjective_field": "Relational / contextual",
    "trauma_dissociation_affect_regulation": "Trauma / affect / severity",
    "psychosis_borderline_primitive_states": "Trauma / affect / severity",
    "body_sexuality_gender": "Body / sexuality / gender",
    "language_narrative_symbolization": "Narrative / symbolic",
    "culture_race_social_ethics": "Relational / contextual",
    "empirical_research_measurement": "Research / method",
    "history_theory_schools": "History / theory",
}

MARKER_STRENGTH_ORDER = {
    "strong": 1,
    "medium": 2,
    "weak": 3,
    "name_marker": 4,
    "unmapped": 5,
    "": 99,
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
        "semantic_refined": title_root / "semantic_refined",
        "semantic_QA": title_root / "semantic_QA",
        "publication_outputs": title_root / "publication_outputs",
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


def family_order_value(family: str) -> int:
    try:
        return SEMANTIC_FAMILY_ORDER.index(str(family))
    except ValueError:
        return 999


def family_label(family: str) -> str:
    return FAMILY_LABELS.get(str(family), str(family).replace("_", " "))


def family_definition(family: str) -> str:
    return FAMILY_DEFINITIONS.get(str(family), "")


def family_group(family: str) -> str:
    return PUBLICATION_FAMILY_GROUPS.get(str(family), "")


def normalize_term_col(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if "term_norm" not in out.columns:
        if "term" in out.columns:
            out["term_norm"] = out["term"]
        elif "keyword_norm" in out.columns:
            out["term_norm"] = out["keyword_norm"]
        else:
            out["term_norm"] = ""
    out["term_norm"] = out["term_norm"].astype(str).str.strip()
    return out


def collapse_terms(terms: Iterable[str], max_terms: int = 8) -> str:
    cleaned = []
    seen = set()
    for t in terms:
        tt = str(t).strip()
        if not tt or tt in seen:
            continue
        seen.add(tt)
        cleaned.append(tt)
        if len(cleaned) >= max_terms:
            break
    return " | ".join(cleaned)


def make_top_terms_long(top_terms: pd.DataFrame, marker_map: pd.DataFrame) -> pd.DataFrame:
    if top_terms.empty:
        return pd.DataFrame()

    t = top_terms.copy()
    t["term_norm"] = t["term"].astype(str).str.strip() if "term" in t.columns else ""

    m = normalize_term_col(marker_map)
    keep_cols = [
        "semantic_family",
        "term_norm",
        "marker_strength",
        "marker_strength_reason",
        "semantic_confidence",
        "mapping_rule",
        "matched_pattern",
        "review_flag",
    ]
    m_small = m[[c for c in keep_cols if c in m.columns]].drop_duplicates()

    out = t.merge(
        m_small,
        on=["semantic_family", "term_norm"],
        how="left",
    )

    out["semantic_family_label"] = out["semantic_family"].map(family_label)
    out["family_group"] = out["semantic_family"].map(family_group)
    out["_family_order"] = out["semantic_family"].map(family_order_value)
    out["rank_within_family"] = num(out, "rank_within_family").astype(int)
    out["n_articles"] = num(out, "n_articles").astype(int)
    if "pct_all_articles" in out.columns:
        out["pct_all_articles"] = num(out, "pct_all_articles").round(4)

    keep = [
        "semantic_family",
        "semantic_family_label",
        "family_group",
        "rank_within_family",
        "term_norm",
        "n_articles",
        "pct_all_articles",
        "n_term_hit_rows",
        "marker_strength",
        "marker_strength_reason",
        "semantic_confidence",
        "mapping_rule",
        "review_flag",
    ]
    out = out[[c for c in keep if c in out.columns]]
    return out.sort_values(["_family_order", "rank_within_family"] if "_family_order" in out.columns else ["semantic_family", "rank_within_family"])


def make_definitions_and_top_terms(
    marker_map: pd.DataFrame,
    top_terms: pd.DataFrame,
    family_counts: pd.DataFrame,
    concentration: pd.DataFrame,
    top_n: int = 8,
) -> pd.DataFrame:
    marker_map = normalize_term_col(marker_map)
    mapped = marker_map[marker_map.get("semantic_action", "").astype(str).eq("mapped_initial")].copy() if "semantic_action" in marker_map.columns else marker_map.copy()
    mapped = mapped[mapped["semantic_family"].astype(str).ne("")]

    if not top_terms.empty:
        tt = top_terms.copy()
        tt["rank_within_family"] = num(tt, "rank_within_family").astype(int)
        tt = tt[tt["rank_within_family"] <= top_n].copy()
    else:
        tt = pd.DataFrame()

    family_counts_small = family_counts.copy()
    concentration_small = concentration.copy()

    rows = []
    for fam in SEMANTIC_FAMILY_ORDER:
        g = mapped[mapped["semantic_family"] == fam].copy()
        tt_fam = tt[tt["semantic_family"] == fam].copy() if not tt.empty else pd.DataFrame()

        strong_terms = collapse_terms(
            g.loc[g["marker_strength"].astype(str).eq("strong"), "term_norm"].sort_values(),
            max_terms=top_n,
        )
        medium_terms = collapse_terms(
            g.loc[g["marker_strength"].astype(str).eq("medium"), "term_norm"].sort_values(),
            max_terms=top_n,
        )
        weak_terms = collapse_terms(
            g.loc[g["marker_strength"].astype(str).eq("weak"), "term_norm"].sort_values(),
            max_terms=top_n,
        )
        name_terms = collapse_terms(
            g.loc[g["marker_strength"].astype(str).eq("name_marker"), "term_norm"].sort_values(),
            max_terms=top_n,
        )

        if not tt_fam.empty:
            top_hit_terms = collapse_terms(tt_fam.sort_values("rank_within_family")["term"].tolist(), max_terms=top_n)
        else:
            top_hit_terms = ""

        fc = family_counts_small[family_counts_small["semantic_family"] == fam] if not family_counts_small.empty else pd.DataFrame()
        conc = concentration_small[concentration_small["semantic_family"] == fam] if not concentration_small.empty else pd.DataFrame()

        row = {
            "semantic_family": fam,
            "semantic_family_label": family_label(fam),
            "family_group": family_group(fam),
            "working_definition": family_definition(fam),
            "n_terms_strong": int((g["marker_strength"].astype(str) == "strong").sum()) if "marker_strength" in g.columns else 0,
            "n_terms_medium": int((g["marker_strength"].astype(str) == "medium").sum()) if "marker_strength" in g.columns else 0,
            "n_terms_weak": int((g["marker_strength"].astype(str) == "weak").sum()) if "marker_strength" in g.columns else 0,
            "n_terms_name_marker": int((g["marker_strength"].astype(str) == "name_marker").sum()) if "marker_strength" in g.columns else 0,
            "example_strong_markers": strong_terms,
            "example_medium_markers": medium_terms,
            "example_weak_markers": weak_terms,
            "example_name_markers": name_terms,
            "top_article_hit_terms": top_hit_terms,
            "n_articles_refined": int(num(fc, "n_articles_refined").iloc[0]) if not fc.empty and "n_articles_refined" in fc.columns else "",
            "pct_articles_refined": round(float(num(fc, "pct_articles_refined").iloc[0]), 4) if not fc.empty and "pct_articles_refined" in fc.columns else "",
            "n_articles_any_marker": int(num(fc, "n_articles_any_marker").iloc[0]) if not fc.empty and "n_articles_any_marker" in fc.columns else "",
            "pct_articles_any_marker": round(float(num(fc, "pct_articles_any_marker").iloc[0]), 4) if not fc.empty and "pct_articles_any_marker" in fc.columns else "",
            "top1_term": conc["top1_term"].iloc[0] if not conc.empty and "top1_term" in conc.columns else "",
            "top1_share_of_family_articles_pct": conc["top1_share_of_family_articles_pct"].iloc[0] if not conc.empty and "top1_share_of_family_articles_pct" in conc.columns else "",
            "content_note": (
                "Working semantic family; examples are derived from refined marker map and QA top-term counts. "
                "Families are interpretive categories, not final ontology."
            ),
        }
        rows.append(row)

    return pd.DataFrame(rows)


def make_marker_strength_examples(marker_map: pd.DataFrame, max_terms: int = 12) -> pd.DataFrame:
    marker_map = normalize_term_col(marker_map)
    mapped = marker_map[marker_map.get("semantic_action", "").astype(str).eq("mapped_initial")].copy() if "semantic_action" in marker_map.columns else marker_map.copy()
    mapped = mapped[mapped["semantic_family"].astype(str).ne("")]

    rows = []
    for fam in SEMANTIC_FAMILY_ORDER:
        g = mapped[mapped["semantic_family"] == fam].copy()
        for strength in ["strong", "medium", "weak", "name_marker"]:
            sg = g[g["marker_strength"].astype(str).eq(strength)].copy() if "marker_strength" in g.columns else pd.DataFrame()
            rows.append({
                "semantic_family": fam,
                "semantic_family_label": family_label(fam),
                "family_group": family_group(fam),
                "marker_strength": strength,
                "n_terms": int(len(sg)),
                "example_terms": collapse_terms(sg["term_norm"].sort_values().tolist(), max_terms=max_terms) if not sg.empty else "",
            })
    out = pd.DataFrame(rows)
    out["_family_order"] = out["semantic_family"].map(family_order_value)
    out["_strength_order"] = out["marker_strength"].map(MARKER_STRENGTH_ORDER).fillna(99)
    return out.sort_values(["_family_order", "_strength_order"]).drop(columns=["_family_order", "_strength_order"])


def make_high_risk_terms_pub(high_risk: pd.DataFrame) -> pd.DataFrame:
    if high_risk.empty:
        return pd.DataFrame()
    out = high_risk.copy()
    out["semantic_family_label"] = out["semantic_family"].map(family_label)
    out["family_group"] = out["semantic_family"].map(family_group)
    out["_family_order"] = out["semantic_family"].map(family_order_value)

    keep = [
        "semantic_family",
        "semantic_family_label",
        "family_group",
        "term",
        "n_articles",
        "n_family_articles",
        "share_of_family_articles_pct",
        "risk_reasons",
        "recommended_action",
    ]
    out = out[[c for c in keep + ["_family_order"] if c in out.columns]]
    sort_cols = [c for c in ["_family_order", "share_of_family_articles_pct"] if c in out.columns]
    if sort_cols:
        out = out.sort_values(sort_cols, ascending=[True, False] if len(sort_cols) == 2 else True)
    return out.drop(columns=[c for c in ["_family_order"] if c in out.columns])


def make_content_audit_summary(
    definitions: pd.DataFrame,
    marker_examples: pd.DataFrame,
    top_terms_long: pd.DataFrame,
    high_risk: pd.DataFrame,
) -> pd.DataFrame:
    rows = []
    for fam in SEMANTIC_FAMILY_ORDER:
        d = definitions[definitions["semantic_family"] == fam]
        m = marker_examples[marker_examples["semantic_family"] == fam]
        t = top_terms_long[top_terms_long["semantic_family"] == fam] if not top_terms_long.empty else pd.DataFrame()
        h = high_risk[high_risk["semantic_family"] == fam] if not high_risk.empty else pd.DataFrame()

        row = {
            "semantic_family": fam,
            "semantic_family_label": family_label(fam),
            "family_group": family_group(fam),
            "n_terms_total_mapped": int(m["n_terms"].sum()) if not m.empty and "n_terms" in m.columns else 0,
            "n_terms_strong": int(d["n_terms_strong"].iloc[0]) if not d.empty else 0,
            "n_terms_medium": int(d["n_terms_medium"].iloc[0]) if not d.empty else 0,
            "n_terms_weak": int(d["n_terms_weak"].iloc[0]) if not d.empty else 0,
            "n_terms_name_marker": int(d["n_terms_name_marker"].iloc[0]) if not d.empty else 0,
            "n_top_terms_reported": int(len(t)),
            "n_high_risk_terms": int(len(h)),
            "top1_term": d["top1_term"].iloc[0] if not d.empty else "",
            "top1_share_of_family_articles_pct": d["top1_share_of_family_articles_pct"].iloc[0] if not d.empty else "",
            "publication_readiness_note": (
                "ready_for_supplement"
                if int(len(h)) <= 3 else
                "review_high_risk_terms_before_main_text"
            ),
        }
        rows.append(row)

    return pd.DataFrame(rows)


def save_figure(fig: plt.Figure, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(path, dpi=300, bbox_inches="tight")
    plt.close(fig)


def figure_content_heatmap(definitions: pd.DataFrame, path: Path) -> None:
    if definitions.empty:
        return

    df = definitions.copy()
    df["_family_order"] = df["semantic_family"].map(family_order_value)
    df = df.sort_values("_family_order")

    value_cols = [
        "n_terms_strong",
        "n_terms_medium",
        "n_terms_weak",
        "n_terms_name_marker",
        "pct_articles_refined",
    ]
    data = df[value_cols].apply(pd.to_numeric, errors="coerce").fillna(0.0)

    fig, ax = plt.subplots(figsize=(9, 7))
    im = ax.imshow(data.values, aspect="auto")

    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(df["semantic_family_label"].astype(str), fontsize=8)
    ax.set_xticks(range(len(value_cols)))
    ax.set_xticklabels([
        "Strong\nterms",
        "Medium\nterms",
        "Weak\nterms",
        "Name\nmarkers",
        "Refined\ncoverage %",
    ], rotation=0)

    ax.set_title("Semantic family content overview")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Count or percentage")

    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            val = data.iloc[i, j]
            label = f"{val:.1f}" if j == len(value_cols) - 1 else f"{int(val)}"
            ax.text(j, i, label, ha="center", va="center", fontsize=7)

    save_figure(fig, path)


def figure_marker_strength_by_family(marker_examples: pd.DataFrame, path: Path) -> None:
    if marker_examples.empty:
        return

    pivot = marker_examples.pivot_table(
        index="semantic_family_label",
        columns="marker_strength",
        values="n_terms",
        aggfunc="sum",
        fill_value=0,
    )

    # Preserve family order.
    label_order = [family_label(f) for f in SEMANTIC_FAMILY_ORDER if family_label(f) in pivot.index]
    pivot = pivot.loc[label_order]
    cols = [c for c in ["strong", "medium", "weak", "name_marker"] if c in pivot.columns]
    pivot = pivot[cols]

    fig, ax = plt.subplots(figsize=(10, 7))
    y = range(len(pivot))
    left = pd.Series([0] * len(pivot), index=pivot.index, dtype=float)

    for col in cols:
        values = pd.to_numeric(pivot[col], errors="coerce").fillna(0)
        ax.barh(list(y), values, left=left.values, label=col)
        left = left + values

    ax.set_yticks(list(y))
    ax.set_yticklabels(pivot.index.astype(str), fontsize=8)
    ax.set_xlabel("Number of mapped terms")
    ax.set_title("Marker strength composition by semantic family")
    ax.legend(title="Marker strength", fontsize="small")
    ax.grid(True, axis="x", alpha=0.3)

    save_figure(fig, path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create publication-facing semantic family content tables.")
    parser.add_argument("--out-dir", default="../data/title_abstract/publication_outputs")
    parser.add_argument("--top-n", type=int, default=8)
    args = parser.parse_args()

    paths = get_paths()

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = (paths["scripts_dir"] / out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    marker_map_path = paths["semantic_refined"] / "psychoanalytic_core_semantic_map_marker_strength.csv"
    family_counts_path = paths["semantic_refined"] / "psychoanalytic_core_semantic_family_counts_refined.csv"
    marker_strength_by_family_path = paths["semantic_refined"] / "psychoanalytic_core_marker_strength_by_family.csv"

    top_terms_path = paths["semantic_QA"] / "psychoanalytic_core_semantic_QA_top_terms_by_family.csv"
    concentration_path = paths["semantic_QA"] / "psychoanalytic_core_semantic_QA_family_term_concentration.csv"
    high_risk_path = paths["semantic_QA"] / "psychoanalytic_core_semantic_QA_high_risk_terms.csv"

    required = [
        marker_map_path,
        family_counts_path,
        top_terms_path,
    ]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        raise SystemExit(f"ERROR: missing required inputs: {missing}")

    marker_map = read_csv_safe(marker_map_path)
    family_counts = read_csv_safe(family_counts_path)
    marker_strength_by_family = read_csv_safe(marker_strength_by_family_path)
    top_terms = read_csv_safe(top_terms_path)
    concentration = read_csv_safe(concentration_path)
    high_risk = read_csv_safe(high_risk_path)

    top_terms_long = make_top_terms_long(top_terms, marker_map)
    definitions = make_definitions_and_top_terms(
        marker_map=marker_map,
        top_terms=top_terms,
        family_counts=family_counts,
        concentration=concentration,
        top_n=args.top_n,
    )
    marker_examples = make_marker_strength_examples(marker_map, max_terms=12)
    high_risk_pub = make_high_risk_terms_pub(high_risk)
    audit_summary = make_content_audit_summary(
        definitions=definitions,
        marker_examples=marker_examples,
        top_terms_long=top_terms_long,
        high_risk=high_risk_pub,
    )

    table_paths = {
        "semantic_family_definitions_and_top_terms": out_dir / "publication_table_09_semantic_family_definitions_and_top_terms.csv",
        "semantic_family_marker_strength_examples": out_dir / "publication_table_10_semantic_family_marker_strength_examples.csv",
        "semantic_family_top_terms_long": out_dir / "publication_table_11_semantic_family_top_terms_long.csv",
        "semantic_family_high_risk_terms": out_dir / "publication_table_12_semantic_family_high_risk_terms.csv",
        "semantic_family_content_audit_summary": out_dir / "publication_table_13_semantic_family_content_audit_summary.csv",
    }

    write_csv(definitions, table_paths["semantic_family_definitions_and_top_terms"])
    write_csv(marker_examples, table_paths["semantic_family_marker_strength_examples"])
    write_csv(top_terms_long, table_paths["semantic_family_top_terms_long"])
    write_csv(high_risk_pub, table_paths["semantic_family_high_risk_terms"])
    write_csv(audit_summary, table_paths["semantic_family_content_audit_summary"])

    figure_paths = {
        "semantic_family_content_heatmap": out_dir / "publication_figure_07_semantic_family_content_heatmap.png",
        "marker_strength_by_family": out_dir / "publication_figure_08_marker_strength_by_family.png",
    }

    figure_content_heatmap(definitions, figure_paths["semantic_family_content_heatmap"])
    figure_marker_strength_by_family(marker_examples, figure_paths["marker_strength_by_family"])

    high_risk_counts = {}
    if not high_risk_pub.empty:
        high_risk_counts = high_risk_pub.groupby("semantic_family")["term"].count().to_dict()

    summary = {
        "script_version": SCRIPT_VERSION,
        "created_at_utc": utc_now_iso(),
        "purpose": "Create publication-facing semantic family content tables and figures.",
        "inputs": {
            "semantic_map_marker_strength": str(marker_map_path),
            "semantic_family_counts_refined": str(family_counts_path),
            "marker_strength_by_family": str(marker_strength_by_family_path),
            "qa_top_terms_by_family": str(top_terms_path),
            "qa_family_term_concentration": str(concentration_path),
            "qa_high_risk_terms": str(high_risk_path),
        },
        "parameters": {
            "top_n_terms_per_family": args.top_n,
        },
        "outputs": {
            "tables": {k: str(v) for k, v in table_paths.items()},
            "figures": {k: str(v) for k, v in figure_paths.items()},
        },
        "counts": {
            "n_semantic_families": int(len(definitions)),
            "n_marker_example_rows": int(len(marker_examples)),
            "n_top_terms_long_rows": int(len(top_terms_long)),
            "n_high_risk_terms": int(len(high_risk_pub)),
            "n_audit_summary_rows": int(len(audit_summary)),
        },
        "high_risk_term_counts_by_family": {str(k): int(v) for k, v in high_risk_counts.items()},
        "recommended_use": {
            "main_text": [
                "publication_table_09_semantic_family_definitions_and_top_terms.csv"
            ],
            "supplement": [
                "publication_table_10_semantic_family_marker_strength_examples.csv",
                "publication_table_11_semantic_family_top_terms_long.csv",
                "publication_table_12_semantic_family_high_risk_terms.csv",
                "publication_table_13_semantic_family_content_audit_summary.csv",
                "publication_figure_07_semantic_family_content_heatmap.png",
                "publication_figure_08_marker_strength_by_family.png",
            ],
        },
        "methodological_note": (
            "These tables describe the content of working semantic families. "
            "They are intended for transparency and reviewer audit, not as a claim that the ontology is final. "
            "Examples combine refined semantic-map terms with QA top-term counts."
        ),
    }

    summary_path = out_dir / "publication_outputs_summary_5d.json"
    write_json(summary, summary_path)
    summary["outputs"]["summary_json"] = str(summary_path)

    print(json.dumps({
        "status": "ok",
        "script_version": SCRIPT_VERSION,
        "n_semantic_families": int(len(definitions)),
        "n_top_terms_long_rows": int(len(top_terms_long)),
        "n_high_risk_terms": int(len(high_risk_pub)),
        "out_dir": str(out_dir),
        "table_09": str(table_paths["semantic_family_definitions_and_top_terms"]),
        "figure_07": str(figure_paths["semantic_family_content_heatmap"]),
        "summary_json": str(summary_path),
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
