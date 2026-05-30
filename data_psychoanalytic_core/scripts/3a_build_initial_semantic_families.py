#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3a_build_initial_semantic_families.py

Andromeda Nowicka v0.5-pre
Initial semantic family mapping for psychoanalytic_core title+abstract corpus.

Purpose
-------
This is the first Stage 3 script.

It builds an initial, auditable semantic family map from the final candidate
terms produced by Stage 2 and applies this map to the ART-only title+abstract
corpus.

It is NOT a final ontology and NOT final interpretation.

Inputs
------
1. Candidate vocabulary:
   ../data/title_abstract/keyness_final/psychoanalytic_core_discriminative_candidate_terms_final.csv

2. Clean title+abstract corpus:
   ../data/title_abstract/global/psychoanalytic_core_ART_title_abstract_clean.csv

Outputs
-------
../data/title_abstract/semantic/
    psychoanalytic_core_initial_semantic_map.csv
    psychoanalytic_core_initial_semantic_map_review_queue.csv
    psychoanalytic_core_unmapped_candidate_terms.csv
    psychoanalytic_core_article_semantic_hits_long.csv
    psychoanalytic_core_article_semantic_hits_wide.csv
    psychoanalytic_core_initial_semantic_family_counts.csv
    psychoanalytic_core_semantic_family_by_journal.csv
    psychoanalytic_core_semantic_family_by_period.csv
    psychoanalytic_core_semantic_family_by_journal_period.csv
    psychoanalytic_core_semantic_family_article_share_by_journal.csv
    psychoanalytic_core_semantic_family_article_share_by_period.csv
    psychoanalytic_core_initial_semantic_summary.json

Run
---
Put this file in:

    data_psychoanalytic_core/scripts/

Run:

    cd data_psychoanalytic_core/scripts
    python 3a_build_initial_semantic_families.py

