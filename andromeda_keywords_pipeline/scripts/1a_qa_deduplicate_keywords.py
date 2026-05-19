#!/usr/bin/env python3
"""QA and deduplication for keyword-long bibliometric corpora."""
import argparse, json
from pathlib import Path
import pandas as pd

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--articles", required=True)
    ap.add_argument("--keywords", required=True)
    ap.add_argument("--outdir", required=True)
    args=ap.parse_args()
    out=Path(args.outdir); out.mkdir(parents=True, exist_ok=True)
    articles=pd.read_csv(args.articles)
    keywords=pd.read_csv(args.keywords)
    article_key="article_id" if "article_id" in articles.columns else "doi"
    articles_dedup=articles.drop_duplicates(subset=[article_key])
    kw_cols=[c for c in ["article_id","keyword_order","keyword_raw"] if c in keywords.columns] or list(keywords.columns)
    keywords_dedup=keywords.drop_duplicates(subset=kw_cols)
    articles_dedup.to_csv(out/"articles_dedup.csv", index=False)
    keywords_dedup.to_csv(out/"keywords_long_dedup.csv", index=False)
    summary={"raw_articles":len(articles),"dedup_articles":len(articles_dedup),"raw_keyword_rows":len(keywords),"dedup_keyword_rows":len(keywords_dedup)}
    (out/"qa_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(summary)
if __name__=="__main__": main()
