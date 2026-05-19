#!/usr/bin/env python3
"""Basic keyword concept trends by period."""
import argparse
from pathlib import Path
import pandas as pd

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--input", required=True)
    ap.add_argument("--concept-col", default="keyword_concept_analysis")
    ap.add_argument("--outdir", required=True)
    args=ap.parse_args()
    out=Path(args.outdir); out.mkdir(parents=True, exist_ok=True)
    df=pd.read_csv(args.input)
    concept=args.concept_col
    counts=df.groupby([concept,"analysis_period"])["article_id"].nunique().reset_index(name="n_articles")
    counts.to_csv(out/"concept_period_counts.csv", index=False)
    overall=df.groupby(concept)["article_id"].nunique().sort_values(ascending=False).reset_index(name="n_articles")
    overall.to_csv(out/"top_concepts_overall.csv", index=False)
if __name__=="__main__": main()
