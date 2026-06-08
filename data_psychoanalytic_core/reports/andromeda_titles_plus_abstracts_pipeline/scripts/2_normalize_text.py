from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import argparse
import pandas as pd

from andromeda_titles_plus_abstracts.utils import ensure_dir, normalize_text, read_config, read_table, write_json


def main() -> None:
    ap = argparse.ArgumentParser(description="Technical normalization of titles and abstracts.")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--config", default="config/default_config.json")
    args = ap.parse_args()

    cfg = read_config(args.config)
    outdir = ensure_dir(args.output_dir)
    df = read_table(args.input)

    for col in cfg.get("text_columns", ["title", "abstract"]):
        if col not in df.columns:
            df[col] = ""
        df[f"{col}_norm"] = df[col].map(lambda x: normalize_text(x, lowercase=True))

    df["analysis_text"] = (
        df.get("title_norm", "").fillna("") + ". " + df.get("abstract_norm", "").fillna("")
    ).str.strip()

    df["n_title_chars_norm"] = df["title_norm"].str.len()
    df["n_abstract_chars_norm"] = df["abstract_norm"].str.len() if "abstract_norm" in df else 0
    df["has_abstract"] = df.get("abstract_norm", "").astype(str).str.len() > 0

    df.to_csv(outdir / "articles_text_normalized.csv", index=False)
    write_json(outdir / "normalization_summary.json", {
        "records": int(len(df)),
        "records_with_abstract": int(df["has_abstract"].sum()),
        "records_without_abstract": int((~df["has_abstract"]).sum()),
        "text_columns": cfg.get("text_columns", ["title", "abstract"]),
    })

    df[["article_id", "title", "title_norm", "abstract", "abstract_norm"] if "abstract" in df.columns else ["article_id", "title", "title_norm"]].head(100).to_csv(
        outdir / "normalization_sample_first100.csv", index=False
    )


if __name__ == "__main__":
    main()
