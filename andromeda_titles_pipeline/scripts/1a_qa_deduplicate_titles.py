#!/usr/bin/env python3
"""QA and deduplication for title-based corpora."""
import argparse, json
from pathlib import Path
import pandas as pd

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--articles", required=True)
    ap.add_argument("--outdir", required=True)
    args=ap.parse_args()
    out=Path(args.outdir); out.mkdir(parents=True, exist_ok=True)
    df=pd.read_csv(args.articles)
    key="article_id" if "article_id" in df.columns else "doi"
    dedup=df.drop_duplicates(subset=[key])
    dedup=dedup[dedup["title"].notna()].copy()
    dedup.to_csv(out/"articles_titles_dedup.csv", index=False)
    summary={"raw_articles":len(df),"dedup_articles_with_titles":len(dedup),"year_min":int(dedup["year"].min()) if "year" in dedup and dedup["year"].notna().any() else None,"year_max":int(dedup["year"].max()) if "year" in dedup and dedup["year"].notna().any() else None}
    (out/"titles_qa_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(summary)
if __name__=="__main__": main()
