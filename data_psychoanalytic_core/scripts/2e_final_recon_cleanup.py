#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2e_final_recon_cleanup.py

Andromeda Nowicka v0.5-pre
Final light cleanup of refined title+abstract vocabulary reconnaissance.

Purpose
-------
After 2d_refine_recon_vocabulary_audit.py, the candidate vocabulary is usable,
but may still contain residual generic/discourse/function terms such as:

    time, following, after, himself, since

This script performs a final, conservative cleanup pass on the already refined
tables. It does NOT recompute keyness and does NOT overwrite 2d outputs.

It creates a new final layer:

    data/title_abstract/keyness_final/

Main input directory:
    data/title_abstract/keyness_refined/

Main output for next semantic stage:
    data/title_abstract/keyness_final/
    psychoanalytic_core_discriminative_candidate_terms_final.csv

Run
---
Put this file in:

    data_psychoanalytic_core/scripts/

Run:

    cd data_psychoanalytic_core/scripts
    python 2e_final_recon_cleanup.py
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import pandas as pd


SCRIPT_VERSION = "v0.1.0"


FINAL_STOP_TERMS = {
    # Explicitly observed residual noise after 2d
    "time", "times", "following", "after", "before", "since", "himself",
    "herself", "itself", "themselves", "ourselves", "myself", "yourself",

    # temporal/deictic/generic connective terms
    "then", "now", "next", "previous", "prior", "subsequent", "earlier",
    "later", "recent", "currently", "formerly", "always", "never", "often",
    "sometimes", "usually", "generally", "finally", "last", "past", "future",
    "present", "presently",

    # generic stance and argument words
    "following", "above", "below", "thereby", "therefore", "whereas",
    "whereby", "wherein", "moreover", "nevertheless", "nonetheless",
    "furthermore", "hence", "thus", "indeed", "however", "although",
    "because", "since", "unless", "whether",

    # residual generic discourse words
    "issue", "issues", "concern", "concerns", "matter", "matters",
    "theme", "themes", "topic", "topics", "area", "areas", "field", "fields",
    "level", "levels", "form", "forms", "kind", "kinds", "type", "types",
    "range", "ranges", "number", "numbers", "group", "groups", "member",
    "members", "factor", "factors", "element", "elements", "relation",
    "relations",  # keep relationship/relationships, but relation/relations are often generic
    "context", "contexts", "condition", "conditions",

    # residual verbs/adjectives as nominal-looking tokens
    "shown", "shows", "showing", "known", "called", "taken", "given",
    "found", "made", "seen", "noted", "noting", "suggesting", "considering",
    "understood", "defined", "described", "presenting", "arguing",
    "exploring", "examining", "developed", "developing",

    # residual function-like terms
    "where", "whose", "whom", "whilst", "amongst", "around", "across",
    "beyond", "towards", "upon", "via", "per", "etc",

    # residual generic quality terms
    "complex", "complexity", "central", "important", "significant",
    "specific", "particular", "general", "common", "basic", "primary",
    "secondary", "multiple", "variety", "varieties", "various",
}

# Remove phrases that are entirely composed of final stop terms and already
# generic terms. This prevents bigrams such as "following paper" or "after all"
# from surviving if present.
FINAL_STOP_PATTERNS = [
    r"^(?:after|before|since|following|during|within|without|between) ",
    r" (?:after|before|since|following|during|within|without|between)$",
    r"^(?:time|times|issue|issues|context|contexts|field|fields) ",
    r" (?:time|times|issue|issues|context|contexts|field|fields)$",
]

