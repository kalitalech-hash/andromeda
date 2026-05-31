#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3d_refine_semantic_map_marker_strength.py

Andromeda Nowicka v0.5-pre
Refine initial semantic map using marker strength.

Purpose
-------
After semantic family QA (3c), several broad terms were identified as inflating
semantic families when used alone, e.g.:

    self, object, mother, relationship, social, early, freud

These terms are not noise. They are psychoanalytically meaningful, but they
should not carry the same evidentiary weight as more specific terms such as:

    projective identification, countertransference, dissociation,
    transitional object, intersubjectivity, object relations

This script adds marker strength to the initial semantic map and reapplies it
to articles using a conservative rule:

    strong marker        -> full family hit
    medium marker        -> full family hit
    name_marker          -> name-only hit; reported separately
    weak marker alone    -> weak-only hit, not counted as full family hit
    2+ weak markers      -> provisional family hit
    weak + name marker   -> provisional family hit
    strong/medium + weak -> full family hit

It does not create a final ontology. It creates a refined diagnostic layer.

Inputs
------
Initial semantic map:
    ../data/title_abstract/semantic/psychoanalytic_core_initial_semantic_map.csv

QA refinement queue:
    ../data/title_abstract/semantic_QA/psychoanalytic_core_semantic_QA_map_refinement_queue.csv

Clean title+abstract corpus:
    ../data/title_abstract/global/psychoanalytic_core_ART_title_abstract_clean.csv

Outputs
-------
../data/title_abstract/semantic_refined/
    psychoanalytic_core_semantic_map_marker_strength.csv
    psychoanalytic_core_article_semantic_hits_long_refined.csv
    psychoanalytic_core_article_semantic_hits_wide_refined.csv
    psychoanalytic_core_semantic_family_counts_refined.csv
    psychoanalytic_core_semantic_family_by_journal_refined.csv
    psychoanalytic_core_semantic_family_by_period_refined.csv
    psychoanalytic_core_semantic_family_by_journal_period_refined.csv
    psychoanalytic_core_semantic_marker_strength_summary.json

Run
---
Put this file in:

    data_psychoanalytic_core/scripts/

Run:

    cd data_psychoanalytic_core/scripts
    python 3d_refine_semantic_map_marker_strength.py
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

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

# Family-specific weak markers identified by QA as broad or polysemous.
WEAK_MARKERS_BY_FAMILY = {
    "attachment_development_infant": {
        "early", "development", "developmental", "child", "children", "mother", "family",
    },
    "relational_intersubjective_field": {
        "relationship", "relationships", "field", "mutual", "dialogue",
    },
    "ego_self_narcissism": {
        "self", "identity", "subjectivity", "subjective",
    },
    "object_relations": {
        "object", "objects", "internal", "external",
    },
    "culture_race_social_ethics": {
        "social", "culture", "cultural", "society", "political", "responsibility",
    },
    "history_theory_schools": {
        "history", "historical", "tradition", "school", "schools", "classical",
    },
    "empirical_research_measurement": {
        "research", "study", "data", "method", "methods", "evidence",
    },
    "technique_interpretation_process": {
        "setting", "frame", "technical", "frequency",
    },
    "trauma_dissociation_affect_regulation": {
        "affect", "feeling", "feelings", "emotion", "emotional", "anxiety",
    },
}

# Names are analytically meaningful, but should be tracked separately because
# a single name can inflate a broad "history/schools" family.
NAME_MARKERS = {
    "freud", "freud's", "freudian",
    "klein", "kleinian",
    "bion", "bionian",
    "winnicott", "winnicottian",
    "lacan", "lacanian",
    "kohut", "kohutian",
    "fairbairn",
    "ferenczi",
    "bowlby",
    "balint",
    "mahler",
    "kernberg",
    "ogden",
    "schafer",
    "orange",
    "laplanche",
}

