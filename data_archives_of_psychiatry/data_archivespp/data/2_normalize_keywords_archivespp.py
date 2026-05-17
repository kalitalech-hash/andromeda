#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Etap 2 pipeline'u APP: konserwatywna normalizacja techniczna keywordów.

Wejście:
    app_articles_dedup_2005_2025.csv
    app_keywords_long_dedup_2005_2025.csv

Wyjście:
    app_keywords_long_normalized.csv
    app_keyword_normalization_map.csv
    app_keyword_top30_normalized.csv
    app_keyword_normalization_collisions.csv
    app_keyword_candidate_merges_for_review.csv
    app_keyword_suspicious_after_normalization.csv
    app_articles_without_keywords_after_normalization.csv
    app_normalization_summary.json
    app_normalization_report.md
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
import difflib

import pandas as pd


def normalize_keyword(s) -> str:
    if pd.isna(s):
        return ""
    raw = str(s)
    x = unicodedata.normalize("NFKC", raw)
    x = x.replace("\u00a0", " ").replace("\u200b", "")
    trans = {
        ord("’"): "'", ord("‘"): "'", ord("`"): "'", ord("´"): "'",
        ord("“"): '"', ord("”"): '"', ord("„"): '"', ord("‟"): '"',
        ord("–"): "-", ord("—"): "-", ord("−"): "-", ord("‐"): "-", ord("‑"): "-",
    }
    x = x.translate(trans)
    x = re.sub(r"\s+", " ", x).strip()
    x = x.strip(" \t\r\n\"'")
    x = x.lower()
    x = re.sub(r"\s*&\s*", " and ", x)
    x = re.sub(r"\s*/\s*", "/", x)
    x = re.sub(r"\s*-\s*", "-", x)
    x = re.sub(r"\s*,\s*", ", ", x)
    x = re.sub(r"\s*;\s*", "; ", x)
    x = re.sub(r"\(\s+", "(", x)
    x = re.sub(r"\s+\)", ")", x)
    x = re.sub(r"\s+([,.;:?!])", r"\1", x)
    x = re.sub(r"[.;:,]+$", "", x).strip()
    x = re.sub(r"\s+", " ", x).strip()
    x = re.sub(r"-{2,}", "-", x)
    return x


