#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
2a_title_abstract_recon.py

Andromeda Nowicka v0.5-pre
First semantic-readiness step for psychoanalytic_core.

Purpose
-------
Prepare and diagnose the ART-only title+abstract corpus before deeper semantic
analysis.

Input:
    ../data/qa/global/psychoanalytic_core_articles_ART_only_with_abstracts.csv

The script works on three levels:
1. global corpus,
2. each journal separately,
3. comparative journal / period tables.

It does NOT perform final semantic normalization.
It only prepares a clean text layer and vocabulary reconnaissance tables.

Main outputs
------------
Global:
    ../data/title_abstract/global/psychoanalytic_core_ART_title_abstract_clean.csv
    ../data/title_abstract/global/psychoanalytic_core_text_quality_summary.csv
    ../data/title_abstract/global/psychoanalytic_core_text_quality_by_journal.csv
    ../data/title_abstract/global/psychoanalytic_core_text_quality_by_period.csv
    ../data/title_abstract/global/psychoanalytic_core_top_terms_global.csv
    ../data/title_abstract/global/psychoanalytic_core_top_bigrams_global.csv
    ../data/title_abstract/global/psychoanalytic_core_top_trigrams_global.csv
    ../data/title_abstract/global/psychoanalytic_core_top_terms_by_journal.csv
    ../data/title_abstract/global/psychoanalytic_core_top_bigrams_by_journal.csv
    ../data/title_abstract/global/psychoanalytic_core_top_terms_by_period.csv
    ../data/title_abstract/global/psychoanalytic_core_top_terms_by_journal_period.csv
    ../data/title_abstract/global/psychoanalytic_core_candidate_terms_for_semantic_map.csv
    ../data/title_abstract/global/psychoanalytic_core_title_abstract_recon_summary.json

By journal:
    ../data/title_abstract/by_journal/<journal_key>/<journal_key>_ART_title_abstract_clean.csv
    ../data/title_abstract/by_journal/<journal_key>/<journal_key>_text_quality_summary.csv
    ../data/title_abstract/by_journal/<journal_key>/<journal_key>_top_terms.csv
    ../data/title_abstract/by_journal/<journal_key>/<journal_key>_top_bigrams.csv
    ../data/title_abstract/by_journal/<journal_key>/<journal_key>_top_trigrams.csv
    ../data/title_abstract/by_journal/<journal_key>/<journal_key>_top_terms_by_period.csv
    ../data/title_abstract/by_journal/<journal_key>/<journal_key>_candidate_terms_for_semantic_map.csv
    ../data/title_abstract/by_journal/<journal_key>/<journal_key>_title_abstract_recon_summary.json

Run
---
Put this file in:

    data_psychoanalytic_core/scripts/

Run:

    cd data_psychoanalytic_core/scripts
    python 2a_title_abstract_recon.py
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
from typing import Dict, Iterable, List, Optional, Tuple

import pandas as pd


SCRIPT_VERSION = "v0.1.0"

DEFAULT_PERIODS = [
    ("1920-1945", 1920, 1945),
    ("1946-1969", 1946, 1969),
    ("1970-1989", 1970, 1989),
    ("1990-2009", 1990, 2009),
    ("2010-2025", 2010, 2025),
]

JOURNAL_ORDER = [
    "ijpa",
    "japa",
    "psychoanalytic_dialogues",
    "psychoanalytic_psychology",
    "psychoanalytic_psychotherapy",
]

