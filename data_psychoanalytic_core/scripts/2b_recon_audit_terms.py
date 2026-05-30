#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2b_recon_audit_terms.py

Andromeda Nowicka v0.5-pre
Audit high-frequency reconnaissance terms after 2a_title_abstract_recon.py.

Purpose
-------
The first title+abstract reconnaissance naturally surfaces many high-frequency
domain-background terms such as "psychoanalytic", "patient", "clinical", etc.
These terms are real signals of the corpus domain, but they are usually not
useful as candidate semantic concepts for later mapping.

This script creates an explicit audit layer. It does NOT overwrite raw top-term
outputs from 2a. It flags terms as:

- candidate_concept
- background_domain_term
- technical_artifact

and creates filtered candidate queues for later semantic work.

It also applies the same audit logic globally and per journal.

Run
---
Put this file in:

    data_psychoanalytic_core/scripts/

Run:

    cd data_psychoanalytic_core/scripts
    python 2b_recon_audit_terms.py

Inputs
------
Global:
    ../data/title_abstract/global/psychoanalytic_core_candidate_terms_for_semantic_map.csv
    ../data/title_abstract/global/psychoanalytic_core_top_terms_global.csv
    ../data/title_abstract/global/psychoanalytic_core_top_terms_by_journal.csv

Per journal:
    ../data/title_abstract/by_journal/<journal>/<journal>_candidate_terms_for_semantic_map.csv
    ../data/title_abstract/by_journal/<journal>/<journal>_top_terms.csv

Outputs
-------
Global:
    ../data/title_abstract/audit/term_recon_audit_map.csv
    ../data/title_abstract/audit/psychoanalytic_core_candidate_terms_for_semantic_map_audited.csv
    ../data/title_abstract/audit/psychoanalytic_core_candidate_terms_for_semantic_map_filtered.csv
    ../data/title_abstract/audit/term_recon_background_terms.csv
    ../data/title_abstract/audit/term_recon_artifacts.csv
    ../data/title_abstract/audit/term_recon_audit_summary.json

Per journal:
    ../data/title_abstract/audit/by_journal/<journal>/<journal>_candidate_terms_for_semantic_map_audited.csv
    ../data/title_abstract/audit/by_journal/<journal>/<journal>_candidate_terms_for_semantic_map_filtered.csv
    ../data/title_abstract/audit/by_journal/<journal>/<journal>_term_recon_audit_summary.json
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

JOURNAL_ORDER = [
    "ijpa",
    "japa",
    "psychoanalytic_dialogues",
    "psychoanalytic_psychology",
    "psychoanalytic_psychotherapy",
]

# Terms that are expected to dominate a psychoanalytic corpus but usually do
# not differentiate theoretical or clinical content at this stage.
# They are not deleted from raw top-term tables; they are excluded from the
# semantic candidate queue unless manually reversed later.
BACKGROUND_DOMAIN_TERMS = {
    "psychoanalytic",
    "psychoanalysis",
    "psychoanalytical",
    "analytic",
    "analysis",
    "analyses",
    "analyst",
    "analysts",
    "analysand",
    "analysands",
    "patient",
    "patients",
    "clinical",
    "clinician",
    "clinicians",
    "treatment",
    "treatments",
    "therapy",
    "therapies",
    "therapist",
    "therapists",
    "psychotherapy",
    "psychotherapies",
    "psychotherapeutic",
    "process",
    "processes",
    "session",
    "sessions",
    "work",
    "working",
    "theory",
    "theoretical",
    "conceptual",
    "practice",
    "practices",
    "experience",
    "experiences",
    "development",
    "developmental",
    # keep "child", "mother", "object", "self" as candidate concepts, not background
}

# Multiword phrases that are common but often too generic for the semantic queue.
BACKGROUND_DOMAIN_PATTERNS = [
    r"^psychoanalytic (?:theory|practice|treatment|process|work)$",
    r"^analytic (?:process|work|treatment|situation)$",
    r"^clinical (?:material|practice|work|process|situation|situations|setting|settings)$",
    r"^psychoanalytic clinical$",
    r"^psychoanalytic treatment$",
    r"^psychoanalytic psychotherapy$",
    r"^psychoanalytic process$",
    r"^psychoanalytic theory$",
    r"^clinical psychoanalysis$",
    r"^patient analyst$",
    r"^analyst patient$",
]

# Obvious extraction/layout artifacts.
TECHNICAL_ARTIFACT_TERMS = {
    "runninghead",
    "running head",
    "running-head",
    "abstract",
    "keywords",
    "keyword",
    "pep-web",
    "pepweb",
    "copyrighted",
    "copyright",
    "authorized",
    "reproduction",
    "prohibited",
    "material",
    "licensed",
    "downloaded",
}