# Some phrase-level markers should be strong even if they contain a weak token.
STRONG_PHRASE_MARKERS = {
    "object relations",
    "internal object",
    "external object",
    "projective identification",
    "transitional object",
    "holding environment",
    "facilitating environment",
    "potential space",
    "affect regulation",
    "psychic reality",
    "therapeutic action",
    "free association",
    "working through",
    "depressive position",
    "paranoid-schizoid",
    "countertransference",
    "intersubjectivity",
    "intersubjective",
    "mentalization",
    "mentalisation",
    "dissociation",
    "dissociative",
    "trauma",
    "traumatic",
    "borderline",
    "psychosis",
    "psychotic",
    "narcissism",
    "narcissistic",
    "transference",
    "interpretation",
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
        "semantic_root": title_root / "semantic",
        "semantic_QA_root": title_root / "semantic_QA",
        "out_root": title_root / "semantic_refined",
        "global_root": title_root / "global",
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


def choose_col(df: pd.DataFrame, candidates: Iterable[str]) -> Optional[str]:
    lower = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c in df.columns:
            return c
        real = lower.get(c.lower())
        if real:
            return real
    return None


def norm_term(term: str) -> str:
    t = str(term or "").strip().lower()
    t = t.replace("—", "-").replace("–", "-").replace("−", "-")
    t = re.sub(r"\s+", " ", t)
    return t.strip(" .;:,")


def term_pattern(term: str) -> str:
    t = norm_term(term)
    if not t:
        return r"a^"
    # Handle possessive apostrophe in Freud's-like strings.
    t = t.replace("'s", "")
    parts = [p for p in re.split(r"[\s\-]+", t) if p]
    if not parts:
        return r"a^"
    escaped = [re.escape(p) for p in parts]
    if len(escaped) == 1:
        base = escaped[0]
        if base.endswith("s") or len(base) <= 3:
            return r"(?<![a-z])" + base + r"(?:'s)?(?![a-z])"
        return r"(?<![a-z])" + base + r"s?(?:'s)?(?![a-z])"
    return r"(?<![a-z])" + r"[\s\-]+".join(escaped) + r"(?![a-z])"


def infer_marker_strength(row: pd.Series, qa_terms: set[tuple[str, str]]) -> Tuple[str, str]:
    term = norm_term(row.get("term_norm", row.get("term", "")))
    family = str(row.get("semantic_family", "")).strip()
    confidence = str(row.get("semantic_confidence", "")).strip().lower()

    if not term or not family:
        return "unmapped", "not_mapped"

    if term in STRONG_PHRASE_MARKERS or " " in term and term in STRONG_PHRASE_MARKERS:
        return "strong", "protected_strong_phrase_marker"

    if term in NAME_MARKERS:
        return "name_marker", "theoretical_name_marker"

    if (family, term) in qa_terms:
        return "weak", "flagged_by_3c_QA_refinement_queue"

    if term in WEAK_MARKERS_BY_FAMILY.get(family, set()):
        return "weak", "family_specific_weak_marker_rule"

    if confidence == "high":
        return "strong", "high_confidence_initial_mapping"
    if confidence == "medium":
        return "medium", "medium_confidence_initial_mapping"
    if confidence == "low":
        return "weak", "low_confidence_initial_mapping"

    return "medium", "default_mapped_marker"


def build_marker_strength_map(sem_map: pd.DataFrame, qa_queue: pd.DataFrame) -> pd.DataFrame:
    out = sem_map.copy()

    if "term_norm" not in out.columns:
        out["term_norm"] = out["term"].map(norm_term)

    qa_terms: set[tuple[str, str]] = set()
    if not qa_queue.empty and {"semantic_family", "term"}.issubset(set(qa_queue.columns)):
        for _, r in qa_queue.iterrows():
            qa_terms.add((str(r.get("semantic_family", "")).strip(), norm_term(r.get("term", ""))))

    strengths = out.apply(lambda r: infer_marker_strength(r, qa_terms), axis=1)
    out["marker_strength"] = strengths.map(lambda x: x[0])
    out["marker_strength_reason"] = strengths.map(lambda x: x[1])

    out["counts_as_full_hit_when_alone"] = out["marker_strength"].isin(["strong", "medium"])
    out["counts_as_provisional_hit_when_combined"] = out["marker_strength"].isin(["weak", "name_marker"])
    out["manual_marker_override"] = ""
    out["manual_marker_note"] = ""

    return out


def build_family_terms(marker_map: pd.DataFrame) -> Dict[str, Dict[str, List[str]]]:
    mapped = marker_map.copy()
    mapped = mapped[mapped["semantic_action"].astype(str).eq("mapped_initial")]
    mapped = mapped[mapped["semantic_family"].astype(str).ne("")]
    mapped = mapped[mapped["term_norm"].astype(str).ne("")]

    family_terms: Dict[str, Dict[str, List[str]]] = {}
    for family in SEMANTIC_FAMILY_ORDER:
        g = mapped[mapped["semantic_family"] == family].copy()
        if g.empty:
            continue
        family_terms[family] = {}
        for strength in ["strong", "medium", "weak", "name_marker"]:
            terms = sorted(
                {norm_term(x) for x in g.loc[g["marker_strength"] == strength, "term_norm"].astype(str) if norm_term(x)},
                key=lambda x: (-len(x), x),
            )
            family_terms[family][strength] = terms
    return family_terms


def find_hits_by_terms(text: str, terms: List[str]) -> List[str]:
    text_low = str(text or "").lower()
    hits = []
    for term in terms:
        if re.search(term_pattern(term), text_low, flags=re.I):
            hits.append(term)
    return sorted(set(hits))


def classify_family_hit(strong_hits: List[str], medium_hits: List[str], weak_hits: List[str], name_hits: List[str]) -> Tuple[str, int]:
    """
    Returns hit_quality and full_hit flag.
    """
    if strong_hits:
        return "full_strong", 1
    if medium_hits:
        return "full_medium", 1
    if len(weak_hits) >= 2:
        return "provisional_multiple_weak", 1
    if weak_hits and name_hits:
        return "provisional_weak_plus_name", 1
    if name_hits and not weak_hits:
        return "name_only", 0
    if len(weak_hits) == 1:
        return "weak_only", 0
    return "no_hit", 0


def apply_refined_map(
    articles: pd.DataFrame,
    family_terms: Dict[str, Dict[str, List[str]]],
    text_col: str,
    article_id_col: str,
    journal_col: str,
    period_col: str,
    year_col: Optional[str],
    title_col: Optional[str],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    long_rows = []
    wide_rows = []

    for _, row in articles.iterrows():
        article_id = row.get(article_id_col, "")
        journal = row.get(journal_col, "")
        period = row.get(period_col, "")
        year = row.get(year_col, "") if year_col else ""
        title = row.get(title_col, "") if title_col else ""
        text = row.get(text_col, "")

        wide = {
            "article_id": article_id,
            "journal_key": journal,
            "year_for_analysis": year,
            "period": period,
            "title_clean": title,
        }

        n_full_or_provisional_families = 0
        n_any_families = 0
        n_weak_only_families = 0
        n_name_only_families = 0

        for family in SEMANTIC_FAMILY_ORDER:
            terms_by_strength = family_terms.get(family, {})
            strong_hits = find_hits_by_terms(text, terms_by_strength.get("strong", []))
            medium_hits = find_hits_by_terms(text, terms_by_strength.get("medium", []))
            weak_hits = find_hits_by_terms(text, terms_by_strength.get("weak", []))
            name_hits = find_hits_by_terms(text, terms_by_strength.get("name_marker", []))

            all_hits = sorted(set(strong_hits + medium_hits + weak_hits + name_hits))
            hit_quality, full_hit = classify_family_hit(strong_hits, medium_hits, weak_hits, name_hits)
            any_hit = 1 if all_hits else 0

            if full_hit:
                n_full_or_provisional_families += 1
            if any_hit:
                n_any_families += 1
            if hit_quality == "weak_only":
                n_weak_only_families += 1
            if hit_quality == "name_only":
                n_name_only_families += 1

            wide[f"family_{family}_refined"] = full_hit
            wide[f"family_{family}_any_marker"] = any_hit
            wide[f"family_{family}_hit_quality"] = hit_quality
            wide[f"terms_{family}_strong"] = " | ".join(strong_hits)
            wide[f"terms_{family}_medium"] = " | ".join(medium_hits)
            wide[f"terms_{family}_weak"] = " | ".join(weak_hits)
            wide[f"terms_{family}_name"] = " | ".join(name_hits)
            wide[f"terms_{family}_all"] = " | ".join(all_hits)

            if any_hit:
                long_rows.append({
                    "article_id": article_id,
                    "journal_key": journal,
                    "year_for_analysis": year,
                    "period": period,
                    "semantic_family": family,
                    "full_or_provisional_family_hit": full_hit,
                    "any_marker_hit": any_hit,
                    "hit_quality": hit_quality,
                    "n_strong_terms_hit": len(strong_hits),
                    "n_medium_terms_hit": len(medium_hits),
                    "n_weak_terms_hit": len(weak_hits),
                    "n_name_terms_hit": len(name_hits),
                    "terms_strong": " | ".join(strong_hits),
                    "terms_medium": " | ".join(medium_hits),
                    "terms_weak": " | ".join(weak_hits),
                    "terms_name": " | ".join(name_hits),
                    "terms_all": " | ".join(all_hits),
                    "title_clean": title,
                })

        wide["n_semantic_families_hit_refined"] = n_full_or_provisional_families
        wide["n_semantic_families_any_marker"] = n_any_families
        wide["n_weak_only_families"] = n_weak_only_families
        wide["n_name_only_families"] = n_name_only_families
        wide_rows.append(wide)

    return pd.DataFrame(long_rows), pd.DataFrame(wide_rows)


def family_counts_refined(long_df: pd.DataFrame, articles_n: int) -> pd.DataFrame:
    if long_df.empty:
        return pd.DataFrame()

    full = long_df[long_df["full_or_provisional_family_hit"] == 1].copy()
    anyhit = long_df[long_df["any_marker_hit"] == 1].copy()

    full_counts = (
        full.groupby("semantic_family", dropna=False)
        .agg(
            n_articles_refined=("article_id", "nunique"),
            n_family_hit_rows_refined=("article_id", "size"),
        )
        .reset_index()
    )

    any_counts = (
        anyhit.groupby("semantic_family", dropna=False)
        .agg(
            n_articles_any_marker=("article_id", "nunique"),
            n_any_marker_rows=("article_id", "size"),
            n_weak_only_rows=("hit_quality", lambda x: int((x == "weak_only").sum())),
            n_name_only_rows=("hit_quality", lambda x: int((x == "name_only").sum())),
        )
        .reset_index()
    )

    out = any_counts.merge(full_counts, on="semantic_family", how="left").fillna(0)
    out["n_articles_refined"] = out["n_articles_refined"].astype(int)
    out["n_family_hit_rows_refined"] = out["n_family_hit_rows_refined"].astype(int)
    out["pct_articles_refined"] = (out["n_articles_refined"] / max(articles_n, 1) * 100).round(4)
    out["pct_articles_any_marker"] = (out["n_articles_any_marker"] / max(articles_n, 1) * 100).round(4)
    out["_family_order"] = out["semantic_family"].map({f: i for i, f in enumerate(SEMANTIC_FAMILY_ORDER)}).fillna(999)
    return out.sort_values(["_family_order", "semantic_family"]).drop(columns=["_family_order"])


def family_by_group_refined(long_df: pd.DataFrame, articles_std: pd.DataFrame, group_cols: List[str]) -> pd.DataFrame:
    if long_df.empty:
        return pd.DataFrame()

    denoms = (
        articles_std.groupby(group_cols, dropna=False)
        .agg(n_articles_group=("article_id", "nunique"))
        .reset_index()
    )

    full = long_df[long_df["full_or_provisional_family_hit"] == 1].copy()

    counts = (
        full.groupby(group_cols + ["semantic_family"], dropna=False)
        .agg(
            n_articles_refined=("article_id", "nunique"),
            n_family_hit_rows_refined=("article_id", "size"),
        )
        .reset_index()
    )

    out = counts.merge(denoms, on=group_cols, how="left")
    out["pct_articles_group_refined"] = (out["n_articles_refined"] / out["n_articles_group"].replace(0, pd.NA) * 100).round(4)
    out["_family_order"] = out["semantic_family"].map({f: i for i, f in enumerate(SEMANTIC_FAMILY_ORDER)}).fillna(999)
    return out.sort_values(group_cols + ["_family_order", "semantic_family"]).drop(columns=["_family_order"])


def marker_strength_summary(marker_map: pd.DataFrame) -> pd.DataFrame:
    if marker_map.empty:
        return pd.DataFrame()

    mapped = marker_map[marker_map["semantic_action"].astype(str).eq("mapped_initial")].copy()
    return (
        mapped.groupby(["semantic_family", "marker_strength"], dropna=False)
        .agg(n_terms=("term_norm", "nunique"))
        .reset_index()
        .sort_values(["semantic_family", "marker_strength"])
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Refine semantic map with marker strength and reapply to articles.")
    parser.add_argument(
        "--semantic-map",
        default="../data/title_abstract/semantic/psychoanalytic_core_initial_semantic_map.csv",
    )
    parser.add_argument(
        "--qa-refinement-queue",
        default="../data/title_abstract/semantic_QA/psychoanalytic_core_semantic_QA_map_refinement_queue.csv",
    )
    parser.add_argument(
        "--articles",
        default="../data/title_abstract/global/psychoanalytic_core_ART_title_abstract_clean.csv",
    )
    parser.add_argument(
        "--out-dir",
        default="../data/title_abstract/semantic_refined",
    )
    args = parser.parse_args()

    paths = get_paths()

    def resolve(p: str) -> Path:
        path = Path(p)
        if not path.is_absolute():
            path = (paths["scripts_dir"] / path).resolve()
        return path

    sem_map_path = resolve(args.semantic_map)
    qa_queue_path = resolve(args.qa_refinement_queue)
    articles_path = resolve(args.articles)
    out_dir = resolve(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if not sem_map_path.exists():
        raise SystemExit(f"ERROR: semantic map not found: {sem_map_path}")
    if not articles_path.exists():
        raise SystemExit(f"ERROR: articles file not found: {articles_path}")

    sem_map = read_csv_safe(sem_map_path)
    qa_queue = read_csv_safe(qa_queue_path)
    articles = read_csv_safe(articles_path)

    text_col = choose_col(articles, ["text_for_analysis", "abstract_clean", "title_clean"])
    article_id_col = choose_col(articles, ["article_id", "document_id", "pep_document_id", "id"])
    journal_col = choose_col(articles, ["journal_key", "journal"])
    period_col = choose_col(articles, ["period", "analysis_period"])
    year_col = choose_col(articles, ["year_for_analysis", "year", "year_record", "publication_year"])
    title_col = choose_col(articles, ["title_clean", "title", "article_title"])

    if text_col is None:
        raise SystemExit("ERROR: no text column found.")
    if article_id_col is None:
        articles = articles.copy()
        articles["article_id"] = "row_" + articles.index.astype(str)
        article_id_col = "article_id"
    if journal_col is None:
        raise SystemExit("ERROR: no journal column found.")
    if period_col is None:
        raise SystemExit("ERROR: no period column found.")

    articles_std = articles.copy()
    if article_id_col != "article_id":
        articles_std["article_id"] = articles_std[article_id_col]
    if journal_col != "journal_key":
        articles_std["journal_key"] = articles_std[journal_col]
    if period_col != "period":
        articles_std["period"] = articles_std[period_col]

    marker_map = build_marker_strength_map(sem_map, qa_queue)
    marker_map_path = out_dir / "psychoanalytic_core_semantic_map_marker_strength.csv"
    write_csv(marker_map, marker_map_path)

    marker_summary = marker_strength_summary(marker_map)
    marker_summary_path = out_dir / "psychoanalytic_core_marker_strength_by_family.csv"
    write_csv(marker_summary, marker_summary_path)

    family_terms = build_family_terms(marker_map)

    long_df, wide_df = apply_refined_map(
        articles=articles,
        family_terms=family_terms,
        text_col=text_col,
        article_id_col=article_id_col,
        journal_col=journal_col,
        period_col=period_col,
        year_col=year_col,
        title_col=title_col,
    )

    long_path = out_dir / "psychoanalytic_core_article_semantic_hits_long_refined.csv"
    wide_path = out_dir / "psychoanalytic_core_article_semantic_hits_wide_refined.csv"
    write_csv(long_df, long_path)
    write_csv(wide_df, wide_path)

    counts = family_counts_refined(long_df, len(articles))
    counts_path = out_dir / "psychoanalytic_core_semantic_family_counts_refined.csv"
    write_csv(counts, counts_path)

    by_journal = family_by_group_refined(long_df, articles_std, ["journal_key"])
    by_period = family_by_group_refined(long_df, articles_std, ["period"])
    by_journal_period = family_by_group_refined(long_df, articles_std, ["journal_key", "period"])

    by_journal_path = out_dir / "psychoanalytic_core_semantic_family_by_journal_refined.csv"
    by_period_path = out_dir / "psychoanalytic_core_semantic_family_by_period_refined.csv"
    by_journal_period_path = out_dir / "psychoanalytic_core_semantic_family_by_journal_period_refined.csv"

    write_csv(by_journal, by_journal_path)
    write_csv(by_period, by_period_path)
    write_csv(by_journal_period, by_journal_period_path)

    n_articles = len(articles)
    n_refined = int((wide_df["n_semantic_families_hit_refined"] > 0).sum()) if "n_semantic_families_hit_refined" in wide_df.columns else 0
    n_any = int((wide_df["n_semantic_families_any_marker"] > 0).sum()) if "n_semantic_families_any_marker" in wide_df.columns else 0
    n_weak_only_articles = int((wide_df["n_weak_only_families"] > 0).sum()) if "n_weak_only_families" in wide_df.columns else 0
    n_name_only_articles = int((wide_df["n_name_only_families"] > 0).sum()) if "n_name_only_families" in wide_df.columns else 0

    marker_counts = marker_map["marker_strength"].value_counts(dropna=False).to_dict()

    summary = {
        "script_version": SCRIPT_VERSION,
        "created_at_utc": utc_now_iso(),
        "purpose": "Refine initial semantic map using marker strength and reapply to articles.",
        "inputs": {
            "semantic_map": str(sem_map_path),
            "qa_refinement_queue": str(qa_queue_path),
            "articles": str(articles_path),
        },
        "policy": {
            "final_ontology": False,
            "weak_marker_alone_counts_as_full_hit": False,
            "two_or_more_weak_markers_count_as_provisional_hit": True,
            "name_marker_alone_counts_as_full_hit": False,
            "name_marker_reported_separately": True,
            "human_review_required": True,
        },
        "marker_map": {
            "n_total_rows": int(len(marker_map)),
            "marker_strength_counts": {str(k): int(v) for k, v in marker_counts.items()},
        },
        "articles": {
            "n_articles": int(n_articles),
            "n_articles_with_refined_semantic_family_hit": n_refined,
            "pct_articles_with_refined_semantic_family_hit": round(n_refined / max(n_articles, 1) * 100, 4),
            "n_articles_with_any_marker_hit": n_any,
            "pct_articles_with_any_marker_hit": round(n_any / max(n_articles, 1) * 100, 4),
            "n_articles_with_weak_only_family": n_weak_only_articles,
            "n_articles_with_name_only_family": n_name_only_articles,
            "n_article_family_rows_any_marker": int(len(long_df)),
            "mean_refined_families_per_article": round(float(wide_df["n_semantic_families_hit_refined"].mean()), 4) if "n_semantic_families_hit_refined" in wide_df.columns else 0.0,
            "median_refined_families_per_article": float(wide_df["n_semantic_families_hit_refined"].median()) if "n_semantic_families_hit_refined" in wide_df.columns else 0.0,
        },
        "outputs": {
            "semantic_map_marker_strength": str(marker_map_path),
            "marker_strength_by_family": str(marker_summary_path),
            "article_semantic_hits_long_refined": str(long_path),
            "article_semantic_hits_wide_refined": str(wide_path),
            "family_counts_refined": str(counts_path),
            "family_by_journal_refined": str(by_journal_path),
            "family_by_period_refined": str(by_period_path),
            "family_by_journal_period_refined": str(by_journal_period_path),
        },
        "interpretive_warning": (
            "Refined hits are still lexical and based on a provisional marker-strength model. "
            "They should be used for QA and orientation, not final claims."
        ),
    }

    summary_path = out_dir / "psychoanalytic_core_semantic_marker_strength_summary.json"
    write_json(summary, summary_path)
    summary["outputs"]["summary_json"] = str(summary_path)

    print(json.dumps({
        "status": "ok",
        "script_version": SCRIPT_VERSION,
        "n_articles": n_articles,
        "n_articles_with_refined_semantic_family_hit": n_refined,
        "pct_articles_with_refined_semantic_family_hit": summary["articles"]["pct_articles_with_refined_semantic_family_hit"],
        "n_articles_with_any_marker_hit": n_any,
        "pct_articles_with_any_marker_hit": summary["articles"]["pct_articles_with_any_marker_hit"],
        "marker_strength_counts": summary["marker_map"]["marker_strength_counts"],
        "summary_json": str(summary_path),
        "family_counts_refined": str(counts_path),
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