Methodological note
-------------------
This script uses transparent lexical rules to assign candidate terms to initial
semantic families. It preserves confidence and review flags. Human review is
required before these families are treated as interpretive results.
"""

from __future__ import annotations

import argparse
import collections
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

# Rule format:
# family: list of (regex pattern, confidence, rule_note)
#
# Notes:
# - Patterns are intentionally transparent and editable.
# - They match candidate terms, not full article text at this stage.
# - Overlaps are allowed in review logic, but the initial map stores one primary
#   family unless ambiguity is detected.
# - Some terms can be historically polysemous; these get lower confidence or review flags.
SEMANTIC_RULES: Dict[str, List[Tuple[str, str, str]]] = {
    "drive_conflict_defense": [
        (r"\bdrive(s)?\b|\binstinct(s|ual)?\b|\blibido\b|\blibidinal\b", "high", "drive_libido_instinct"),
        (r"\bconflict(s)?\b|\bintrapsychic conflict\b", "high", "conflict_terms"),
        (r"\bdefen[sc]e(s)?\b|\brepression\b|\bresistance\b|\bdenial\b|\bsublimation\b", "high", "defense_repression_resistance"),
        (r"\baggression\b|\baggressive\b|\bhostility\b|\brage\b|\bdestructiveness\b", "medium", "aggression_terms"),
        (r"\boedip(al|us)?\b|\boedipus\b|\bcastration\b|\bincest\b", "high", "oedipal_complex_terms"),
    ],
    "dream_fantasy_unconscious": [
        (r"\bunconscious\b|\bpreconscious\b|\bsubconscious\b", "high", "unconscious_terms"),
        (r"\bdream(s|ing)?\b|\bnightmare(s)?\b", "high", "dream_terms"),
        (r"\bfantasy\b|\bfantasies\b|\bphantasy\b|\bphantasies\b", "high", "fantasy_phantasy_terms"),
        (r"\bwish(es)?\b|\bwish[- ]fulfillment\b", "medium", "wish_terms"),
        (r"\bpsychic reality\b", "high", "psychic_reality"),
    ],
    "ego_self_narcissism": [
        (r"\bego\b|\bid\b|\bsuperego\b|\bego[- ]ideal\b", "high", "structural_ego_terms"),
        (r"\bself\b|\bselfhood\b|\bself[- ]experience\b|\bself[- ]state(s)?\b|\bselfobject(s)?\b", "medium", "self_terms_polysemous"),
        (r"\bnarcissis(m|tic)\b|\bnarcissist(s)?\b", "high", "narcissism_terms"),
        (r"\bidentity\b|\bidentities\b|\bsubjectivity\b|\bsubjective\b", "medium", "identity_subjectivity_terms"),
        (r"\bshame\b|\bguilt\b", "medium", "self_affect_overlap"),
    ],
    "object_relations": [
        (r"\bobject(s)?\b|\bobject[- ]relations\b|\binternal object(s)?\b|\bexternal object(s)?\b", "high", "object_relations_terms"),
        (r"\bprojective identification\b|\bprojection\b|\bintrojection\b|\bintrojective\b", "high", "projective_introjective_terms"),
        (r"\bsplitting\b|\bparanoid[- ]schizoid\b|\bdepressive position\b", "high", "kleinian_object_relations_overlap"),
        (r"\binternal\b|\bexternal\b", "low", "broad_internal_external_review"),
    ],
    "kleinian_bionian": [
        (r"\bklein\b|\bkleinian\b|\bmelanie klein\b", "high", "kleinian_name_terms"),
        (r"\bbion\b|\bbionian\b|\bcontainer\b|\bcontained\b|\bcontainment\b|\bcontaining\b", "high", "bion_containment_terms"),
        (r"\bprojective identification\b|\bparanoid[- ]schizoid\b|\bdepressive position\b", "high", "kleinian_position_terms"),
        (r"\bbeta\b|\balpha function\b|\balpha-function\b|\breverie\b", "medium", "bion_specific_terms"),
    ],
    "winnicottian_environment_holding": [
        (r"\bwinnicott\b|\bwinnicottian\b", "high", "winnicott_name_terms"),
        (r"\bholding\b|\bholding environment\b|\bfacilitating environment\b", "high", "holding_environment_terms"),
        (r"\btransitional\b|\btransitional object(s)?\b|\bpotential space\b", "high", "transitional_space_terms"),
        (r"\bmother\b|\bmaternal\b|\bmothering\b|\benvironment\b|\bcaregiver(s)?\b", "medium", "maternal_environment_overlap"),
        (r"\bplay\b|\bplaying\b|\bcreativity\b|\bcreative\b", "medium", "play_creativity_terms"),
    ],
    "attachment_development_infant": [
        (r"\battachment\b|\bbowlby\b|\bsecure base\b|\bseparation\b|\bloss\b", "high", "attachment_terms"),
        (r"\binfant(s)?\b|\binfancy\b|\bbaby\b|\bbabies\b|\btoddler(s)?\b", "high", "infant_terms"),
        (r"\bchild\b|\bchildren\b|\bchildhood\b|\badolescent(s|ce)?\b|\badolescence\b", "medium", "child_adolescent_terms"),
        (r"\bdevelopment(al)?\b|\bdevelopmentally\b|\bearly\b|\bearly life\b", "medium", "development_terms"),
        (r"\bmother\b|\bmaternal\b|\bparent(s|al)?\b|\bfamily\b", "medium", "family_maternal_overlap"),
    ],
    "transference_countertransference": [
        (r"\btransference\b|\btransferential\b", "high", "transference_terms"),
        (r"\bcountertransference\b|\bcounter[- ]transference\b", "high", "countertransference_terms"),
        (r"\benactment(s)?\b|\breenactment(s)?\b", "high", "enactment_terms"),
        (r"\banalytic field\b|\bfield\b", "low", "field_overlap_review"),
    ],
    "technique_interpretation_process": [
        (r"\binterpretation(s)?\b|\binterpretive\b|\binterpreting\b", "high", "interpretation_terms"),
        (r"\btechnique(s)?\b|\btechnical\b|\bsetting\b|\bframe\b", "medium", "technique_setting_terms"),
        (r"\btermination\b|\bending\b|\bfrequency\b|\bsilence\b", "medium", "clinical_technique_terms"),
        (r"\btherapeutic action\b|\bworking through\b|\bworking-through\b", "high", "therapeutic_action_terms"),
        (r"\bfree association\b|\bassociation(s)?\b", "medium", "free_association_overlap"),
    ],
    "relational_intersubjective_field": [
        (r"\brelational\b|\brelationship(s)?\b|\binterpersonal\b", "high", "relational_terms"),
        (r"\bintersubjective\b|\bintersubjectivity\b|\bsubjectivities\b", "high", "intersubjective_terms"),
        (r"\bfield\b|\banalytic field\b|\bbi[- ]personal\b|\btwo[- ]person\b", "medium", "field_two_person_terms"),
        (r"\bmutual\b|\breciprocal\b|\bdialogue\b|\bdialogic\b|\bdialogical\b", "medium", "dialogue_mutuality_terms"),
        (r"\brecognition\b|\bthirdness\b|\bthird\b", "medium", "recognition_thirdness_terms"),
    ],
    "trauma_dissociation_affect_regulation": [
        (r"\btrauma\b|\btraumatic\b|\bpost[- ]traumatic\b|\bptsd\b", "high", "trauma_terms"),
        (r"\bdissociation\b|\bdissociative\b|\bdissociated\b", "high", "dissociation_terms"),
        (r"\baffect(s|ive)?\b|\bemotion(s|al)?\b|\bfeeling(s)?\b", "medium", "affect_emotion_terms"),
        (r"\bregulation\b|\bdysregulation\b|\baffect regulation\b", "high", "regulation_terms"),
        (r"\bshame\b|\bguilt\b|\bfear\b|\banxiety\b|\bterror\b", "medium", "affect_specific_terms"),
    ],
    "psychosis_borderline_primitive_states": [
        (r"\bpsychosis\b|\bpsychotic\b|\bschizophrenia\b|\bschizoid\b", "high", "psychosis_terms"),
        (r"\bborderline\b|\bborderline states?\b|\bborderline personality\b", "high", "borderline_terms"),
        (r"\bprimitive\b|\barchaic\b|\bearly states?\b|\bautistic\b", "medium", "primitive_early_state_terms"),
        (r"\bperversion\b|\bperverse\b|\bparanoid\b|\bmanic\b", "medium", "severe_pathology_terms"),
    ],
    "body_sexuality_gender": [
        (r"\bbody\b|\bbodily\b|\bsomatic\b|\bcorporeal\b|\bembod(ied|iment)\b", "high", "body_terms"),
        (r"\bsexual\b|\bsexuality\b|\bsex\b|\berotic\b|\beroticism\b", "high", "sexuality_terms"),
        (r"\bgender\b|\bfemininity\b|\bmasculinity\b|\bfemale\b|\bmale\b|\bqueer\b|\btransgender\b", "high", "gender_terms"),
        (r"\bhomosexuality\b|\bheterosexuality\b|\bbisexuality\b", "medium", "sexual_identity_terms"),
    ],
    "language_narrative_symbolization": [
        (r"\blanguage\b|\blinguistic\b|\bspeech\b|\bword(s)?\b|\bverbal\b", "high", "language_terms"),
        (r"\bnarrative(s)?\b|\bstory\b|\bstories\b|\btelling\b|\bretelling\b", "high", "narrative_terms"),
        (r"\bsymboli[sz]ation\b|\bsymboli[sz]ing\b|\bsymbolic\b|\bsymbol(s)?\b", "high", "symbolization_terms"),
        (r"\brepresentation(s)?\b|\brepresentational\b|\bmeaning\b|\bmetaphor(s)?\b", "medium", "representation_meaning_terms"),
    ],
    "culture_race_social_ethics": [
        (r"\bculture\b|\bcultural\b|\bsociety\b|\bsocial\b|\bpolitical\b", "medium", "culture_social_terms"),
        (r"\brace\b|\bracial\b|\bracism\b|\bethnic\b|\bethnicity\b|\bcolonial\b|\bpostcolonial\b", "high", "race_ethnicity_terms"),
        (r"\bethic(s|al)?\b|\bmoral\b|\bresponsibility\b|\bjustice\b", "medium", "ethics_terms"),
        (r"\bwar\b|\bviolence\b|\bholocaust\b|\bgenocide\b|\bmigration\b|\brefugee(s)?\b", "medium", "social_historical_trauma_overlap"),
    ],
    "empirical_research_measurement": [
        (r"\bempirical\b|\bresearch\b|\bstudy\b|\bdata\b|\bevidence\b", "medium", "empirical_terms"),
        (r"\bmeasure(s|ment)?\b|\bscale(s)?\b|\binstrument(s)?\b|\bassessment\b", "high", "measurement_terms"),
        (r"\bquantitative\b|\bqualitative\b|\bstatistical\b|\bmethod(s)?\b", "medium", "methods_terms"),
        (r"\boutcome(s)?\b|\befficacy\b|\beffectiveness\b|\brandomi[sz]ed\b", "high", "outcome_research_terms"),
    ],
    "history_theory_schools": [
        (r"\bfreud\b|\bfreudian\b|\bsigmund freud\b", "high", "freud_school_terms"),
        (r"\blacan\b|\blacanian\b|\bkohut\b|\bkohutian\b|\bfairbairn\b|\bferenczi\b|\bbalint\b", "high", "school_author_terms"),
        (r"\bclassical\b|\bego psychology\b|\bself psychology\b|\bobject relations\b", "medium", "school_terms"),
        (r"\bhistory\b|\bhistorical\b|\btradition\b|\bschool(s)?\b", "low", "broad_history_theory_review"),
    ],
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


def norm_term(term: str) -> str:
    t = str(term or "").strip().lower()
    t = t.replace("—", "-").replace("–", "-").replace("−", "-")
    t = re.sub(r"\s+", " ", t)
    return t.strip(" .;:,")


def pattern_matches(term: str, pattern: str) -> bool:
    return bool(re.search(pattern, norm_term(term), flags=re.I))


def map_term(term: str) -> Dict[str, object]:
    t = norm_term(term)
    matches = []

    for family in SEMANTIC_FAMILY_ORDER:
        for pattern, confidence, rule_note in SEMANTIC_RULES.get(family, []):
            if pattern_matches(t, pattern):
                matches.append({
                    "semantic_family": family,
                    "semantic_confidence": confidence,
                    "mapping_rule": rule_note,
                    "matched_pattern": pattern,
                })

    if not matches:
        return {
            "term": term,
            "term_norm": t,
            "semantic_family": "",
            "semantic_action": "unmapped",
            "semantic_confidence": "none",
            "mapping_rule": "",
            "matched_pattern": "",
            "n_family_matches": 0,
            "all_family_matches": "",
            "review_flag": "manual_review_unmapped",
            "manual_override_family": "",
            "manual_note": "",
        }

    # Prefer high confidence matches, then family order.
    confidence_rank = {"high": 3, "medium": 2, "low": 1, "none": 0}
    family_rank = {family: i for i, family in enumerate(SEMANTIC_FAMILY_ORDER)}

    matches_sorted = sorted(
        matches,
        key=lambda m: (
            -confidence_rank.get(str(m["semantic_confidence"]), 0),
            family_rank.get(str(m["semantic_family"]), 999),
        ),
    )
    primary = matches_sorted[0]
    unique_families = []
    for m in matches_sorted:
        f = m["semantic_family"]
        if f not in unique_families:
            unique_families.append(f)

    review_flag = ""
    if len(unique_families) > 1:
        review_flag = "manual_review_multiple_family_matches"
    elif primary["semantic_confidence"] == "low":
        review_flag = "manual_review_low_confidence"
    elif primary["semantic_confidence"] == "medium":
        review_flag = "optional_review_medium_confidence"

    return {
        "term": term,
        "term_norm": t,
        "semantic_family": primary["semantic_family"],
        "semantic_action": "mapped_initial",
        "semantic_confidence": primary["semantic_confidence"],
        "mapping_rule": primary["mapping_rule"],
        "matched_pattern": primary["matched_pattern"],
        "n_family_matches": len(unique_families),
        "all_family_matches": " | ".join(unique_families),
        "review_flag": review_flag,
        "manual_override_family": "",
        "manual_note": "",
    }


def build_semantic_map(candidate_df: pd.DataFrame) -> pd.DataFrame:
    if "term" not in candidate_df.columns:
        raise ValueError("Candidate file must contain a 'term' column.")

    terms = sorted({norm_term(t) for t in candidate_df["term"].dropna().astype(str) if norm_term(t)})
    rows = [map_term(t) for t in terms]

    sem_map = pd.DataFrame(rows)

    # Add candidate-source summary from candidate_df.
    work = candidate_df.copy()
    work["term_norm"] = work["term"].map(norm_term)

    source_cols = [c for c in ["source_table", "journal_key", "period", "keyness_score", "pct_point_lift", "doc_count", "doc_pct"] if c in work.columns]

    source_summary_rows = []
    for term, g in work.groupby("term_norm", dropna=False):
        item = {"term_norm": term}
        if "source_table" in g.columns:
            item["candidate_sources"] = " | ".join(sorted(set(g["source_table"].astype(str))))
        if "journal_key" in g.columns:
            vals = sorted({x for x in g["journal_key"].astype(str) if x})
            item["candidate_journals"] = " | ".join(vals)
        if "period" in g.columns:
            vals = sorted({x for x in g["period"].astype(str) if x})
            item["candidate_periods"] = " | ".join(vals)
        for numeric_col in ["keyness_score", "pct_point_lift", "doc_count", "doc_pct"]:
            if numeric_col in g.columns:
                numeric = pd.to_numeric(g[numeric_col], errors="coerce")
                item[f"max_{numeric_col}"] = round(float(numeric.max()), 6) if numeric.notna().any() else ""
        source_summary_rows.append(item)

    source_summary = pd.DataFrame(source_summary_rows)
    if not source_summary.empty:
        sem_map = sem_map.merge(source_summary, on="term_norm", how="left")

    return sem_map.fillna("")


def terms_for_family(sem_map: pd.DataFrame, family: str) -> List[str]:
    return sorted(set(sem_map.loc[sem_map["semantic_family"] == family, "term_norm"].astype(str)))


def term_regex(term: str) -> str:
    """
    Build a conservative word-boundary regex for a mapped term.
    Hyphen/space within multiword terms may vary.
    """
    t = norm_term(term)
    parts = re.split(r"[\s\-]+", t)
    escaped = [re.escape(p) for p in parts if p]
    if not escaped:
        return r"a^"
    if len(escaped) == 1:
        return r"\b" + escaped[0] + r"s?\b"
    return r"\b" + r"[\s\-]+".join(escaped) + r"\b"


def find_term_hits(text: str, terms: List[str]) -> List[str]:
    text_low = str(text or "").lower()
    hits = []
    for term in terms:
        pat = term_regex(term)
        if re.search(pat, text_low, flags=re.I):
            hits.append(term)
    return hits


def apply_semantic_map(articles: pd.DataFrame, sem_map: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    mapped = sem_map[sem_map["semantic_action"] == "mapped_initial"].copy()
    mapped = mapped[mapped["semantic_family"].astype(str).ne("")].copy()

    family_terms = {
        family: terms_for_family(mapped, family)
        for family in SEMANTIC_FAMILY_ORDER
    }
    family_terms = {k: v for k, v in family_terms.items() if v}

    rows_long = []
    rows_wide = []

    for idx, row in articles.iterrows():
        article_id = row.get("article_id", "")
        journal_key = row.get("journal_key", "")
        year = row.get("year_for_analysis", row.get("year", ""))
        period = row.get("period", "")
        title = row.get("title_clean", "")
        text = row.get("text_for_analysis", "")

        wide_item = {
            "article_id": article_id,
            "journal_key": journal_key,
            "year_for_analysis": year,
            "period": period,
            "title_clean": title,
        }

        total_hits = 0

        for family, terms in family_terms.items():
            hits = find_term_hits(text, terms)
            hit_count = len(hits)
            total_hits += hit_count

            wide_item[f"family_{family}"] = 1 if hit_count > 0 else 0
            wide_item[f"terms_{family}"] = " | ".join(hits)

            if hit_count > 0:
                rows_long.append({
                    "article_id": article_id,
                    "journal_key": journal_key,
                    "year_for_analysis": year,
                    "period": period,
                    "semantic_family": family,
                    "n_terms_hit": hit_count,
                    "terms_hit": " | ".join(hits),
                    "title_clean": title,
                })

        wide_item["n_semantic_families_hit"] = sum(
            1 for k, v in wide_item.items()
            if k.startswith("family_") and v == 1
        )
        wide_item["n_semantic_terms_hit"] = total_hits
        rows_wide.append(wide_item)

    long_df = pd.DataFrame(rows_long)
    wide_df = pd.DataFrame(rows_wide)
    return long_df, wide_df


def family_counts(long_df: pd.DataFrame, articles_n: int) -> pd.DataFrame:
    if long_df.empty:
        return pd.DataFrame(columns=["semantic_family", "n_articles", "pct_articles", "n_family_hits"])

    out = (
        long_df.groupby("semantic_family")
        .agg(
            n_articles=("article_id", "nunique"),
            n_family_hits=("article_id", "size"),
        )
        .reset_index()
    )
    out["pct_articles"] = (out["n_articles"] / max(articles_n, 1) * 100).round(4)
    out["_order"] = out["semantic_family"].map({f: i for i, f in enumerate(SEMANTIC_FAMILY_ORDER)}).fillna(999)
    return out.sort_values(["_order", "semantic_family"]).drop(columns=["_order"])


def family_by_group(long_df: pd.DataFrame, articles: pd.DataFrame, group_cols: List[str]) -> pd.DataFrame:
    if long_df.empty:
        return pd.DataFrame()

    article_denoms = (
        articles.groupby(group_cols, dropna=False)
        .agg(n_articles_group=("article_id", "nunique"))
        .reset_index()
    )

    counts = (
        long_df.groupby(group_cols + ["semantic_family"], dropna=False)
        .agg(
            n_articles=("article_id", "nunique"),
            n_family_hits=("article_id", "size"),
        )
        .reset_index()
    )

    out = counts.merge(article_denoms, on=group_cols, how="left")
    out["pct_articles_group"] = (out["n_articles"] / out["n_articles_group"].replace(0, pd.NA) * 100).round(4)
    out["_family_order"] = out["semantic_family"].map({f: i for i, f in enumerate(SEMANTIC_FAMILY_ORDER)}).fillna(999)
    return out.sort_values(group_cols + ["_family_order", "semantic_family"]).drop(columns=["_family_order"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Build initial semantic family map for psychoanalytic_core.")
    parser.add_argument(
        "--candidates",
        default="../data/title_abstract/keyness_final/psychoanalytic_core_discriminative_candidate_terms_final.csv",
        help="Final candidate terms from Stage 2.",
    )
    parser.add_argument(
        "--articles",
        default="../data/title_abstract/global/psychoanalytic_core_ART_title_abstract_clean.csv",
        help="Clean ART-only title+abstract corpus from 2a.",
    )
    parser.add_argument(
        "--out-dir",
        default="../data/title_abstract/semantic",
        help="Output directory.",
    )
    args = parser.parse_args()

    paths = get_paths()

    candidates_path = Path(args.candidates)
    if not candidates_path.is_absolute():
        candidates_path = (paths["scripts_dir"] / candidates_path).resolve()

    articles_path = Path(args.articles)
    if not articles_path.is_absolute():
        articles_path = (paths["scripts_dir"] / articles_path).resolve()

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = (paths["scripts_dir"] / out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not candidates_path.exists():
        raise SystemExit(f"ERROR: candidate file not found: {candidates_path}")
    if not articles_path.exists():
        raise SystemExit(f"ERROR: articles file not found: {articles_path}")

    candidate_df = read_csv_safe(candidates_path)
    articles = read_csv_safe(articles_path)

    if "article_id" not in articles.columns:
        # Fall back to row-based stable ID if needed.
        articles = articles.copy()
        articles["article_id"] = "row_" + articles.index.astype(str)

    required_article_cols = {"text_for_analysis", "journal_key", "period"}
    missing = required_article_cols - set(articles.columns)
    if missing:
        raise SystemExit(f"ERROR: articles file missing columns: {sorted(missing)}")

    sem_map = build_semantic_map(candidate_df)

    sem_map_path = out_dir / "psychoanalytic_core_initial_semantic_map.csv"
    write_csv(sem_map, sem_map_path)

    review_queue = sem_map[sem_map["review_flag"].astype(str).ne("")].copy()
    review_queue_path = out_dir / "psychoanalytic_core_initial_semantic_map_review_queue.csv"
    write_csv(review_queue, review_queue_path)

    unmapped = sem_map[sem_map["semantic_action"] == "unmapped"].copy()
    unmapped_path = out_dir / "psychoanalytic_core_unmapped_candidate_terms.csv"
    write_csv(unmapped, unmapped_path)

    long_df, wide_df = apply_semantic_map(articles, sem_map)

    long_path = out_dir / "psychoanalytic_core_article_semantic_hits_long.csv"
    wide_path = out_dir / "psychoanalytic_core_article_semantic_hits_wide.csv"
    write_csv(long_df, long_path)
    write_csv(wide_df, wide_path)

    counts = family_counts(long_df, articles_n=len(articles))
    counts_path = out_dir / "psychoanalytic_core_initial_semantic_family_counts.csv"
    write_csv(counts, counts_path)

    by_journal = family_by_group(long_df, articles, ["journal_key"])
    by_period = family_by_group(long_df, articles, ["period"])
    by_journal_period = family_by_group(long_df, articles, ["journal_key", "period"])

    by_journal_path = out_dir / "psychoanalytic_core_semantic_family_by_journal.csv"
    by_period_path = out_dir / "psychoanalytic_core_semantic_family_by_period.csv"
    by_journal_period_path = out_dir / "psychoanalytic_core_semantic_family_by_journal_period.csv"

    write_csv(by_journal, by_journal_path)
    write_csv(by_period, by_period_path)
    write_csv(by_journal_period, by_journal_period_path)

    # Convenience aliases, because these are article-share tables.
    by_journal_share_path = out_dir / "psychoanalytic_core_semantic_family_article_share_by_journal.csv"
    by_period_share_path = out_dir / "psychoanalytic_core_semantic_family_article_share_by_period.csv"
    write_csv(by_journal, by_journal_share_path)
    write_csv(by_period, by_period_share_path)

    mapped_n = int((sem_map["semantic_action"] == "mapped_initial").sum())
    unmapped_n = int((sem_map["semantic_action"] == "unmapped").sum())
    review_n = int(sem_map["review_flag"].astype(str).ne("").sum())
    articles_with_any_family = int((wide_df["n_semantic_families_hit"] > 0).sum()) if "n_semantic_families_hit" in wide_df.columns else 0

    family_map_counts = (
        sem_map[sem_map["semantic_family"].astype(str).ne("")]
        ["semantic_family"].value_counts()
        .to_dict()
    )

    summary = {
        "script_version": SCRIPT_VERSION,
        "created_at_utc": utc_now_iso(),
        "purpose": "Initial semantic family mapping of Stage 2 candidate vocabulary and article-level hit detection.",
        "inputs": {
            "candidate_terms": str(candidates_path),
            "clean_articles": str(articles_path),
        },
        "policy": {
            "final_ontology": False,
            "semantic_mapping_status": "initial_rule_based_mapping",
            "human_review_required": True,
            "manual_override_columns_included": True,
            "article_level_hits_are_lexical": True,
        },
        "candidate_terms": {
            "n_candidate_rows": int(len(candidate_df)),
            "n_unique_candidate_terms": int(candidate_df["term"].map(norm_term).nunique()) if "term" in candidate_df.columns else None,
            "n_mapped_terms": mapped_n,
            "n_unmapped_terms": unmapped_n,
            "n_terms_with_review_flag": review_n,
            "family_map_counts": {str(k): int(v) for k, v in family_map_counts.items()},
        },
        "articles": {
            "n_articles": int(len(articles)),
            "n_articles_with_any_semantic_family_hit": articles_with_any_family,
            "pct_articles_with_any_semantic_family_hit": round(articles_with_any_family / max(len(articles), 1) * 100, 4),
            "n_article_family_hit_rows": int(len(long_df)),
        },
        "outputs": {
            "initial_semantic_map": str(sem_map_path),
            "review_queue": str(review_queue_path),
            "unmapped_candidate_terms": str(unmapped_path),
            "article_semantic_hits_long": str(long_path),
            "article_semantic_hits_wide": str(wide_path),
            "family_counts": str(counts_path),
            "family_by_journal": str(by_journal_path),
            "family_by_period": str(by_period_path),
            "family_by_journal_period": str(by_journal_period_path),
            "family_article_share_by_journal": str(by_journal_share_path),
            "family_article_share_by_period": str(by_period_share_path),
        },
        "interpretive_warning": (
            "These are initial lexical semantic-family assignments. They should be used for QA, "
            "orientation, and human review, not as final interpretive findings."
        ),
    }

    summary_path = out_dir / "psychoanalytic_core_initial_semantic_summary.json"
    write_json(summary, summary_path)
    summary["outputs"]["summary_json"] = str(summary_path)

    print(json.dumps({
        "status": "ok",
        "script_version": SCRIPT_VERSION,
        "n_unique_candidate_terms": summary["candidate_terms"]["n_unique_candidate_terms"],
        "n_mapped_terms": mapped_n,
        "n_unmapped_terms": unmapped_n,
        "n_terms_with_review_flag": review_n,
        "n_articles": summary["articles"]["n_articles"],
        "n_articles_with_any_semantic_family_hit": articles_with_any_family,
        "pct_articles_with_any_semantic_family_hit": summary["articles"]["pct_articles_with_any_semantic_family_hit"],
        "summary_json": str(summary_path),
        "main_map": str(sem_map_path),
        "review_queue": str(review_queue_path),
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
