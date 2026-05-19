#!/usr/bin/env python3
"""Apply a human-reviewed semantic map to normalized keywords."""
import argparse
from pathlib import Path
import pandas as pd

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--keywords-normalized", required=True)
    ap.add_argument("--semantic-map", required=True, help="CSV with keyword_norm, keyword_concept, semantic_confidence, review_flag")
    ap.add_argument("--outdir", required=True)
    args=ap.parse_args()
    out=Path(args.outdir); out.mkdir(parents=True, exist_ok=True)
    df=pd.read_csv(args.keywords_normalized)
    m=pd.read_csv(args.semantic_map)
    final=df.merge(m, on="keyword_norm", how="left")
    final["keyword_concept_analysis"]=final.get("keyword_concept", final["keyword_norm"])
    final.to_csv(out/"keywords_long_semantic.csv", index=False)
    final["keyword_concept_analysis"].value_counts().rename_axis("concept").reset_index(name="n").to_csv(out/"semantic_concept_counts.csv", index=False)
if __name__=="__main__": main()