# Conservative stopword list for reconnaissance only.
# We keep psychoanalytic terms such as object, self, mother, child, analysis,
# psychic, dream, interpretation, etc.
STOPWORDS = {
    # English function words
    "a", "an", "and", "are", "as", "at", "be", "because", "been", "being", "but",
    "by", "can", "could", "did", "do", "does", "doing", "during", "each", "few",
    "for", "from", "had", "has", "have", "having", "he", "her", "hers", "him",
    "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself", "may",
    "might", "more", "most", "no", "not", "of", "on", "or", "our", "ours",
    "she", "should", "so", "some", "such", "than", "that", "the", "their",
    "them", "then", "there", "these", "they", "this", "those", "through", "to",
    "under", "up", "upon", "us", "use", "used", "using", "was", "we", "were",
    "what", "when", "where", "which", "while", "who", "whose", "why", "will",
    "with", "within", "without", "would", "you", "your",

    # Generic academic/abstract rhetoric
    "article", "paper", "papers", "author", "authors", "study", "studies",
    "essay", "essays", "chapter", "chapters", "book", "books", "review",
    "reviews", "discusses", "discussion", "discussed", "present", "presents",
    "presented", "examines", "examined", "explores", "explored", "describes",
    "described", "suggests", "suggested", "argues", "argued", "proposes",
    "proposed", "considers", "considered", "focus", "focused", "based",
    "case", "cases", "example", "examples", "view", "views", "perspective",
    "perspectives", "approach", "approaches", "concept", "concepts", "term",
    "terms", "issue", "issues", "part", "parts", "point", "points", "role",
    "roles", "way", "ways",

    # Avoid PEP/access/copyright noise if leaked
    "copyrighted", "authorized", "users", "pep", "web", "terms", "conditions",
    "reproduction", "prohibited", "copyright", "licensed", "materials",
}


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def get_paths() -> Dict[str, Path]:
    scripts_dir = Path(__file__).resolve().parent
    project_root = scripts_dir.parent
    return {
        "scripts_dir": scripts_dir,
        "project_root": project_root,
        "title_abstract": project_root / "data" / "title_abstract",
    }


def read_csv_safe(path: Path) -> pd.DataFrame:
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


def clean_text_basic(value: str) -> str:
    text = str(value or "")
    text = unicodedata.normalize("NFKC", text)
    text = html.unescape(text)

    # Remove HTML/XML remnants.
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<[^>]+>", " ", text)

    # Remove recurring PEP/copyright fragments if leaked.
    text = re.sub(r"Copyrighted Material\..*$", " ", text, flags=re.I | re.S)
    text = re.sub(r"For use only by .*?PEP terms.*$", " ", text, flags=re.I | re.S)
    text = re.sub(r"Authorized Users.*$", " ", text, flags=re.I | re.S)
    text = re.sub(r"PEP-Web Copyright.*$", " ", text, flags=re.I | re.S)

    # Normalize dashes, quotes and soft hyphens.
    text = text.replace("—", "-").replace("–", "-").replace("−", "-")
    text = text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"')
    text = text.replace("\u00ad", "")

    # Fix common line-break hyphenation artifacts without destroying meaningful hyphens.
    text = re.sub(r"(\w)-\s+(\w)", r"\1\2", text)

    # Normalize whitespace.
    text = re.sub(r"\s+", " ", text).strip()
    return text


def assign_period(year_value: str, periods=DEFAULT_PERIODS) -> str:
    try:
        year = int(float(str(year_value).strip()))
    except Exception:
        return "unknown"
    for label, start, end in periods:
        if start <= year <= end:
            return label
    return "outside_periods"


def tokenize(text: str) -> List[str]:
    text = text.lower()
    # Keep hyphenated terms and apostrophes inside words.
    tokens = re.findall(r"[a-z][a-z'\-]{2,}", text)
    out = []
    for tok in tokens:
        tok = tok.strip("-'")
        if not tok:
            continue
        if tok in STOPWORDS:
            continue
        if len(tok) < 3:
            continue
        if not re.search(r"[a-z]", tok):
            continue
        out.append(tok)
    return out


def make_ngrams(tokens: List[str], n: int) -> Iterable[str]:
    for i in range(len(tokens) - n + 1):
        gram = tokens[i:i + n]
        if len(gram) != n:
            continue
        if any(t in STOPWORDS for t in gram):
            continue
        yield " ".join(gram)


def count_top_terms(records: Iterable[str], ngram_n: int = 1, top_n: int = 250) -> pd.DataFrame:
    counter = collections.Counter()
    doc_counter = collections.Counter()
    n_docs = 0

    for text in records:
        toks = tokenize(text)
        if ngram_n == 1:
            items = toks
        else:
            items = list(make_ngrams(toks, ngram_n))
        counter.update(items)
        doc_counter.update(set(items))
        n_docs += 1

    rows = []
    for rank, (term, count) in enumerate(counter.most_common(top_n), start=1):
        rows.append({
            "rank": rank,
            "term": term,
            "ngram_n": ngram_n,
            "count": int(count),
            "doc_count": int(doc_counter[term]),
            "doc_pct": round(doc_counter[term] / max(n_docs, 1) * 100, 3),
            "n_docs_base": int(n_docs),
        })
    return pd.DataFrame(rows)


