#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Andromeda Nowicka — title corpus builder

Builds an auditable title-corpus layer from a raw bibliographic scrape directory.

Input:
  *_articles.csv
  *_scrape_log.csv       optional
  *_scrape_summary.json  optional
  *_keywords_long.csv    optional, may be empty

Output:
  QA files + title-pipeline input: worldcorpus_titles_input.csv
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Iterable

import pandas as pd


TITLE_COLUMNS = [
    "article_id",
    "doi",
    "article_url",
    "source_issue_url",
    "journal_key",
    "journal_title",
    "year",
    "volume",
    "issue_number",
    "title_raw",
    "title_clean_initial",
    "authors",
    "publication_date",
    "online_publication_date",
    "article_type",
    "abstract_text",
    "n_keywords",
]


def read_csv_files(files: Iterable[Path], source_col: str = "source_file") -> pd.DataFrame:
    frames = []
    for path in files:
        try:
            df = pd.read_csv(path)
        except pd.errors.EmptyDataError:
            df = pd.DataFrame()
        df[source_col] = path.name
        frames.append(df)
    return pd.concat(frames, ignore_index=True, sort=False) if frames else pd.DataFrame()


def clean_object_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:
        if df[col].dtype == "object" or str(df[col].dtype).startswith("string"):
            df[col] = df[col].astype("string").str.strip()
            df.loc[df[col].isin(["", "nan", "None", "NONE", "null", "NULL", "<NA>"]), col] = pd.NA
    return df


def normalize_doi(value):
    if pd.isna(value):
        return pd.NA
    s = str(value).strip()
    s = re.sub(r"^https?://(dx\.)?doi\.org/", "", s, flags=re.I)
    s = re.sub(r"^doi:\s*", "", s, flags=re.I)
    s = s.strip().lower()
    return s if s else pd.NA


def clean_title_initial(value):
    if pd.isna(value):
        return pd.NA
    s = re.sub(r"\s+", " ", str(value)).strip()
    return s if s else pd.NA


def first_existing(df: pd.DataFrame, candidates: list[str]) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def ensure_column(df: pd.DataFrame, col: str, default=pd.NA) -> pd.DataFrame:
    if col not in df.columns:
        df[col] = default
    return df


def load_summaries(summary_files: list[Path]) -> pd.DataFrame:
    rows = []
    for path in summary_files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                data["source_file"] = path.name
                rows.append(data)
        except Exception as exc:
            rows.append({"source_file": path.name, "summary_read_error": str(exc)})
    return pd.DataFrame(rows)


