#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1c_consolidate_and_qa_harvest.py

Andromeda Nowicka v0.4/v0.5-pre
Consolidate and QA PEP metadata harvest outputs for data_psychoanalytic_core.

Purpose
-------
This script consolidates per-year harvest CSV files produced by:

    1b_pep_full_metadata_harvest.py

It creates:
- one raw consolidated article table per journal,
- one raw consolidated keyword-long table per journal,
- one ART-only analytical article table per journal,
- one excluded non-ART audit table per journal,
- article type summaries,
- year coverage summaries,
- field completeness summaries,
- duplicate checks,
- one JSON QA summary per run.

It does NOT download anything. It works only on local harvest outputs.

Article type policy
-------------------
Main downstream analytical corpus:

    article_type == "ART"

All non-ART records are retained in raw consolidated outputs and written to an
explicit exclusion/audit table.

Run location
------------
Put this file in:

    data_psychoanalytic_core/scripts/

Run for the first harvested journal:

    cd data_psychoanalytic_core/scripts
    python 1c_consolidate_and_qa_harvest.py --journal psychoanalytic_dialogues

Run later for all journals with available harvest outputs:

    python 1c_consolidate_and_qa_harvest.py --journal all
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

JOURNALS = [
    "ijpa",
    "japa",
    "psychoanalytic_dialogues",
    "psychoanalytic_psychology",
    "psychoanalytic_psychotherapy",
]


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def get_paths() -> Dict[str, Path]:
    scripts_dir = Path(__file__).resolve().parent
    project_root = scripts_dir.parent
    return {
        "scripts_dir": scripts_dir,
        "project_root": project_root,
        "harvest_root": project_root / "data" / "harvest",
        "qa_root": project_root / "data" / "qa",
        "logs_root": project_root / "data" / "logs",
    }


def ensure_dirs(paths: Dict[str, Path]) -> None:
    for key in ["qa_root", "logs_root"]:
        paths[key].mkdir(parents=True, exist_ok=True)

    for sub in [
        "articles_raw",
        "articles_ART_only",
        "excluded_non_ART",
        "keywords_long_raw",
        "summaries",
        "duplicates",
        "field_completeness",
        "year_coverage",
        "article_type",
    ]:
        (paths["qa_root"] / sub).mkdir(parents=True, exist_ok=True)


def parse_journals(value: str) -> List[str]:
    if value == "all":
        return JOURNALS.copy()
    journals = [x.strip() for x in value.split(",") if x.strip()]
    unknown = [j for j in journals if j not in JOURNALS]
    if unknown:
        raise SystemExit(f"Unknown journal(s): {unknown}. Allowed: all, {', '.join(JOURNALS)}")
    return journals


