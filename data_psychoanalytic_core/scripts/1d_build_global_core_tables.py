#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1d_build_global_core_tables.py

Andromeda Nowicka v0.4/v0.5-pre
Build global psychoanalytic_core tables from per-journal QA outputs.

Purpose
-------
After running:

    1b_pep_full_metadata_harvest.py
    1c_consolidate_and_qa_harvest.py --journal all

this script builds the actual multi-journal corpus tables:

- psychoanalytic_core_articles_raw_consolidated.csv
- psychoanalytic_core_articles_ART_only.csv
- psychoanalytic_core_excluded_non_ART.csv
- psychoanalytic_core_keywords_long_raw_consolidated.csv
- psychoanalytic_core_journal_summary.csv
- psychoanalytic_core_year_summary.csv
- psychoanalytic_core_journal_year_summary.csv
- psychoanalytic_core_article_type_summary.csv
- psychoanalytic_core_field_completeness.csv
- psychoanalytic_core_duplicate_article_id.csv
- psychoanalytic_core_global_build_summary_<run_id>.json

It does NOT download anything. It only merges existing local QA outputs.

Main analytical rule
--------------------
The main analytical article corpus is:

    article_type == "ART"

All non-ART records are retained in the raw consolidated table and in an explicit
excluded_non_ART audit table.

Run location
------------
Put this file in:

    data_psychoanalytic_core/scripts/

Run:

    cd data_psychoanalytic_core/scripts
    python 1d_build_global_core_tables.py
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

import pandas as pd


SCRIPT_VERSION = "v0.1.0"

JOURNALS = [
    "ijpa",
    "japa",
    "psychoanalytic_dialogues",
    "psychoanalytic_psychology",
    "psychoanalytic_psychotherapy",
]

JOURNAL_LABELS = {
    "ijpa": "The International Journal of Psychoanalysis",
    "japa": "Journal of the American Psychoanalytic Association",
    "psychoanalytic_dialogues": "Psychoanalytic Dialogues",
    "psychoanalytic_psychology": "Psychoanalytic Psychology",
    "psychoanalytic_psychotherapy": "Psychoanalytic Psychotherapy",
}

PEP_PREFIXES = {
    "ijpa": "IJP",
    "japa": "APA",
    "psychoanalytic_dialogues": "PD",
    "psychoanalytic_psychology": "PPSY",
    "psychoanalytic_psychotherapy": "PPTX",
}


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def get_paths() -> Dict[str, Path]:
    scripts_dir = Path(__file__).resolve().parent
    project_root = scripts_dir.parent
    qa_root = project_root / "data" / "qa"
    global_root = qa_root / "global"
    return {
        "scripts_dir": scripts_dir,
        "project_root": project_root,
        "qa_root": qa_root,
        "global_root": global_root,
        "summaries": qa_root / "summaries",
        "articles_raw": qa_root / "articles_raw",
        "articles_ART_only": qa_root / "articles_ART_only",
        "excluded_non_ART": qa_root / "excluded_non_ART",
        "keywords_long_raw": qa_root / "keywords_long_raw",
    }


def ensure_dirs(paths: Dict[str, Path]) -> None:
    paths["global_root"].mkdir(parents=True, exist_ok=True)
    paths["summaries"].mkdir(parents=True, exist_ok=True)


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


def choose_col(df: pd.DataFrame, candidates: Iterable[str]) -> Optional[str]:
    lower = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c in df.columns:
            return c
        real = lower.get(c.lower())
        if real:
            return real
    return None


