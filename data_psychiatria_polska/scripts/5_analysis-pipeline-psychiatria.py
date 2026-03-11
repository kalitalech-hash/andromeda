#!/usr/bin/env python3
# -*- coding: utf-8 -*-

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

PERIOD_ORDER = ["2007–2011", "2012–2016", "2017–2021", "2022–2025"]


def assign_period(year: int):
    if 2007 <= year <= 2011:
        return "2007–2011"
    elif 2012 <= year <= 2016:
        return "2012–2016"
    elif 2017 <= year <= 2021:
        return "2017–2021"
    elif 2022 <= year <= 2025:
        return "2022–2025"
    return np.nan


def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    required = {"url", "year", "keyword_final_polish"}
    if not required.issubset(df.columns):
        raise ValueError(f"Brak wymaganych kolumn: {required - set(df.columns)}")

    df = df.rename(columns={"url": "article_id", "keyword_final_polish": "keyword"}).copy()
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
    table1.columns = ["temat", "liczba rekordów"]
    top10 = table1.head(10)
    top10.to_csv(outdir / "tabela1_top10.csv", index=False, encoding="utf-8-sig")

    top_keywords = top10["temat"].tolist()
    table2 = (
        df[df["keyword"].isin(top_keywords)]
        .groupby(["keyword", "period"])
        .size()
        .unstack(fill_value=0)
        .reindex(columns=PERIOD_ORDER, fill_value=0)
        .reindex(top_keywords)
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
    full_period_table["zmiana"] = full_period_table["2022–2025"] - full_period_table["2007–2011"]

    growth = (
        full_period_table.sort_values("zmiana", ascending=False)
        .head(10)
        .reset_index()
        .rename(columns={"keyword": "temat"})
    )[["temat", "2007–2011", "2022–2025", "zmiana"]]

    decline = (
        full_period_table.sort_values("zmiana", ascending=True)
        .head(10)
        .reset_index()
        .rename(columns={"keyword": "temat"})
    )[["temat", "2007–2011", "2022–2025", "zmiana"]]

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
    df1 = top10.sort_values("liczba rekordów", ascending=True)
    plt.barh(df1["temat"], df1["liczba rekordów"])
    plt.xlabel("Liczba rekordów")
    plt.ylabel("Temat")
    plt.title("Najczęściej występujące tematy w korpusie „Psychiatria Polska” (2007–2025)")
    plt.tight_layout()
    plt.savefig(outdir / "rycina_tabela1_top_tematy_PP.png", dpi=300, bbox_inches="tight")
    plt.close()

    plt.figure(figsize=(12, 7))
    for _, row in table2.iterrows():
        plt.plot(PERIOD_ORDER, [row[p] for p in PERIOD_ORDER], marker="o", label=row["temat"])
    plt.xlabel("Okres analityczny")
    plt.ylabel("Liczba rekordów")
    plt.title("Zmiany częstości głównych tematów w kolejnych okresach publikacji")
    plt.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False)
    plt.tight_layout()
    plt.savefig(outdir / "rycina_tabela2_trendy_okresowe_PP.png", dpi=300, bbox_inches="tight")
    plt.close()

    changes = pd.concat([growth.assign(kategoria="wzrost"), decline.assign(kategoria="spadek")], ignore_index=True)
    changes = changes.sort_values("zmiana", ascending=True)

    plt.figure(figsize=(11, 8))
    plt.barh(changes["temat"], changes["zmiana"])
    plt.axvline(0, linewidth=1)
    plt.xlabel("Zmiana liczby rekordów między 2007–2011 a 2022–2025")
    plt.ylabel("Temat")
    plt.title("Tematy o największym wzroście i względnym spadku częstości występowania")
    plt.tight_layout()
    plt.savefig(outdir / "rycina_tabela3_zmiany_PP.png", dpi=300, bbox_inches="tight")
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

    plt.title("Mapa współwystępowania słów kluczowych w „Psychiatrii Polskiej”")
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(outdir / "pp_mapa_wspolwystepowania_klastry.png", dpi=300, bbox_inches="tight")
    plt.close()


def export_excel(top10, table2, growth, decline, cluster_df, nodes_df, top_edges, outdir: Path):
    with pd.ExcelWriter(outdir / "pp_tables_and_network.xlsx", engine="openpyxl") as writer:
        top10.to_excel(writer, sheet_name="Tabela1_top10", index=False)
        table2.to_excel(writer, sheet_name="Tabela2_okresy", index=False)
        growth.to_excel(writer, sheet_name="Tabela3_rosnace", index=False)
        decline.to_excel(writer, sheet_name="Tabela3_malejace", index=False)
        cluster_df.to_excel(writer, sheet_name="Tabela4_klastry", index=False)
        nodes_df.to_excel(writer, sheet_name="Wezly", index=False)
        top_edges.to_excel(writer, sheet_name="Top_edges", index=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="pp_keywords_final_clean_v7.csv")
    parser.add_argument("--outdir", default="outputs_pp")
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