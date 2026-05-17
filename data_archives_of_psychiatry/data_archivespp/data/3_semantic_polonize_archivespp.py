#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Etap 3 ArchivesPP: polonizacja i konserwatywne scalenie semantyczne keywordów.

Uwaga: pełna mapa decyzyjna znajduje się w pliku
`app_keyword_semantic_polish_map.csv`. Ten skrypt w repozytorium można
rozbudować, importując mapę i nakładając ją na `app_keywords_long_normalized.csv`.
"""

from pathlib import Path
import pandas as pd

BASE = Path(__file__).resolve().parents[1]
DATA = BASE / "data"

keywords = pd.read_csv(DATA / "app_keywords_long_normalized.csv")
semantic_map = pd.read_csv(DATA / "app_keyword_semantic_polish_map.csv")

out = keywords.merge(semantic_map, on="keyword_norm", how="left", validate="many_to_one")
out.to_csv(DATA / "app_keywords_long_polish_semantic.csv", index=False, encoding="utf-8-sig")

concept_counts = (
    out.groupby(["keyword_semantic_id", "keyword_final_en", "keyword_final_polish"], dropna=False)
    .agg(
        n_keyword_records=("keyword_raw", "size"),
        n_articles=("article_id", "nunique"),
        n_raw_variants=("keyword_raw", "nunique"),
        n_norm_variants=("keyword_norm", "nunique"),
        first_year=("year", "min"),
        last_year=("year", "max"),
    )
    .reset_index()
    .sort_values(["n_keyword_records", "keyword_final_en"], ascending=[False, True])
)
concept_counts.to_csv(DATA / "app_keyword_semantic_concept_counts.csv", index=False, encoding="utf-8-sig")
print("Saved semantic Polish layer and concept counts.")
