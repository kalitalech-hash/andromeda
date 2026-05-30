#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2c_discriminative_vocabulary_recon.py

Andromeda Nowicka v0.5-pre
Discriminative vocabulary reconnaissance for psychoanalytic_core.

Purpose
-------
Move beyond raw high-frequency terms from 2a and the first audit layer from 2b.
This script identifies terms and n-grams that are more characteristic of:

1. the whole corpus after generic/background filtering,
2. each journal,
3. each historical period,
4. each journal × period cell.

It is still a reconnaissance step, not final semantic normalization.

Inputs
------
Main clean corpus:
    ../data/title_abstract/global/psychoanalytic_core_ART_title_abstract_clean.csv

Optional audit map from 2b:
    ../data/title_abstract/audit/term_recon_audit_map.csv

Outputs
-------
    ../data/title_abstract/keyness/psychoanalytic_core_terms_clean_for_keyness.csv
    ../data/title_abstract/keyness/psychoanalytic_core_global_core_terms_after_audit.csv
    ../data/title_abstract/keyness/psychoanalytic_core_global_core_bigrams_after_audit.csv
    ../data/title_abstract/keyness/psychoanalytic_core_key_terms_by_journal.csv
    ../data/title_abstract/keyness/psychoanalytic_core_key_bigrams_by_journal.csv
    ../data/title_abstract/keyness/psychoanalytic_core_key_terms_by_period.csv
    ../data/title_abstract/keyness/psychoanalytic_core_key_bigrams_by_period.csv
    ../data/title_abstract/keyness/psychoanalytic_core_key_terms_by_journal_period.csv
    ../data/title_abstract/keyness/psychoanalytic_core_key_bigrams_by_journal_period.csv
    ../data/title_abstract/keyness/psychoanalytic_core_discriminative_candidate_terms.csv
    ../data/title_abstract/keyness/psychoanalytic_core_vocabulary_recon_v2_summary.json

Run
---
Put this file in:

    data_psychoanalytic_core/scripts/

Run:

    cd data_psychoanalytic_core/scripts
    python 2c_discriminative_vocabulary_recon.py
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import html
import json
import math
import re
import unicodedata
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple

import pandas as pd


SCRIPT_VERSION = "v0.1.0"

JOURNAL_ORDER = [
    "ijpa",
    "japa",
    "psychoanalytic_dialogues",
    "psychoanalytic_psychology",
    "psychoanalytic_psychotherapy",
]

PERIOD_ORDER = [
    "1920-1945",
    "1946-1969",
    "1970-1989",
    "1990-2009",
    "2010-2025",
]

# Additional generic stop/audit terms observed after 2a/2b.
# These terms are not deleted from earlier raw outputs. This is a specific
# keyness-stage filter to improve discriminative vocabulary reconnaissance.
GENERIC_RECON_STOPWORDS = {
    # general abstract language
    "new", "between", "one", "about", "other", "others", "also", "all", "both",
    "two", "three", "first", "second", "third", "only", "same", "many", "much",
    "several", "various", "particular", "general", "specific", "important",
    "central", "significant", "major", "main", "different", "similar",
    "possible", "certain", "given", "rather", "further", "another", "however",
    "therefore", "thus", "although", "including", "include", "includes",
    "despite", "among", "toward", "towards", "concerning", "related",

    # academic rhetoric
    "research", "findings", "found", "data", "method", "methods", "model",
    "models", "question", "questions", "understanding", "understand",
    "consideration", "considerations", "aspects", "aspect", "years", "year",
    "history", "historical", "literature", "current", "recent", "traditional",
    "contemporary", "modern", "classic", "classical",

    # metadata/layout/affiliation-like terms
    "runninghead", "running", "head", "york", "university", "college",
    "institute", "department", "school", "hospital", "clinic", "phd", "md",
    "e-mail", "email", "mail", "street", "avenue", "road", "london", "new-york",
    "city", "state", "usa", "uk", "com", "org", "edu",

    # too broad clinical/professional background terms caught after 2b
    "psychoanalytic", "psychoanalysis", "psychoanalytical", "analytic",
    "analysis", "analyses", "analyst", "analysts", "analysand", "analysands",
    "patient", "patients", "clinical", "clinician", "clinicians", "treatment",
    "treatments", "therapy", "therapies", "therapist", "therapists",
    "psychotherapy", "psychotherapies", "psychotherapeutic", "process",
    "processes", "session", "sessions", "practice", "practices", "theory",
    "theoretical", "conceptual", "paper", "article", "case", "cases",
}

