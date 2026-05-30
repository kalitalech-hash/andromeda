#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2d_refine_recon_vocabulary_audit.py

Andromeda Nowicka v0.5-pre
Second-pass audit/refinement of discriminative vocabulary reconnaissance.

Purpose
-------
After 2c_discriminative_vocabulary_recon.py, the term lists are cleaner than raw
frequency lists, but still contain non-informative words, metadata/affiliation
noise, personal names, and generic academic/discourse words.

This script creates another explicit audit layer. It does NOT overwrite 2c
outputs. It classifies terms and writes refined versions of the keyness tables.

Audit categories:
- candidate_concept
- background_domain_term
- generic_academic_language
- generic_discourse_language
- affiliation_or_metadata_noise
- personal_name_noise
- technical_artifact
- non_english_function_word

Main inputs
-----------
../data/title_abstract/keyness/psychoanalytic_core_global_core_terms_after_audit.csv
../data/title_abstract/keyness/psychoanalytic_core_global_core_bigrams_after_audit.csv
../data/title_abstract/keyness/psychoanalytic_core_key_terms_by_journal.csv
../data/title_abstract/keyness/psychoanalytic_core_key_bigrams_by_journal.csv
../data/title_abstract/keyness/psychoanalytic_core_key_terms_by_period.csv
../data/title_abstract/keyness/psychoanalytic_core_key_bigrams_by_period.csv
../data/title_abstract/keyness/psychoanalytic_core_key_terms_by_journal_period.csv
../data/title_abstract/keyness/psychoanalytic_core_key_bigrams_by_journal_period.csv
../data/title_abstract/keyness/psychoanalytic_core_discriminative_candidate_terms.csv

Outputs
-------
../data/title_abstract/keyness_refined/
    term_refinement_audit_map.csv
    term_refinement_excluded_terms.csv
    term_refinement_candidate_concepts.csv
    psychoanalytic_core_global_core_terms_refined.csv
    psychoanalytic_core_global_core_bigrams_refined.csv
    psychoanalytic_core_key_terms_by_journal_refined.csv
    psychoanalytic_core_key_bigrams_by_journal_refined.csv
    psychoanalytic_core_key_terms_by_period_refined.csv
    psychoanalytic_core_key_bigrams_by_period_refined.csv
    psychoanalytic_core_key_terms_by_journal_period_refined.csv
    psychoanalytic_core_key_bigrams_by_journal_period_refined.csv
    psychoanalytic_core_discriminative_candidate_terms_refined.csv
    psychoanalytic_core_discriminative_candidate_terms_audited.csv
    psychoanalytic_core_vocabulary_recon_v3_summary.json

Run
---
Put this file in:

    data_psychoanalytic_core/scripts/

Run:

    cd data_psychoanalytic_core/scripts
    python 2d_refine_recon_vocabulary_audit.py

Notes
-----
This is a conservative cleaning layer. It removes obvious non-analytic terms
from the candidate queues, but does not perform final semantic mapping.
Manual override columns are included for later human review.
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


# Terms that should not enter semantic concept mapping.
# This set is intentionally larger than in 2b/2c and reflects the first
# inspection of 2c outputs.
TECHNICAL_ARTIFACT_TERMS = {
    "runninghead", "running head", "running-head", "abstract", "keyword",
    "keywords", "copyright", "copyrighted", "authorized", "reproduction",
    "prohibited", "pep-web", "pepweb", "doi", "http", "https", "www",
}

AFFILIATION_METADATA_TERMS = {
    "university", "college", "institute", "department", "faculty", "school",
    "hospital", "clinic", "center", "centre", "foundation", "society",
    "association", "program", "programme", "division", "unit", "laboratory",
    "london", "york", "new-york", "chicago", "boston", "washington",
    "california", "san", "francisco", "angeles", "toronto", "paris", "berlin",
    "israel", "usa", "uk", "street", "avenue", "road", "suite", "west", "east",
    "north", "south", "email", "e-mail", "gmail", "com", "org", "edu",
    "professor", "phd", "md", "psyd", "dr",
}

PERSONAL_NAME_TERMS = {
    # Common author/figure first names and surnames that often appear as
    # citation/name noise. Some theoretically important names are intentionally
    # NOT excluded here: freud, klein, bion, winnicott, lacan, kohut, fairbairn.
    "john", "robert", "david", "michael", "james", "william", "richard",
    "charles", "thomas", "paul", "peter", "daniel", "donald", "stephen",
    "martin", "mark", "george", "joseph", "edward", "frank", "arthur",
    "anne", "anna", "mary", "susan", "jane", "elizabeth", "sarah", "nancy",
    "marion", "margaret", "jessica", "donna", "philip", "lewis", "alan",
}

