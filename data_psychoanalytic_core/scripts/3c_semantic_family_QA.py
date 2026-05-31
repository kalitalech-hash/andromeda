#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
3c_semantic_family_QA.py

Andromeda Nowicka v0.5-pre
QA of initial semantic family application.

Purpose
-------
After:

    3a_build_initial_semantic_families.py
    3b_apply_semantic_map_to_articles.py

we have an initial semantic map and article-level lexical family hits.
Before interpreting results, we need to inspect whether broad semantic families
are inflated by overly generic terms.

This script creates QA tables showing:

- top hit terms per semantic family,
- family term concentration,
- article examples per family,
- single-term vs multi-term family hits,
- high-risk terms and high-risk families,
- family coverage by journal and period,
- audit queue for semantic-map refinement.

It does NOT modify the semantic map and does NOT create a final ontology.

Inputs
------
Semantic map:
    ../data/title_abstract/semantic/psychoanalytic_core_initial_semantic_map.csv

Article semantic hits:
    ../data/title_abstract/semantic_application/psychoanalytic_core_article_semantic_hits_long.csv
    ../data/title_abstract/semantic_application/psychoanalytic_core_article_semantic_hits_wide.csv

Family counts:
    ../data/title_abstract/semantic_application/psychoanalytic_core_initial_semantic_family_counts.csv
    ../data/title_abstract/semantic_application/psychoanalytic_core_semantic_family_by_journal.csv
    ../data/title_abstract/semantic_application/psychoanalytic_core_semantic_family_by_period.csv

Clean article corpus:
    ../data/title_abstract/global/psychoanalytic_core_ART_title_abstract_clean.csv

Outputs
-------
../data/title_abstract/semantic_QA/
    psychoanalytic_core_semantic_QA_top_terms_by_family.csv
    psychoanalytic_core_semantic_QA_family_term_concentration.csv
    psychoanalytic_core_semantic_QA_single_vs_multi_term_hits.csv
    psychoanalytic_core_semantic_QA_family_examples.csv
    psychoanalytic_core_semantic_QA_high_risk_terms.csv
    psychoanalytic_core_semantic_QA_high_risk_families.csv
    psychoanalytic_core_semantic_QA_map_refinement_queue.csv
    psychoanalytic_core_semantic_QA_summary.json

Run
---
Put this file in:

    data_psychoanalytic_core/scripts/

Run:

    cd data_psychoanalytic_core/scripts
    python 3c_semantic_family_QA.py
