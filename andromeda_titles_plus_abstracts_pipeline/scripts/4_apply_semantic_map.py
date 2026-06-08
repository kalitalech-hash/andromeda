from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import argparse
import pandas as pd

from andromeda_titles_plus_abstracts.utils import ensure_dir, read_table, write_json


REQUIRED_MAP_COLUMNS = [
    "candidate_term",
    "concept_id",
    "concept_label_en",
    "concept_label_pl",
    "semantic_action",
    "semantic_confidence",
    "audit_decision",
]


def main() -> None:
    ap = argparse.ArgumentParser(description="Apply human-audited semantic map to candidate terms.")
    ap.add_argument("--terms", required=True)
    ap.add_argument("--map", required=True)
    ap.add_argument("--output-dir", required=True)
    args = ap.parse_args()

    outdir = ensure_dir(args.output_dir)
    terms = read_table(args.terms)
    smap = read_table(args.map)

    missing = [c for c in REQUIRED_MAP_COLUMNS if c not in smap.columns]
    if missing:
        raise ValueError(f"Semantic map missing columns: {missing}")

    merged = terms.merge(smap, on="candidate_term", how="left")
    merged["semantic_action"] = merged["semantic_action"].fillna("unmapped")
    merged["semantic_confidence"] = merged["semantic_confidence"].fillna("none")
    merged["audit_decision"] = merged["audit_decision"].fillna("review")
    merged["concept_id"] = merged["concept_id"].fillna("UNMAPPED::" + merged["candidate_term"].astype(str))
    merged["concept_label_en"] = merged["concept_label_en"].fillna(merged["candidate_term"])
    merged["concept_label_pl"] = merged["concept_label_pl"].fillna(merged["candidate_term"])
    merged["include_in_analysis"] = ~merged["audit_decision"].astype(str).str.lower().isin(["exclude", "drop", "remove"])

    final = merged[merged["include_in_analysis"]].copy()
    audit = merged[merged["audit_decision"].astype(str).str.lower().isin(["review", "manual_review", ""])]
    excluded = merged[~merged["include_in_analysis"]].copy()

    final.to_csv(outdir / "terms_semantic_final.csv", index=False)
    audit.to_csv(outdir / "semantic_audit_queue.csv", index=False)
    excluded.to_csv(outdir / "semantic_excluded_records.csv", index=False)

    concept_counts = (
        final.drop_duplicates(["article_id", "concept_id"])
        .groupby(["concept_id", "concept_label_en", "concept_label_pl"])
        .agg(n_articles=("article_id", "nunique"), n_assignments=("article_id", "size"))
        .reset_index()
        .sort_values(["n_articles", "concept_label_en"], ascending=[False, True])
    )
    concept_counts.to_csv(outdir / "semantic_concept_counts.csv", index=False)

    write_json(outdir / "semantic_summary.json", {
        "candidate_assignments": int(len(terms)),
        "final_assignments": int(len(final)),
        "excluded_assignments": int(len(excluded)),
        "audit_queue_assignments": int(len(audit)),
        "unique_final_concepts": int(final["concept_id"].nunique()),
        "semantic_map_file": args.map,
    })


if __name__ == "__main__":
    main()