def count_by_group(
    df: pd.DataFrame,
    group_cols: List[str],
    text_col: str,
    ngram_n: int = 1,
    top_n: int = 100,
) -> pd.DataFrame:
    rows = []
    if df.empty:
        return pd.DataFrame()

    for group_key, g in df.groupby(group_cols, dropna=False):
        top = count_top_terms(g[text_col].fillna("").astype(str), ngram_n=ngram_n, top_n=top_n)
        if top.empty:
            continue

        if not isinstance(group_key, tuple):
            group_key = (group_key,)

        for col, value in zip(group_cols, group_key):
            top.insert(0, col, value)
        top.insert(len(group_cols), "n_records_group", len(g))
        rows.append(top)

    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


def word_count(text: str) -> int:
    return len(re.findall(r"\b\w+\b", str(text or "")))


def make_quality_summary(df: pd.DataFrame, label: str = "global") -> pd.DataFrame:
    rows = []
    for col in ["title_clean", "abstract_clean", "text_for_analysis"]:
        s = df[col].fillna("").astype(str)
        lengths = s.str.len()
        words = s.apply(word_count)
        rows.append({
            "scope": label,
            "field": col,
            "n_records": int(len(df)),
            "n_nonempty": int(s.str.strip().ne("").sum()),
            "pct_nonempty": round(s.str.strip().ne("").mean() * 100, 2) if len(df) else 0.0,
            "median_chars": float(lengths.median()) if len(df) else 0.0,
            "mean_chars": round(float(lengths.mean()), 2) if len(df) else 0.0,
            "min_chars": int(lengths.min()) if len(df) else 0,
            "max_chars": int(lengths.max()) if len(df) else 0,
            "median_words": float(words.median()) if len(df) else 0.0,
            "mean_words": round(float(words.mean()), 2) if len(df) else 0.0,
            "n_very_short_lt_80_chars": int((lengths < 80).sum()) if len(df) else 0,
            "n_possible_html_artifact": int(df.get("flag_possible_html_artifact", pd.Series(dtype=bool)).sum()) if "flag_possible_html_artifact" in df.columns else 0,
            "n_possible_copyright_artifact": int(df.get("flag_possible_copyright_artifact", pd.Series(dtype=bool)).sum()) if "flag_possible_copyright_artifact" in df.columns else 0,
        })
    return pd.DataFrame(rows)


def make_quality_by_group(df: pd.DataFrame, group_cols: List[str]) -> pd.DataFrame:
    rows = []
    for group_key, g in df.groupby(group_cols, dropna=False):
        if not isinstance(group_key, tuple):
            group_key = (group_key,)
        item = {col: value for col, value in zip(group_cols, group_key)}

        s_abs = g["abstract_clean"].fillna("").astype(str)
        s_title = g["title_clean"].fillna("").astype(str)
        s_text = g["text_for_analysis"].fillna("").astype(str)

        abs_lengths = s_abs.str.len()
        text_lengths = s_text.str.len()
        abs_words = s_abs.apply(word_count)
        text_words = s_text.apply(word_count)

        item.update({
            "n_records": int(len(g)),
            "n_with_title": int(s_title.str.strip().ne("").sum()),
            "n_with_abstract": int(s_abs.str.strip().ne("").sum()),
            "pct_with_abstract": round(s_abs.str.strip().ne("").mean() * 100, 2) if len(g) else 0.0,
            "median_abstract_chars": float(abs_lengths.median()) if len(g) else 0.0,
            "mean_abstract_chars": round(float(abs_lengths.mean()), 2) if len(g) else 0.0,
            "median_abstract_words": float(abs_words.median()) if len(g) else 0.0,
            "mean_abstract_words": round(float(abs_words.mean()), 2) if len(g) else 0.0,
            "median_text_words": float(text_words.median()) if len(g) else 0.0,
            "mean_text_words": round(float(text_words.mean()), 2) if len(g) else 0.0,
            "n_very_short_abstract_lt_80_chars": int((abs_lengths < 80).sum()),
            "n_very_short_text_lt_120_chars": int((text_lengths < 120).sum()),
            "n_possible_html_artifact": int(g["flag_possible_html_artifact"].sum()) if "flag_possible_html_artifact" in g.columns else 0,
            "n_possible_copyright_artifact": int(g["flag_possible_copyright_artifact"].sum()) if "flag_possible_copyright_artifact" in g.columns else 0,
        })
        rows.append(item)
    return pd.DataFrame(rows)