def read_csv_safe(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    try:
        return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")


def list_year_files(base: Path, journal: str, kind: str) -> List[Path]:
    if kind == "articles":
        d = base / "articles_by_year" / journal
        pattern = f"{journal}_*_pep_articles_raw.csv"
    elif kind == "keywords":
        d = base / "keywords_by_year" / journal
        pattern = f"{journal}_*_pep_keywords_long_raw.csv"
    else:
        raise ValueError(kind)

    if not d.exists():
        return []

    def year_key(path: Path) -> int:
        m = re.search(r"_(\d{4})_pep_", path.name)
        return int(m.group(1)) if m else 999999

    return sorted(d.glob(pattern), key=year_key)


def extract_year_from_filename(path: Path) -> Optional[int]:
    m = re.search(r"_(\d{4})_pep_", path.name)
    return int(m.group(1)) if m else None


def load_year_files(files: List[Path], journal: str, file_kind: str) -> Tuple[pd.DataFrame, List[Dict[str, object]]]:
    frames = []
    manifest = []

    for path in files:
        df = read_csv_safe(path)
        year = extract_year_from_filename(path)

        manifest.append(
            {
                "journal": journal,
                "file_kind": file_kind,
                "year": year,
                "path": str(path),
                "rows": int(len(df)),
                "columns": list(df.columns),
            }
        )

        if len(df) == 0:
            continue

        if "harvest_file" not in df.columns:
            df["harvest_file"] = str(path)
        if "harvest_year_from_filename" not in df.columns:
            df["harvest_year_from_filename"] = str(year or "")

        frames.append(df)

    if not frames:
        return pd.DataFrame(), manifest

    return pd.concat(frames, ignore_index=True, sort=False).fillna(""), manifest


def choose_col(df: pd.DataFrame, candidates: Iterable[str]) -> Optional[str]:
    lower_map = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c in df.columns:
            return c
        real = lower_map.get(c.lower())
        if real:
            return real
    return None


def nonempty_mask(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip().ne("")


def make_article_type_summary(df: pd.DataFrame) -> pd.DataFrame:
    col = choose_col(df, ["article_type", "document_type", "type"])
    if col is None or df.empty:
        return pd.DataFrame(columns=["article_type", "n_records", "pct_records"])

    out = (
        df[col]
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


def make_year_summary(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    year_col = choose_col(df, ["year", "year_record", "publication_year", "query_year", "harvest_year_from_filename"])
    article_type_col = choose_col(df, ["article_type", "document_type", "type"])
    abstract_col = choose_col(df, ["abstract_text", "abstract", "abstract_clean"])
    doi_col = choose_col(df, ["doi", "DOI"])
    authors_col = choose_col(df, ["authors", "author", "author_names"])
    title_col = choose_col(df, ["title", "article_title"])

    work = df.copy()
    if year_col is None:
        work["_year_for_summary"] = work.get("harvest_year_from_filename", "")
        year_col = "_year_for_summary"

    rows = []
    for year, g in work.groupby(year_col, dropna=False):
        item = {"year": year, "n_records": int(len(g))}
        if article_type_col:
            item["n_ART"] = int((g[article_type_col].fillna("").astype(str).str.strip() == "ART").sum())
            item["n_non_ART"] = int(len(g) - item["n_ART"])
        if abstract_col:
            item["n_with_abstract"] = int(nonempty_mask(g[abstract_col]).sum())
        if doi_col:
            item["n_with_doi"] = int(nonempty_mask(g[doi_col]).sum())
        if authors_col:
            item["n_with_authors"] = int(nonempty_mask(g[authors_col]).sum())
        if title_col:
            item["n_with_title"] = int(nonempty_mask(g[title_col]).sum())
        rows.append(item)

    out = pd.DataFrame(rows)
    try:
        out["_sort_year"] = pd.to_numeric(out["year"], errors="coerce")
        out = out.sort_values(["_sort_year", "year"]).drop(columns=["_sort_year"])
    except Exception:
        pass
    return out


def make_field_completeness(df: pd.DataFrame, fields: List[str]) -> pd.DataFrame:
    rows = []
    n = len(df)
    lower_map = {c.lower(): c for c in df.columns}

    for field in fields:
        col = lower_map.get(field.lower())
        if col is None:
            rows.append(
                {
                    "field": field,
                    "present_as_column": False,
                    "actual_column": "",
                    "n_nonempty": 0,
                    "pct_nonempty": 0.0,
                }
            )
            continue
        n_nonempty = int(nonempty_mask(df[col]).sum())
        rows.append(
            {
                "field": field,
                "present_as_column": True,
                "actual_column": col,
                "n_nonempty": n_nonempty,
                "pct_nonempty": round(n_nonempty / max(n, 1) * 100, 2),
            }
        )
    return pd.DataFrame(rows)


def make_duplicate_tables(df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    out: Dict[str, pd.DataFrame] = {}
    if df.empty:
        return out

    for logical_name, candidates in {
        "article_id": ["article_id", "document_id", "pep_document_id", "id"],
        "article_url": ["article_url", "url"],
        "doi": ["doi", "DOI"],
    }.items():
        col = choose_col(df, candidates)
        if col is None:
            out[logical_name] = pd.DataFrame()
            continue
        vals = df[col].fillna("").astype(str).str.strip()
        nonempty = df[vals.ne("")].copy()
        dup_vals = vals[vals.ne("")].value_counts()
        dup_vals = dup_vals[dup_vals > 1]
        if dup_vals.empty:
            out[logical_name] = pd.DataFrame(columns=[col, "duplicate_count"])
            continue
        dup_df = nonempty[nonempty[col].isin(dup_vals.index)].copy()
        dup_df["duplicate_count"] = dup_df[col].map(dup_vals).astype(str)
        out[logical_name] = dup_df.sort_values([col])
    return out


def write_csv(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False, encoding="utf-8-sig")


def consolidate_one_journal(paths: Dict[str, Path], journal: str, run_id: str) -> Dict[str, object]:
    article_files = list_year_files(paths["harvest_root"], journal, "articles")
    keyword_files = list_year_files(paths["harvest_root"], journal, "keywords")

    articles, article_file_manifest = load_year_files(article_files, journal, "articles")
    keywords, keyword_file_manifest = load_year_files(keyword_files, journal, "keywords")

    if articles.empty:
        return {
            "journal": journal,
            "status": "no_article_files_or_empty",
            "n_article_files": len(article_files),
            "n_keyword_files": len(keyword_files),
            "article_rows": 0,
            "keyword_rows": int(len(keywords)),
        }

    articles_raw_path = paths["qa_root"] / "articles_raw" / f"{journal}_articles_raw_consolidated.csv"
    keywords_raw_path = paths["qa_root"] / "keywords_long_raw" / f"{journal}_keywords_long_raw_consolidated.csv"

    write_csv(articles, articles_raw_path)
    write_csv(keywords, keywords_raw_path)

    article_type_col = choose_col(articles, ["article_type", "document_type", "type"])
    if article_type_col is None:
        articles_art = pd.DataFrame(columns=list(articles.columns))
        excluded_non_art = articles.copy()
        excluded_non_art["exclusion_reason"] = "missing_article_type_column"
    else:
        is_art = articles[article_type_col].fillna("").astype(str).str.strip().eq("ART")
        articles_art = articles[is_art].copy()
        excluded_non_art = articles[~is_art].copy()
        excluded_non_art["exclusion_reason"] = "article_type_not_ART"

    articles_art_path = paths["qa_root"] / "articles_ART_only" / f"{journal}_articles_ART_only.csv"
    excluded_path = paths["qa_root"] / "excluded_non_ART" / f"{journal}_excluded_non_ART.csv"

    write_csv(articles_art, articles_art_path)
    write_csv(excluded_non_art, excluded_path)

    article_type_summary = make_article_type_summary(articles)
    year_summary = make_year_summary(articles)
    field_summary = make_field_completeness(
        articles,
        [
            "article_id",
            "journal_key",
            "source_title",
            "year",
            "volume",
            "issue_number",
            "title",
            "authors",
            "pages",
            "doi",
            "article_type",
            "abstract_text",
            "n_keywords",
            "keyword_extraction_source",
        ],
    )

    article_type_summary_path = paths["qa_root"] / "article_type" / f"{journal}_article_type_summary.csv"
    year_summary_path = paths["qa_root"] / "year_coverage" / f"{journal}_year_summary.csv"
    field_summary_path = paths["qa_root"] / "field_completeness" / f"{journal}_field_completeness.csv"

    write_csv(article_type_summary, article_type_summary_path)
    write_csv(year_summary, year_summary_path)
    write_csv(field_summary, field_summary_path)

    duplicate_paths = {}
    duplicate_counts = {}
    dup_tables = make_duplicate_tables(articles)
    for key, dup_df in dup_tables.items():
        p = paths["qa_root"] / "duplicates" / f"{journal}_duplicate_{key}.csv"
        write_csv(dup_df, p)
        duplicate_paths[key] = str(p)
        duplicate_counts[key] = int(len(dup_df))

    keyword_year_summary_path = paths["qa_root"] / "year_coverage" / f"{journal}_keyword_year_summary.csv"
    if not keywords.empty:
        kw_year_col = choose_col(keywords, ["year", "query_year", "harvest_year_from_filename"])
        if kw_year_col:
            kw_year_summary = (
                keywords.groupby(kw_year_col, dropna=False)
                .size()
                .reset_index(name="n_keyword_rows")
                .rename(columns={kw_year_col: "year"})
            )
        else:
            kw_year_summary = pd.DataFrame({"year": ["(unknown)"], "n_keyword_rows": [len(keywords)]})
    else:
        kw_year_summary = pd.DataFrame(columns=["year", "n_keyword_rows"])
    write_csv(kw_year_summary, keyword_year_summary_path)

    abstract_col = choose_col(articles, ["abstract_text", "abstract", "abstract_clean"])
    doi_col = choose_col(articles, ["doi", "DOI"])
    authors_col = choose_col(articles, ["authors", "author", "author_names"])
    title_col = choose_col(articles, ["title", "article_title"])
    article_id_col = choose_col(articles, ["article_id", "document_id", "pep_document_id", "id"])
    year_col = choose_col(articles, ["year", "year_record", "publication_year", "query_year", "harvest_year_from_filename"])

    n = len(articles)
    years = sorted(set(articles[year_col].astype(str))) if year_col else []

    metrics = {
        "journal": journal,
        "status": "ok",
        "n_article_files": len(article_files),
        "n_keyword_files": len(keyword_files),
        "article_rows": int(n),
        "keyword_rows": int(len(keywords)),
        "unique_article_ids": int(articles[article_id_col].nunique()) if article_id_col else None,
        "n_ART": int(len(articles_art)),
        "n_non_ART": int(len(excluded_non_art)),
        "pct_ART": round(len(articles_art) / max(n, 1) * 100, 2),
        "n_with_abstract": int(nonempty_mask(articles[abstract_col]).sum()) if abstract_col else None,
        "pct_with_abstract": round(int(nonempty_mask(articles[abstract_col]).sum()) / max(n, 1) * 100, 2) if abstract_col else None,
        "n_with_doi": int(nonempty_mask(articles[doi_col]).sum()) if doi_col else None,
        "n_with_authors": int(nonempty_mask(articles[authors_col]).sum()) if authors_col else None,
        "n_with_title": int(nonempty_mask(articles[title_col]).sum()) if title_col else None,
        "min_year": years[0] if years else None,
        "max_year": years[-1] if years else None,
        "duplicate_row_counts": duplicate_counts,
        "outputs": {
            "articles_raw_consolidated": str(articles_raw_path),
            "keywords_long_raw_consolidated": str(keywords_raw_path),
            "articles_ART_only": str(articles_art_path),
            "excluded_non_ART": str(excluded_path),
            "article_type_summary": str(article_type_summary_path),
            "year_summary": str(year_summary_path),
            "keyword_year_summary": str(keyword_year_summary_path),
            "field_completeness": str(field_summary_path),
            "duplicates": duplicate_paths,
        },
        "input_files": {
            "article_files": [str(p) for p in article_files],
            "keyword_files": [str(p) for p in keyword_files],
        },
        "file_manifests": {
            "articles": article_file_manifest,
            "keywords": keyword_file_manifest,
        },
    }

    journal_summary_path = paths["qa_root"] / "summaries" / f"{journal}_qa_summary_{run_id}.json"
    journal_summary_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    metrics["outputs"]["journal_summary_json"] = str(journal_summary_path)

    return metrics


def main() -> int:
    parser = argparse.ArgumentParser(description="Consolidate and QA PEP harvest outputs.")
    parser.add_argument(
        "--journal",
        default="psychoanalytic_dialogues",
        help=f"Journal key, comma-separated journal keys, or all. Known: {', '.join(JOURNALS)}",
    )
    parser.add_argument(
        "--run-id",
        default=None,
        help="Optional run id for output JSON names. Defaults to timestamp.",
    )

    args = parser.parse_args()

    paths = get_paths()
    ensure_dirs(paths)

    journals = parse_journals(args.journal)
    run_id = args.run_id or dt.datetime.now().strftime("%Y%m%d_%H%M%S")

    all_summaries = []
    for journal in journals:
        print(f"\n=== Consolidating {journal} ===")
        summary = consolidate_one_journal(paths, journal, run_id)
        all_summaries.append(summary)
        print(json.dumps(
            {
                "journal": summary.get("journal"),
                "status": summary.get("status"),
                "article_rows": summary.get("article_rows"),
                "keyword_rows": summary.get("keyword_rows"),
                "n_ART": summary.get("n_ART"),
                "n_non_ART": summary.get("n_non_ART"),
                "pct_ART": summary.get("pct_ART"),
                "n_with_abstract": summary.get("n_with_abstract"),
                "pct_with_abstract": summary.get("pct_with_abstract"),
            },
            ensure_ascii=False,
            indent=2,
        ))

    global_summary = {
        "run_id": run_id,
        "script_version": SCRIPT_VERSION,
        "created_at_utc": utc_now_iso(),
        "journals": journals,
        "policy": {
            "metadata_first": True,
            "downloads": "none",
            "main_downstream_corpus_rule": "article_type == 'ART'",
            "non_ART_handling": "retained in raw/audit, excluded from main analytical dataset",
        },
        "summaries": all_summaries,
        "totals": {
            "article_rows": sum(int(s.get("article_rows") or 0) for s in all_summaries),
            "keyword_rows": sum(int(s.get("keyword_rows") or 0) for s in all_summaries),
            "n_ART": sum(int(s.get("n_ART") or 0) for s in all_summaries),
            "n_non_ART": sum(int(s.get("n_non_ART") or 0) for s in all_summaries),
        },
    }

    out = paths["qa_root"] / "summaries" / f"psychoanalytic_core_harvest_qa_summary_{run_id}.json"
    out.write_text(json.dumps(global_summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\nGlobal QA summary:")
    print(json.dumps(
        {
            "summary_json": str(out),
            "totals": global_summary["totals"],
        },
        ensure_ascii=False,
        indent=2,
    ))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
