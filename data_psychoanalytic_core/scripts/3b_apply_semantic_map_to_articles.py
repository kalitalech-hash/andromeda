#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3b_apply_semantic_map_to_articles.py

Andromeda Nowicka v0.5-pre
Apply initial semantic map to ART-only title+abstract articles.

Purpose
-------
The first Stage 3 script (`3a_build_initial_semantic_families.py`) successfully
created the initial semantic map, review queue and unmapped queue, but the
article-level application step was too heavy in the first version.

This script separates the application step:

    existing semantic map
    + clean title/abstract corpus
    → article-level semantic family hits
    → family counts by journal, period, journal × period

It does NOT rebuild the semantic map and does NOT perform final interpretation.

Inputs
------
Semantic map from 3a:
    ../data/title_abstract/semantic/psychoanalytic_core_initial_semantic_map.csv

Clean title+abstract corpus from 2a:
    ../data/title_abstract/global/psychoanalytic_core_ART_title_abstract_clean.csv

Outputs
-------
../data/title_abstract/semantic_application/
    psychoanalytic_core_article_semantic_hits_long.csv
    psychoanalytic_core_article_semantic_hits_wide.csv
    psychoanalytic_core_initial_semantic_family_counts.csv
    psychoanalytic_core_semantic_family_by_journal.csv
    psychoanalytic_core_semantic_family_by_period.csv
    psychoanalytic_core_semantic_family_by_journal_period.csv
    psychoanalytic_core_semantic_family_article_share_by_journal.csv
    psychoanalytic_core_semantic_family_article_share_by_period.csv
    psychoanalytic_core_article_semantic_hit_count_distribution.csv
    psychoanalytic_core_semantic_family_term_counts.csv
    psychoanalytic_core_semantic_application_summary.json

Run
---
Put this file in:

    data_psychoanalytic_core/scripts/

Run:

    cd data_psychoanalytic_core/scripts
    python 3b_apply_semantic_map_to_articles.py
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
from pathlib import Path
from typing import Dict, Iterable, Optional, Tuple

import pandas as pd


SCRIPT_VERSION = "v0.1.0"

