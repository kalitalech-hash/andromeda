# 3_analyze_pp_trends.py
# -*- coding: utf-8 -*-

import os
import pandas as pd

IN_PATH = os.path.join("output", "pp_keywords_long_normalized.csv")
OUT_DIR = "output"

def add_period(year: int) -> str:
    # pięciolatki
    if year is None:
        return "unknown"
    y = int(year)
    if 2005 <= y <= 2009: return "2005–2009"
    if 2010 <= y <= 2014: return "2010–2014"
    if 2015 <= y <= 2019: return "2015–2019"
    if 2020 <= y <= 2024: return "2020–2024"
    if 2025 <= y <= 2029: return "2025–2029"
    return "other"

def main() -> None:
    df = pd.read_csv(IN_PATH)
    df = df.dropna(subset=["year", "keyword_norm"]).copy()
    df["year"] = df["year"].astype(int)
    df["period"] = df["year"].map(add_period)

    # Top tematy ogółem
    top = df["keyword_norm"].value_counts().head(30).rename_axis("keyword").reset_index(name="count")
    top.to_csv(os.path.join(OUT_DIR, "pp_top_keywords.csv"), index=False, encoding="utf-8")

    # Tabela trendów w pięciolatkach (top 25)
    top25 = set(top["keyword"].head(25))
    pivot = (
        df[df["keyword_norm"].isin(top25)]
        .groupby(["keyword_norm", "period"])
        .size()
        .reset_index(name="count")
        .pivot_table(index="keyword_norm", columns="period", values="count", fill_value=0)
    )
    pivot.to_csv(os.path.join(OUT_DIR, "pp_trends_by_5y.csv"), encoding="utf-8")

    # Rosnące vs malejące: porównaj pierwszy i ostatni dostępny okres
    # (tu bierzemy 2005–2009 vs 2020–2024; możesz zmienić)
    early = "2005–2009"
    late = "2020–2024"
    if early in pivot.columns and late in pivot.columns:
        tmp = pivot.copy()
        tmp["change"] = tmp[late] - tmp[early]
        rising = tmp.sort_values("change", ascending=False).head(20)
        falling = tmp.sort_values("change", ascending=True).head(20)
        rising.to_csv(os.path.join(OUT_DIR, "pp_rising_topics.csv"), encoding="utf-8")
        falling.to_csv(os.path.join(OUT_DIR, "pp_falling_topics.csv"), encoding="utf-8")

    print("[DONE] Wrote:\n- pp_top_keywords.csv\n- pp_trends_by_5y.csv\n- pp_rising_topics.csv (if periods exist)\n- pp_falling_topics.csv (if periods exist)")

if __name__ == "__main__":
    main()