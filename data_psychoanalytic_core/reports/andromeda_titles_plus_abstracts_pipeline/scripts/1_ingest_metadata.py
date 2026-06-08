from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import argparse
import pandas as pd

from andromeda_titles_plus_abstracts.utils import ensure_dir, read_config, read_table, write_json, add_title_year_hash


def main() -> None:
    ap = argparse.ArgumentParser(description="Ingest title + abstract metadata from CSV/JSONL.")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output", required=True)
    ap.add_argument("--config", default="config/default_config.json")
    args = ap.parse_args()

    cfg = read_config(args.config)
    df = read_table(args.input)

    for col in cfg["required_columns"]:
        if col not in df.columns:
            raise ValueError(f"Missing required column: {col}")

    for col in cfg.get("text_columns", []):
        if col not in df.columns:
            df[col] = ""

    df = add_title_year_hash(df)
    df["ingest_row_id"] = range(1, len(df) + 1)

    out = Path(args.output)
    ensure_dir(out.parent)
    df.to_csv(out, index=False)

    summary = {
        "input": args.input,
        "output": str(out),
        "n_records": int(len(df)),
        "columns": list(df.columns),
        "missing_title": int(df["title"].isna().sum() + (df["title"].astype(str).str.strip() == "").sum()),
        "missing_abstract": int(df["abstract"].isna().sum() + (df["abstract"].astype(str).str.strip() == "").sum()) if "abstract" in df else None,
    }
    write_json(out.with_suffix(".summary.json"), summary)


if __name__ == "__main__":
    main()
