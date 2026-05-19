#!/usr/bin/env python3
"""Apply a human-reviewed semantic map to extracted title terms."""
import argparse
from pathlib import Path
import pandas as pd

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--terms", required=True)
    ap.add_argument("--semantic-map", required=True, help="CSV with term_raw, term_concept, term_family, review_flag")
    ap.add_argument("--outdir", required=True)
    args=ap.parse_args()
    out=Path(args.outdir); out.mkdir(parents=True, exist_ok=True)
    terms=pd.read_csv(args.terms)
    m=pd.read_csv(args.semantic_map)
    final=terms.merge(m, on="term_raw", how="left")
    final["term_concept_analysis"]=final.get("term_concept", final["term_raw"])
    final.to_csv(out/"title_terms_semantic.csv", index=False)
if __name__=="__main__": main()
