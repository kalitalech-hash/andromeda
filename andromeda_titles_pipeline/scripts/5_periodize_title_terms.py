#!/usr/bin/env python3
"""Assign analytical periods to article-title records."""
import argparse
from pathlib import Path
import pandas as pd

def period(y):
    if pd.isna(y): return None
    y=int(y)
    if 2005 <= y <= 2009: return "2005-2009"
    if 2010 <= y <= 2014: return "2010-2014"
    if 2015 <= y <= 2019: return "2015-2019"
    if 2020 <= y <= 2025: return "2020-2025"
    return "out_of_scope"

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--articles-clean", required=True)
    ap.add_argument("--outdir", required=True)
    args=ap.parse_args()
    out=Path(args.outdir); out.mkdir(parents=True, exist_ok=True)
    df=pd.read_csv(args.articles_clean)
    df["analysis_period"]=df["year"].apply(period)
    df.to_csv(out/"articles_titles_periodized.csv", index=False)
if __name__=="__main__": main()