GENERIC_ACADEMIC_TERMS = {
    "study", "studies", "research", "data", "findings", "method", "methods",
    "model", "models", "literature", "paper", "article", "articles", "author",
    "authors", "book", "books", "chapter", "chapters", "review", "reviews",
    "discussion", "discussions", "discuss", "discussed", "discusses",
    "present", "presents", "presented", "presentation", "examines", "examined",
    "explores", "explored", "describes", "described", "suggests", "suggested",
    "argues", "argued", "proposes", "proposed", "considers", "considered",
    "based", "example", "examples", "summary", "introduction", "conclusion",
    "conclusions", "hypothesis", "hypotheses", "result", "results",
    "empirical", "qualitative", "quantitative", "sample", "samples",
    "interview", "interviews", "questionnaire", "questionnaires",
}

GENERIC_DISCOURSE_TERMS = {
    "new", "between", "one", "two", "three", "first", "second", "third",
    "about", "other", "others", "also", "all", "both", "only", "same", "many",
    "much", "several", "various", "particular", "general", "specific",
    "important", "importance", "central", "significant", "major", "main",
    "different", "similar", "possible", "certain", "given", "rather",
    "further", "another", "however", "therefore", "thus", "although",
    "including", "include", "includes", "despite", "among", "toward",
    "towards", "concerning", "related", "time", "times", "life", "out", "own",
    "well", "way", "ways", "part", "role", "roles", "view", "views", "very",
    "made", "make", "making", "even", "must", "need", "needs", "needed",
    "point", "points", "place", "subject", "subjects", "problem", "problems",
    "question", "questions", "perspective", "perspectives", "approach",
    "approaches", "aspect", "aspects", "individual", "individuals", "become",
    "becomes", "later", "before", "seen", "special", "take", "takes", "taken",
    "know", "knowing", "whether", "especially", "good", "greater", "less",
    "more", "most", "within", "without", "over", "under", "again", "yet",
    "still", "long", "short", "high", "low", "large", "small", "open",
}

BACKGROUND_DOMAIN_TERMS = {
    "psychoanalytic", "psychoanalysis", "psychoanalytical", "analytic",
    "analysis", "analyses", "analyst", "analysts", "analysand", "analysands",
    "patient", "patients", "clinical", "clinician", "clinicians", "treatment",
    "treatments", "therapy", "therapies", "therapist", "therapists",
    "psychotherapy", "psychotherapies", "psychotherapeutic", "process",
    "processes", "session", "sessions", "practice", "practices", "theory",
    "theoretical", "conceptual", "concept", "concepts", "case", "cases",
    "material", "work", "working",
}

NON_ENGLISH_FUNCTION_TERMS = {
    "der", "die", "das", "des", "den", "dem", "und", "ein", "eine", "einer",
    "eines", "les", "des", "une", "pour", "avec", "sur", "dans", "del", "los",
    "las", "una", "para", "con", "por", "gli", "una", "uno", "della", "delle",
}

# Multiword patterns.
TECHNICAL_ARTIFACT_PATTERNS = [
    r"\brunning\s*-?\s*head\b",
    r"\bcopyright(ed)?\b",
    r"\bauthorized users?\b",
    r"\breproduction prohibited\b",
    r"\bpep[- ]?web\b",
    r"\bhttp(s)?\b",
    r"\bwww\b",
]

AFFILIATION_METADATA_PATTERNS = [
    r"\b(?:university|college|institute|department|faculty|school|hospital|center|centre)\b",
    r"\b(?:street|avenue|road|suite|gmail|e-mail|email|professor|phd|psyd|md)\b",
    r"\b(?:new york|san francisco|los angeles)\b",
]

GENERIC_ACADEMIC_PATTERNS = [
    r"^(?:study|studies|research|literature|paper|article|book|chapter|review)(?: .*)?$",
    r"^(?:present|presented|discussion|summary|introduction|conclusion)(?: .*)?$",
    r"^(?:based|using|method|methods|model|models)(?: .*)?$",
]

