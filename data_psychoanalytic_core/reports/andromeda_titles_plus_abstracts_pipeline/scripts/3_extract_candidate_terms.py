from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer

from andromeda_titles_plus_abstracts.utils import ensure_dir, read_config, read_table, write_json


def load_stopwords(path: str | Path) -> list[str]:
    p = Path(path)
    if not p.exists():
        return []
    return [line.strip() for line in p.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]


def main() -> None:
    ap = argparse.ArgumentParser(description="Extract candidate lexical terms from normalized title + abstract text.")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--config", default="config/default_config.json")
    args = ap.parse_args()

    cfg = read_config(args.config)
    outdir = ensure_dir(args.output_dir)
    df = read_table(args.input)
    tcfg = cfg["term_extraction"]

    stopwords = load_stopwords(tcfg.get("stopwords_file", "templates/stopwords_domain.txt"))
    vectorizer = TfidfVectorizer(
        lowercase=False,
        stop_words=stopwords or None,
        ngram_range=tuple(tcfg.get("ngram_range", [1, 3])),
        min_df=tcfg.get("min_df", 2),
        max_df=tcfg.get("max_df", 0.85),
        max_features=tcfg.get("max_features", 5000),
        token_pattern=r"(?u)\b[a-zA-Z][a-zA-Z\-]{2,}\b",
    )
    texts = df["analysis_text"].fillna("").astype(str).tolist()
    X = vectorizer.fit_transform(texts)
    terms = np.array(vectorizer.get_feature_names_out())

    top_n = int(tcfg.get("top_terms_per_article", 20))
    rows = []
    for i in range(X.shape[0]):
        row = X.getrow(i)
        if row.nnz == 0:
            continue
        order = np.argsort(row.data)[::-1][:top_n]
        article_id = df.iloc[i]["article_id"]
        for rank, pos in enumerate(order, start=1):
            term_idx = row.indices[pos]
            rows.append({
                "article_id": article_id,
                "candidate_rank": rank,
                "candidate_term": terms[term_idx],
                "tfidf_score": float(row.data[pos]),
                "extraction_method": "tfidf_ngram_title_abstract",
                "review_flag": "auto_candidate"
            })

    long = pd.DataFrame(rows)
    long.to_csv(outdir / "candidate_terms_long.csv", index=False)

    vocab = pd.DataFrame({
        "candidate_term": terms,
        "document_frequency": (X > 0).sum(axis=0).A1,
        "mean_tfidf": np.asarray(X.mean(axis=0)).ravel(),
    }).sort_values(["document_frequency", "mean_tfidf"], ascending=[False, False])
    vocab.to_csv(outdir / "candidate_vocabulary.csv", index=False)

    write_json(outdir / "term_extraction_summary.json", {
        "records": int(len(df)),
        "candidate_assignments": int(len(long)),
        "unique_candidate_terms": int(vocab["candidate_term"].nunique()),
        "method": "TfidfVectorizer n-grams over normalized title + abstract",
        "parameters": tcfg,
    })


if __name__ == "__main__":
    main()
