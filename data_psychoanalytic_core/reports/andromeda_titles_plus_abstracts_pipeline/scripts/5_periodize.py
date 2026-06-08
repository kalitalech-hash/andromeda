from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import argparse
import pandas as pd

from andromeda_titles_plus_abstracts.utils import ensure_dir, periodize_year, read_config, read_table, write_json


def main() -> None:
    ap = argparse.ArgumentParser(description="Assign analysis periods to articles and term records.")
    ap.add_argument("--articles", required=True)
    ap.add_argument("--terms", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--config", default="config/default_config.json")
    args = ap.parse_args()

    cfg = read_config(args.config)
    outdir = ensure_dir(args.output_dir)
    articles = read_table(args.articles)
    terms = read_table(args.terms)

    periods = cfg["periods"]
    periodized = articles.copy()
    period_info = periodized["year"].map(lambda y: periodize_year(y, periods))
    periodized["analysis_period"] = [x[0] for x in period_info]
    periodized["analysis_period_order"] = [x[1] for x in period_info]
    periodized.to_csv(outdir / "articles_periodized.csv", index=False)

    termp = terms.merge(
        periodized[["article_id", "year", "analysis_period", "analysis_period_order"]],
        on="article_id",
        how="left"
    )
    termp.to_csv(outdir / "terms_periodized.csv", index=False)

    period_summary = (
        periodized.groupby(["analysis_period", "analysis_period_order"])
        .agg(n_articles=("article_id", "nunique"), n_with_abstract=("has_abstract", "sum") if "has_abstract" in periodized else ("article_id", "size"))
        .reset_index()
        .sort_values("analysis_period_order")
    )
    period_summary.to_csv(outdir / "period_summary.csv", index=False)

    concept_period_counts = (
        termp.drop_duplicates(["article_id", "concept_id"])
        .groupby(["analysis_period", "analysis_period_order", "concept_id", "concept_label_en", "concept_label_pl"])
        .agg(n_articles=("article_id", "nunique"))
        .reset_index()
        .sort_values(["analysis_period_order", "n_articles"], ascending=[True, False])
    )
    concept_period_counts.to_csv(outdir / "concept_period_counts.csv", index=False)

    write_json(outdir / "periodization_summary.json", {
        "articles": int(len(periodized)),
        "term_assignments": int(len(termp)),
        "periods": periods,
        "missing_or_outside_period_articles": int(periodized["analysis_period"].isin(["missing_year", "out_of_defined_periods"]).sum()),
    })


if __name__ == "__main__":
    main()
