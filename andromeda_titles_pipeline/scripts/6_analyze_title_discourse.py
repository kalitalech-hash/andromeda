#!/usr/bin/env python3
"""Basic descriptive outputs for title-based discourse mapping."""
import argparse, re
from pathlib import Path
import pandas as pd

def contains_term(title, term):
    return bool(re.search(r"\b" + re.escape(str(term)) + r"\b", str(title)))

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--articles-periodized", required=True)
    ap.add_argument("--terms-semantic", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--top-n", type=int, default=300)
    args=ap.parse_args()
    out=Path(args.outdir); out.mkdir(parents=True, exist_ok=True)
    articles=pd.read_csv(args.articles_periodized)
    terms=pd.read_csv(args.terms_semantic).head(args.top_n)
    rows=[]
    for _, term in terms.iterrows():
        raw=term["term_raw"]
        mask=articles["title_clean"].fillna("").apply(lambda s: contains_term(s, raw))
        subset=articles[mask]
        if len(subset):
            for p, grp in subset.groupby("analysis_period"):
                rows.append({"term_raw":raw,"term_concept_analysis":term.get("term_concept_analysis", raw),"analysis_period":p,"n_titles":grp["article_id"].nunique() if "article_id" in grp.columns else len(grp)})
    pd.DataFrame(rows).to_csv(out/"title_term_period_counts.csv", index=False)
if __name__=="__main__": main()