BACKGROUND_DOMAIN_PATTERNS = [
    r"^psychoanalytic (?:theory|practice|treatment|process|work|psychotherapy|clinical)$",
    r"^analytic (?:process|work|treatment|situation)$",
    r"^clinical (?:material|practice|work|process|situation|setting|settings)$",
    r"^(?:patient analyst|analyst patient)$",
]


# These are meaningful psychoanalytic names and should remain as candidate concepts.
PROTECTED_THEORETICAL_NAMES = {
    "freud", "freudian", "klein", "kleinian", "bion", "bionian", "winnicott",
    "winnicottian", "lacan", "lacanian", "kohut", "kohutian", "fairbairn",
    "ferenczi", "balint", "mahler", "kernberg", "ogden", "bowlby", "schafer",
    "orange", "laplanche", "andre", "andre green", "green",
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
        "keyness_root": title_root / "keyness",
        "out_root": title_root / "keyness_refined",
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
    term = str(term or "").strip().lower()
    term = term.replace("—", "-").replace("–", "-").replace("−", "-")
    term = re.sub(r"\s+", " ", term)
    term = term.strip(" .;:,")
    return term


def matches_any(term: str, patterns: Iterable[str]) -> bool:
    t = norm_term(term)
    return any(re.search(p, t, flags=re.I) for p in patterns)


def term_tokens(term: str) -> List[str]:
    return [x for x in re.split(r"\s+", norm_term(term)) if x]


def all_tokens_in(term: str, vocab: set[str]) -> bool:
    toks = term_tokens(term)
    return bool(toks) and all(t in vocab for t in toks)


def any_token_in(term: str, vocab: set[str]) -> bool:
    toks = term_tokens(term)
    return any(t in vocab for t in toks)


def classify_term(term: str) -> Tuple[str, str, bool]:
    """
    Returns:
        audit_category, audit_reason, include_in_semantic_review
    """
    t = norm_term(term)

    if not t:
        return "technical_artifact", "empty_term", False

    if t in PROTECTED_THEORETICAL_NAMES:
        return "candidate_concept", "protected_theoretical_name", True

    if t in TECHNICAL_ARTIFACT_TERMS or matches_any(t, TECHNICAL_ARTIFACT_PATTERNS):
        return "technical_artifact", "technical_artifact_rule", False

    if t in AFFILIATION_METADATA_TERMS or matches_any(t, AFFILIATION_METADATA_PATTERNS):
        return "affiliation_or_metadata_noise", "affiliation_metadata_rule", False

    if t in NON_ENGLISH_FUNCTION_TERMS or all_tokens_in(t, NON_ENGLISH_FUNCTION_TERMS):
        return "non_english_function_word", "non_english_function_word_rule", False

    if t in PERSONAL_NAME_TERMS:
        return "personal_name_noise", "personal_name_rule", False

    # For multiword terms composed only of generic discourse/academic/background
    # tokens, exclude them.
    if t in GENERIC_ACADEMIC_TERMS or matches_any(t, GENERIC_ACADEMIC_PATTERNS):
        return "generic_academic_language", "generic_academic_rule", False

    if t in GENERIC_DISCOURSE_TERMS or all_tokens_in(t, GENERIC_DISCOURSE_TERMS):
        return "generic_discourse_language", "generic_discourse_rule", False

    if t in BACKGROUND_DOMAIN_TERMS or matches_any(t, BACKGROUND_DOMAIN_PATTERNS):
        return "background_domain_term", "background_domain_rule", False

    if all_tokens_in(t, BACKGROUND_DOMAIN_TERMS | GENERIC_DISCOURSE_TERMS | GENERIC_ACADEMIC_TERMS):
        return "generic_discourse_language", "all_tokens_generic_or_background", False

    # Remove phrases contaminated by affiliation/metadata tokens.
    if any_token_in(t, AFFILIATION_METADATA_TERMS):
        return "affiliation_or_metadata_noise", "phrase_contains_affiliation_metadata", False

    return "candidate_concept", "kept_for_semantic_review", True


def audit_table(df: pd.DataFrame, source_table: str) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    if "term" not in df.columns:
        raise ValueError(f"{source_table} has no 'term' column.")

    out = df.copy()
    cls = out["term"].map(classify_term)
    out["term_norm_for_refinement"] = out["term"].map(norm_term)
    out["refined_audit_category"] = cls.map(lambda x: x[0])
    out["refined_audit_reason"] = cls.map(lambda x: x[1])
    out["include_in_refined_semantic_review"] = cls.map(lambda x: x[2])
    out["refinement_source_table"] = source_table
    out["manual_override"] = ""
    out["manual_override_note"] = ""
    return out


def filtered(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    return df[df["include_in_refined_semantic_review"].astype(bool)].copy()


def summarize(df: pd.DataFrame, label: str) -> Dict[str, object]:
    if df.empty:
        return {
            "table": label,
            "n_rows": 0,
            "n_unique_terms": 0,
            "n_included": 0,
            "n_excluded": 0,
            "category_counts": {},
        }
    counts = df["refined_audit_category"].value_counts(dropna=False).to_dict()
    include = df["include_in_refined_semantic_review"].astype(bool)
    return {
        "table": label,
        "n_rows": int(len(df)),
        "n_unique_terms": int(df["term_norm_for_refinement"].nunique()),
        "n_included": int(include.sum()),
        "n_excluded": int((~include).sum()),
        "category_counts": {str(k): int(v) for k, v in counts.items()},
    }


def build_audit_map(audited_tables: List[pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for df in audited_tables:
        if df.empty:
            continue
        cols = [
            "term_norm_for_refinement",
            "refined_audit_category",
            "refined_audit_reason",
            "include_in_refined_semantic_review",
        ]
        rows.append(df[cols].drop_duplicates())
    if not rows:
        return pd.DataFrame(columns=[
            "term_norm_for_refinement",
            "refined_audit_category",
            "refined_audit_reason",
            "include_in_refined_semantic_review",
            "manual_override",
            "manual_override_note",
        ])

    out = pd.concat(rows, ignore_index=True).drop_duplicates("term_norm_for_refinement", keep="first")
    out["manual_override"] = ""
    out["manual_override_note"] = ""
    return out.sort_values(["refined_audit_category", "term_norm_for_refinement"])


def load_tables(keyness_root: Path) -> Dict[str, Path]:
    return {
        "global_core_terms": keyness_root / "psychoanalytic_core_global_core_terms_after_audit.csv",
        "global_core_bigrams": keyness_root / "psychoanalytic_core_global_core_bigrams_after_audit.csv",
        "key_terms_by_journal": keyness_root / "psychoanalytic_core_key_terms_by_journal.csv",
        "key_bigrams_by_journal": keyness_root / "psychoanalytic_core_key_bigrams_by_journal.csv",
        "key_terms_by_period": keyness_root / "psychoanalytic_core_key_terms_by_period.csv",
        "key_bigrams_by_period": keyness_root / "psychoanalytic_core_key_bigrams_by_period.csv",
        "key_terms_by_journal_period": keyness_root / "psychoanalytic_core_key_terms_by_journal_period.csv",
        "key_bigrams_by_journal_period": keyness_root / "psychoanalytic_core_key_bigrams_by_journal_period.csv",
        "discriminative_candidate_terms": keyness_root / "psychoanalytic_core_discriminative_candidate_terms.csv",
    }


def output_name_for(table_name: str) -> str:
    mapping = {
        "global_core_terms": "psychoanalytic_core_global_core_terms_refined.csv",
        "global_core_bigrams": "psychoanalytic_core_global_core_bigrams_refined.csv",
        "key_terms_by_journal": "psychoanalytic_core_key_terms_by_journal_refined.csv",
        "key_bigrams_by_journal": "psychoanalytic_core_key_bigrams_by_journal_refined.csv",
        "key_terms_by_period": "psychoanalytic_core_key_terms_by_period_refined.csv",
        "key_bigrams_by_period": "psychoanalytic_core_key_bigrams_by_period_refined.csv",
        "key_terms_by_journal_period": "psychoanalytic_core_key_terms_by_journal_period_refined.csv",
        "key_bigrams_by_journal_period": "psychoanalytic_core_key_bigrams_by_journal_period_refined.csv",
        "discriminative_candidate_terms": "psychoanalytic_core_discriminative_candidate_terms_refined.csv",
    }
    return mapping[table_name]


def main() -> int:
    parser = argparse.ArgumentParser(description="Second-pass audit/refinement of 2c vocabulary reconnaissance.")
    parser.add_argument(
        "--keyness-root",
        default="../data/title_abstract/keyness",
        help="Input directory from 2c.",
    )
    parser.add_argument(
        "--out-dir",
        default="../data/title_abstract/keyness_refined",
        help="Output directory for refined tables.",
    )
    args = parser.parse_args()

    paths = get_paths()
    keyness_root = Path(args.keyness_root)
    if not keyness_root.is_absolute():
        keyness_root = (paths["scripts_dir"] / keyness_root).resolve()

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = (paths["scripts_dir"] / out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    table_paths = load_tables(keyness_root)

    audited_tables: Dict[str, pd.DataFrame] = {}
    refined_tables: Dict[str, pd.DataFrame] = {}
    table_summaries: List[Dict[str, object]] = []
    outputs: Dict[str, str] = {}

    for table_name, path in table_paths.items():
        df = read_csv_safe(path)
        if df.empty:
            audited = pd.DataFrame()
            refined = pd.DataFrame()
        else:
            audited = audit_table(df, table_name)
            refined = filtered(audited)

        audited_tables[table_name] = audited
        refined_tables[table_name] = refined
        table_summaries.append(summarize(audited, table_name))

        refined_path = out_dir / output_name_for(table_name)
        write_csv(refined, refined_path)
        outputs[table_name + "_refined"] = str(refined_path)

        # For the main candidate table, also write full audited version.
        if table_name == "discriminative_candidate_terms":
            audited_path = out_dir / "psychoanalytic_core_discriminative_candidate_terms_audited.csv"
            write_csv(audited, audited_path)
            outputs["discriminative_candidate_terms_audited"] = str(audited_path)

    audit_map = build_audit_map(list(audited_tables.values()))
    audit_map_path = out_dir / "term_refinement_audit_map.csv"
    write_csv(audit_map, audit_map_path)

    excluded = audit_map[~audit_map["include_in_refined_semantic_review"].astype(bool)].copy()
    included = audit_map[audit_map["include_in_refined_semantic_review"].astype(bool)].copy()

    excluded_path = out_dir / "term_refinement_excluded_terms.csv"
    included_path = out_dir / "term_refinement_candidate_concepts.csv"
    write_csv(excluded, excluded_path)
    write_csv(included, included_path)

    outputs["audit_map"] = str(audit_map_path)
    outputs["excluded_terms"] = str(excluded_path)
    outputs["candidate_concepts"] = str(included_path)

    global_candidate_count = 0
    if "discriminative_candidate_terms" in refined_tables:
        global_candidate_count = int(len(refined_tables["discriminative_candidate_terms"]))

    category_counts_total = {}
    if not audit_map.empty:
        category_counts_total = {
            str(k): int(v)
            for k, v in audit_map["refined_audit_category"].value_counts(dropna=False).to_dict().items()
        }

    summary = {
        "script_version": SCRIPT_VERSION,
        "created_at_utc": utc_now_iso(),
        "purpose": "Second-pass refinement of 2c vocabulary/keyness outputs.",
        "policy": {
            "source_tables_overwritten": False,
            "semantic_normalization_performed": False,
            "creates_audit_layer_only": True,
            "manual_override_columns_included": True,
        },
        "inputs": {k: str(v) for k, v in table_paths.items()},
        "outputs": outputs,
        "tables": table_summaries,
        "audit_map": {
            "n_unique_terms": int(len(audit_map)),
            "n_candidate_concepts": int(len(included)),
            "n_excluded_terms": int(len(excluded)),
            "category_counts": category_counts_total,
        },
        "main_next_file": outputs.get("discriminative_candidate_terms_refined", ""),
        "notes": {
            "runninghead": "technical_artifact",
            "gmail_faculty_professor_center": "affiliation_or_metadata_noise",
            "john_robert_david_michael": "personal_name_noise unless protected theoretical name",
            "freud_klein_bion_winnicott_lacan_kohut": "protected theoretical names kept as candidate concepts",
            "generic_words": "removed only from refined candidate queues, not from raw 2a/2c outputs",
        },
    }

    summary_path = out_dir / "psychoanalytic_core_vocabulary_recon_v3_summary.json"
    write_json(summary, summary_path)
    summary["outputs"]["summary_json"] = str(summary_path)

    print(json.dumps({
        "status": "ok",
        "script_version": SCRIPT_VERSION,
        "audit_map_unique_terms": summary["audit_map"]["n_unique_terms"],
        "candidate_concepts": summary["audit_map"]["n_candidate_concepts"],
        "excluded_terms": summary["audit_map"]["n_excluded_terms"],
        "refined_candidate_rows": global_candidate_count,
        "main_next_file": summary["main_next_file"],
        "summary_json": str(summary_path),
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
