import os
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go

IN = "output/keywords_long_normalized.csv"


def make_interactive_html(pivot: pd.DataFrame, years, out_path: str):

    # konwersja numpy -> python int
    years = [int(y) for y in years]

    data = {}

    for kw in pivot.index:
        series = pivot.loc[kw].astype(int).to_dict()
        data[kw] = [int(series.get(y, 0)) for y in years]

    overall = pivot.sum(axis=1).sort_values(ascending=False)
    default_kw = overall.index[0]

    top_per_year = {}

    for y in years:
        col = pivot[y].sort_values(ascending=False).head(15)
        top_per_year[str(int(y))] = [(str(k), int(v)) for k, v in col.items() if int(v) > 0]

    payload = {
        "years": years,
        "data": data,
        "default": str(default_kw),
        "topPerYear": top_per_year,
    }

    html = f"""
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Psychoterapia – trendy słów kluczowych</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>

<style>
body {{
font-family: Arial;
margin:40px;
}}

#chart {{
height:500px;
}}

input {{
padding:10px;
font-size:16px;
width:400px;
}}
</style>

</head>
<body>

<h1>Psychoterapia – historia słów kluczowych</h1>

<p>Wpisz słowo kluczowe:</p>

<input id="kw" list="kwlist">

<datalist id="kwlist"></datalist>

<div id="chart"></div>

<script>

const payload = {json.dumps(payload, ensure_ascii=False)};

const years = payload.years;
const data = payload.data;

const input = document.getElementById("kw");
const list = document.getElementById("kwlist");

Object.keys(data).forEach(k => {{
let o = document.createElement("option");
o.value = k;
list.appendChild(o);
}});

function draw(keyword)
{{
if(!data[keyword]) return;

let trace = {{
x: years,
y: data[keyword],
mode: "lines+markers",
name: keyword
}}

let layout = {{
title: keyword,
xaxis: {{title:"rok"}},
yaxis: {{title:"liczba artykułów"}}
}}

Plotly.newPlot("chart",[trace],layout)
}}

input.value = payload.default
draw(payload.default)

input.addEventListener("change", e=>draw(e.target.value))

</script>

</body>
</html>
"""

    with open(out_path, "w", encoding="utf8") as f:
        f.write(html)


def main():

    os.makedirs("output", exist_ok=True)

    df = pd.read_csv(IN)

    df_unique = df.drop_duplicates(subset=["year", "url", "keyword_final"])

    yearly = (
        df_unique.groupby(["year", "keyword_final"])
        .size()
        .reset_index(name="count")
    )

    yearly.to_csv("output/keywords_yearly.csv", index=False)

    years = sorted([int(y) for y in df_unique["year"].dropna().unique()])

    pivot = yearly.pivot_table(
        index="keyword_final",
        columns="year",
        values="count",
        fill_value=0
    )

    pivot.columns = [int(c) for c in pivot.columns]

    x = np.array(pivot.columns)
    X = x - x.mean()

    slopes = []

    for kw, row in pivot.iterrows():

        y = row.values.astype(float)

        slope = np.cov(X, y, bias=True)[0, 1] / (np.var(X) + 1e-9)

        slopes.append((kw, slope, y.sum()))

    trend = pd.DataFrame(slopes, columns=["keyword", "slope", "total"])

    top_up = trend.sort_values("slope", ascending=False).head(30)
    top_down = trend.sort_values("slope").head(30)

    mid = len(pivot.columns) // 2

    first = pivot.iloc[:, :mid].sum(axis=1)
    second = pivot.iloc[:, mid:].sum(axis=1)

    emerging = pd.DataFrame({
        "keyword": pivot.index,
        "first": first,
        "second": second,
        "ratio": (second + 1) / (first + 1)
    }).sort_values("ratio", ascending=False)

    declining = pd.DataFrame({
        "keyword": pivot.index,
        "first": first,
        "second": second,
        "ratio": (first + 1) / (second + 1)
    }).sort_values("ratio", ascending=False)

    emerging.to_csv("output/emerging_keywords.csv", index=False)
    declining.to_csv("output/declining_keywords.csv", index=False)

    for kw in top_up["keyword"].head(10):

        series = pivot.loc[kw]

        plt.figure()

        plt.plot(series.index, series.values, marker="o")

        plt.title(kw)

        plt.xlabel("rok")

        plt.ylabel("liczba artykułów")

        plt.tight_layout()

        name = "".join(c for c in kw if c.isalnum())

        plt.savefig(f"output/trend_{name}.png")

        plt.close()

    make_interactive_html(pivot, years, "output/report_interactive.html")

    html = "<h1>Raport trendów</h1>"

    html += "<h2>Najszybciej rosnące</h2>"
    html += top_up.to_html(index=False)

    html += "<h2>Najszybciej spadające</h2>"
    html += top_down.to_html(index=False)

    html += "<h2>Emerging</h2>"
    html += emerging.head(40).to_html(index=False)

    html += "<h2>Declining</h2>"
    html += declining.head(40).to_html(index=False)

    with open("output/report.html", "w", encoding="utf8") as f:
        f.write(html)

    print("Raport gotowy → output/report.html")
    print("Interaktywny raport → output/report_interactive.html")


if __name__ == "__main__":
    main()