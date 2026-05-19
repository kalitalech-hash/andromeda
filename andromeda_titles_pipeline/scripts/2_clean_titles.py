#!/usr/bin/env python3
"""Clean and normalize article titles."""
import argparse, re, unicodedata
from pathlib import Path
import pandas as pd

def clean(s):
    if pd.isna(s): return None
    s=unicodedata.normalize("NFKC", str(s))
    s=re.sub(r"<[^>]+>", " ", s)
    s=s.replace("&", " and ")
    s=re.sub(r"[^A-Za-z0-9\- /:]", " ", s)
    s=re.sub(r"\s+", " ", s).strip().lower()
    return s or None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--articles", required=True)
    ap.add_argument("--outdir", required=True)
    args=ap.parse_args()
    out=Path(args.outdir); out.mkdir(parents=True, exist_ok=True)
    df=pd.read_csv(args.articles)
    df["title_clean"]=df["title"].apply(clean)
    df.to_csv(out/"articles_titles_clean.csv", index=False)
if __name__=="__main__": main()