def nonempty_mask(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip().ne("")


def add_journal_metadata(df: pd.DataFrame, journal: str) -> pd.DataFrame:
    if df.empty:
        return df
    out = df.copy()
    if "journal_key" not in out.columns or out["journal_key"].fillna("").astype(str).str.strip().eq("").all():
        out["journal_key"] = journal
    if "journal_label" not in out.columns:
        out["journal_label"] = JOURNAL_LABELS.get(journal, journal)
    if "pep_prefix" not in out.columns:
        out["pep_prefix"] = PEP_PREFIXES.get(journal, "")
    return out


def load_per_journal_tables(paths: Dict[str, Path], journal: str) -> Dict[str, pd.DataFrame]:
    files = {
        "articles_raw": paths["articles_raw"] / f"{journal}_articles_raw_consolidated.csv",
        "articles_ART_only": paths["articles_ART_only"] / f"{journal}_articles_ART_only.csv",
        "excluded_non_ART": paths["excluded_non_ART"] / f"{journal}_excluded_non_ART.csv",
        "keywords_long_raw": paths["keywords_long_raw"] / f"{journal}_keywords_long_raw_consolidated.csv",
    }

    tables = {}
    for key, path in files.items():
        df = read_csv_safe(path)
        if not df.empty:
            df = add_journal_metadata(df, journal)
        tables[key] = df
    return tables


def concat_tables(tables: List[pd.DataFrame]) -> pd.DataFrame:
    nonempty = [df for df in tables if not df.empty]
    if not nonempty:
        return pd.DataFrame()
    return pd.concat(nonempty, ignore_index=True, sort=False).fillna("")


def make_article_type_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["article_type", "n_records", "pct_records"])

    article_type_col = choose_col(df, ["article_type", "document_type", "type"])
    if article_type_col is None:
        return pd.DataFrame(columns=["article_type", "n_records", "pct_records"])

    out = (
        df[article_type_col]
        .fillna("")
        .astype(str)
        .str.strip()
        .replace("", "(missing)")
        .value_counts(dropna=False)
        .rename_axis("article_type")
        .reset_index(name="n_records")
    )
    total = max(int(out["n_records"].sum()), 1)
    out["pct_records"] = (out["n_records"] / total * 100).round(2)
    return out