# Keep a conservative set of standard function words too.
FUNCTION_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "because", "been", "being",
    "but", "by", "can", "could", "did", "do", "does", "doing", "during",
    "each", "few", "for", "from", "had", "has", "have", "having", "he",
    "her", "hers", "him", "his", "how", "i", "if", "in", "into", "is",
    "it", "its", "itself", "may", "might", "more", "most", "no", "not",
    "of", "on", "or", "our", "ours", "she", "should", "so", "some",
    "such", "than", "that", "the", "their", "them", "then", "there",
    "these", "they", "this", "those", "through", "to", "under", "up",
    "upon", "us", "use", "used", "using", "was", "we", "were", "what",
    "when", "where", "which", "while", "who", "whose", "why", "will",
    "with", "within", "without", "would", "you", "your",
}

STOPWORDS = FUNCTION_STOPWORDS | GENERIC_RECON_STOPWORDS

TECHNICAL_PATTERNS = [
    r"\brunning\s*-?\s*head\b",
    r"\brunninghead\b",
    r"\bcopyright(ed)?\b",
    r"\bauthorized users?\b",
    r"\breproduction prohibited\b",
    r"\bpep[- ]?web\b",
    r"\bdoi\b",
    r"\bwww\b",
    r"\bhttp\b",
    r"\bhttps\b",
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
        "audit_root": title_root / "audit",
        "keyness_root": title_root / "keyness",
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
    term = unicodedata.normalize("NFKC", term)
    term = term.replace("—", "-").replace("–", "-").replace("−", "-")
    term = re.sub(r"\s+", " ", term)
    term = term.strip(" .;:,")
    return term


def token_is_noise(token: str, audit_exclude_terms: Set[str]) -> bool:
    t = norm_term(token)
    if not t:
        return True
    if t in STOPWORDS:
        return True
    if t in audit_exclude_terms:
        return True
    if len(t) < 3:
        return True
    if re.fullmatch(r"\d+", t):
        return True
    if any(re.search(p, t, flags=re.I) for p in TECHNICAL_PATTERNS):
        return True
    return False


def tokenize(text: str, audit_exclude_terms: Set[str]) -> List[str]:
    text = str(text or "").lower()
    # Keep hyphenated forms; this helps with object-relations, self-psychology, etc.
    toks = re.findall(r"[a-z][a-z'\-]{2,}", text)
    cleaned = []
    for tok in toks:
        tok = tok.strip("-'")
        if not token_is_noise(tok, audit_exclude_terms):
            cleaned.append(tok)
    return cleaned


def make_ngrams(tokens: List[str], n: int) -> List[str]:
    out = []
    for i in range(len(tokens) - n + 1):
        gram = tokens[i:i+n]
        if len(gram) != n:
            continue
        if any(t in STOPWORDS for t in gram):
            continue
        out.append(" ".join(gram))
    return out


def load_audit_exclude_terms(path: Path) -> Set[str]:
    df = read_csv_safe(path)
    if df.empty:
        return set()
    if "term_norm_for_audit" not in df.columns or "include_in_semantic_review" not in df.columns:
        return set()

    include = df["include_in_semantic_review"].astype(str).str.lower().isin(["true", "1", "yes"])
    excluded = df.loc[~include, "term_norm_for_audit"].dropna().astype(str).map(norm_term)
    return set(excluded)


def prepare_document_terms(
    df: pd.DataFrame,
    audit_exclude_terms: Set[str],
    text_col: str = "text_for_analysis",
) -> pd.DataFrame:
    rows = []
    for idx, row in df.iterrows():
        text = row.get(text_col, "")
        tokens = tokenize(text, audit_exclude_terms)
        bigrams = make_ngrams(tokens, 2)

        rows.append({
            "row_index": idx,
            "article_id": row.get("article_id", ""),
            "journal_key": row.get("journal_key", ""),
            "period": row.get("period", ""),
            "year_for_analysis": row.get("year_for_analysis", ""),
            "n_tokens_clean": len(tokens),
            "terms_unigram": " | ".join(tokens),
            "terms_bigram": " | ".join(bigrams),
        })
    return pd.DataFrame(rows)


def count_terms_for_docs(doc_terms: pd.DataFrame, term_col: str) -> pd.DataFrame:
    counter = collections.Counter()
    doc_counter = collections.Counter()
    n_docs = len(doc_terms)

    for items in doc_terms[term_col].fillna("").astype(str):
        terms = [x.strip() for x in items.split("|") if x.strip()]
        counter.update(terms)
        doc_counter.update(set(terms))

    rows = []
    for rank, (term, count) in enumerate(counter.most_common(), start=1):
        rows.append({
            "rank": rank,
            "term": term,
            "count": int(count),
            "doc_count": int(doc_counter[term]),
            "doc_pct": round(doc_counter[term] / max(n_docs, 1) * 100, 4),
            "n_docs_base": int(n_docs),
        })
    return pd.DataFrame(rows)


def group_keyness(
    doc_terms: pd.DataFrame,
    group_cols: List[str],
    term_col: str,
    min_doc_count_group: int = 3,
    top_n: int = 100,
) -> pd.DataFrame:
    """
    Simple auditable keyness:
    - group_doc_pct: percentage of documents in group containing term
    - rest_doc_pct: percentage of documents outside group containing term
    - pct_point_lift: group_doc_pct - rest_doc_pct
    - ratio_lift: smoothed group/rest ratio
    - keyness_score: pct_point_lift * log1p(group_doc_count)
    """
    if doc_terms.empty:
        return pd.DataFrame()

    all_rows = []

    # Precompute term sets per row.
    work = doc_terms.copy()
    work["_term_set"] = work[term_col].fillna("").astype(str).apply(
        lambda x: {t.strip() for t in x.split("|") if t.strip()}
    )

    for group_key, g in work.groupby(group_cols, dropna=False):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)

        rest = work.drop(index=g.index)
        n_group = len(g)
        n_rest = len(rest)

        group_counter = collections.Counter()
        rest_counter = collections.Counter()

        for terms in g["_term_set"]:
            group_counter.update(terms)
        for terms in rest["_term_set"]:
            rest_counter.update(terms)

        rows = []
        for term, g_doc_count in group_counter.items():
            if g_doc_count < min_doc_count_group:
                continue

            r_doc_count = rest_counter.get(term, 0)
            group_doc_pct = g_doc_count / max(n_group, 1) * 100
            rest_doc_pct = r_doc_count / max(n_rest, 1) * 100 if n_rest else 0.0
            pct_point_lift = group_doc_pct - rest_doc_pct
            ratio_lift = (g_doc_count + 0.5) / (n_group + 1.0) / ((r_doc_count + 0.5) / (n_rest + 1.0)) if n_rest else math.inf
            keyness_score = pct_point_lift * math.log1p(g_doc_count)

            if pct_point_lift <= 0:
                continue

            item = {
                "term": term,
                "term_col": term_col,
                "n_docs_group": int(n_group),
                "n_docs_rest": int(n_rest),
                "group_doc_count": int(g_doc_count),
                "rest_doc_count": int(r_doc_count),
                "group_doc_pct": round(group_doc_pct, 4),
                "rest_doc_pct": round(rest_doc_pct, 4),
                "pct_point_lift": round(pct_point_lift, 4),
                "ratio_lift": round(ratio_lift, 4) if math.isfinite(ratio_lift) else "inf",
                "keyness_score": round(keyness_score, 6),
            }
            for col, value in zip(group_cols, group_key):
                item[col] = value
            rows.append(item)

        if rows:
            group_df = pd.DataFrame(rows)
            group_df = group_df.sort_values(
                ["keyness_score", "pct_point_lift", "group_doc_count"],
                ascending=[False, False, False],
            ).head(top_n)
            group_df.insert(0, "rank_within_group", range(1, len(group_df) + 1))
            all_rows.append(group_df)

    if not all_rows:
        return pd.DataFrame()

    out = pd.concat(all_rows, ignore_index=True, sort=False)

    # Put group columns first.
    first_cols = ["rank_within_group"] + group_cols
    rest_cols = [c for c in out.columns if c not in first_cols]
    return out[first_cols + rest_cols]