def candidate_terms_from_tables(tables: List[pd.DataFrame], source_label: str) -> pd.DataFrame:
    frames = []
    for df in tables:
        if df is not None and not df.empty:
            frames.append(df.copy())
    if not frames:
        return pd.DataFrame()

    terms = pd.concat(frames, ignore_index=True, sort=False).fillna("")
    terms["semantic_review_status"] = "pending"
    terms["candidate_reason"] = source_label
    terms["suggested_family"] = ""

    # Hints only; no final semantic normalization.
    family_patterns = [
        ("transference_countertransference", r"\b(transference|countertransference|enactment|enactments)\b"),
        ("object_relations", r"\b(object|objects|object-relations|internal object|projective|identification|splitting)\b"),
        ("self_narcissism", r"\b(self|selfobject|selfobjects|narcissism|narcissistic)\b"),
        ("development_attachment", r"\b(infant|infancy|child|children|mother|maternal|attachment|development|developmental)\b"),
        ("affect_trauma_regulation", r"\b(affect|affective|emotion|emotional|trauma|traumatic|regulation|dissociation|shame)\b"),
        ("relational_intersubjective", r"\b(relational|intersubjective|intersubjectivity|field|dialogue|mutual)\b"),
        ("technique_process", r"\b(interpretation|technique|treatment|therapy|therapeutic|process|analytic)\b"),
        ("language_narrative_meaning", r"\b(language|narrative|meaning|symbolization|symbolisation|representation|metaphor)\b"),
        ("culture_social_ethics", r"\b(culture|cultural|race|racial|gender|social|ethics|ethical)\b"),
        ("body_sexuality", r"\b(body|bodily|corporeality|sexual|sexuality|gender)\b"),
    ]
    for family, pattern in family_patterns:
        mask = terms["term"].astype(str).str.contains(pattern, regex=True, case=False, na=False)
        terms.loc[mask & terms["suggested_family"].eq(""), "suggested_family"] = family

    # Put human-audit columns at end.
    cols = list(terms.columns)
    return terms[cols]


