from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import argparse
from pathlib import Path

import networkx as nx
import pandas as pd

from andromeda_titles_plus_abstracts.utils import build_cooccurrence_edges, ensure_dir, read_config, read_table, write_json


def main() -> None:
    ap = argparse.ArgumentParser(description="Final analyses for title + abstract semantic concepts.")
    ap.add_argument("--articles", required=True)
    ap.add_argument("--terms", required=True)
    ap.add_argument("--output-dir", required=True)
    ap.add_argument("--config", default="config/default_config.json")
    args = ap.parse_args()

    cfg = read_config(args.config)
    outdir = ensure_dir(args.output_dir)
    articles = read_table(args.articles)
    terms = read_table(args.terms)

    article_concepts = terms.drop_duplicates(["article_id", "concept_id"]).copy()
    article_concepts.to_csv(outdir / "stage6_article_concepts.csv", index=False)

    period_descriptives = (
        articles.groupby(["analysis_period", "analysis_period_order"])
        .agg(n_articles=("article_id", "nunique"))
        .reset_index()
        .merge(
            article_concepts.groupby(["analysis_period", "analysis_period_order"])
            .agg(n_concept_assignments=("concept_id", "size"), n_unique_concepts=("concept_id", "nunique"))
            .reset_index(),
            on=["analysis_period", "analysis_period_order"],
            how="left"
        )
        .sort_values("analysis_period_order")
    )
    period_descriptives["mean_concepts_per_article"] = period_descriptives["n_concept_assignments"] / period_descriptives["n_articles"]
    period_descriptives.to_csv(outdir / "stage6_period_descriptives.csv", index=False)

    top_overall = (
        article_concepts.groupby(["concept_id", "concept_label_en", "concept_label_pl"])
        .agg(n_articles=("article_id", "nunique"))
        .reset_index()
        .sort_values(["n_articles", "concept_label_en"], ascending=[False, True])
    )
    top_overall["pct_articles"] = 100 * top_overall["n_articles"] / articles["article_id"].nunique()
    top_overall.to_csv(outdir / "stage6_top_terms_overall.csv", index=False)

    period_counts = (
        article_concepts.groupby(["analysis_period", "analysis_period_order", "concept_id", "concept_label_en", "concept_label_pl"])
        .agg(n_articles=("article_id", "nunique"))
        .reset_index()
        .merge(period_descriptives[["analysis_period", "n_articles"]].rename(columns={"n_articles": "period_n_articles"}), on="analysis_period", how="left")
    )
    period_counts["pct_articles_in_period"] = 100 * period_counts["n_articles"] / period_counts["period_n_articles"]
    period_counts.to_csv(outdir / "stage6_concept_period_counts.csv", index=False)

    wide = period_counts.pivot_table(index=["concept_id", "concept_label_en", "concept_label_pl"], columns="analysis_period_order", values="pct_articles_in_period", fill_value=0)
    wide.columns = [f"period_{c}_pct" for c in wide.columns]
    wide = wide.reset_index()
    pct_cols = [c for c in wide.columns if c.endswith("_pct")]
    if pct_cols:
        wide["first_period_pct"] = wide[pct_cols[0]]
        wide["last_period_pct"] = wide[pct_cols[-1]]
        wide["delta_first_last_pct"] = wide["last_period_pct"] - wide["first_period_pct"]
        wide["n_periods_present"] = (wide[pct_cols] > 0).sum(axis=1)
        wide["peak_period_column"] = wide[pct_cols].idxmax(axis=1)
    wide.to_csv(outdir / "stage6_term_period_trends.csv", index=False)

    wide.sort_values("delta_first_last_pct", ascending=False).head(100).to_csv(outdir / "stage6_rising_terms.csv", index=False)
    wide.sort_values("delta_first_last_pct", ascending=True).head(100).to_csv(outdir / "stage6_falling_terms.csv", index=False)
    wide[(wide["first_period_pct"] == 0) & (wide["last_period_pct"] > 0)].sort_values("last_period_pct", ascending=False).to_csv(outdir / "stage6_emerging_terms.csv", index=False)
    wide[wide["n_periods_present"] == len(pct_cols)].sort_values("last_period_pct", ascending=False).to_csv(outdir / "stage6_persistent_terms.csv", index=False)

    edges = build_cooccurrence_edges(article_concepts, "article_id", "concept_label_en")
    edges.to_csv(outdir / "stage6_cooccurrence_edges_all.csv", index=False)
    min_w = int(cfg.get("cooccurrence", {}).get("min_edge_weight", 3))
    fedges = edges[edges["weight"] >= min_w].copy()
    fedges.to_csv(outdir / "stage6_cooccurrence_edges_filtered.csv", index=False)

    G = nx.Graph()
    for _, r in fedges.iterrows():
        G.add_edge(r["source"], r["target"], weight=int(r["weight"]))
    communities = []
    if G.number_of_nodes() > 0:
        comms = nx.community.greedy_modularity_communities(G, weight="weight")
        for i, c in enumerate(comms, start=1):
            for node in c:
                communities.append({"concept_label_en": node, "community_id": i})
    comm_df = pd.DataFrame(communities)
    comm_df.to_csv(outdir / "stage6_network_communities.csv", index=False)

    nodes = pd.DataFrame([{"concept_label_en": n, "degree": int(G.degree(n)), "weighted_degree": float(G.degree(n, weight="weight"))} for n in G.nodes()])
    if not nodes.empty and not comm_df.empty:
        nodes = nodes.merge(comm_df, on="concept_label_en", how="left")
    nodes.to_csv(outdir / "stage6_network_nodes.csv", index=False)

    write_json(outdir / "stage6_summary.json", {
        "n_articles": int(articles["article_id"].nunique()),
        "n_article_concept_pairs": int(len(article_concepts)),
        "n_unique_concepts": int(article_concepts["concept_id"].nunique()),
        "n_periods": int(period_descriptives["analysis_period"].nunique()),
        "cooccurrence_min_edge_weight": min_w,
        "network_nodes": int(G.number_of_nodes()),
        "network_edges": int(G.number_of_edges()),
        "network_communities": int(comm_df["community_id"].nunique()) if not comm_df.empty else 0,
    })


if __name__ == "__main__":
    main()
