#!/usr/bin/env python3
"""Technical normalization of keyword strings."""
import argparse, re, unicodedata
from pathlib import Path
import pandas as pd

def norm(s):
    if pd.isna(s): return None
    s=unicodedata.normalize("NFKC", str(s)).lower().strip()
    s=s.replace("&"," and ")
    s=re.sub(r"[‐‑‒–—−]", "-", s)
    s=re.sub(r"\s*/\s*", "/", s)
    s=re.sub(r"\s+", " ", s)
    s=re.sub(r"[\.;:,]+$", "", s).strip()
    return s or None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--keywords", required=True)
    ap.add_argument("--outdir", required=True)
    args=ap.parse_args()
    out=Path(args.outdir); out.mkdir(parents=True, exist_ok=True)
    df=pd.read_csv(args.keywords)
    df["keyword_norm"]=df["keyword_raw"].apply(norm)
    df.to_csv(out/"keywords_long_normalized.csv", index=False)
    df[["keyword_raw","keyword_norm"]].drop_duplicates().to_csv(out/"keyword_normalization_map.csv", index=False)
    df["keyword_norm"].value_counts().rename_axis("keyword_norm").reset_index(name="n").to_csv(out/"keyword_top_normalized.csv", index=False)
if __name__=="__main__": main()