"""

from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional

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

# Terms that may inflate broad families if used alone.
# This is a QA flag only. It does not remove terms.
HIGH_RISK_TERM_RULES = {
    "attachment_development_infant": {
        "early", "development", "developmental", "child", "children", "mother", "family",
    },
    "relational_intersubjective_field": {
        "relationship", "relationships", "field", "mutual", "dialogue",
    },
    "ego_self_narcissism": {
        "self", "identity", "subjectivity", "subjective",
    },
    "object_relations": {
        "object", "objects", "internal", "external",
    },
    "culture_race_social_ethics": {
        "social", "culture", "cultural", "society", "political", "responsibility",
    },
    "history_theory_schools": {
        "history", "historical", "tradition", "school", "schools", "classical",
    },
    "empirical_research_measurement": {
        "research", "study", "data", "method", "methods", "evidence",
    },
    "technique_interpretation_process": {
        "setting", "frame", "technical", "frequency",
    },
    "trauma_dissociation_affect_regulation": {
        "affect", "feeling", "feelings", "emotion", "emotional", "anxiety",
    },
}

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
        "semantic_application_root": title_root / "semantic_application",
        "semantic_QA_root": title_root / "semantic_QA",
        "global_root": title_root / "global",
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


def split_terms(value: str) -> List[str]:
    if value is None:
        return []
    return [norm_term(x) for x in str(value).split("|") if norm_term(x)]


def family_order_value(family: str) -> int:
    try:
        return SEMANTIC_FAMILY_ORDER.index(family)
    except ValueError:
        return 999


def explode_terms(long_df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for _, row in long_df.iterrows():
        terms = split_terms(row.get("terms_hit", ""))
        for term in terms:
            rows.append({
                "article_id": row.get("article_id", ""),
                "journal_key": row.get("journal_key", ""),
                "year_for_analysis": row.get("year_for_analysis", ""),
                "period": row.get("period", ""),
                "semantic_family": row.get("semantic_family", ""),
                "term": term,
                "title_clean": row.get("title_clean", ""),
            })
    return pd.DataFrame(rows)


def make_top_terms_by_family(term_hits: pd.DataFrame, articles_n: int) -> pd.DataFrame:
    if term_hits.empty:
        return pd.DataFrame()

    rows = []
    for (family, term), g in term_hits.groupby(["semantic_family", "term"], dropna=False):
        rows.append({
            "semantic_family": family,
            "term": term,
            "n_articles": int(g["article_id"].nunique()),
            "pct_all_articles": round(g["article_id"].nunique() / max(articles_n, 1) * 100, 4),
            "n_term_hit_rows": int(len(g)),
        })
    out = pd.DataFrame(rows)
    out["_family_order"] = out["semantic_family"].map(family_order_value)
    out = out.sort_values(["_family_order", "semantic_family", "n_articles"], ascending=[True, True, False])
    out["rank_within_family"] = out.groupby("semantic_family")["n_articles"].rank(method="first", ascending=False).astype(int)
    return out.drop(columns=["_family_order"])


def make_family_term_concentration(top_terms: pd.DataFrame, family_counts: pd.DataFrame) -> pd.DataFrame:
    if top_terms.empty or family_counts.empty:
        return pd.DataFrame()

    family_articles = dict(zip(family_counts["semantic_family"], pd.to_numeric(family_counts["n_articles"], errors="coerce").fillna(0)))

    rows = []
    for family, g in top_terms.groupby("semantic_family", dropna=False):
        n_family_articles = int(family_articles.get(family, 0))
        top1 = g.sort_values("n_articles", ascending=False).head(1)
        top3 = g.sort_values("n_articles", ascending=False).head(3)
        top5 = g.sort_values("n_articles", ascending=False).head(5)

        top1_share = float(top1["n_articles"].sum()) / max(n_family_articles, 1) * 100
        top3_share = float(top3["n_articles"].sum()) / max(n_family_articles, 1) * 100
        top5_share = float(top5["n_articles"].sum()) / max(n_family_articles, 1) * 100

        rows.append({
            "semantic_family": family,
            "n_family_articles": n_family_articles,
            "n_unique_terms_hit": int(g["term"].nunique()),
            "top1_term": top1["term"].iloc[0] if not top1.empty else "",
            "top1_n_articles": int(top1["n_articles"].iloc[0]) if not top1.empty else 0,
            "top1_share_of_family_articles_pct": round(top1_share, 2),
            "top3_share_of_family_articles_pct_sum": round(top3_share, 2),
            "top5_share_of_family_articles_pct_sum": round(top5_share, 2),
            "concentration_flag": (
                "high_top1_concentration" if top1_share >= 60 else
                "medium_top1_concentration" if top1_share >= 40 else
                ""
            ),
        })

    out = pd.DataFrame(rows)
    out["_family_order"] = out["semantic_family"].map(family_order_value)
    return out.sort_values(["_family_order", "semantic_family"]).drop(columns=["_family_order"])


def make_single_vs_multi(long_df: pd.DataFrame) -> pd.DataFrame:
    if long_df.empty:
        return pd.DataFrame()

    work = long_df.copy()
    work["n_terms_hit_num"] = pd.to_numeric(work["n_terms_hit"], errors="coerce").fillna(0).astype(int)
    work["hit_type"] = work["n_terms_hit_num"].apply(lambda x: "single_term_hit" if x == 1 else "multi_term_hit")

    rows = []
    for family, g in work.groupby("semantic_family", dropna=False):
        n_rows = len(g)
        n_articles = g["article_id"].nunique()
        n_single = int((g["hit_type"] == "single_term_hit").sum())
        n_multi = int((g["hit_type"] == "multi_term_hit").sum())
        rows.append({
            "semantic_family": family,
            "n_article_family_rows": int(n_rows),
            "n_articles": int(n_articles),
            "n_single_term_hit_rows": n_single,
            "n_multi_term_hit_rows": n_multi,
            "pct_single_term_hit_rows": round(n_single / max(n_rows, 1) * 100, 2),
            "single_hit_flag": "high_single_term_dependence" if n_single / max(n_rows, 1) >= 0.75 else "",
        })

    out = pd.DataFrame(rows)
    out["_family_order"] = out["semantic_family"].map(family_order_value)
    return out.sort_values(["_family_order", "semantic_family"]).drop(columns=["_family_order"])


def make_examples(term_hits: pd.DataFrame, articles: pd.DataFrame, per_family: int = 12) -> pd.DataFrame:
    if term_hits.empty:
        return pd.DataFrame()

    # Add abstract preview if possible.
    cols = ["article_id"]
    preview_cols = []
    for c in ["abstract_clean", "text_for_analysis", "title_clean"]:
        if c in articles.columns:
            preview_cols.append(c)
    cols += [c for c in preview_cols if c not in cols]
    art_small = articles[cols].drop_duplicates("article_id") if "article_id" in articles.columns else pd.DataFrame()

    rows = []
    for family, g in term_hits.groupby("semantic_family", dropna=False):
        # Prefer examples with multiple different terms in the family if possible.
        article_terms = (
            g.groupby(["article_id", "journal_key", "year_for_analysis", "period", "title_clean"], dropna=False)
            .agg(
                n_distinct_family_terms=("term", "nunique"),
                terms_hit=("term", lambda x: " | ".join(sorted(set(x)))),
            )
            .reset_index()
            .sort_values(["n_distinct_family_terms", "year_for_analysis"], ascending=[False, True])
            .head(per_family)
        )
        rows.append(article_terms.assign(semantic_family=family))

    out = pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()
    if not art_small.empty:
        out = out.merge(art_small, on="article_id", how="left", suffixes=("", "_article"))
    if "abstract_clean" in out.columns:
        out["abstract_preview"] = out["abstract_clean"].astype(str).str.slice(0, 500)
    elif "text_for_analysis" in out.columns:
        out["abstract_preview"] = out["text_for_analysis"].astype(str).str.slice(0, 500)
    else:
        out["abstract_preview"] = ""

    out["_family_order"] = out["semantic_family"].map(family_order_value)
    return out.sort_values(["_family_order", "semantic_family", "n_distinct_family_terms"], ascending=[True, True, False]).drop(columns=["_family_order"])


def make_high_risk_terms(top_terms: pd.DataFrame, family_counts: pd.DataFrame) -> pd.DataFrame:
    if top_terms.empty:
        return pd.DataFrame()

    family_articles = dict(zip(family_counts["semantic_family"], pd.to_numeric(family_counts["n_articles"], errors="coerce").fillna(0))) if not family_counts.empty else {}

    rows = []
    for _, row in top_terms.iterrows():
        family = row["semantic_family"]
        term = norm_term(row["term"])
        n_family_articles = int(family_articles.get(family, 0))
        n_articles = int(row["n_articles"])
        share = n_articles / max(n_family_articles, 1) * 100

        risk_reasons = []
        if term in HIGH_RISK_TERM_RULES.get(family, set()):
            risk_reasons.append("family_specific_high_risk_term")
        if share >= 40:
            risk_reasons.append("high_share_within_family")
        if len(term) <= 4 and " " not in term:
            risk_reasons.append("short_single_token")
        if family in {"object_relations", "ego_self_narcissism", "relational_intersubjective_field"} and term in {"object", "self", "relationship", "field"}:
            risk_reasons.append("known_broad_polysemous_term")

        if risk_reasons:
            rows.append({
                "semantic_family": family,
                "term": term,
                "n_articles": n_articles,
                "n_family_articles": n_family_articles,
                "share_of_family_articles_pct": round(share, 2),
                "risk_reasons": " | ".join(risk_reasons),
                "recommended_action": "review_term_specificity",
            })

    out = pd.DataFrame(rows)
    if not out.empty:
        out["_family_order"] = out["semantic_family"].map(family_order_value)
        out = out.sort_values(["_family_order", "share_of_family_articles_pct"], ascending=[True, False]).drop(columns=["_family_order"])
    return out


def make_high_risk_families(concentration: pd.DataFrame, single_multi: pd.DataFrame, family_counts: pd.DataFrame) -> pd.DataFrame:
    if family_counts.empty:
        return pd.DataFrame()

    out = family_counts.copy()
    if not concentration.empty:
        out = out.merge(
            concentration[["semantic_family", "n_unique_terms_hit", "top1_term", "top1_share_of_family_articles_pct", "concentration_flag"]],
            on="semantic_family",
            how="left",
        )
    if not single_multi.empty:
        out = out.merge(
            single_multi[["semantic_family", "pct_single_term_hit_rows", "single_hit_flag"]],
            on="semantic_family",
            how="left",
        )

    risk_flags = []
    for _, r in out.iterrows():
        flags = []
        if str(r.get("concentration_flag", "")):
            flags.append(str(r.get("concentration_flag")))
        if str(r.get("single_hit_flag", "")):
            flags.append(str(r.get("single_hit_flag")))
        pct_articles = float(r.get("pct_articles", 0) or 0)
        if pct_articles > 50:
            flags.append("very_high_family_coverage_review_specificity")
        risk_flags.append(" | ".join(flags))

    out["family_QA_flags"] = risk_flags
    out["recommended_action"] = out["family_QA_flags"].apply(lambda x: "review_family_rules" if x else "")
    return out


def make_refinement_queue(high_risk_terms: pd.DataFrame, sem_map: pd.DataFrame) -> pd.DataFrame:
    if high_risk_terms.empty:
        return pd.DataFrame()

    term_col = "term_norm" if "term_norm" in sem_map.columns else "term"
    m = sem_map.copy()
    m["term_norm_join"] = m[term_col].map(norm_term)
    h = high_risk_terms.copy()
    h["term_norm_join"] = h["term"].map(norm_term)

    queue = h.merge(
        m[["term_norm_join", "semantic_family", "semantic_confidence", "mapping_rule", "matched_pattern", "review_flag"]],
        on=["term_norm_join", "semantic_family"],
        how="left",
        suffixes=("", "_map"),
    )
    queue["proposed_audit_decision"] = ""
    queue["manual_new_family"] = ""
    queue["manual_note"] = ""
    return queue.drop(columns=["term_norm_join"])


def main() -> int:
    parser = argparse.ArgumentParser(description="QA of initial semantic family application.")
    parser.add_argument(
        "--semantic-map",
        default="../data/title_abstract/semantic/psychoanalytic_core_initial_semantic_map.csv",
    )
    parser.add_argument(
        "--hits-long",
        default="../data/title_abstract/semantic_application/psychoanalytic_core_article_semantic_hits_long.csv",
    )
    parser.add_argument(
        "--hits-wide",
        default="../data/title_abstract/semantic_application/psychoanalytic_core_article_semantic_hits_wide.csv",
    )
    parser.add_argument(
        "--family-counts",
        default="../data/title_abstract/semantic_application/psychoanalytic_core_initial_semantic_family_counts.csv",
    )
    parser.add_argument(
        "--family-by-journal",
        default="../data/title_abstract/semantic_application/psychoanalytic_core_semantic_family_by_journal.csv",
    )
    parser.add_argument(
        "--family-by-period",
        default="../data/title_abstract/semantic_application/psychoanalytic_core_semantic_family_by_period.csv",
    )
    parser.add_argument(
        "--articles",
        default="../data/title_abstract/global/psychoanalytic_core_ART_title_abstract_clean.csv",
    )
    parser.add_argument(
        "--out-dir",
        default="../data/title_abstract/semantic_QA",
    )
    parser.add_argument("--examples-per-family", type=int, default=12)
    args = parser.parse_args()

    paths = get_paths()

    def resolve(p: str) -> Path:
        path = Path(p)
        if not path.is_absolute():
            path = (paths["scripts_dir"] / path).resolve()
        return path

    sem_map_path = resolve(args.semantic_map)
    hits_long_path = resolve(args.hits_long)
    hits_wide_path = resolve(args.hits_wide)
    family_counts_path = resolve(args.family_counts)
    family_by_journal_path = resolve(args.family_by_journal)
    family_by_period_path = resolve(args.family_by_period)
    articles_path = resolve(args.articles)
    out_dir = resolve(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    required_paths = {
        "semantic_map": sem_map_path,
        "hits_long": hits_long_path,
        "hits_wide": hits_wide_path,
        "family_counts": family_counts_path,
        "articles": articles_path,
    }
    missing = [name for name, path in required_paths.items() if not path.exists()]
    if missing:
        raise SystemExit(f"ERROR: missing required input files: {missing}")

    sem_map = read_csv_safe(sem_map_path)
    hits_long = read_csv_safe(hits_long_path)
    hits_wide = read_csv_safe(hits_wide_path)
    family_counts_df = read_csv_safe(family_counts_path)
    family_by_journal = read_csv_safe(family_by_journal_path)
    family_by_period = read_csv_safe(family_by_period_path)
    articles = read_csv_safe(articles_path)

    if "article_id" not in articles.columns:
        articles = articles.copy()
        articles["article_id"] = "row_" + articles.index.astype(str)

    term_hits = explode_terms(hits_long)
    top_terms = make_top_terms_by_family(term_hits, articles_n=len(articles))
    concentration = make_family_term_concentration(top_terms, family_counts_df)
    single_multi = make_single_vs_multi(hits_long)
    examples = make_examples(term_hits, articles, per_family=args.examples_per_family)
    high_risk_terms = make_high_risk_terms(top_terms, family_counts_df)
    high_risk_families = make_high_risk_families(concentration, single_multi, family_counts_df)
    refinement_queue = make_refinement_queue(high_risk_terms, sem_map)

    outputs = {
        "top_terms_by_family": out_dir / "psychoanalytic_core_semantic_QA_top_terms_by_family.csv",
        "family_term_concentration": out_dir / "psychoanalytic_core_semantic_QA_family_term_concentration.csv",
        "single_vs_multi_term_hits": out_dir / "psychoanalytic_core_semantic_QA_single_vs_multi_term_hits.csv",
        "family_examples": out_dir / "psychoanalytic_core_semantic_QA_family_examples.csv",
        "high_risk_terms": out_dir / "psychoanalytic_core_semantic_QA_high_risk_terms.csv",
        "high_risk_families": out_dir / "psychoanalytic_core_semantic_QA_high_risk_families.csv",
        "map_refinement_queue": out_dir / "psychoanalytic_core_semantic_QA_map_refinement_queue.csv",
    }

    write_csv(top_terms, outputs["top_terms_by_family"])
    write_csv(concentration, outputs["family_term_concentration"])
    write_csv(single_multi, outputs["single_vs_multi_term_hits"])
    write_csv(examples, outputs["family_examples"])
    write_csv(high_risk_terms, outputs["high_risk_terms"])
    write_csv(high_risk_families, outputs["high_risk_families"])
    write_csv(refinement_queue, outputs["map_refinement_queue"])

    # Compact summary for console and audit.
    top_risk_terms_preview = []
    if not high_risk_terms.empty:
        top_risk_terms_preview = (
            high_risk_terms
            .sort_values(["share_of_family_articles_pct", "n_articles"], ascending=[False, False])
            .head(20)
            .to_dict(orient="records")
        )

    high_risk_family_preview = []
    if not high_risk_families.empty:
        high_risk_family_preview = (
            high_risk_families[high_risk_families["family_QA_flags"].astype(str).ne("")]
            .to_dict(orient="records")
        )

    summary = {
        "script_version": SCRIPT_VERSION,
        "created_at_utc": utc_now_iso(),
        "purpose": "QA of initial semantic family application before semantic-map refinement.",
        "inputs": {
            "semantic_map": str(sem_map_path),
            "hits_long": str(hits_long_path),
            "hits_wide": str(hits_wide_path),
            "family_counts": str(family_counts_path),
            "family_by_journal": str(family_by_journal_path),
            "family_by_period": str(family_by_period_path),
            "articles": str(articles_path),
        },
        "qa_counts": {
            "n_articles": int(len(articles)),
            "n_article_family_hit_rows": int(len(hits_long)),
            "n_term_hit_rows_exploded": int(len(term_hits)),
            "n_top_term_rows": int(len(top_terms)),
            "n_high_risk_term_rows": int(len(high_risk_terms)),
            "n_high_risk_family_rows": int(len(high_risk_family_preview)),
            "n_refinement_queue_rows": int(len(refinement_queue)),
        },
        "outputs": {k: str(v) for k, v in outputs.items()},
        "top_risk_terms_preview": top_risk_terms_preview,
        "high_risk_family_preview": high_risk_family_preview,
        "interpretive_warning": (
            "This QA layer identifies likely over-broad terms and family inflation risks. "
            "It does not modify the semantic map. Use the refinement queue for 3d/3c-map revision."
        ),
    }

    summary_path = out_dir / "psychoanalytic_core_semantic_QA_summary.json"
    write_json(summary, summary_path)
    summary["outputs"]["summary_json"] = str(summary_path)

    print(json.dumps({
        "status": "ok",
        "script_version": SCRIPT_VERSION,
        "n_articles": summary["qa_counts"]["n_articles"],
        "n_article_family_hit_rows": summary["qa_counts"]["n_article_family_hit_rows"],
        "n_term_hit_rows_exploded": summary["qa_counts"]["n_term_hit_rows_exploded"],
        "n_high_risk_term_rows": summary["qa_counts"]["n_high_risk_term_rows"],
        "n_refinement_queue_rows": summary["qa_counts"]["n_refinement_queue_rows"],
        "summary_json": str(summary_path),
        "refinement_queue": str(outputs["map_refinement_queue"]),
    }, ensure_ascii=False, indent=2))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