TECHNICAL_ARTIFACT_PATTERNS = [
    r"\brunning\s*-?\s*head\b",
    r"\brunninghead\b",
    r"\bcopyright(ed)?\b",
    r"\bauthorized users?\b",
    r"\breproduction prohibited\b",
    r"\bpep[- ]?web\b",
    r"\blicensed materials?\b",
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
        "global_root": title_root / "global",
        "by_journal_root": title_root / "by_journal",
        "audit_root": title_root / "audit",
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


def normalize_term(term: str) -> str:
    term = str(term or "").strip().lower()
    term = re.sub(r"\s+", " ", term)
    term = term.strip(" .;:,")
    return term


def matches_any_pattern(term: str, patterns: Iterable[str]) -> bool:
    t = normalize_term(term)
    return any(re.search(p, t, flags=re.I) for p in patterns)


def classify_term(term: str) -> Tuple[str, str, bool]:
    """
    Returns:
        audit_category, audit_reason, include_in_semantic_review
    """
    t = normalize_term(term)

    if not t:
        return "technical_artifact", "empty_term", False

    if t in TECHNICAL_ARTIFACT_TERMS or matches_any_pattern(t, TECHNICAL_ARTIFACT_PATTERNS):
        return "technical_artifact", "explicit_artifact_rule", False

    if t in BACKGROUND_DOMAIN_TERMS or matches_any_pattern(t, BACKGROUND_DOMAIN_PATTERNS):
        return "background_domain_term", "explicit_background_domain_rule", False

    # Single-token generic adjective/adverb endings can be weak candidates,
    # but we do not exclude them automatically unless listed above.
    return "candidate_concept", "kept_for_semantic_review", True


def audit_terms(df: pd.DataFrame, scope: str) -> pd.DataFrame:
    if df.empty:
        return df.copy()

    out = df.copy()
    if "term" not in out.columns:
        raise ValueError("Input candidate/top-term table must contain a 'term' column.")

    classifications = out["term"].apply(classify_term)
    out["term_norm_for_audit"] = out["term"].apply(normalize_term)
    out["audit_category"] = classifications.apply(lambda x: x[0])
    out["audit_reason"] = classifications.apply(lambda x: x[1])
    out["include_in_semantic_review"] = classifications.apply(lambda x: x[2])
    out["audit_scope"] = scope
    out["audit_stage"] = "2b_recon_audit_terms"
    out["manual_override"] = ""
    out["manual_override_note"] = ""
    return out


def build_audit_map(all_terms: pd.Series) -> pd.DataFrame:
    unique_terms = sorted({normalize_term(x) for x in all_terms.dropna().astype(str) if normalize_term(x)})
    rows = []
    for term in unique_terms:
        cat, reason, include = classify_term(term)
        rows.append({
            "term_norm_for_audit": term,
            "audit_category": cat,
            "audit_reason": reason,
            "include_in_semantic_review": include,
            "manual_override": "",
            "manual_override_note": "",
        })
    return pd.DataFrame(rows)


def summarize_audited(df: pd.DataFrame, scope: str) -> Dict[str, object]:
    if df.empty:
        return {
            "scope": scope,
            "n_rows": 0,
            "n_unique_terms": 0,
            "category_counts": {},
            "n_included": 0,
            "n_excluded": 0,
        }

    category_counts = df["audit_category"].value_counts(dropna=False).to_dict()
    return {
        "scope": scope,
        "n_rows": int(len(df)),
        "n_unique_terms": int(df["term_norm_for_audit"].nunique()),
        "category_counts": {str(k): int(v) for k, v in category_counts.items()},
        "n_included": int(df["include_in_semantic_review"].astype(bool).sum()),
        "n_excluded": int((~df["include_in_semantic_review"].astype(bool)).sum()),
    }


def filter_candidates(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    return df[df["include_in_semantic_review"].astype(bool)].copy()


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit reconnaissance candidate terms after 2a.")
    parser.add_argument(
        "--title-root",
        default="../data/title_abstract",
        help="Root of title_abstract outputs.",
    )
    parser.add_argument(
        "--journals",
        default="all",
        help="Comma-separated journal keys or all.",
    )
    args = parser.parse_args()

    paths = get_paths()

    title_root = Path(args.title_root)
    if not title_root.is_absolute():
        title_root = (paths["scripts_dir"] / title_root).resolve()

    global_root = title_root / "global"
    by_journal_root = title_root / "by_journal"
    audit_root = title_root / "audit"
    audit_root.mkdir(parents=True, exist_ok=True)

    journals = JOURNAL_ORDER if args.journals == "all" else [x.strip() for x in args.journals.split(",") if x.strip()]

    # Global candidate and top-term files.
    global_candidates_path = global_root / "psychoanalytic_core_candidate_terms_for_semantic_map.csv"
    global_top_terms_path = global_root / "psychoanalytic_core_top_terms_global.csv"
    global_top_by_journal_path = global_root / "psychoanalytic_core_top_terms_by_journal.csv"

    global_candidates = read_csv_safe(global_candidates_path)
    global_top_terms = read_csv_safe(global_top_terms_path)
    global_top_by_journal = read_csv_safe(global_top_by_journal_path)

    if global_candidates.empty:
        raise SystemExit(f"ERROR: Missing or empty global candidates file: {global_candidates_path}")

    audited_global = audit_terms(global_candidates, scope="psychoanalytic_core_global_candidate_queue")
    filtered_global = filter_candidates(audited_global)

    # Build a global audit map from all available term sources.
    term_sources = [global_candidates.get("term", pd.Series(dtype=str))]
    if not global_top_terms.empty and "term" in global_top_terms.columns:
        term_sources.append(global_top_terms["term"])
    if not global_top_by_journal.empty and "term" in global_top_by_journal.columns:
        term_sources.append(global_top_by_journal["term"])

    audit_map = build_audit_map(pd.concat(term_sources, ignore_index=True))
    background_terms = audit_map[audit_map["audit_category"] == "background_domain_term"].copy()
    artifacts = audit_map[audit_map["audit_category"] == "technical_artifact"].copy()

    global_audited_path = audit_root / "psychoanalytic_core_candidate_terms_for_semantic_map_audited.csv"
    global_filtered_path = audit_root / "psychoanalytic_core_candidate_terms_for_semantic_map_filtered.csv"
    audit_map_path = audit_root / "term_recon_audit_map.csv"
    background_path = audit_root / "term_recon_background_terms.csv"
    artifacts_path = audit_root / "term_recon_artifacts.csv"

    write_csv(audited_global, global_audited_path)
    write_csv(filtered_global, global_filtered_path)
    write_csv(audit_map, audit_map_path)
    write_csv(background_terms, background_path)
    write_csv(artifacts, artifacts_path)

    # Per-journal audit.
    by_journal_outputs = {}
    by_journal_summaries = []

    for journal in journals:
        j_in = by_journal_root / journal / f"{journal}_candidate_terms_for_semantic_map.csv"
        if not j_in.exists():
            continue

        j_df = read_csv_safe(j_in)
        if j_df.empty:
            continue

        j_audited = audit_terms(j_df, scope=f"{journal}_candidate_queue")
        j_filtered = filter_candidates(j_audited)

        j_out_dir = audit_root / "by_journal" / journal
        j_audited_path = j_out_dir / f"{journal}_candidate_terms_for_semantic_map_audited.csv"
        j_filtered_path = j_out_dir / f"{journal}_candidate_terms_for_semantic_map_filtered.csv"
        j_summary_path = j_out_dir / f"{journal}_term_recon_audit_summary.json"

        write_csv(j_audited, j_audited_path)
        write_csv(j_filtered, j_filtered_path)

        j_summary = summarize_audited(j_audited, scope=journal)
        j_summary["outputs"] = {
            "audited": str(j_audited_path),
            "filtered": str(j_filtered_path),
            "summary_json": str(j_summary_path),
        }
        write_json(j_summary, j_summary_path)

        by_journal_outputs[journal] = j_summary["outputs"]
        by_journal_summaries.append(j_summary)

    summary = {
        "script_version": SCRIPT_VERSION,
        "created_at_utc": utc_now_iso(),
        "purpose": "Audit candidate terms after title+abstract reconnaissance; flag background domain terms and technical artifacts.",
        "policy": {
            "raw_top_terms_modified": False,
            "semantic_normalization_performed": False,
            "creates_audit_layer_only": True,
            "technical_artifacts_excluded_from_semantic_review": True,
            "background_domain_terms_excluded_from_semantic_review": True,
        },
        "global_summary": summarize_audited(audited_global, scope="psychoanalytic_core_global_candidate_queue"),
        "by_journal_summaries": by_journal_summaries,
        "known_initial_decisions": {
            "runninghead": "technical_artifact",
            "psychoanalytic_patient_clinical_family": "background_domain_term",
            "applies_to": "global and per-journal candidate queues",
        },
        "outputs": {
            "audit_map": str(audit_map_path),
            "global_audited_candidates": str(global_audited_path),
            "global_filtered_candidates": str(global_filtered_path),
            "background_terms": str(background_path),
            "technical_artifacts": str(artifacts_path),
            "by_journal_root": str(audit_root / "by_journal"),
        },
    }

    summary_path = audit_root / "term_recon_audit_summary.json"
    write_json(summary, summary_path)
    summary["outputs"]["summary_json"] = str(summary_path)

    print(json.dumps({
        "status": "ok",
        "script_version": SCRIPT_VERSION,
        "global_summary": summary["global_summary"],
        "n_journals_processed": len(by_journal_summaries),
        "summary_json": str(summary_path),
        "global_filtered_candidates": str(global_filtered_path),
        "background_terms": str(background_path),
        "technical_artifacts": str(artifacts_path),
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