def pct(num: int | float, den: int | float) -> float:
    return round((num / den * 100), 2) if den else 0.0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build QA layer and title-pipeline input from raw bibliographic scrape."
    )
    parser.add_argument("--raw-dir", required=True, help="Directory containing *_articles.csv files.")
    parser.add_argument("--qa-dir", required=True, help="Directory for QA outputs.")
    parser.add_argument("--title-dir", required=True, help="Directory for title-pipeline input.")
    parser.add_argument("--from-year", type=int, default=None)
    parser.add_argument("--to-year", type=int, default=None)
    parser.add_argument(
        "--dedup-key",
        default="auto",
        choices=["auto", "article_id", "doi", "article_url", "title_year_journal"],
    )
    args = parser.parse_args()

    raw_dir = Path(args.raw_dir)
    qa_dir = Path(args.qa_dir)
    title_dir = Path(args.title_dir)
    qa_dir.mkdir(parents=True, exist_ok=True)
    title_dir.mkdir(parents=True, exist_ok=True)

    article_files = sorted(raw_dir.glob("*_articles.csv"))
    log_files = sorted(raw_dir.glob("*_scrape_log.csv"))
    keyword_files = sorted(raw_dir.glob("*_keywords_long.csv"))
    summary_files = sorted(raw_dir.glob("*_scrape_summary.json"))

    if not article_files:
        raise FileNotFoundError(f"No *_articles.csv files found in {raw_dir}")

    articles = clean_object_columns(read_csv_files(article_files))
    logs = clean_object_columns(read_csv_files(log_files)) if log_files else pd.DataFrame()
    summaries = load_summaries(summary_files) if summary_files else pd.DataFrame()

    title_col = first_existing(articles, ["title", "article_title", "title_raw"])
    if title_col is None:
        raise ValueError("No title column found. Expected one of: title, article_title, title_raw.")

    articles["title_raw"] = articles[title_col].map(clean_title_initial)
    articles["title_clean_initial"] = articles["title_raw"].map(clean_title_initial)

    if "year" in articles.columns:
        articles["year"] = pd.to_numeric(articles["year"], errors="coerce").astype("Int64")
    else:
        articles["year"] = pd.NA

    if "doi" in articles.columns:
        articles["doi_norm"] = articles["doi"].map(normalize_doi)
    else:
        articles["doi"] = pd.NA
        articles["doi_norm"] = pd.NA

    for col in [
        "article_id", "article_url", "source_issue_url", "journal_key", "journal_title",
        "volume", "issue_number", "authors", "publication_date", "online_publication_date",
        "article_type", "abstract_text", "n_keywords",
    ]:
        articles = ensure_column(articles, col, pd.NA)

    if articles["journal_title"].isna().all() and "journal_key" in articles.columns:
        articles["journal_title"] = articles["journal_key"]

    if args.dedup_key == "auto":
        if articles["doi_norm"].notna().any():
            dedup_strategy = "doi_norm"
            dedup_cols = ["doi_norm"]
        elif articles["article_id"].notna().any():
            dedup_strategy = "article_id"
            dedup_cols = ["article_id"]
        elif articles["article_url"].notna().any():
            dedup_strategy = "article_url"
            dedup_cols = ["article_url"]
        else:
            dedup_strategy = "title_year_journal"
            dedup_cols = ["journal_key", "year", "title_clean_initial"]
    elif args.dedup_key == "doi":
        dedup_strategy = "doi_norm"
        dedup_cols = ["doi_norm"]
    elif args.dedup_key == "title_year_journal":
        dedup_strategy = "title_year_journal"
        dedup_cols = ["journal_key", "year", "title_clean_initial"]
    else:
        dedup_strategy = args.dedup_key
        dedup_cols = [args.dedup_key]

    # Avoid collapsing all missing DOI records into one row.
    if dedup_strategy == "doi_norm":
        with_doi = articles[articles["doi_norm"].notna()].copy()
        without_doi = articles[articles["doi_norm"].isna()].copy()
        duplicates_doi = with_doi[with_doi.duplicated(subset=dedup_cols, keep=False)].copy()
        dedup_with_doi = with_doi.drop_duplicates(subset=dedup_cols, keep="first").copy()

        if without_doi["article_id"].notna().any():
            duplicates_no_doi = without_doi[without_doi.duplicated(subset=["article_id"], keep=False)].copy()
            dedup_without_doi = without_doi.drop_duplicates(subset=["article_id"], keep="first").copy()
        else:
            fallback = ["journal_key", "year", "title_clean_initial"]
            duplicates_no_doi = without_doi[without_doi.duplicated(subset=fallback, keep=False)].copy()
            dedup_without_doi = without_doi.drop_duplicates(subset=fallback, keep="first").copy()

        duplicates = pd.concat([duplicates_doi, duplicates_no_doi], ignore_index=True, sort=False)
        articles_dedup = pd.concat([dedup_with_doi, dedup_without_doi], ignore_index=True, sort=False)
    else:
        duplicates = articles[articles.duplicated(subset=dedup_cols, keep=False)].copy()
        articles_dedup = articles.drop_duplicates(subset=dedup_cols, keep="first").copy()

    articles_dedup["in_scope_year"] = True
    if args.from_year is not None:
        articles_dedup.loc[articles_dedup["year"].notna(), "in_scope_year"] = (
            articles_dedup.loc[articles_dedup["year"].notna(), "year"] >= args.from_year
        )
    if args.to_year is not None:
        articles_dedup.loc[articles_dedup["year"].notna(), "in_scope_year"] = (
            articles_dedup.loc[articles_dedup["year"].notna(), "in_scope_year"]
            & (articles_dedup.loc[articles_dedup["year"].notna(), "year"] <= args.to_year)
        )

    articles_missing_year = articles_dedup[articles_dedup["year"].isna()].copy()
    articles_out_of_scope = articles_dedup[articles_dedup["in_scope_year"] == False].copy()
    articles_in_scope = articles_dedup[
        (articles_dedup["in_scope_year"] == True) | articles_dedup["year"].isna()
    ].copy()

    articles_without_title = articles_in_scope[articles_in_scope["title_clean_initial"].isna()].copy()
    title_input = articles_in_scope[articles_in_scope["title_clean_initial"].notna()].copy()

    articles.to_csv(qa_dir / "worldcorpus_articles_raw_combined.csv", index=False)
    articles_dedup.to_csv(qa_dir / "worldcorpus_articles_dedup.csv", index=False)
    duplicates.to_csv(qa_dir / "worldcorpus_articles_duplicates.csv", index=False)
    articles_without_title.to_csv(qa_dir / "worldcorpus_articles_without_title.csv", index=False)
    articles_missing_year.to_csv(qa_dir / "worldcorpus_articles_missing_year.csv", index=False)
    articles_out_of_scope.to_csv(qa_dir / "worldcorpus_articles_out_of_scope.csv", index=False)

    if not logs.empty:
        logs.to_csv(qa_dir / "worldcorpus_scrape_log_combined.csv", index=False)
        if "event" in logs.columns:
            logs["event"].value_counts().rename_axis("event").reset_index(name="n").to_csv(
                qa_dir / "worldcorpus_scrape_log_event_summary.csv", index=False
            )

    if not summaries.empty:
        summaries.to_csv(qa_dir / "worldcorpus_scrape_summary_combined.csv", index=False)

    keyword_rows = []
    for kf in keyword_files:
        try:
            kdf = pd.read_csv(kf)
            keyword_rows.append({
                "source_file": kf.name,
                "n_rows": int(len(kdf)),
                "n_columns": int(len(kdf.columns)),
                "columns": "|".join(map(str, kdf.columns)),
            })
        except pd.errors.EmptyDataError:
            keyword_rows.append({"source_file": kf.name, "n_rows": 0, "n_columns": 0, "columns": ""})
        except Exception as exc:
            keyword_rows.append({"source_file": kf.name, "n_rows": None, "n_columns": None, "columns": "", "read_error": str(exc)})

    keyword_summary = pd.DataFrame(keyword_rows)
    if not keyword_summary.empty:
        keyword_summary.to_csv(qa_dir / "worldcorpus_keyword_files_summary.csv", index=False)

    by_journal_year = (
        title_input.groupby(["journal_key", "year"], dropna=False)
        .agg(
            n_articles=("title_clean_initial", "size"),
            n_with_doi=("doi_norm", lambda s: int(s.notna().sum())),
            n_with_abstract=("abstract_text", lambda s: int(s.notna().sum())),
        )
        .reset_index()
        .sort_values(["journal_key", "year"])
    )
    by_journal_year.to_csv(qa_dir / "worldcorpus_articles_by_journal_year.csv", index=False)

    journal_summary = (
        title_input.groupby("journal_key", dropna=False)
        .agg(
            n_articles=("title_clean_initial", "size"),
            year_min=("year", "min"),
            year_max=("year", "max"),
            n_with_doi=("doi_norm", lambda s: int(s.notna().sum())),
            n_with_abstract=("abstract_text", lambda s: int(s.notna().sum())),
            n_unique_titles=("title_clean_initial", "nunique"),
        )
        .reset_index()
        .sort_values("n_articles", ascending=False)
    )
    journal_summary["doi_coverage_pct"] = journal_summary.apply(lambda r: pct(r["n_with_doi"], r["n_articles"]), axis=1)
    journal_summary["abstract_coverage_pct"] = journal_summary.apply(lambda r: pct(r["n_with_abstract"], r["n_articles"]), axis=1)
    journal_summary.to_csv(qa_dir / "worldcorpus_journal_summary.csv", index=False)

    for col in TITLE_COLUMNS:
        title_input = ensure_column(title_input, col, pd.NA)

    title_input_out = title_input[TITLE_COLUMNS].copy()
    title_input_out.to_csv(title_dir / "worldcorpus_titles_input.csv", index=False)

    total_keyword_rows = int(keyword_summary["n_rows"].fillna(0).sum()) if not keyword_summary.empty else 0
    summary = {
        "raw_dir": str(raw_dir),
        "qa_dir": str(qa_dir),
        "title_dir": str(title_dir),
        "n_article_files": len(article_files),
        "n_log_files": len(log_files),
        "n_summary_files": len(summary_files),
        "n_keyword_files": len(keyword_files),
        "raw_article_rows": int(len(articles)),
        "dedup_article_rows": int(len(articles_dedup)),
        "duplicate_rows_flagged": int(len(duplicates)),
        "dedup_strategy": dedup_strategy,
        "dedup_columns": dedup_cols,
        "in_scope_title_rows": int(len(title_input_out)),
        "articles_without_title": int(len(articles_without_title)),
        "articles_missing_year": int(len(articles_missing_year)),
        "articles_out_of_scope": int(len(articles_out_of_scope)),
        "year_min": int(title_input_out["year"].min()) if title_input_out["year"].notna().any() else None,
        "year_max": int(title_input_out["year"].max()) if title_input_out["year"].notna().any() else None,
        "n_journals": int(title_input_out["journal_key"].nunique(dropna=True)),
        "n_with_doi": int(title_input_out["doi"].notna().sum()),
        "doi_coverage_pct": pct(int(title_input_out["doi"].notna().sum()), len(title_input_out)),
        "n_with_abstract": int(title_input_out["abstract_text"].notna().sum()),
        "abstract_coverage_pct": pct(int(title_input_out["abstract_text"].notna().sum()), len(title_input_out)),
        "total_keyword_rows_in_raw_keyword_files": total_keyword_rows,
    }

    (qa_dir / "worldcorpus_qa_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    report = f"""# World corpus — QA and title-corpus extraction report

## Purpose

This report documents the extraction of a title-based analytical corpus from an immutable raw bibliographic scrape.

## Input

- Raw directory: `{summary["raw_dir"]}`
- Article files detected: {summary["n_article_files"]}
- Scrape-log files detected: {summary["n_log_files"]}
- Scrape-summary files detected: {summary["n_summary_files"]}
- Keyword-long files detected: {summary["n_keyword_files"]}

## Main counts

- Raw article rows: {summary["raw_article_rows"]}
- Deduplicated article rows: {summary["dedup_article_rows"]}
- Duplicate rows flagged: {summary["duplicate_rows_flagged"]}
- Deduplication strategy: `{summary["dedup_strategy"]}`
- Deduplication columns: `{summary["dedup_columns"]}`

## Title-corpus output

- In-scope title rows: {summary["in_scope_title_rows"]}
- Articles without title: {summary["articles_without_title"]}
- Articles missing year: {summary["articles_missing_year"]}
- Articles outside requested year scope: {summary["articles_out_of_scope"]}
- Year range in title corpus: {summary["year_min"]}–{summary["year_max"]}
- Journals represented: {summary["n_journals"]}
- DOI coverage: {summary["doi_coverage_pct"]}%
- Abstract coverage: {summary["abstract_coverage_pct"]}%

## Keyword status

Total rows found in raw keyword-long files: {summary["total_keyword_rows_in_raw_keyword_files"]}

If this value is zero or near zero, the dataset should not be interpreted as an author-keyword corpus. It should be treated as a bibliographic/title corpus unless additional keyword metadata are obtained from a reliable external export.

## Main output files

QA layer:

- `worldcorpus_articles_raw_combined.csv`
- `worldcorpus_articles_dedup.csv`
- `worldcorpus_articles_duplicates.csv`
- `worldcorpus_articles_without_title.csv`
- `worldcorpus_articles_missing_year.csv`
- `worldcorpus_articles_out_of_scope.csv`
- `worldcorpus_articles_by_journal_year.csv`
- `worldcorpus_journal_summary.csv`
- `worldcorpus_keyword_files_summary.csv`
- `worldcorpus_qa_summary.json`

Title-pipeline input:

- `worldcorpus_titles_input.csv`

## Methodological note

The raw layer is preserved as an immutable source layer. This script creates a derived title-corpus input table for downstream title-based discourse mapping. Article titles are treated as standardized, consistently available indicators of article self-presentation, not as substitutes for full-text discourse analysis.
"""
    (qa_dir / "worldcorpus_qa_report.md").write_text(report, encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print("\\nCreated:")
    print(f"- {qa_dir / 'worldcorpus_qa_report.md'}")
    print(f"- {qa_dir / 'worldcorpus_journal_summary.csv'}")
    print(f"- {title_dir / 'worldcorpus_titles_input.csv'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
