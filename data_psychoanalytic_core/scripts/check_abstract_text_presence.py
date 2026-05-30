#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_abstract_text_presence.py

Quick diagnostic for psychoanalytic_core ART-only table.

Purpose
-------
Check whether the global ART-only corpus contains actual abstract text,
not only abstract flags.

Default input:
    ../data/qa/global/psychoanalytic_core_articles_ART_only.csv

Run from:
    data_psychoanalytic_core/scripts/

Usage:
    python check_abstract_text_presence.py

Optional:
    python check_abstract_text_presence.py --input ../data/qa/global/psychoanalytic_core_articles_ART_only.csv
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd


def read_csv_safe(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")


def is_probably_flag_series(s: pd.Series) -> bool:
    vals = (
        s.fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
        .value_counts()
        .head(20)
        .index
        .tolist()
    )
    allowed = {"", "true", "false", "yes", "no", "0", "1", "nan", "none"}
    return bool(vals) and all(v in allowed for v in vals)


def clean_preview(x: str, n: int = 350) -> str:
    x = str(x or "")
    x = re.sub(r"\s+", " ", x).strip()
    return x[:n]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="../data/qa/global/psychoanalytic_core_articles_ART_only.csv",
        help="Path to ART-only global corpus CSV.",
    )
    parser.add_argument(
        "--out-json",
        default="../data/qa/global/psychoanalytic_core_abstract_presence_diagnostic.json",
    )
    parser.add_argument(
        "--out-samples",
        default="../data/qa/global/psychoanalytic_core_abstract_presence_samples.csv",
    )
    args = parser.parse_args()

    input_path = Path(args.input).resolve()
    out_json = Path(args.out_json).resolve()
    out_samples = Path(args.out_samples).resolve()

    if not input_path.exists():
        raise SystemExit(f"ERROR: input file not found: {input_path}")

    df = read_csv_safe(input_path)
    n = len(df)

    abstract_like_cols = [
        c for c in df.columns
        if "abstract" in c.lower() or c.lower() in {"abs", "summary"}
    ]

    journal_col = next((c for c in ["journal_key", "journal", "source_title"] if c in df.columns), None)
    year_col = next((c for c in ["year", "year_record", "publication_year"] if c in df.columns), None)
    id_col = next((c for c in ["article_id", "document_id", "pep_document_id", "id"] if c in df.columns), None)
    title_col = next((c for c in ["title", "article_title"] if c in df.columns), None)

    col_summaries = []
    sample_rows = []

    for col in abstract_like_cols:
        s = df[col].fillna("").astype(str).str.strip()
        lengths = s.str.len()
        nonempty = s.ne("")
        probably_flag = is_probably_flag_series(s)

        long_text_mask = lengths >= 80
        real_text_mask = nonempty & ~probably_flag & long_text_mask

        summary = {
            "column": col,
            "n_nonempty": int(nonempty.sum()),
            "pct_nonempty": round(float(nonempty.mean() * 100), 2) if n else 0.0,
            "median_length_nonempty": float(lengths[nonempty].median()) if nonempty.any() else 0.0,
            "max_length": int(lengths.max()) if n else 0,
            "n_length_ge_80": int(long_text_mask.sum()),
            "pct_length_ge_80": round(float(long_text_mask.mean() * 100), 2) if n else 0.0,
            "probably_flag_column": bool(probably_flag),
            "likely_contains_abstract_text": bool(real_text_mask.sum() > 0),
            "n_likely_text_rows": int(real_text_mask.sum()),
        }
        col_summaries.append(summary)

        sample_idx = lengths.sort_values(ascending=False).head(10).index.tolist()
        for idx in sample_idx:
            row = df.loc[idx]
            sample_rows.append({
                "abstract_column": col,
                "row_index": int(idx),
                "length": int(lengths.loc[idx]),
                "journal_key": row.get(journal_col, "") if journal_col else "",
                "year": row.get(year_col, "") if year_col else "",
                "article_id": row.get(id_col, "") if id_col else "",
                "title": clean_preview(row.get(title_col, ""), 180) if title_col else "",
                "abstract_preview": clean_preview(row.get(col, ""), 600),
            })

    by_journal = []
    if journal_col and abstract_like_cols:
        for col in abstract_like_cols:
            s = df[col].fillna("").astype(str).str.strip()
            tmp = df[[journal_col]].copy()
            tmp["_nonempty"] = s.ne("")
            tmp["_len_ge_80"] = s.str.len().ge(80)
            g = tmp.groupby(journal_col, dropna=False).agg(
                n_records=("_nonempty", "size"),
                n_nonempty=("_nonempty", "sum"),
                n_len_ge_80=("_len_ge_80", "sum"),
            ).reset_index()
            g["abstract_column"] = col
            g["pct_nonempty"] = (g["n_nonempty"] / g["n_records"] * 100).round(2)
            g["pct_len_ge_80"] = (g["n_len_ge_80"] / g["n_records"] * 100).round(2)
            by_journal.extend(g.to_dict(orient="records"))

    diagnostic = {
        "input": str(input_path),
        "n_rows": int(n),
        "n_columns": int(len(df.columns)),
        "columns": list(df.columns),
        "abstract_like_columns": abstract_like_cols,
        "column_summaries": col_summaries,
        "by_journal": by_journal,
        "interpretation_hint": (
            "A real abstract text column should have many non-empty values, "
            "median length well above simple boolean flags, and previews containing sentences. "
            "A flag-only column will usually contain values such as true/false or 0/1."
        ),
        "outputs": {
            "json": str(out_json),
            "samples_csv": str(out_samples),
        },
    }

    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(diagnostic, ensure_ascii=False, indent=2), encoding="utf-8")

    samples_df = pd.DataFrame(sample_rows)
    out_samples.parent.mkdir(parents=True, exist_ok=True)
    samples_df.to_csv(out_samples, index=False, encoding="utf-8-sig")

    print(json.dumps({
        "input": str(input_path),
        "n_rows": int(n),
        "abstract_like_columns": abstract_like_cols,
        "column_summaries": col_summaries,
        "samples_csv": str(out_samples),
        "json": str(out_json),
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
