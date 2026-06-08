from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from itertools import combinations
from pathlib import Path
from typing import Iterable

import pandas as pd


def read_config(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def read_table(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() in {".jsonl", ".ndjson"}:
        return pd.read_json(path, lines=True)
    if path.suffix.lower() == ".json":
        return pd.read_json(path)
    raise ValueError(f"Unsupported input format: {path.suffix}")


def write_json(path: str | Path, data: dict) -> None:
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def normalize_text(value: object, lowercase: bool = True) -> str:
    if pd.isna(value):
        return ""
    text = str(value)
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = text.replace("–", "-").replace("—", "-").replace("−", "-")
    text = re.sub(r"[\r\n\t]+", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    if lowercase:
        text = text.lower()
    return text


def stable_hash(parts: Iterable[object], n: int = 16) -> str:
    raw = "||".join("" if pd.isna(x) else str(x) for x in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:n]


def add_title_year_hash(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    title_norm = df.get("title", "").map(lambda x: normalize_text(x, lowercase=True))
    years = df.get("year", "")
    df["title_year_hash"] = [stable_hash([t, y]) for t, y in zip(title_norm, years)]
    return df


def periodize_year(year: object, periods: list[dict]) -> tuple[str, int]:
    try:
        y = int(float(year))
    except Exception:
        return ("missing_year", 999)
    for p in periods:
        if int(p["start"]) <= y <= int(p["end"]):
            return (p["label"], int(p["order"]))
    return ("out_of_defined_periods", 998)


def article_term_pairs(df: pd.DataFrame, article_col: str, term_col: str) -> pd.DataFrame:
    return df[[article_col, term_col]].dropna().drop_duplicates()


def build_cooccurrence_edges(df: pd.DataFrame, article_col: str, term_col: str) -> pd.DataFrame:
    rows = []
    for article_id, group in df[[article_col, term_col]].dropna().drop_duplicates().groupby(article_col):
        terms = sorted(set(group[term_col].astype(str)))
        for a, b in combinations(terms, 2):
            rows.append((a, b, article_id))
    if not rows:
        return pd.DataFrame(columns=["source", "target", "weight", "article_ids"])
    edges = pd.DataFrame(rows, columns=["source", "target", "article_id"])
    out = (
        edges.groupby(["source", "target"])
        .agg(weight=("article_id", "nunique"), article_ids=("article_id", lambda x: "|".join(sorted(map(str, set(x))))))
        .reset_index()
        .sort_values(["weight", "source", "target"], ascending=[False, True, True])
    )
    return out