def make_discriminative_candidates(*tables: pd.DataFrame) -> pd.DataFrame:
    frames = []
    for df in tables:
        if df is not None and not df.empty:
            frames.append(df.copy())
    if not frames:
        return pd.DataFrame()

    rows = []
    for df in frames:
        for _, r in df.iterrows():
            rows.append({
                "term": r.get("term", ""),
                "source_table": r.get("source_table", ""),
                "term_col": r.get("term_col", ""),
                "journal_key": r.get("journal_key", ""),
                "period": r.get("period", ""),
                "count": r.get("count", ""),
                "doc_count": r.get("doc_count", r.get("group_doc_count", "")),
                "doc_pct": r.get("doc_pct", r.get("group_doc_pct", "")),
                "keyness_score": r.get("keyness_score", ""),
                "pct_point_lift": r.get("pct_point_lift", ""),
                "candidate_review_status": "pending",
                "suggested_semantic_family": "",
                "manual_note": "",
            })

    out = pd.DataFrame(rows)
    if out.empty:
        return out

    # Deduplicate lightly by term/source/journal/period.
    out["term_norm"] = out["term"].map(norm_term)
    out = out.drop_duplicates(subset=["term_norm", "source_table", "journal_key", "period"], keep="first")
    return out


def add_source(df: pd.DataFrame, source: str) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    out["source_table"] = source
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description="Discriminative vocabulary reconnaissance for psychoanalytic_core.")
    parser.add_argument(
        "--input",
        default="../data/title_abstract/global/psychoanalytic_core_ART_title_abstract_clean.csv",
        help="Clean title+abstract corpus from 2a.",
    )
    parser.add_argument(
        "--audit-map",
        default="../data/title_abstract/audit/term_recon_audit_map.csv",
        help="Audit map from 2b.",
    )
    parser.add_argument(
        "--out-dir",
        default="../data/title_abstract/keyness",
        help="Output directory.",
    )
    parser.add_argument("--top-n-global", type=int, default=300)
    parser.add_argument("--top-n-group", type=int, default=100)
    parser.add_argument("--min-doc-count-group", type=int, default=3)
    args = parser.parse_args()

    paths = get_paths()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = (paths["scripts_dir"] / input_path).resolve()

    audit_map_path = Path(args.audit_map)
    if not audit_map_path.is_absolute():
        audit_map_path = (paths["scripts_dir"] / audit_map_path).resolve()

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = (paths["scripts_dir"] / out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise SystemExit(f"ERROR: clean corpus not found: {input_path}")

    df = read_csv_safe(input_path)

    required = {"text_for_analysis", "journal_key", "period"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"ERROR: input missing columns: {sorted(missing)}")

    audit_exclude_terms = load_audit_exclude_terms(audit_map_path)
    audit_exclude_terms |= GENERIC_RECON_STOPWORDS

    doc_terms = prepare_document_terms(df, audit_exclude_terms)
    doc_terms_path = out_dir / "psychoanalytic_core_terms_clean_for_keyness.csv"
    write_csv(doc_terms, doc_terms_path)

    global_unigrams = count_terms_for_docs(doc_terms, "terms_unigram").head(args.top_n_global)
    global_bigrams = count_terms_for_docs(doc_terms, "terms_bigram").head(args.top_n_global)

    global_unigrams_path = out_dir / "psychoanalytic_core_global_core_terms_after_audit.csv"
    global_bigrams_path = out_dir / "psychoanalytic_core_global_core_bigrams_after_audit.csv"
    write_csv(global_unigrams, global_unigrams_path)
    write_csv(global_bigrams, global_bigrams_path)

    key_terms_by_journal = group_keyness(
        doc_terms,
        ["journal_key"],
        "terms_unigram",
        min_doc_count_group=args.min_doc_count_group,
        top_n=args.top_n_group,
    )
    key_bigrams_by_journal = group_keyness(
        doc_terms,
        ["journal_key"],
        "terms_bigram",
        min_doc_count_group=args.min_doc_count_group,
        top_n=args.top_n_group,
    )
    key_terms_by_period = group_keyness(
        doc_terms,
        ["period"],
        "terms_unigram",
        min_doc_count_group=args.min_doc_count_group,
        top_n=args.top_n_group,
    )
    key_bigrams_by_period = group_keyness(
        doc_terms,
        ["period"],
        "terms_bigram",
        min_doc_count_group=args.min_doc_count_group,
        top_n=args.top_n_group,
    )
    key_terms_by_journal_period = group_keyness(
        doc_terms,
        ["journal_key", "period"],
        "terms_unigram",
        min_doc_count_group=args.min_doc_count_group,
        top_n=args.top_n_group,
    )
    key_bigrams_by_journal_period = group_keyness(
        doc_terms,
        ["journal_key", "period"],
        "terms_bigram",
        min_doc_count_group=args.min_doc_count_group,
        top_n=args.top_n_group,
    )

    outputs = {
        "key_terms_by_journal": out_dir / "psychoanalytic_core_key_terms_by_journal.csv",
        "key_bigrams_by_journal": out_dir / "psychoanalytic_core_key_bigrams_by_journal.csv",
        "key_terms_by_period": out_dir / "psychoanalytic_core_key_terms_by_period.csv",
        "key_bigrams_by_period": out_dir / "psychoanalytic_core_key_bigrams_by_period.csv",
        "key_terms_by_journal_period": out_dir / "psychoanalytic_core_key_terms_by_journal_period.csv",
        "key_bigrams_by_journal_period": out_dir / "psychoanalytic_core_key_bigrams_by_journal_period.csv",
    }

    write_csv(key_terms_by_journal, outputs["key_terms_by_journal"])
    write_csv(key_bigrams_by_journal, outputs["key_bigrams_by_journal"])
    write_csv(key_terms_by_period, outputs["key_terms_by_period"])
    write_csv(key_bigrams_by_period, outputs["key_bigrams_by_period"])
    write_csv(key_terms_by_journal_period, outputs["key_terms_by_journal_period"])
    write_csv(key_bigrams_by_journal_period, outputs["key_bigrams_by_journal_period"])

    # Candidate pool for later semantic mapping.
    candidate_pool = make_discriminative_candidates(
        add_source(global_unigrams.head(200), "global_core_terms_after_audit"),
        add_source(global_bigrams.head(200), "global_core_bigrams_after_audit"),
        add_source(key_terms_by_journal, "key_terms_by_journal"),
        add_source(key_bigrams_by_journal, "key_bigrams_by_journal"),
        add_source(key_terms_by_period, "key_terms_by_period"),
        add_source(key_bigrams_by_period, "key_bigrams_by_period"),
        add_source(key_terms_by_journal_period, "key_terms_by_journal_period"),
        add_source(key_bigrams_by_journal_period, "key_bigrams_by_journal_period"),
    )

    candidate_pool_path = out_dir / "psychoanalytic_core_discriminative_candidate_terms.csv"
    write_csv(candidate_pool, candidate_pool_path)

    # Simple summaries.
    period_counts = doc_terms["period"].value_counts(dropna=False).to_dict()
    journal_counts = doc_terms["journal_key"].value_counts(dropna=False).to_dict()

    summary = {
        "script_version": SCRIPT_VERSION,
        "created_at_utc": utc_now_iso(),
        "purpose": "Discriminative vocabulary reconnaissance after high-frequency audit.",
        "inputs": {
            "clean_corpus": str(input_path),
            "audit_map": str(audit_map_path),
        },
        "parameters": {
            "top_n_global": args.top_n_global,
            "top_n_group": args.top_n_group,
            "min_doc_count_group": args.min_doc_count_group,
            "generic_recon_stopwords_n": len(GENERIC_RECON_STOPWORDS),
            "audit_exclude_terms_total_n": len(audit_exclude_terms),
        },
        "corpus": {
            "n_records": int(len(df)),
            "n_journals": int(doc_terms["journal_key"].nunique()),
            "n_periods": int(doc_terms["period"].nunique()),
            "journal_counts": {str(k): int(v) for k, v in journal_counts.items()},
            "period_counts": {str(k): int(v) for k, v in period_counts.items()},
            "median_clean_tokens_per_record": float(doc_terms["n_tokens_clean"].median()) if len(doc_terms) else 0.0,
            "mean_clean_tokens_per_record": round(float(doc_terms["n_tokens_clean"].mean()), 2) if len(doc_terms) else 0.0,
        },
        "outputs": {
            "terms_clean_for_keyness": str(doc_terms_path),
            "global_core_terms_after_audit": str(global_unigrams_path),
            "global_core_bigrams_after_audit": str(global_bigrams_path),
            "key_terms_by_journal": str(outputs["key_terms_by_journal"]),
            "key_bigrams_by_journal": str(outputs["key_bigrams_by_journal"]),
            "key_terms_by_period": str(outputs["key_terms_by_period"]),
            "key_bigrams_by_period": str(outputs["key_bigrams_by_period"]),
            "key_terms_by_journal_period": str(outputs["key_terms_by_journal_period"]),
            "key_bigrams_by_journal_period": str(outputs["key_bigrams_by_journal_period"]),
            "discriminative_candidate_terms": str(candidate_pool_path),
        },
        "interpretive_note": (
            "This stage does not define final semantic families. It only improves the candidate "
            "queue by combining cleaned global frequency with journal, period, and journal-period "
            "keyness. All results require human review before interpretation."
        ),
    }

    summary_path = out_dir / "psychoanalytic_core_vocabulary_recon_v2_summary.json"
    write_json(summary, summary_path)
    summary["outputs"]["summary_json"] = str(summary_path)

    print(json.dumps({
        "status": "ok",
        "script_version": SCRIPT_VERSION,
        "n_records": summary["corpus"]["n_records"],
        "n_journals": summary["corpus"]["n_journals"],
        "n_periods": summary["corpus"]["n_periods"],
        "candidate_terms_rows": int(len(candidate_pool)),
        "summary_json": str(summary_path),
        "candidate_terms": str(candidate_pool_path),
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
