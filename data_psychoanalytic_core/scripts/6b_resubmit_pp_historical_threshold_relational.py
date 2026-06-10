#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
6b_resubmit_pp_historical_threshold_relational.py

Separates:
1. lexical relational/intersubjective coverage in the title-and-abstract layer;
2. historically interpretable school-signaling use after 1990.

This directly addresses the anachronism concern: early occurrences of "relational" or related
words should not automatically be interpreted as evidence of the relational/intersubjective school.

Preferred input:
  semantic_refined/psychoanalytic_core_article_semantic_hits_long_refined.csv
  global/psychoanalytic_core_ART_title_abstract_clean.csv

Fallback:
  semantic_refined/psychoanalytic_core_semantic_family_by_journal_period_refined.csv
"""
from __future__ import annotations
import json, re
from pathlib import Path
import pandas as pd
from _resubmit_pp_common import paths, read_csv, write_csv, write_json, make_period, aggregate_family_period, pivot_indices, lineplot, now, sort_df

STRICT_SCHOOL_PATTERNS = [
    r"\brelational\b",
    r"\brelationality\b",
    r"\brelational psychoanalysis\b",
    r"\bintersubjective\b",
    r"\bintersubjectivity\b",
    r"\binterpersonal psychoanalysis\b",
    r"\bfield theory\b",
    r"\banalytic field\b",
    r"\bmutual recognition\b",
    r"\bthirdness\b",
    r"\benactment\b",
]

def choose_col(df, candidates):
    lower={c.lower():c for c in df.columns}
    for c in candidates:
        if c in df.columns: return c
        if c.lower() in lower: return lower[c.lower()]
    return None

def article_level_threshold(hits: pd.DataFrame, articles: pd.DataFrame) -> pd.DataFrame:
    # Normalize article ID and join year/journal/period if needed.
    aid_h=choose_col(hits,["article_id","id","pep_id","article_code"])
    fam_col=choose_col(hits,["semantic_family","family"])
    term_col=choose_col(hits,["term_norm","term","marker","matched_term"])
    strength_col=choose_col(hits,["marker_strength","strength"])
    if not aid_h or not fam_col or not term_col:
        return pd.DataFrame()

    h=hits.copy()
    h["_article_id"]=h[aid_h].astype(str)
    h["_family"]=h[fam_col].astype(str)
    h["_term"]=h[term_col].astype(str).str.lower().str.strip()
    if strength_col:
        h["_strength"]=h[strength_col].astype(str).str.lower().str.strip()
    else:
        h["_strength"]=""

    h=h[h["_family"].eq("relational_intersubjective_field")].copy()
    if h.empty:
        return pd.DataFrame()

    # Add article metadata.
    aid_a=choose_col(articles,["article_id","id","pep_id","article_code"])
    year_col=choose_col(articles,["year","publication_year"])
    journal_col=choose_col(articles,["journal_key","journal","source"])
    period_col=choose_col(articles,["period"])
    if aid_a:
        a=articles.copy()
        a["_article_id"]=a[aid_a].astype(str)
        keep=["_article_id"]
        if year_col: keep.append(year_col)
        if journal_col: keep.append(journal_col)
        if period_col: keep.append(period_col)
        h=h.merge(a[keep].drop_duplicates("_article_id"), on="_article_id", how="left")
    if year_col and year_col in h.columns:
        h["_year"]=pd.to_numeric(h[year_col], errors="coerce")
    else:
        h["_year"]=pd.NA
    if period_col and period_col in h.columns:
        h["period"]=h[period_col].astype(str)
    else:
        h["period"]=h["_year"].map(make_period)
    if journal_col and journal_col in h.columns:
        h["journal_key"]=h[journal_col].astype(str)
    else:
        h["journal_key"]=""

    strict_regex=re.compile("|".join(STRICT_SCHOOL_PATTERNS), flags=re.I)
    h["strict_school_marker"]=h["_term"].map(lambda x: bool(strict_regex.search(str(x))))
    h["post_1990"]=pd.to_numeric(h["_year"], errors="coerce").fillna(0).ge(1990)

    # Article-level presence.
    art=(h.groupby(["_article_id","period","journal_key"], as_index=False)
        .agg(
            relational_lexical_hit=("_term", lambda s: int(len(s)>0)),
            relational_strong_or_medium_hit=("_strength", lambda s: int(any(x in {"strong","medium"} for x in s))),
            relational_strict_school_marker=("strict_school_marker","max"),
            relational_school_signal_post_1990=("post_1990", lambda s: 0),
        ))
    # Need post-1990 at article level separately.
    post=h.groupby("_article_id")["post_1990"].max().reset_index().rename(columns={"post_1990":"_post_1990"})
    art=art.merge(post,on="_article_id",how="left")
    art["relational_school_signal_post_1990"]=(art["relational_strict_school_marker"].astype(bool) & art["_post_1990"].astype(bool)).astype(int)

    period=art.groupby("period", as_index=False).agg(
        articles_with_any_relational_lexical_marker=("relational_lexical_hit","sum"),
        articles_with_strong_or_medium_relational_marker=("relational_strong_or_medium_hit","sum"),
        articles_with_strict_school_marker=("relational_strict_school_marker","sum"),
        articles_with_school_signal_post_1990=("relational_school_signal_post_1990","sum"),
        n_articles_with_relational_records=("_article_id","nunique"),
    )
    period["note"]="Denominators here are articles with relational-family records. For percent-of-corpus use R1 aggregate table."
    return sort_df(period)

def fallback_aggregate_threshold(jp: pd.DataFrame) -> pd.DataFrame:
    # Lexical/refined relational coverage by period. Pre-1990 school-signaling is explicitly not interpreted.
    fam=aggregate_family_period(jp, "full_corpus_all_periods", exclude=None, post1990=False)
    rel=fam[fam["semantic_family"].eq("relational_intersubjective_field")].copy()
    rel=rel.rename(columns={"pct":"relational_refined_coverage_pct","n_hits":"relational_hits","n_articles":"n_articles"})
    rel["school_signaling_interpretation_allowed"]=rel["period"].isin(["1990-2009","2010-2025"])
    rel["relational_school_signal_coverage_pct_thresholded"]=rel.apply(
        lambda r: r["relational_refined_coverage_pct"] if r["school_signaling_interpretation_allowed"] else pd.NA, axis=1
    )
    rel["note"]="Fallback aggregate mode: cannot separate exact terms; use as conservative period-threshold diagnostic."
    return sort_df(rel[["period","n_articles","relational_hits","relational_refined_coverage_pct","school_signaling_interpretation_allowed","relational_school_signal_coverage_pct_thresholded","note"]])

def main() -> int:
    p=paths()
    refined=p["refined"]; global_root=p["global"]; out=p["out"]/"historical_threshold_relational"
    out.mkdir(parents=True, exist_ok=True)
    hits=read_csv(refined/"psychoanalytic_core_article_semantic_hits_long_refined.csv")
    articles=read_csv(global_root/"psychoanalytic_core_ART_title_abstract_clean.csv")
    jp=read_csv(refined/"psychoanalytic_core_semantic_family_by_journal_period_refined.csv")

    mode="article_level" if not hits.empty and not articles.empty else "aggregate_fallback"
    if mode=="article_level":
        table=article_level_threshold(hits, articles)
        if table.empty:
            mode="aggregate_fallback"
    if mode=="aggregate_fallback":
        if jp.empty:
            raise SystemExit("No article-level inputs and no aggregate fallback table found.")
        table=fallback_aggregate_threshold(jp)

    write_csv(table,out/"pp_resubmit_R2_historical_threshold_relational_markers.csv")

    # If aggregate fallback, create a simple figure. If article-level, figure is counts because denominator not safely known.
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(8,5))
    t=sort_df(table)
    if "relational_refined_coverage_pct" in t.columns:
        ax.plot(t["period"], pd.to_numeric(t["relational_refined_coverage_pct"],errors="coerce"), marker="o", label="lexical/refined relational coverage")
        ax.plot(t["period"], pd.to_numeric(t["relational_school_signal_coverage_pct_thresholded"],errors="coerce"), marker="o", label="post-1990 school-signaling interpretation")
        ax.set_ylabel("Percent of ART articles")
    else:
        ax.plot(t["period"], pd.to_numeric(t["articles_with_any_relational_lexical_marker"],errors="coerce"), marker="o", label="any relational lexical marker")
        ax.plot(t["period"], pd.to_numeric(t["articles_with_school_signal_post_1990"],errors="coerce"), marker="o", label="post-1990 strict school-signal marker")
        ax.set_ylabel("Article count")
    ax.set_title("Relational language: lexical occurrence vs historical school-signaling interpretation")
    ax.set_xlabel("Period"); ax.tick_params(axis="x", rotation=35); ax.legend(fontsize=8); fig.tight_layout()
    fig.savefig(out/"fig_R2_historical_threshold_relational.png", dpi=300); plt.close(fig)

    write_json({
        "script":"6b_resubmit_pp_historical_threshold_relational.py",
        "created_at_utc":now(),
        "mode":mode,
        "outputs":{"threshold_table":str(out/"pp_resubmit_R2_historical_threshold_relational_markers.csv")},
        "interpretive_use":"Use to state that pre-1990 relational/intersubjective lexical occurrences are not interpreted as evidence of a school-specific relational/intersubjective paradigm."
    }, out/"pp_resubmit_R2_summary.json")
    print(json.dumps({"status":"ok","mode":mode,"out_dir":str(out)}, indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