# Terms that should stay even though they may be close to generic language.
PROTECTED_TERMS = {
    "object", "objects", "object relations", "self", "ego", "id", "superego",
    "unconscious", "preconscious", "transference", "countertransference",
    "interpretation", "dream", "dreams", "fantasy", "phantasy", "defense",
    "defence", "resistance", "conflict", "anxiety", "trauma", "traumatic",
    "attachment", "mother", "maternal", "infant", "child", "children",
    "body", "sexual", "sexuality", "gender", "race", "culture", "relational",
    "intersubjective", "intersubjectivity", "mentalization", "mentalisation",
    "symbolization", "symbolisation", "representation", "narcissism",
    "narcissistic", "borderline", "psychosis", "psychotic", "depression",
    "depressive", "mourning", "melancholia", "grief", "shame", "guilt",
    "aggression", "aggressive", "love", "hate", "death", "desire",
    "reality", "psychic reality", "mind", "mental", "personality",
    "relationship", "relationships", "developmental", "early", "internal",
    "external", "subjectivity", "identity", "language", "narrative",
    "meaning", "ethics", "ethical",
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
        "input_root": title_root / "keyness_refined",
        "out_root": title_root / "keyness_final",
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


def term_tokens(term: str) -> List[str]:
    return [x for x in re.split(r"\s+", norm_term(term)) if x]


def all_tokens_stop(term: str) -> bool:
    toks = term_tokens(term)
    return bool(toks) and all(t in FINAL_STOP_TERMS for t in toks)


def matches_stop_pattern(term: str) -> bool:
    t = norm_term(term)
    return any(re.search(p, t, flags=re.I) for p in FINAL_STOP_PATTERNS)


def classify_final(term: str) -> Tuple[str, str, bool]:
    t = norm_term(term)

    if not t:
        return "final_exclude", "empty_term", False

    if t in PROTECTED_TERMS:
        return "final_keep", "protected_psychoanalytic_term", True

    if t in FINAL_STOP_TERMS:
        return "final_exclude", "final_stop_term", False

    if all_tokens_stop(t):
        return "final_exclude", "all_tokens_final_stop_terms", False

    if matches_stop_pattern(t):
        return "final_exclude", "final_stop_pattern", False

    return "final_keep", "kept_after_final_cleanup", True


def audit_and_filter(df: pd.DataFrame, source_table: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
    if df.empty:
        return df.copy(), df.copy()

    if "term" not in df.columns:
        return df.copy(), df.copy()

    out = df.copy()
    cls = out["term"].map(classify_final)
    out["term_norm_final_cleanup"] = out["term"].map(norm_term)
    out["final_cleanup_category"] = cls.map(lambda x: x[0])
    out["final_cleanup_reason"] = cls.map(lambda x: x[1])
    out["include_in_final_semantic_review"] = cls.map(lambda x: x[2])
    out["final_cleanup_source_table"] = source_table
    out["manual_override"] = ""
    out["manual_override_note"] = ""

    filtered = out[out["include_in_final_semantic_review"].astype(bool)].copy()
    return out, filtered


def input_tables(input_root: Path) -> Dict[str, Path]:
    return {
        "global_core_terms": input_root / "psychoanalytic_core_global_core_terms_refined.csv",
        "global_core_bigrams": input_root / "psychoanalytic_core_global_core_bigrams_refined.csv",
        "key_terms_by_journal": input_root / "psychoanalytic_core_key_terms_by_journal_refined.csv",
        "key_bigrams_by_journal": input_root / "psychoanalytic_core_key_bigrams_by_journal_refined.csv",
        "key_terms_by_period": input_root / "psychoanalytic_core_key_terms_by_period_refined.csv",
        "key_bigrams_by_period": input_root / "psychoanalytic_core_key_bigrams_by_period_refined.csv",
        "key_terms_by_journal_period": input_root / "psychoanalytic_core_key_terms_by_journal_period_refined.csv",
        "key_bigrams_by_journal_period": input_root / "psychoanalytic_core_key_bigrams_by_journal_period_refined.csv",
        "discriminative_candidate_terms": input_root / "psychoanalytic_core_discriminative_candidate_terms_refined.csv",
    }


def final_output_name(table_name: str) -> str:
    return {
        "global_core_terms": "psychoanalytic_core_global_core_terms_final.csv",
        "global_core_bigrams": "psychoanalytic_core_global_core_bigrams_final.csv",
        "key_terms_by_journal": "psychoanalytic_core_key_terms_by_journal_final.csv",
        "key_bigrams_by_journal": "psychoanalytic_core_key_bigrams_by_journal_final.csv",
        "key_terms_by_period": "psychoanalytic_core_key_terms_by_period_final.csv",
        "key_bigrams_by_period": "psychoanalytic_core_key_bigrams_by_period_final.csv",
        "key_terms_by_journal_period": "psychoanalytic_core_key_terms_by_journal_period_final.csv",
        "key_bigrams_by_journal_period": "psychoanalytic_core_key_bigrams_by_journal_period_final.csv",
        "discriminative_candidate_terms": "psychoanalytic_core_discriminative_candidate_terms_final.csv",
    }[table_name]


def summarize(audited: pd.DataFrame, table_name: str) -> Dict[str, object]:
    if audited.empty or "include_in_final_semantic_review" not in audited.columns:
        return {
            "table": table_name,
            "n_rows": int(len(audited)),
            "n_kept": int(len(audited)),
            "n_removed": 0,
            "category_counts": {},
        }

    keep = audited["include_in_final_semantic_review"].astype(bool)
    return {
        "table": table_name,
        "n_rows": int(len(audited)),
        "n_kept": int(keep.sum()),
        "n_removed": int((~keep).sum()),
        "category_counts": {
            str(k): int(v)
            for k, v in audited["final_cleanup_category"].value_counts(dropna=False).to_dict().items()
        },
    }


def build_final_audit_map(audited_tables: List[pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for df in audited_tables:
        if df.empty or "term_norm_final_cleanup" not in df.columns:
            continue
        rows.append(
            df[
                [
                    "term_norm_final_cleanup",
                    "final_cleanup_category",
                    "final_cleanup_reason",
                    "include_in_final_semantic_review",
                ]
            ].drop_duplicates()
        )
    if not rows:
        return pd.DataFrame()

    out = pd.concat(rows, ignore_index=True)
    out = out.drop_duplicates("term_norm_final_cleanup", keep="first")
    out["manual_override"] = ""
    out["manual_override_note"] = ""
    return out.sort_values(["final_cleanup_category", "term_norm_final_cleanup"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Final cleanup of refined keyness vocabulary.")
    parser.add_argument(
        "--input-root",
        default="../data/title_abstract/keyness_refined",
        help="Input directory from 2d.",
    )
    parser.add_argument(
        "--out-dir",
        default="../data/title_abstract/keyness_final",
        help="Output directory for final cleaned vocabulary tables.",
    )
    args = parser.parse_args()

    paths = get_paths()

    input_root = Path(args.input_root)
    if not input_root.is_absolute():
        input_root = (paths["scripts_dir"] / input_root).resolve()

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = (paths["scripts_dir"] / out_dir).resolve()

    out_dir.mkdir(parents=True, exist_ok=True)

    table_paths = input_tables(input_root)

    outputs = {}
    table_summaries = []
    audited_tables = []

    for table_name, path in table_paths.items():
        df = read_csv_safe(path)
        audited, final = audit_and_filter(df, table_name)

        final_path = out_dir / final_output_name(table_name)
        write_csv(final, final_path)
        outputs[table_name + "_final"] = str(final_path)

        if table_name == "discriminative_candidate_terms":
            audited_path = out_dir / "psychoanalytic_core_discriminative_candidate_terms_final_audited.csv"
            write_csv(audited, audited_path)
            outputs["discriminative_candidate_terms_final_audited"] = str(audited_path)

        audited_tables.append(audited)
        table_summaries.append(summarize(audited, table_name))

    audit_map = build_final_audit_map(audited_tables)
    audit_map_path = out_dir / "term_final_cleanup_audit_map.csv"
    write_csv(audit_map, audit_map_path)
    outputs["final_cleanup_audit_map"] = str(audit_map_path)

    removed = audit_map[~audit_map["include_in_final_semantic_review"].astype(bool)].copy() if not audit_map.empty else pd.DataFrame()
    kept = audit_map[audit_map["include_in_final_semantic_review"].astype(bool)].copy() if not audit_map.empty else pd.DataFrame()

    removed_path = out_dir / "term_final_cleanup_removed_terms.csv"
    kept_path = out_dir / "term_final_cleanup_candidate_terms.csv"
    write_csv(removed, removed_path)
    write_csv(kept, kept_path)
    outputs["removed_terms"] = str(removed_path)
    outputs["candidate_terms"] = str(kept_path)

    main_next_file = outputs.get("discriminative_candidate_terms_final", "")

    summary = {
        "script_version": SCRIPT_VERSION,
        "created_at_utc": utc_now_iso(),
        "purpose": "Final light cleanup of residual generic/function terms after 2d.",
        "policy": {
            "source_tables_overwritten": False,
            "semantic_normalization_performed": False,
            "creates_final_recon_layer": True,
            "manual_override_columns_included": True,
        },
        "inputs": {k: str(v) for k, v in table_paths.items()},
        "outputs": outputs,
        "tables": table_summaries,
        "audit_map": {
            "n_unique_terms": int(len(audit_map)),
            "n_kept_terms": int(len(kept)),
            "n_removed_terms": int(len(removed)),
            "category_counts": {
                str(k): int(v)
                for k, v in audit_map["final_cleanup_category"].value_counts(dropna=False).to_dict().items()
            } if not audit_map.empty else {},
        },
        "explicitly_targeted_residual_terms": [
            "time", "following", "after", "himself", "since",
        ],
        "main_next_file": main_next_file,
        "interpretive_note": (
            "This is still reconnaissance cleanup, not final semantic ontology construction. "
            "The output is a cleaner candidate queue for human-led semantic family mapping."
        ),
    }

    summary_path = out_dir / "psychoanalytic_core_vocabulary_recon_v4_summary.json"
    write_json(summary, summary_path)
    summary["outputs"]["summary_json"] = str(summary_path)

    print(json.dumps({
        "status": "ok",
        "script_version": SCRIPT_VERSION,
        "audit_map_unique_terms": summary["audit_map"]["n_unique_terms"],
        "kept_terms": summary["audit_map"]["n_kept_terms"],
        "removed_terms": summary["audit_map"]["n_removed_terms"],
        "main_next_file": main_next_file,
        "summary_json": str(summary_path),
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