SEMANTIC_FAMILY_ORDER = [
    "drive_conflict_defense",
    "dream_fantasy_unconscious",
    "ego_self_narcissism",
    "object_relations",
    "kleinian_bionian",
    "winnicottian_environment_holding",
    "attachment_development_infant",
    "transference_countertransference",
    "technique_interpretation_process",
    "relational_intersubjective_field",
    "trauma_dissociation_affect_regulation",
    "psychosis_borderline_primitive_states",
    "body_sexuality_gender",
    "language_narrative_symbolization",
    "culture_race_social_ethics",
    "empirical_research_measurement",
    "history_theory_schools",
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
        "semantic_root": title_root / "semantic",
        "application_root": title_root / "semantic_application",
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


def choose_col(df: pd.DataFrame, candidates: Iterable[str]) -> Optional[str]:
    lower = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c in df.columns:
            return c
        real = lower.get(c.lower())
        if real:
            return real
    return None


def term_pattern(term: str) -> str:
    """
    Conservative pattern:
    - supports spaces/hyphens between multiword components,
    - permits simple plural s for single-token terms,
    - avoids matching inside longer words.
    """
    t = norm_term(term)
    if not t:
        return r"a^"

    parts = [p for p in re.split(r"[\s\-]+", t) if p]
    if not parts:
        return r"a^"

    escaped = [re.escape(p) for p in parts]

    if len(escaped) == 1:
        base = escaped[0]
        if base.endswith("s") or len(base) <= 3:
            return r"(?<![a-z])" + base + r"(?![a-z])"
        return r"(?<![a-z])" + base + r"s?(?![a-z])"

    return r"(?<![a-z])" + r"[\s\-]+".join(escaped) + r"(?![a-z])"


def build_family_patterns(sem_map: pd.DataFrame) -> Dict[str, Dict[str, object]]:
    if "semantic_action" not in sem_map.columns or "semantic_family" not in sem_map.columns:
        raise ValueError("Semantic map must contain semantic_action and semantic_family columns.")

    term_col = "term_norm" if "term_norm" in sem_map.columns else "term"
    mapped = sem_map.copy()
    mapped = mapped[mapped["semantic_action"].astype(str).eq("mapped_initial")]
    mapped = mapped[mapped["semantic_family"].astype(str).ne("")]
    mapped = mapped[mapped[term_col].astype(str).ne("")]

    family_patterns: Dict[str, Dict[str, object]] = {}

    for family in SEMANTIC_FAMILY_ORDER:
        g = mapped[mapped["semantic_family"] == family].copy()
        if g.empty:
            continue

        terms = sorted(
            {norm_term(x) for x in g[term_col].fillna("").astype(str) if norm_term(x)},
            key=lambda x: (-len(x), x),
        )

        if not terms:
            continue

        pattern_parts = [term_pattern(t) for t in terms]
        combined = re.compile("|".join(f"(?:{p})" for p in pattern_parts), flags=re.I)

        family_patterns[family] = {
            "terms": terms,
            "regex": combined,
        }

    return family_patterns


def find_family_hits(text: str, family_info: Dict[str, object]) -> list[str]:
    text_low = str(text or "").lower()

    combined = family_info["regex"]
    if not combined.search(text_low):
        return []

    hits = []
    for term in family_info["terms"]:
        if re.search(term_pattern(term), text_low, flags=re.I):
            hits.append(term)

    return sorted(set(hits))


def apply_map(
    articles: pd.DataFrame,
    family_patterns: Dict[str, Dict[str, object]],
    text_col: str,
    article_id_col: str,
    journal_col: str,
    period_col: str,
    year_col: Optional[str],
    title_col: Optional[str],
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    long_rows = []
    wide_rows = []

    for _, row in articles.iterrows():
        article_id = row.get(article_id_col, "")
        journal = row.get(journal_col, "")
        period = row.get(period_col, "")
        year = row.get(year_col, "") if year_col else ""
        title = row.get(title_col, "") if title_col else ""
        text = row.get(text_col, "")

        wide = {
            "article_id": article_id,
            "journal_key": journal,
            "year_for_analysis": year,
            "period": period,
            "title_clean": title,
        }

        total_term_hits = 0
        family_count = 0

        for family in SEMANTIC_FAMILY_ORDER:
            info = family_patterns.get(family)
            if not info:
                wide[f"family_{family}"] = 0
                wide[f"terms_{family}"] = ""
                continue

            hits = find_family_hits(text, info)
            n_hits = len(hits)
            total_term_hits += n_hits

            if n_hits:
                family_count += 1
                long_rows.append({
                    "article_id": article_id,
                    "journal_key": journal,
                    "year_for_analysis": year,
                    "period": period,
                    "semantic_family": family,
                    "n_terms_hit": n_hits,
                    "terms_hit": " | ".join(hits),
                    "title_clean": title,
                })

            wide[f"family_{family}"] = 1 if n_hits else 0
            wide[f"terms_{family}"] = " | ".join(hits)

        wide["n_semantic_families_hit"] = family_count
        wide["n_semantic_terms_hit"] = total_term_hits
        wide_rows.append(wide)

    return pd.DataFrame(long_rows), pd.DataFrame(wide_rows)


def family_counts(long_df: pd.DataFrame, articles_n: int) -> pd.DataFrame:
    if long_df.empty:
        return pd.DataFrame(columns=["semantic_family", "n_articles", "pct_articles", "n_family_hits", "total_terms_hit"])

    out = (
        long_df.groupby("semantic_family", dropna=False)
        .agg(
            n_articles=("article_id", "nunique"),
            n_family_hits=("article_id", "size"),
            total_terms_hit=("n_terms_hit", "sum"),
        )
        .reset_index()
    )
    out["pct_articles"] = (out["n_articles"] / max(articles_n, 1) * 100).round(4)
    out["_family_order"] = out["semantic_family"].map({f: i for i, f in enumerate(SEMANTIC_FAMILY_ORDER)}).fillna(999)
    return out.sort_values(["_family_order", "semantic_family"]).drop(columns=["_family_order"])


def family_by_group(long_df: pd.DataFrame, articles: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    if long_df.empty:
        return pd.DataFrame()

    article_denoms = (
        articles.groupby(group_cols, dropna=False)
        .agg(n_articles_group=("article_id", "nunique"))
        .reset_index()
    )

    counts = (
        long_df.groupby(group_cols + ["semantic_family"], dropna=False)
        .agg(
            n_articles=("article_id", "nunique"),
            n_family_hits=("article_id", "size"),
            total_terms_hit=("n_terms_hit", "sum"),
        )
        .reset_index()
    )

    out = counts.merge(article_denoms, on=group_cols, how="left")
    out["pct_articles_group"] = (out["n_articles"] / out["n_articles_group"].replace(0, pd.NA) * 100).round(4)
    out["_family_order"] = out["semantic_family"].map({f: i for i, f in enumerate(SEMANTIC_FAMILY_ORDER)}).fillna(999)
    return out.sort_values(group_cols + ["_family_order", "semantic_family"]).drop(columns=["_family_order"])


def articles_by_hit_count(wide_df: pd.DataFrame) -> pd.DataFrame:
    if wide_df.empty or "n_semantic_families_hit" not in wide_df.columns:
        return pd.DataFrame()
    return (
        wide_df["n_semantic_families_hit"]
        .value_counts(dropna=False)
        .rename_axis("n_semantic_families_hit")
        .reset_index(name="n_articles")
        .sort_values("n_semantic_families_hit")
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply initial semantic map to articles.")
    parser.add_argument(
        "--semantic-map",
        default="../data/title_abstract/semantic/psychoanalytic_core_initial_semantic_map.csv",
        help="Initial semantic map from 3a.",
    )
    parser.add_argument(
        "--articles",
        default="../data/title_abstract/global/psychoanalytic_core_ART_title_abstract_clean.csv",
        help="Clean ART-only title+abstract corpus.",
    )
    parser.add_argument(
        "--out-dir",
        default="../data/title_abstract/semantic_application",
        help="Output directory.",
    )
    args = parser.parse_args()

    paths = get_paths()

    sem_map_path = Path(args.semantic_map)
    if not sem_map_path.is_absolute():
        sem_map_path = (paths["scripts_dir"] / sem_map_path).resolve()

    articles_path = Path(args.articles)
    if not articles_path.is_absolute():
        articles_path = (paths["scripts_dir"] / articles_path).resolve()

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = (paths["scripts_dir"] / out_dir).resolve()

    out_dir.mkdir(parents=True, exist_ok=True)

    if not sem_map_path.exists():
        raise SystemExit(f"ERROR: semantic map not found: {sem_map_path}")
    if not articles_path.exists():
        raise SystemExit(f"ERROR: articles file not found: {articles_path}")

    sem_map = read_csv_safe(sem_map_path)
    articles = read_csv_safe(articles_path)

    if sem_map.empty:
        raise SystemExit("ERROR: semantic map is empty.")
    if articles.empty:
        raise SystemExit("ERROR: articles table is empty.")

    text_col = choose_col(articles, ["text_for_analysis", "abstract_clean", "title_clean"])
    article_id_col = choose_col(articles, ["article_id", "document_id", "pep_document_id", "id"])
    journal_col = choose_col(articles, ["journal_key", "journal"])
    period_col = choose_col(articles, ["period", "analysis_period"])
    year_col = choose_col(articles, ["year_for_analysis", "year", "year_record", "publication_year"])
    title_col = choose_col(articles, ["title_clean", "title", "article_title"])

    if text_col is None:
        raise SystemExit("ERROR: no text column found.")
    if article_id_col is None:
        articles = articles.copy()
        articles["article_id"] = "row_" + articles.index.astype(str)
        article_id_col = "article_id"
    if journal_col is None:
        raise SystemExit("ERROR: no journal column found.")
    if period_col is None:
        raise SystemExit("ERROR: no period column found.")

    # Standardize grouping columns for denominators.
    articles_std = articles.copy()
    if article_id_col != "article_id":
        articles_std["article_id"] = articles_std[article_id_col]
    if journal_col != "journal_key":
        articles_std["journal_key"] = articles_std[journal_col]
    if period_col != "period":
        articles_std["period"] = articles_std[period_col]

    family_patterns = build_family_patterns(sem_map)
    if not family_patterns:
        raise SystemExit("ERROR: no mapped semantic families found in semantic map.")

    long_df, wide_df = apply_map(
        articles=articles,
        family_patterns=family_patterns,
        text_col=text_col,
        article_id_col=article_id_col,
        journal_col=journal_col,
        period_col=period_col,
        year_col=year_col,
        title_col=title_col,
    )

    long_path = out_dir / "psychoanalytic_core_article_semantic_hits_long.csv"
    wide_path = out_dir / "psychoanalytic_core_article_semantic_hits_wide.csv"
    write_csv(long_df, long_path)
    write_csv(wide_df, wide_path)

    counts = family_counts(long_df, len(articles))
    counts_path = out_dir / "psychoanalytic_core_initial_semantic_family_counts.csv"
    write_csv(counts, counts_path)

    by_journal = family_by_group(long_df, articles_std, ["journal_key"])
    by_period = family_by_group(long_df, articles_std, ["period"])
    by_journal_period = family_by_group(long_df, articles_std, ["journal_key", "period"])

    by_journal_path = out_dir / "psychoanalytic_core_semantic_family_by_journal.csv"
    by_period_path = out_dir / "psychoanalytic_core_semantic_family_by_period.csv"
    by_journal_period_path = out_dir / "psychoanalytic_core_semantic_family_by_journal_period.csv"
    by_journal_share_path = out_dir / "psychoanalytic_core_semantic_family_article_share_by_journal.csv"
    by_period_share_path = out_dir / "psychoanalytic_core_semantic_family_article_share_by_period.csv"

    write_csv(by_journal, by_journal_path)
    write_csv(by_period, by_period_path)
    write_csv(by_journal_period, by_journal_period_path)
    write_csv(by_journal, by_journal_share_path)
    write_csv(by_period, by_period_share_path)

    hit_distribution = articles_by_hit_count(wide_df)
    hit_distribution_path = out_dir / "psychoanalytic_core_article_semantic_hit_count_distribution.csv"
    write_csv(hit_distribution, hit_distribution_path)

    mapped_terms = sem_map[sem_map["semantic_action"].astype(str).eq("mapped_initial")].copy()
    term_col = "term_norm" if "term_norm" in mapped_terms.columns else "term"
    family_term_counts = (
        mapped_terms.groupby("semantic_family", dropna=False)
        .agg(n_mapped_terms=(term_col, "nunique"))
        .reset_index()
    )
    family_term_counts_path = out_dir / "psychoanalytic_core_semantic_family_term_counts.csv"
    write_csv(family_term_counts, family_term_counts_path)

    n_articles = len(articles)
    n_articles_with_any = int((wide_df["n_semantic_families_hit"] > 0).sum()) if "n_semantic_families_hit" in wide_df.columns else 0

    summary = {
        "script_version": SCRIPT_VERSION,
        "created_at_utc": utc_now_iso(),
        "purpose": "Apply initial semantic map to ART-only title+abstract articles.",
        "inputs": {
            "semantic_map": str(sem_map_path),
            "articles": str(articles_path),
        },
        "policy": {
            "semantic_map_rebuilt": False,
            "final_ontology": False,
            "article_level_hits_are_lexical": True,
            "human_review_required": True,
        },
        "columns": {
            "text_col": text_col,
            "article_id_col": article_id_col,
            "journal_col": journal_col,
            "period_col": period_col,
            "year_col": year_col,
            "title_col": title_col,
        },
        "semantic_map": {
            "n_total_map_rows": int(len(sem_map)),
            "n_mapped_terms": int(len(mapped_terms)),
            "n_families_with_terms": int(len(family_patterns)),
            "families_with_terms": sorted(family_patterns.keys()),
        },
        "articles": {
            "n_articles": int(n_articles),
            "n_articles_with_any_semantic_family_hit": n_articles_with_any,
            "pct_articles_with_any_semantic_family_hit": round(n_articles_with_any / max(n_articles, 1) * 100, 4),
            "n_article_family_hit_rows": int(len(long_df)),
            "mean_families_hit_per_article": round(float(wide_df["n_semantic_families_hit"].mean()), 4) if "n_semantic_families_hit" in wide_df.columns else 0.0,
            "median_families_hit_per_article": float(wide_df["n_semantic_families_hit"].median()) if "n_semantic_families_hit" in wide_df.columns else 0.0,
        },
        "outputs": {
            "article_semantic_hits_long": str(long_path),
            "article_semantic_hits_wide": str(wide_path),
            "family_counts": str(counts_path),
            "family_by_journal": str(by_journal_path),
            "family_by_period": str(by_period_path),
            "family_by_journal_period": str(by_journal_period_path),
            "family_article_share_by_journal": str(by_journal_share_path),
            "family_article_share_by_period": str(by_period_share_path),
            "hit_count_distribution": str(hit_distribution_path),
            "family_term_counts": str(family_term_counts_path),
        },
        "interpretive_warning": (
            "These article-level hits are lexical matches to an initial semantic map. "
            "They are intended for QA and orientation before manual semantic refinement."
        ),
    }

    summary_path = out_dir / "psychoanalytic_core_semantic_application_summary.json"
    write_json(summary, summary_path)
    summary["outputs"]["summary_json"] = str(summary_path)

    print(json.dumps({
        "status": "ok",
        "script_version": SCRIPT_VERSION,
        "n_articles": n_articles,
        "n_articles_with_any_semantic_family_hit": n_articles_with_any,
        "pct_articles_with_any_semantic_family_hit": summary["articles"]["pct_articles_with_any_semantic_family_hit"],
        "n_article_family_hit_rows": int(len(long_df)),
        "n_families_with_terms": int(len(family_patterns)),
        "summary_json": str(summary_path),
        "long": str(long_path),
        "wide": str(wide_path),
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
