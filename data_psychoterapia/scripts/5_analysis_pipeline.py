#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
02_analysis_pipeline_psychoterapia.py

Repo-ready pipeline analityczny dla korpusu "Psychoterapia".

Wejście:
    keywords_long_polish_semantic.csv
        oczekiwane kolumny:
        - year
        - issue_label
        - item_type
        - title
        - url
        - keyword_semantic_auto
"""

from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations
from pathlib import Path

import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from networkx.algorithms.community import greedy_modularity_communities, modularity

PERIOD_ORDER = ["2005–2009", "2010–2014", "2015–2019", "2020–2025"]


def assign_period(year: int):
    if 2005 <= year <= 2009:
        return "2005–2009"
    elif 2010 <= year <= 2014:
        return "2010–2014"
    elif 2015 <= year <= 2019:
        return "2015–2019"
    elif 2020 <= year <= 2025:
        return "2020–2025"
    return np.nan


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    if "keyword_semantic_auto" not in df.columns:
        raise ValueError("Brak kolumny keyword_semantic_auto.")

    df = df.rename(columns={"url": "article_id", "keyword_semantic_auto": "keyword"}).copy()
    df["keyword"] = df["keyword"].astype(str).str.strip()
    df = df.dropna(subset=["article_id", "year", "keyword"])
    df = df[df["keyword"] != ""]
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    df = df.dropna(subset=["year"])
    df["year"] = df["year"].astype(int)
    df["period"] = df["year"].apply(assign_period)
    df = df.dropna(subset=["period"])
    df = df.drop_duplicates(subset=["article_id", "keyword"]).reset_index(drop=True)
    return df


def descriptive_tables(df: pd.DataFrame, outdir: Path):
    table1 = df["keyword"].value_counts().reset_index()
    table1.columns = ["temat", "liczba artykułów"]
    top10 = table1.head(10)
    top10.to_csv(outdir / "tabela1_top10.csv", index=False, encoding="utf-8-sig")

    table2_keywords = [
        "proces psychoterapii (ogólnie)",
        "psychoterapia psychodynamiczna",
        "cbt",
        "lęk",
        "zaburzenia osobowości",
        "terapia par",
        "borderline",
        "depresja",
        "kryzys relacyjny",
        "perspektywa rozwojowa",
        "trauma",
    ]
    existing = [kw for kw in table2_keywords if kw in set(df["keyword"].unique())]

    table2 = (
        df[df["keyword"].isin(existing)]
        .groupby(["keyword", "period"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=PERIOD_ORDER, fill_value=0)
        .reindex(existing)
        .reset_index()
        .rename(columns={"keyword": "temat"})
    )
    table2.to_csv(outdir / "tabela2_okresy.csv", index=False, encoding="utf-8-sig")

    full_period_table = (
        df.groupby(["keyword", "period"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=PERIOD_ORDER, fill_value=0)
    )
    full_period_table["zmiana"] = full_period_table["2020–2025"] - full_period_table["2005–2009"]

    growth = (
        full_period_table.sort_values("zmiana", ascending=False)
        .head(10)
        .reset_index()
        .rename(columns={"keyword": "temat"})
    )[["temat", "2005–2009", "2020–2025", "zmiana"]]

    decline = (
        full_period_table.sort_values("zmiana", ascending=True)
        .head(10)
        .reset_index()
        .rename(columns={"keyword": "temat"})
    )[["temat", "2005–2009", "2020–2025", "zmiana"]]

    growth.to_csv(outdir / "tabela3_rosnace.csv", index=False, encoding="utf-8-sig")
    decline.to_csv(outdir / "tabela3_malejace.csv", index=False, encoding="utf-8-sig")

    yearly_records = df.groupby("year").size().reset_index(name="liczba_rekordow")
    yearly_unique = df.groupby("year")["keyword"].nunique().reset_index(name="liczba_unikalnych_keywordow")
    yearly_records.to_csv(outdir / "yearly_records.csv", index=False, encoding="utf-8-sig")
    yearly_unique.to_csv(outdir / "yearly_unique_keywords.csv", index=False, encoding="utf-8-sig")

    return top10, table2, growth, decline


def build_cooccurrence_network(df: pd.DataFrame, outdir: Path, threshold: int = 2):
    article_keywords = df.groupby("article_id")["keyword"].apply(lambda x: sorted(set(x)))
    edge_counter = Counter()

    for keywords in article_keywords:
        if len(keywords) < 2:
            continue
        for pair in combinations(keywords, 2):
            edge_counter[pair] += 1

    edges = pd.DataFrame(
        [(a, b, w) for (a, b), w in edge_counter.items()],
        columns=["source", "target", "weight"]
    )

    edges_thr = edges[edges["weight"] >= threshold].copy()
    edges_thr.to_csv(outdir / "cooccurrence_edges_threshold2.csv", index=False, encoding="utf-8-sig")

    G = nx.Graph()
    for _, row in edges_thr.iterrows():
        G.add_edge(row["source"], row["target"], weight=row["weight"])

    keyword_freq = df["keyword"].value_counts().to_dict()
    nx.set_node_attributes(G, keyword_freq, "frequency")

    communities = list(greedy_modularity_communities(G, weight="weight"))
    mod_value = modularity(G, communities, weight="weight") if G.number_of_edges() else np.nan

    node_to_cluster = {}
    for i, comm in enumerate(communities, start=1):
        for node in comm:
            node_to_cluster[node] = i

    weighted_degree = dict(G.degree(weight="weight"))
    nodes_df = pd.DataFrame({"keyword": list(G.nodes())})
    nodes_df["cluster"] = nodes_df["keyword"].map(node_to_cluster)
    nodes_df["frequency"] = nodes_df["keyword"].map(keyword_freq)
    nodes_df["weighted_degree"] = nodes_df["keyword"].map(weighted_degree)
    nodes_df = nodes_df.sort_values(["cluster", "weighted_degree"], ascending=[True, False])

    cluster_rows = []
    for cluster_id, comm in enumerate(communities, start=1):
        sub = nodes_df[nodes_df["keyword"].isin(comm)].sort_values("weighted_degree", ascending=False)
        cluster_rows.append({
            "klaster": cluster_id,
            "liczba_węzłów": len(comm),
            "reprezentatywne_terminy": ", ".join(sub["keyword"].head(8).tolist())
        })

    cluster_df = pd.DataFrame(cluster_rows).sort_values("liczba_węzłów", ascending=False)
    top_edges = edges_thr.sort_values("weight", ascending=False).reset_index(drop=True)

    nodes_df.to_csv(outdir / "nodes_with_clusters.csv", index=False, encoding="utf-8-sig")
    cluster_df.to_csv(outdir / "tabela4_klastry.csv", index=False, encoding="utf-8-sig")
    top_edges.to_csv(outdir / "top_edges.csv", index=False, encoding="utf-8-sig")

    return G, nodes_df, cluster_df, top_edges, mod_value


def make_figures(top10, table2, growth, decline, G, nodes_df, outdir: Path):
    plt.figure(figsize=(11, 7))
    df1 = top10.sort_values("liczba artykułów", ascending=True)
    plt.barh(df1["temat"], df1["liczba artykułów"])
    plt.xlabel("Liczba artykułów")
    plt.ylabel("Temat")
    plt.title("Najczęściej występujące tematy w korpusie „Psychoterapia” (2005–2025)")
    plt.tight_layout()
    plt.savefig(outdir / "rycina_tabela1_top_tematy_psychoterapia.png", dpi=300, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(12, 7))
    for _, row in table2.iterrows():
        plt.plot(PERIOD_ORDER, [row[p] for p in PERIOD_ORDER], marker="o", label=row["temat"])
    plt.xlabel("Okres analityczny")
    plt.ylabel("Liczba artykułów")
    plt.title("Zmiany częstości głównych tematów w kolejnych okresach publikacji")
    plt.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)
    plt.tight_layout()
    plt.savefig(outdir / "rycina_tabela2_trendy_okresowe_psychoterapia.png", dpi=300, bbox_inches="tight")
    plt.close()

    changes = pd.concat([growth.assign(kategoria="wzrost"), decline.assign(kategoria="spadek")], ignore_index=True)
    changes = changes.sort_values("zmiana", ascending=True)

    plt.figure(figsize=(11, 8))
    plt.barh(changes["temat"], changes["zmiana"])
    plt.axvline(0, linewidth=1)
    plt.xlabel("Zmiana liczby artykułów między 2005–2009 a 2020–2025")
    plt.ylabel("Temat")
    plt.title("Tematy o największym wzroście i spadku częstości występowania")
    plt.tight_layout()
    plt.savefig(outdir / "rycina_tabela3_zmiany_psychoterapia.png", dpi=300, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(14, 11))
    pos = nx.spring_layout(G, k=0.45, seed=42, weight="weight")

    cluster_ids = sorted(nodes_df["cluster"].dropna().unique())
    cluster_color_map = {cid: i for i, cid in enumerate(cluster_ids)}

    node_to_cluster = dict(zip(nodes_df["keyword"], nodes_df["cluster"]))
    keyword_freq = dict(zip(nodes_df["keyword"], nodes_df["frequency"]))

    node_colors = [cluster_color_map[node_to_cluster[n]] for n in G.nodes()]
    node_sizes = [keyword_freq.get(n, 1) * 18 for n in G.nodes()]
    edge_widths = [G[u][v]["weight"] * 0.18 for u, v in G.edges()]

    nx.draw_networkx_edges(G, pos, width=edge_widths, alpha=0.25)
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors, alpha=0.9)

    label_nodes = nodes_df.sort_values("frequency", ascending=False).head(30)["keyword"].tolist()
    labels = {n: n for n in G.nodes() if n in label_nodes}
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=9)

    plt.title("Mapa współwystępowania słów kluczowych w „Psychoterapii”")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(outdir / "psychoterapia_mapa_wspolwystepowania_klastry.png", dpi=300, bbox_inches="tight")
    plt.close()


def export_excel(top10, table2, growth, decline, cluster_df, nodes_df, top_edges, outdir: Path):
    with pd.ExcelWriter(outdir / "psychoterapia_tables_and_network.xlsx", engine="openpyxl") as writer:
        top10.to_excel(writer, sheet_name="Tabela1_top10", index=False)
        table2.to_excel(writer, sheet_name="Tabela2_okresy", index=False)
        growth.to_excel(writer, sheet_name="Tabela3_rosnace", index=False)
        decline.to_excel(writer, sheet_name="Tabela3_malejace", index=False)
        cluster_df.to_excel(writer, sheet_name="Tabela4_klastry", index=False)
        nodes_df.to_excel(writer, sheet_name="Wezly", index=False)
        top_edges.to_excel(writer, sheet_name="Top_edges", index=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="keywords_long_polish_semantic.csv")
    parser.add_argument("--outdir", default="outputs_psychoterapia")
    parser.add_argument("--threshold", type=int, default=2)
    args = parser.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = load_data(args.input)

    print(f"Liczba rekordów po deduplikacji artykuł–keyword: {len(df)}")
    print(f"Liczba artykułów: {df['article_id'].nunique()}")
    print(f"Liczba unikalnych słów kluczowych: {df['keyword'].nunique()}")
    print(df["period"].value_counts().sort_index())

    top10, table2, growth, decline = descriptive_tables(df, outdir)
    G, nodes_df, cluster_df, top_edges, mod_value = build_cooccurrence_network(df, outdir, threshold=args.threshold)

    print(f"Węzły po progowaniu: {G.number_of_nodes()}")
    print(f"Krawędzie po progowaniu: {G.number_of_edges()}")
    print(f"Liczba klastrów: {cluster_df.shape[0]}")
    print(f"Modularność: {round(mod_value, 3) if pd.notna(mod_value) else 'NA'}")

    make_figures(top10, table2, growth, decline, G, nodes_df, outdir)
    export_excel(top10, table2, growth, decline, cluster_df, nodes_df, top_edges, outdir)

    print(f"Gotowe. Wyniki zapisano w: {outdir}")


if __name__ == "__main__":
    main()