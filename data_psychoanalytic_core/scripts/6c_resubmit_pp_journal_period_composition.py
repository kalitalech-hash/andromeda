#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
6c_resubmit_pp_journal_period_composition.py

Journal-by-period composition and abstract availability diagnostics for the
Psychoanalytic Psychology resubmission.

This table should be used in Methods/Limitations to make clear that journal
founding dates, available period ranges, and abstract availability shape what
can be inferred from the title-and-abstract layer.
"""
from __future__ import annotations
import json
import pandas as pd
from _resubmit_pp_common import paths, read_csv, write_csv, write_json, make_period, sort_df, now

def choose_col(df, candidates):
    lower={c.lower():c for c in df.columns}
    for c in candidates:
        if c in df.columns: return c
        if c.lower() in lower: return lower[c.lower()]
    return None

def from_global_articles(articles: pd.DataFrame) -> pd.DataFrame:
    year_col=choose_col(articles,["year","publication_year"])
    journal_col=choose_col(articles,["journal_key","journal","source"])
    article_type_col=choose_col(articles,["article_type","publication_type","type"])
    abstract_col=choose_col(articles,["abstract_clean","abstract_norm","abstract","abstract_raw"])
    title_col=choose_col(articles,["title_clean","title_norm","title","title_raw"])

    if not year_col or not journal_col:
        return pd.DataFrame()

    a=articles.copy()
    a["journal_key"]=a[journal_col].astype(str)
    a["year_num"]=pd.to_numeric(a[year_col], errors="coerce")
    a["period"]=a["year_num"].map(make_period)
    if article_type_col:
        a["is_ART"]=a[article_type_col].astype(str).str.upper().eq("ART")
    else:
        a["is_ART"]=True

    if abstract_col:
        a["has_abstract"]=a[abstract_col].astype(str).str.strip().ne("")
    else:
        a["has_abstract"]=False
    if title_col:
        a["has_title"]=a[title_col].astype(str).str.strip().ne("")
    else:
        a["has_title"]=False

    g=(a.groupby(["journal_key","period"], as_index=False)
       .agg(
           n_records=("journal_key","size"),
           n_ART=("is_ART","sum"),
           n_with_title=("has_title","sum"),
           n_with_abstract=("has_abstract","sum"),
           first_year=("year_num","min"),
           last_year=("year_num","max"),
       ))
    g["pct_with_abstract_all_records"]=(100*g["n_with_abstract"]/g["n_records"].replace(0,pd.NA)).round(2)
    g["pct_ART_of_records"]=(100*g["n_ART"]/g["n_records"].replace(0,pd.NA)).round(2)
    return sort_df(g)

def fallback_from_semantic_jp(jp: pd.DataFrame) -> pd.DataFrame:
    if jp.empty:
        return pd.DataFrame()
    d=jp.copy()
    d["period"]=d["period"].astype(str)
    d["n_articles_group"]=pd.to_numeric(d["n_articles_group"], errors="coerce").fillna(0)
    # Denominator repeated by family; take max/first per cell.
    g=(d.groupby(["journal_key","period"], as_index=False)
       .agg(n_ART=("n_articles_group","max")))
    g["n_records"]=""
    g["n_with_title"]=""
    g["n_with_abstract"]=""
    g["pct_with_abstract_all_records"]=""
    g["pct_ART_of_records"]=""
    g["first_year"]=""
    g["last_year"]=""
    g["note"]="Fallback from semantic by-journal-period table; no abstract-availability fields available."
    return sort_df(g)

def main() -> int:
    p=paths(); out=p["out"]/"journal_period_composition"; out.mkdir(parents=True, exist_ok=True)
    articles=read_csv(p["global"]/"psychoanalytic_core_ART_title_abstract_clean.csv")
    jp=read_csv(p["refined"]/"psychoanalytic_core_semantic_family_by_journal_period_refined.csv")
    mode="global_articles" if not articles.empty else "semantic_jp_fallback"

    if mode=="global_articles":
        comp=from_global_articles(articles)
        if comp.empty:
            mode="semantic_jp_fallback"
    if mode=="semantic_jp_fallback":
        comp=fallback_from_semantic_jp(jp)
    if comp.empty:
        raise SystemExit("No usable composition input found.")

    write_csv(comp, out/"pp_resubmit_R3_journal_period_composition.csv")

    # Journal totals
    if "n_ART" in comp.columns:
        totals=(comp.groupby("journal_key", as_index=False)
                .agg(n_ART=("n_ART","sum"),
                     n_records=("n_records","sum") if pd.api.types.is_numeric_dtype(comp["n_records"]) else ("journal_key","size")))
        write_csv(sort_df(totals), out/"pp_resubmit_R3_journal_totals.csv")

    # Figure: ART records by journal and period.
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(9,5))
    d=sort_df(comp)
    pivot=d.pivot_table(index="period", columns="journal_key", values="n_ART", aggfunc="sum", fill_value=0)
    pivot=pivot.reindex(["1920-1945","1946-1969","1970-1989","1990-2009","2010-2025"])
    pivot.plot(kind="bar", ax=ax)
    ax.set_title("Journal-period composition of ART analytical corpus")
    ax.set_xlabel("Period"); ax.set_ylabel("ART records")
    ax.legend(fontsize=7); fig.tight_layout()
    fig.savefig(out/"fig_R3_journal_period_composition.png", dpi=300); plt.close(fig)

    write_json({
        "script":"6c_resubmit_pp_journal_period_composition.py",
        "created_at_utc":now(),
        "mode":mode,
        "outputs":{"composition":str(out/"pp_resubmit_R3_journal_period_composition.csv")},
        "interpretive_use":"Use to document journal ecology, unequal founding dates, period coverage, and abstract availability."
    }, out/"pp_resubmit_R3_summary.json")
    print(json.dumps({"status":"ok","mode":mode,"out_dir":str(out),"n_rows":len(comp)}, indent=2))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