def make_journal_summary(articles_raw: pd.DataFrame, keywords: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for journal in JOURNALS:
        a = articles_raw[articles_raw["journal_key"] == journal] if "journal_key" in articles_raw.columns else pd.DataFrame()
        k = keywords[keywords["journal_key"] == journal] if "journal_key" in keywords.columns else pd.DataFrame()

        article_type_col = choose_col(a, ["article_type", "document_type", "type"]) if not a.empty else None
        abstract_col = choose_col(a, ["abstract_text", "abstract", "abstract_clean"]) if not a.empty else None
        doi_col = choose_col(a, ["doi", "DOI"]) if not a.empty else None
        title_col = choose_col(a, ["title", "article_title"]) if not a.empty else None
        authors_col = choose_col(a, ["authors", "author", "author_names"]) if not a.empty else None
        article_id_col = choose_col(a, ["article_id", "document_id", "pep_document_id", "id"]) if not a.empty else None

        n = len(a)
        n_art = int((a[article_type_col].fillna("").astype(str).str.strip() == "ART").sum()) if article_type_col else 0
        rows.append({
            "journal_key": journal,
            "journal_label": JOURNAL_LABELS.get(journal, journal),
            "pep_prefix": PEP_PREFIXES.get(journal, ""),
            "article_rows_raw": int(n),
            "unique_article_ids": int(a[article_id_col].nunique()) if article_id_col else "",
            "n_ART": n_art,
            "n_non_ART": int(n - n_art),
            "pct_ART": round(n_art / max(n, 1) * 100, 2),
            "keyword_rows": int(len(k)),
            "n_with_abstract": int(nonempty_mask(a[abstract_col]).sum()) if abstract_col else "",
            "pct_with_abstract": round(int(nonempty_mask(a[abstract_col]).sum()) / max(n, 1) * 100, 2) if abstract_col else "",
            "n_with_doi": int(nonempty_mask(a[doi_col]).sum()) if doi_col else "",
            "n_with_title": int(nonempty_mask(a[title_col]).sum()) if title_col else "",
            "n_with_authors": int(nonempty_mask(a[authors_col]).sum()) if authors_col else "",
        })
    return pd.DataFrame(rows)


def make_year_summary(df: pd.DataFrame, by_journal: bool = False) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    year_col = choose_col(df, ["year", "year_record", "publication_year", "query_year", "harvest_year_from_filename"])
    article_type_col = choose_col(df, ["article_type", "document_type", "type"])
    abstract_col = choose_col(df, ["abstract_text", "abstract", "abstract_clean"])
    doi_col = choose_col(df, ["doi", "DOI"])
    title_col = choose_col(df, ["title", "article_title"])
    authors_col = choose_col(df, ["authors", "author", "author_names"])

    if year_col is None:
        return pd.DataFrame()

    group_cols = ["journal_key", year_col] if by_journal and "journal_key" in df.columns else [year_col]

    rows = []
    for key, g in df.groupby(group_cols, dropna=False):
        if by_journal and "journal_key" in df.columns:
            journal, year = key
            row = {"journal_key": journal, "year": year}
        else:
            year = key
            row = {"year": year}

        row["n_records_raw"] = int(len(g))
        if article_type_col:
            row["n_ART"] = int((g[article_type_col].fillna("").astype(str).str.strip() == "ART").sum())
            row["n_non_ART"] = int(len(g) - row["n_ART"])
        if abstract_col:
            row["n_with_abstract"] = int(nonempty_mask(g[abstract_col]).sum())
        if doi_col:
            row["n_with_doi"] = int(nonempty_mask(g[doi_col]).sum())
        if title_col:
            row["n_with_title"] = int(nonempty_mask(g[title_col]).sum())
        if authors_col:
            row["n_with_authors"] = int(nonempty_mask(g[authors_col]).sum())
        rows.append(row)

    out = pd.DataFrame(rows)
    try:
        out["_sort_year"] = pd.to_numeric(out["year"], errors="coerce")
        sort_cols = ["journal_key", "_sort_year", "year"] if by_journal and "journal_key" in out.columns else ["_sort_year", "year"]
        out = out.sort_values(sort_cols).drop(columns=["_sort_year"])
    except Exception:
        pass
    return out


def make_keyword_year_summary(keywords: pd.DataFrame, by_journal: bool = False) -> pd.DataFrame:
    if keywords.empty:
        return pd.DataFrame(columns=["year", "n_keyword_rows"])

    year_col = choose_col(keywords, ["year", "query_year", "harvest_year_from_filename"])
    if year_col is None:
        return pd.DataFrame({"n_keyword_rows": [len(keywords)]})

    group_cols = ["journal_key", year_col] if by_journal and "journal_key" in keywords.columns else [year_col]
    out = keywords.groupby(group_cols, dropna=False).size().reset_index(name="n_keyword_rows")
    out = out.rename(columns={year_col: "year"})
    try:
        out["_sort_year"] = pd.to_numeric(out["year"], errors="coerce")
        sort_cols = ["journal_key", "_sort_year", "year"] if by_journal and "journal_key" in out.columns else ["_sort_year", "year"]
        out = out.sort_values(sort_cols).drop(columns=["_sort_year"])
    except Exception:
        pass
    return out


def make_field_completeness(df: pd.DataFrame) -> pd.DataFrame:
    fields = [
        "article_id", "journal_key", "journal_label", "pep_prefix", "source_title",
        "year", "volume", "issue_number", "title", "authors", "pages", "doi",
        "article_type", "abstract_text", "n_keywords", "keyword_extraction_source",
    ]
    rows = []
    n = len(df)
    lower = {c.lower(): c for c in df.columns}
    for field in fields:
        col = lower.get(field.lower())
        if col is None:
            rows.append({
                "field": field,
                "present_as_column": False,
                "actual_column": "",
                "n_nonempty": 0,
                "pct_nonempty": 0.0,
            })
        else:
            n_nonempty = int(nonempty_mask(df[col]).sum())
            rows.append({
                "field": field,
                "present_as_column": True,
                "actual_column": col,
                "n_nonempty": n_nonempty,
                "pct_nonempty": round(n_nonempty / max(n, 1) * 100, 2),
            })
    return pd.DataFrame(rows)


def make_duplicate_article_id(df: pd.DataFrame) -> pd.DataFrame:
    article_id_col = choose_col(df, ["article_id", "document_id", "pep_document_id", "id"])
    if df.empty or article_id_col is None:
        return pd.DataFrame()
    vals = df[article_id_col].fillna("").astype(str).str.strip()
    counts = vals[vals.ne("")].value_counts()
    dup_ids = counts[counts > 1]
    if dup_ids.empty:
        return pd.DataFrame(columns=[article_id_col, "duplicate_count"])
    out = df[df[article_id_col].isin(dup_ids.index)].copy()
    out["duplicate_count"] = out[article_id_col].map(dup_ids).astype(str)
    return out.sort_values([article_id_col])


def main() -> int:
    parser = argparse.ArgumentParser(description="Build global psychoanalytic_core tables.")
    parser.add_argument("--run-id", default=None)
    args = parser.parse_args()

    run_id = args.run_id or dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    paths = get_paths()
    ensure_dirs(paths)

    per_journal = {journal: load_per_journal_tables(paths, journal) for journal in JOURNALS}

    articles_raw = concat_tables([per_journal[j]["articles_raw"] for j in JOURNALS])
    articles_art = concat_tables([per_journal[j]["articles_ART_only"] for j in JOURNALS])
    excluded_non_art = concat_tables([per_journal[j]["excluded_non_ART"] for j in JOURNALS])
    keywords = concat_tables([per_journal[j]["keywords_long_raw"] for j in JOURNALS])

    out = paths["global_root"]

    articles_raw_path = out / "psychoanalytic_core_articles_raw_consolidated.csv"
    articles_art_path = out / "psychoanalytic_core_articles_ART_only.csv"
    excluded_path = out / "psychoanalytic_core_excluded_non_ART.csv"
    keywords_path = out / "psychoanalytic_core_keywords_long_raw_consolidated.csv"

    write_csv(articles_raw, articles_raw_path)
    write_csv(articles_art, articles_art_path)
    write_csv(excluded_non_art, excluded_path)
    write_csv(keywords, keywords_path)

    journal_summary = make_journal_summary(articles_raw, keywords)
    year_summary = make_year_summary(articles_raw, by_journal=False)
    journal_year_summary = make_year_summary(articles_raw, by_journal=True)
    keyword_year_summary = make_keyword_year_summary(keywords, by_journal=False)
    keyword_journal_year_summary = make_keyword_year_summary(keywords, by_journal=True)
    article_type_summary = make_article_type_summary(articles_raw)
    field_completeness = make_field_completeness(articles_raw)
    dup_article_id = make_duplicate_article_id(articles_raw)

    paths_out = {
        "journal_summary": out / "psychoanalytic_core_journal_summary.csv",
        "year_summary": out / "psychoanalytic_core_year_summary.csv",
        "journal_year_summary": out / "psychoanalytic_core_journal_year_summary.csv",
        "keyword_year_summary": out / "psychoanalytic_core_keyword_year_summary.csv",
        "keyword_journal_year_summary": out / "psychoanalytic_core_keyword_journal_year_summary.csv",
        "article_type_summary": out / "psychoanalytic_core_article_type_summary.csv",
        "field_completeness": out / "psychoanalytic_core_field_completeness.csv",
        "duplicate_article_id": out / "psychoanalytic_core_duplicate_article_id.csv",
    }

    write_csv(journal_summary, paths_out["journal_summary"])
    write_csv(year_summary, paths_out["year_summary"])
    write_csv(journal_year_summary, paths_out["journal_year_summary"])
    write_csv(keyword_year_summary, paths_out["keyword_year_summary"])
    write_csv(keyword_journal_year_summary, paths_out["keyword_journal_year_summary"])
    write_csv(article_type_summary, paths_out["article_type_summary"])
    write_csv(field_completeness, paths_out["field_completeness"])
    write_csv(dup_article_id, paths_out["duplicate_article_id"])

    summary = {
        "run_id": run_id,
        "script_version": SCRIPT_VERSION,
        "created_at_utc": utc_now_iso(),
        "policy": {
            "metadata_first": True,
            "downloads": "none",
            "main_analytical_corpus": "psychoanalytic_core_articles_ART_only.csv",
            "main_corpus_rule": "article_type == 'ART'",
            "non_ART_handling": "retained in raw and explicit excluded_non_ART audit table",
            "keywords_handling": "supplementary metadata layer, historically uneven",
        },
        "totals": {
            "articles_raw": int(len(articles_raw)),
            "articles_ART_only": int(len(articles_art)),
            "excluded_non_ART": int(len(excluded_non_art)),
            "keyword_rows": int(len(keywords)),
            "duplicate_article_id_rows": int(len(dup_article_id)),
        },
        "journals": JOURNALS,
        "outputs": {
            "articles_raw": str(articles_raw_path),
            "articles_ART_only": str(articles_art_path),
            "excluded_non_ART": str(excluded_path),
            "keywords_long_raw": str(keywords_path),
            **{k: str(v) for k, v in paths_out.items()},
        },
    }

    summary_path = paths["summaries"] / f"psychoanalytic_core_global_build_summary_{run_id}.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    summary["outputs"]["summary_json"] = str(summary_path)

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