def make_period_summary(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for period, g in df.groupby("period", dropna=False):
        rows.append({
            "period": period,
            "n_records": int(len(g)),
            "n_journals": int(g["journal_key"].nunique()) if "journal_key" in g.columns else "",
            "min_year": str(g["year_for_analysis"].min()) if "year_for_analysis" in g.columns else "",
            "max_year": str(g["year_for_analysis"].max()) if "year_for_analysis" in g.columns else "",
        })
    out = pd.DataFrame(rows)
    if not out.empty:
        order = {label: i for i, (label, _, _) in enumerate(DEFAULT_PERIODS)}
        out["_order"] = out["period"].map(order).fillna(999)
        out = out.sort_values(["_order", "period"]).drop(columns=["_order"])
    return out


def write_scope_outputs(
    df: pd.DataFrame,
    out_dir: Path,
    stem: str,
    top_n: int,
    scope_label: str,
) -> Dict[str, str]:
    out_dir.mkdir(parents=True, exist_ok=True)

    clean_path = out_dir / f"{stem}_ART_title_abstract_clean.csv"
    quality_path = out_dir / f"{stem}_text_quality_summary.csv"
    top_terms_path = out_dir / f"{stem}_top_terms.csv"
    top_bigrams_path = out_dir / f"{stem}_top_bigrams.csv"
    top_trigrams_path = out_dir / f"{stem}_top_trigrams.csv"
    top_terms_by_period_path = out_dir / f"{stem}_top_terms_by_period.csv"
    candidates_path = out_dir / f"{stem}_candidate_terms_for_semantic_map.csv"
    period_summary_path = out_dir / f"{stem}_period_summary.csv"
    summary_path = out_dir / f"{stem}_title_abstract_recon_summary.json"

    write_csv(df, clean_path)

    quality = make_quality_summary(df, label=scope_label)
    write_csv(quality, quality_path)

    top_terms = count_top_terms(df["text_for_analysis"].fillna("").astype(str), ngram_n=1, top_n=top_n)
    top_bigrams = count_top_terms(df["text_for_analysis"].fillna("").astype(str), ngram_n=2, top_n=top_n)
    top_trigrams = count_top_terms(df["text_for_analysis"].fillna("").astype(str), ngram_n=3, top_n=top_n)

    write_csv(top_terms, top_terms_path)
    write_csv(top_bigrams, top_bigrams_path)
    write_csv(top_trigrams, top_trigrams_path)

    top_terms_by_period = count_by_group(df, ["period"], "text_for_analysis", ngram_n=1, top_n=min(top_n, 100))
    write_csv(top_terms_by_period, top_terms_by_period_path)

    candidates = candidate_terms_from_tables(
        [
            top_terms.head(top_n),
            top_bigrams.head(top_n),
            top_trigrams.head(top_n),
        ],
        source_label=f"{scope_label}_high_frequency_recon",
    )
    write_csv(candidates, candidates_path)

    period_summary = make_period_summary(df)
    write_csv(period_summary, period_summary_path)

    summary = {
        "script_version": SCRIPT_VERSION,
        "created_at_utc": utc_now_iso(),
        "scope": scope_label,
        "n_records": int(len(df)),
        "n_journals": int(df["journal_key"].nunique()) if "journal_key" in df.columns else None,
        "years": {
            "min": str(df["year_for_analysis"].min()) if "year_for_analysis" in df.columns and len(df) else "",
            "max": str(df["year_for_analysis"].max()) if "year_for_analysis" in df.columns and len(df) else "",
        },
        "period_counts": df["period"].value_counts(dropna=False).to_dict() if "period" in df.columns else {},
        "outputs": {
            "clean": str(clean_path),
            "quality": str(quality_path),
            "top_terms": str(top_terms_path),
            "top_bigrams": str(top_bigrams_path),
            "top_trigrams": str(top_trigrams_path),
            "top_terms_by_period": str(top_terms_by_period_path),
            "candidate_terms": str(candidates_path),
            "period_summary": str(period_summary_path),
            "summary_json": str(summary_path),
        },
    }
    write_json(summary, summary_path)
    return summary["outputs"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Title+abstract reconnaissance for psychoanalytic_core.")
    parser.add_argument(
        "--input",
        default="../data/qa/global/psychoanalytic_core_articles_ART_only_with_abstracts.csv",
        help="Global ART-only title+abstract CSV.",
    )
    parser.add_argument(
        "--out-root",
        default="../data/title_abstract",
        help="Output root directory.",
    )
    parser.add_argument("--top-n", type=int, default=250)
    parser.add_argument(
        "--journal-col",
        default="",
        help="Optional explicit journal column name.",
    )
    args = parser.parse_args()

    paths = get_paths()

    input_path = Path(args.input)
    if not input_path.is_absolute():
        input_path = (paths["scripts_dir"] / input_path).resolve()

    out_root = Path(args.out_root)
    if not out_root.is_absolute():
        out_root = (paths["scripts_dir"] / out_root).resolve()

    global_dir = out_root / "global"
    by_journal_root = out_root / "by_journal"
    global_dir.mkdir(parents=True, exist_ok=True)
    by_journal_root.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        raise SystemExit(f"ERROR: input not found: {input_path}")

    df = read_csv_safe(input_path)

    title_col = choose_col(df, ["title", "article_title"])
    abstract_col = choose_col(df, ["abstract_text"])
    year_col = choose_col(df, ["year", "year_record", "publication_year", "harvest_year_from_filename"])
    journal_col = args.journal_col or choose_col(df, ["journal_key", "journal"])

    if title_col is None:
        raise SystemExit("ERROR: title column not found.")
    if abstract_col is None:
        raise SystemExit("ERROR: abstract_text column not found.")
    if year_col is None:
        raise SystemExit("ERROR: year column not found.")
    if journal_col is None:
        raise SystemExit("ERROR: journal_key/journal column not found.")

    out = df.copy()
    if journal_col != "journal_key":
        out["journal_key"] = out[journal_col].fillna("").astype(str)
    else:
        out["journal_key"] = out["journal_key"].fillna("").astype(str)

    out["title_clean"] = out[title_col].apply(clean_text_basic)
    out["abstract_clean"] = out[abstract_col].apply(clean_text_basic)
    out["text_for_analysis"] = (
        out["title_clean"].fillna("").astype(str).str.strip()
        + ". "
        + out["abstract_clean"].fillna("").astype(str).str.strip()
    ).str.strip()

    out["year_for_analysis"] = pd.to_numeric(out[year_col], errors="coerce").astype("Int64").astype(str)
    out["period"] = out[year_col].apply(assign_period)

    out["flag_possible_html_artifact"] = out["text_for_analysis"].str.contains(
        r"<[^>]+>|&[a-z]+;", case=False, regex=True, na=False
    )
    out["flag_possible_copyright_artifact"] = out["text_for_analysis"].str.contains(
        r"copyrighted material|authorized users|reproduction prohibited|pep-web copyright",
        case=False,
        regex=True,
        na=False,
    )
    out["title_word_count"] = out["title_clean"].apply(word_count)
    out["abstract_word_count"] = out["abstract_clean"].apply(word_count)
    out["text_word_count"] = out["text_for_analysis"].apply(word_count)

    # Global clean and global scope outputs.
    global_clean_path = global_dir / "psychoanalytic_core_ART_title_abstract_clean.csv"
    write_csv(out, global_clean_path)

    global_quality = make_quality_summary(out, label="psychoanalytic_core")
    quality_by_journal = make_quality_by_group(out, ["journal_key"])
    quality_by_period = make_quality_by_group(out, ["period"])
    quality_by_journal_period = make_quality_by_group(out, ["journal_key", "period"])

    write_csv(global_quality, global_dir / "psychoanalytic_core_text_quality_summary.csv")
    write_csv(quality_by_journal, global_dir / "psychoanalytic_core_text_quality_by_journal.csv")
    write_csv(quality_by_period, global_dir / "psychoanalytic_core_text_quality_by_period.csv")
    write_csv(quality_by_journal_period, global_dir / "psychoanalytic_core_text_quality_by_journal_period.csv")

    top_terms_global = count_top_terms(out["text_for_analysis"], 1, args.top_n)
    top_bigrams_global = count_top_terms(out["text_for_analysis"], 2, args.top_n)
    top_trigrams_global = count_top_terms(out["text_for_analysis"], 3, args.top_n)

    write_csv(top_terms_global, global_dir / "psychoanalytic_core_top_terms_global.csv")
    write_csv(top_bigrams_global, global_dir / "psychoanalytic_core_top_bigrams_global.csv")
    write_csv(top_trigrams_global, global_dir / "psychoanalytic_core_top_trigrams_global.csv")

    top_terms_by_journal = count_by_group(out, ["journal_key"], "text_for_analysis", 1, min(args.top_n, 150))
    top_bigrams_by_journal = count_by_group(out, ["journal_key"], "text_for_analysis", 2, min(args.top_n, 150))
    top_trigrams_by_journal = count_by_group(out, ["journal_key"], "text_for_analysis", 3, min(args.top_n, 150))
    top_terms_by_period = count_by_group(out, ["period"], "text_for_analysis", 1, min(args.top_n, 150))
    top_bigrams_by_period = count_by_group(out, ["period"], "text_for_analysis", 2, min(args.top_n, 150))
    top_terms_by_journal_period = count_by_group(out, ["journal_key", "period"], "text_for_analysis", 1, 75)

    write_csv(top_terms_by_journal, global_dir / "psychoanalytic_core_top_terms_by_journal.csv")
    write_csv(top_bigrams_by_journal, global_dir / "psychoanalytic_core_top_bigrams_by_journal.csv")
    write_csv(top_trigrams_by_journal, global_dir / "psychoanalytic_core_top_trigrams_by_journal.csv")
    write_csv(top_terms_by_period, global_dir / "psychoanalytic_core_top_terms_by_period.csv")
    write_csv(top_bigrams_by_period, global_dir / "psychoanalytic_core_top_bigrams_by_period.csv")
    write_csv(top_terms_by_journal_period, global_dir / "psychoanalytic_core_top_terms_by_journal_period.csv")

    global_candidates = candidate_terms_from_tables(
        [
            top_terms_global.head(args.top_n),
            top_bigrams_global.head(args.top_n),
            top_trigrams_global.head(args.top_n),
            top_terms_by_journal.head(args.top_n * max(out["journal_key"].nunique(), 1)),
            top_terms_by_period.head(args.top_n),
        ],
        source_label="global_and_comparative_high_frequency_recon",
    )
    write_csv(global_candidates, global_dir / "psychoanalytic_core_candidate_terms_for_semantic_map.csv")

    period_summary = make_period_summary(out)
    write_csv(period_summary, global_dir / "psychoanalytic_core_period_summary.csv")

    # Per-journal outputs.
    journal_outputs = {}
    journals = [j for j in JOURNAL_ORDER if j in set(out["journal_key"])]
    journals += sorted(set(out["journal_key"]) - set(journals))

    for journal in journals:
        g = out[out["journal_key"] == journal].copy()
        j_dir = by_journal_root / journal
        outputs = write_scope_outputs(
            g,
            j_dir,
            stem=journal,
            top_n=args.top_n,
            scope_label=journal,
        )
        journal_outputs[journal] = outputs

    # A short global summary JSON.
    global_summary = {
        "script_version": SCRIPT_VERSION,
        "created_at_utc": utc_now_iso(),
        "input": str(input_path),
        "n_records": int(len(out)),
        "n_journals": int(out["journal_key"].nunique()),
        "journals": journals,
        "periods": [label for label, _, _ in DEFAULT_PERIODS],
        "policy": {
            "stage": "title_abstract_recon",
            "semantic_normalization_performed": False,
            "final_interpretation_performed": False,
            "main_text_field": "text_for_analysis",
            "main_text_formula": "title_clean + '. ' + abstract_clean",
            "global_and_per_journal_outputs": True,
        },
        "quality_flags": {
            "possible_html_artifact_rows": int(out["flag_possible_html_artifact"].sum()),
            "possible_copyright_artifact_rows": int(out["flag_possible_copyright_artifact"].sum()),
            "very_short_abstract_lt_80_chars": int((out["abstract_clean"].str.len() < 80).sum()),
        },
        "outputs": {
            "global_clean": str(global_clean_path),
            "global_text_quality_summary": str(global_dir / "psychoanalytic_core_text_quality_summary.csv"),
            "global_text_quality_by_journal": str(global_dir / "psychoanalytic_core_text_quality_by_journal.csv"),
            "global_text_quality_by_period": str(global_dir / "psychoanalytic_core_text_quality_by_period.csv"),
            "global_top_terms": str(global_dir / "psychoanalytic_core_top_terms_global.csv"),
            "global_top_bigrams": str(global_dir / "psychoanalytic_core_top_bigrams_global.csv"),
            "global_top_trigrams": str(global_dir / "psychoanalytic_core_top_trigrams_global.csv"),
            "global_top_terms_by_journal": str(global_dir / "psychoanalytic_core_top_terms_by_journal.csv"),
            "global_top_bigrams_by_journal": str(global_dir / "psychoanalytic_core_top_bigrams_by_journal.csv"),
            "global_top_terms_by_period": str(global_dir / "psychoanalytic_core_top_terms_by_period.csv"),
            "global_top_terms_by_journal_period": str(global_dir / "psychoanalytic_core_top_terms_by_journal_period.csv"),
            "global_candidate_terms": str(global_dir / "psychoanalytic_core_candidate_terms_for_semantic_map.csv"),
            "global_period_summary": str(global_dir / "psychoanalytic_core_period_summary.csv"),
            "by_journal_root": str(by_journal_root),
        },
        "by_journal_outputs": journal_outputs,
    }

    summary_path = global_dir / "psychoanalytic_core_title_abstract_recon_summary.json"
    write_json(global_summary, summary_path)
    global_summary["outputs"]["summary_json"] = str(summary_path)

    print(json.dumps({
        "status": "ok",
        "script_version": SCRIPT_VERSION,
        "n_records": global_summary["n_records"],
        "n_journals": global_summary["n_journals"],
        "journals": journals,
        "summary_json": str(summary_path),
        "main_clean_file": str(global_clean_path),
        "by_journal_root": str(by_journal_root),
        "quality_flags": global_summary["quality_flags"],
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
