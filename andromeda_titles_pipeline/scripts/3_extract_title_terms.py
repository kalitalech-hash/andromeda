#!/usr/bin/env python3
"""Extract candidate 1-4gram terms from cleaned titles."""
import argparse
from pathlib import Path
import pandas as pd
from sklearn.feature_extraction.text import CountVectorizer

DEFAULT_STOPWORDS = set("""
a an and are as at based be between by can case clinical controlled for from in into is of on or randomized
study the to trial using with without among after before over during effects effect role analysis review treatment
""".split())

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--articles-clean", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--min-df", type=int, default=5)
    ap.add_argument("--max-ngram", type=int, default=4)
    args=ap.parse_args()
    out=Path(args.outdir); out.mkdir(parents=True, exist_ok=True)
    df=pd.read_csv(args.articles_clean)
    texts=df["title_clean"].fillna("")
    vectorizer=CountVectorizer(stop_words=list(DEFAULT_STOPWORDS), ngram_range=(1,args.max_ngram), min_df=args.min_df)
    X=vectorizer.fit_transform(texts)
    terms=vectorizer.get_feature_names_out()
    counts=X.sum(axis=0).A1
    term_df=pd.DataFrame({"term_raw":terms,"n_titles":counts}).sort_values("n_titles", ascending=False)
    term_df.to_csv(out/"title_candidate_terms.csv", index=False)
if __name__=="__main__": main()
