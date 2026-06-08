from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import argparse
import pandas as pd

from andromeda_titles_plus_abstracts.utils import ensure_dir, read_config, read_table, write_json, add_title_year_hash


def first_existing(columns, candidates):
    return [c for c in candidates if c in columns]


def main() -> None:
    ap = argparse.ArgumentParser(description="QA and deduplicate title + abstract metadata.")
    ap.add_argument("--input", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--config", default="config/default_config.json")
    args = ap.parse_args()

    cfg = read_config(args.config)
    outdir = ensure_dir(args.output_dir)
    df = read_table(args.input)
    if "title_year_hash" not in df.columns:
        df = add_title_year_hash(df)

    qa_rows = []
    for col in ["article_id", "article_url", "doi", "title_year_hash"]:
        if col in df.columns:
            qa_rows.append({"check": f"unique_{col}", "value": int(df[col].nunique(dropna=True))})
            dup = df[df[col].notna() & df.duplicated(col, keep=False)]
            if len(dup):
                dup.to_csv(outdir / f"duplicate_{col}.csv", index=False)

    qa_rows.extend([
        {"check": "records_raw", "value": int(len(df))},
        {"check": "missing_title", "value": int(df["title"].isna().sum() + (df["title"].astype(str).str.strip() == "").sum()) if "title" in df else None},
        {"check": "missing_abstract", "value": int(df["abstract"].isna().sum() + (df["abstract"].astype(str).str.strip() == "").sum()) if "abstract" in df else None},
        {"check": "missing_year", "value": int(df["year"].isna().sum()) if "year" in df else None},
    ])

    year_min = cfg.get("year_min")
    year_max = cfg.get("year_max")
    scoped = df.copy()
    scoped["year_numeric"] = pd.to_numeric(scoped.get("year"), errors="coerce")
    out_of_scope = pd.DataFrame()
    if year_min is not None:
        out_of_scope = pd.concat([out_of_scope, scoped[scoped["year_numeric"] < int(year_min)]])
        scoped = scoped[scoped["year_numeric"] >= int(year_min)]
    if year_max is not None:
        out_of_scope = pd.concat([out_of_scope, scoped[scoped["year_numeric"] > int(year_max)]])
        scoped = scoped[scoped["year_numeric"] <= int(year_max)]
    if len(out_of_scope):
        out_of_scope.drop_duplicates().to_csv(outdir / "articles_out_of_scope_year.csv", index=False)

    keys = first_existing(scoped.columns, cfg.get("deduplication_keys", []))
    dedup = scoped.copy()
    removed = []
    for key in keys:
        before = len(dedup)
        dup_rows = dedup[dedup[key].notna() & dedup.duplicated(key, keep="first")].copy()
        if len(dup_rows):
            dup_rows["deduplication_key"] = key
            removed.append(dup_rows)
        dedup = dedup.drop_duplicates(subset=[key], keep="first")
        qa_rows.append({"check": f"removed_by_{key}", "value": int(before - len(dedup))})

    if removed:
        pd.concat(removed, ignore_index=True).to_csv(outdir / "articles_removed_duplicates.csv", index=False)

    dedup.to_csv(outdir / "articles_deduplicated.csv", index=False)
    pd.DataFrame(qa_rows).to_csv(outdir / "qa_checks.csv", index=False)
    write_json(outdir / "qa_summary.json", {
        "records_raw": int(len(df)),
        "records_after_scope_and_dedup": int(len(dedup)),
        "deduplication_keys_used": keys,
        "out_of_scope_records": int(len(out_of_scope)),
    })

    (outdir / "qa_report.md").write_text(
        "# QA report\n\n"
        f"Raw records: {len(df)}\n\n"
        f"Records after scope filtering and deduplication: {len(dedup)}\n\n"
        f"Deduplication keys used: {', '.join(keys)}\n",
        encoding="utf-8"
    )


if __name__ == "__main__":
    main()