def transformations(raw, norm) -> str:
    raw_s = str(raw)
    tr = []
    if raw_s != unicodedata.normalize("NFKC", raw_s):
        tr.append("unicode_nfkc")
    if raw_s.strip() != raw_s:
        tr.append("trim")
    if re.search(r"\s{2,}|\u00a0|\u200b", raw_s):
        tr.append("whitespace")
    if raw_s.lower() != raw_s:
        tr.append("lowercase")
    if any(ch in raw_s for ch in "’‘`´“”„‟–—−‐‑"):
        tr.append("typographic_chars")
    if re.search(r"\s+-\s+|\s+-|-\s+", raw_s):
        tr.append("hyphen_spacing")
    if re.search(r"\s/|/\s", raw_s):
        tr.append("slash_spacing")
    if re.search(r"\(\s+|\s+\)", raw_s):
        tr.append("parentheses_spacing")
    if "&" in raw_s:
        tr.append("ampersand_to_and")
    if re.search(r"[.;:,]\s*$", raw_s):
        tr.append("trailing_punctuation")
    if not tr:
        if raw_s == norm:
            tr.append("unchanged")
        else:
            tr.append("other_technical")
    return "|".join(tr)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--indir", default="../data")
    parser.add_argument("--outdir", default="../data")
    parser.add_argument("--articles", default="app_articles_dedup_2005_2025.csv")
    parser.add_argument("--keywords", default="app_keywords_long_dedup_2005_2025.csv")
    args = parser.parse_args()

    indir = Path(args.indir)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    art = pd.read_csv(indir / args.articles)
    kw = pd.read_csv(indir / args.keywords)
    kw["keyword_raw"] = kw["keyword_raw"].fillna("").astype(str)
    kw["keyword_norm"] = kw["keyword_raw"].apply(normalize_keyword)
    kw["normalization_actions"] = [
        transformations(r, n) for r, n in zip(kw["keyword_raw"], kw["keyword_norm"])
    ]

    unique_norm = sorted(kw["keyword_norm"].dropna().unique())
    norm_id = {v: f"app_kw_{i:04d}" for i, v in enumerate(unique_norm, start=1)}
    kw["keyword_norm_id"] = kw["keyword_norm"].map(norm_id)

    mapping = (
        kw.groupby(["keyword_raw", "keyword_norm", "keyword_norm_id", "normalization_actions"], dropna=False)
        .agg(
            n_records=("article_id", "size"),
            n_articles=("article_id", "nunique"),
            first_year=("year", "min"),
            last_year=("year", "max"),
        )
        .reset_index()
        .sort_values(["keyword_norm", "keyword_raw"])
    )

    top_norm = (
        kw.groupby("keyword_norm")
        .agg(
            n_records=("article_id", "size"),
            n_articles=("article_id", "nunique"),
            first_year=("year", "min"),
            last_year=("year", "max"),
            variants=("keyword_raw", lambda x: " | ".join(sorted(set(map(str, x)))[:12])),
        )
        .reset_index()
        .sort_values(["n_records", "keyword_norm"], ascending=[False, True])
    )

    collisions = (
        mapping.groupby("keyword_norm")
        .agg(
            n_raw_variants=("keyword_raw", "nunique"),
            raw_variants=("keyword_raw", lambda x: " | ".join(sorted(set(map(str, x))))),
            total_records=("n_records", "sum"),
            n_articles=("n_articles", "sum"),
        )
        .reset_index()
    )
    collisions = collisions[collisions["n_raw_variants"] > 1].sort_values(
        ["n_raw_variants", "total_records"], ascending=[False, False]
    )

    norm_counts = kw["keyword_norm"].value_counts()
    terms = list(norm_counts.index)
    cands = []
    for i, a in enumerate(terms):
        if len(a) < 5:
            continue
        for b in terms[i + 1:]:
            if len(b) < 5:
                continue
            if a[0] != b[0] and a not in b and b not in a:
                continue
            ratio = difflib.SequenceMatcher(None, a, b).ratio()
            containment = (a in b or b in a) and abs(len(a) - len(b)) <= 12
            if ratio >= 0.88 or containment:
                cands.append({
                    "keyword_norm_a": a,
                    "keyword_norm_b": b,
                    "count_a": int(norm_counts[a]),
                    "count_b": int(norm_counts[b]),
                    "similarity": round(ratio, 3),
                    "candidate_reason": "string_similarity" if ratio >= 0.88 else "containment",
                    "decision_status": "review_required",
                })
    cands_df = pd.DataFrame(cands).sort_values(
        ["similarity", "count_a", "count_b"], ascending=[False, False, False]
    ).head(300) if cands else pd.DataFrame()

    suspicious_rows = []
    for _, row in kw.iterrows():
        k = row["keyword_norm"]
        flags = []
        if re.fullmatch(r"\d+", k):
            flags.append("numeric_only")
        if len(k) <= 2:
            flags.append("very_short")
        if re.search(r"\beditorial\b", k):
            flags.append("contains_editorial")
        if re.search(r"\b(article|issue)\b", k):
            flags.append("contains_article_issue")
        if "?" in k:
            flags.append("question_mark")
        if flags:
            d = row.to_dict()
            d["qa_flags"] = "|".join(flags)
            suspicious_rows.append(d)
    suspicious = pd.DataFrame(suspicious_rows)

    articles_with_kw = set(kw.loc[kw["keyword_norm"].ne(""), "article_id"])
    art_no_kw = art[~art["article_id"].isin(articles_with_kw)].copy()

    kw.to_csv(outdir / "app_keywords_long_normalized.csv", index=False, encoding="utf-8-sig")
    mapping.to_csv(outdir / "app_keyword_normalization_map.csv", index=False, encoding="utf-8-sig")
    top_norm.head(30).to_csv(outdir / "app_keyword_top30_normalized.csv", index=False, encoding="utf-8-sig")
    collisions.to_csv(outdir / "app_keyword_normalization_collisions.csv", index=False, encoding="utf-8-sig")
    cands_df.to_csv(outdir / "app_keyword_candidate_merges_for_review.csv", index=False, encoding="utf-8-sig")
    suspicious.to_csv(outdir / "app_keyword_suspicious_after_normalization.csv", index=False, encoding="utf-8-sig")
    art_no_kw.to_csv(outdir / "app_articles_without_keywords_after_normalization.csv", index=False, encoding="utf-8-sig")

    summary = {
        "input_articles": int(len(art)),
        "input_keyword_records": int(len(kw)),
        "unique_keyword_raw_input": int(kw["keyword_raw"].nunique()),
        "output_keyword_records": int(len(kw)),
        "unique_keyword_norm_output": int(kw["keyword_norm"].nunique()),
        "raw_variants_merged_by_technical_normalization": int(kw["keyword_raw"].nunique() - kw["keyword_norm"].nunique()),
        "normalized_forms_with_multiple_raw_variants": int(len(collisions)),
        "empty_normalized_keywords": int((kw["keyword_norm"] == "").sum()),
        "articles_without_keywords_after_normalization": int(len(art_no_kw)),
        "candidate_merge_pairs_for_manual_review": int(len(cands_df)),
        "year_min": int(kw["year"].min()),
        "year_max": int(kw["year"].max()),
        "actions_counts": dict(Counter("|".join(kw["normalization_actions"]).split("|"))),
    }
    (outdir / "app_normalization_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
