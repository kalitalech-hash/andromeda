#!/usr/bin/env python3
"""
Andromeda keyword-source audit.

This script samples article landing pages from an already scraped article table
and checks whether author keywords are publicly exposed in HTML/meta/JSON-LD.

It should be run before investing in a large keyword extraction job for a new
corpus or publisher family.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm


def make_session(mailto: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": f"AndromedaKeywordSourceAudit/0.2 (mailto:{mailto})",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    return s


def get(session: requests.Session, url: str, timeout=(10, 30), tries=3, delay=1.0) -> requests.Response:
    last = None
    for i in range(tries):
        try:
            return session.get(url, timeout=timeout, allow_redirects=True)
        except requests.RequestException as exc:
            last = exc
            if i < tries - 1:
                time.sleep(delay * (i + 1))
    raise last


def read_articles(raw_dir: Path) -> pd.DataFrame:
    files = sorted(raw_dir.glob("*_articles.csv"))
    if not files:
        files = sorted(raw_dir.glob("combined_articles.csv"))
    if not files:
        raise FileNotFoundError(f"No *_articles.csv files found in {raw_dir}")
    frames = []
    for p in files:
        df = pd.read_csv(p)
        df["source_file"] = p.name
        frames.append(df)
    df = pd.concat(frames, ignore_index=True)
    if "article_url" not in df.columns:
        raise ValueError("Article table must contain article_url.")
    if "journal_key" not in df.columns:
        df["journal_key"] = "unknown"
    return df.drop_duplicates(subset=[c for c in ["article_id", "article_url"] if c in df.columns])


def inspect_html(html: str) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
    soup = BeautifulSoup(html, "lxml")
    signals = {
        "meta_citation_keywords": 0,
        "meta_dc_subject": 0,
        "meta_keywords": 0,
        "jsonld_keywords_or_about": 0,
        "keyword_class_or_id": 0,
        "visible_keyword_text": 0,
    }
    snippets: List[Dict[str, str]] = []

    for tag in soup.find_all("meta"):
        name = (tag.get("name") or tag.get("property") or "").lower()
        content = tag.get("content") or ""
        if "citation_keywords" in name:
            signals["meta_citation_keywords"] += 1
            snippets.append({"signal": "meta_citation_keywords", "snippet": content[:500]})
        if "dc.subject" in name or name.endswith("subject"):
            signals["meta_dc_subject"] += 1
            snippets.append({"signal": "meta_dc_subject", "snippet": content[:500]})
        if name == "keywords" or name.endswith(":tag"):
            signals["meta_keywords"] += 1
            snippets.append({"signal": "meta_keywords", "snippet": content[:500]})

    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        txt = script.string or ""
        if re.search(r'"(keywords|about)"\s*:', txt, flags=re.I):
            signals["jsonld_keywords_or_about"] += 1
            snippets.append({"signal": "jsonld_keywords_or_about", "snippet": txt[:500]})

    nodes = soup.find_all(attrs={"class": re.compile("keyword|subject|tag", re.I)})
    nodes += soup.find_all(attrs={"id": re.compile("keyword|subject|tag", re.I)})
    signals["keyword_class_or_id"] = len(nodes)
    for node in nodes[:5]:
        text = node.get_text(" ", strip=True)
        if text:
            snippets.append({"signal": "keyword_class_or_id", "snippet": text[:500]})

    text = soup.get_text(" ", strip=True)
    m = re.search(r"\bkeywords?\b.{0,350}", text, flags=re.I)
    if m:
        signals["visible_keyword_text"] += 1
        snippets.append({"signal": "visible_keyword_text", "snippet": m.group(0)[:500]})

    return signals, snippets


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", required=True)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--samples-per-journal", type=int, default=10)
    ap.add_argument("--mailto", required=True)
    ap.add_argument("--delay", type=float, default=0.8)
    args = ap.parse_args()

    raw_dir = Path(args.raw_dir)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    articles = read_articles(raw_dir)
    articles = articles[articles["article_url"].notna()].copy()

    samples = (
        articles.groupby("journal_key", group_keys=False)
        .apply(lambda x: x.sample(min(len(x), args.samples_per_journal), random_state=42))
        .reset_index(drop=True)
    )

    session = make_session(args.mailto)
    rows: List[Dict[str, Any]] = []
    snippet_rows: List[Dict[str, Any]] = []

    for _, row in tqdm(samples.iterrows(), total=len(samples), desc="keyword-source audit", unit="article"):
        url = row["article_url"]
        rec = {
            "journal_key": row.get("journal_key"),
            "article_id": row.get("article_id"),
            "year": row.get("year"),
            "title": row.get("title"),
            "article_url": url,
        }
        try:
            r = get(session, url, delay=args.delay)
            rec.update({
                "http_status": r.status_code,
                "final_url": r.url,
                "content_type": r.headers.get("Content-Type", ""),
            })
            if r.status_code == 200 and "html" in rec["content_type"].lower():
                signals, snippets = inspect_html(r.text)
                rec.update(signals)
                rec["candidate_signal"] = int(any(v > 0 for v in signals.values()))
                for s in snippets:
                    snippet_rows.append({**rec, **s})
            else:
                rec["candidate_signal"] = 0
        except Exception as exc:
            rec.update({"http_status": "exception", "error": repr(exc), "candidate_signal": 0})
        rows.append(rec)
        time.sleep(args.delay)

    detail = pd.DataFrame(rows)
    detail.to_csv(outdir / "keyword_source_audit_samples.csv", index=False)
    pd.DataFrame(snippet_rows).to_csv(outdir / "keyword_source_audit_snippets.csv", index=False)

    summary = (
        detail.groupby("journal_key")
        .agg(
            n_samples=("article_url", "count"),
            n_http_200=("http_status", lambda x: int((x == 200).sum())),
            n_with_candidate_signal=("candidate_signal", "sum"),
        )
        .reset_index()
    )
    summary["candidate_signal_pct"] = (summary["n_with_candidate_signal"] / summary["n_samples"] * 100).round(2)
    summary.to_csv(outdir / "keyword_source_audit_summary_by_journal.csv", index=False)

    (outdir / "keyword_source_audit_summary.json").write_text(
        json.dumps({
            "n_samples": int(len(detail)),
            "n_with_candidate_signal": int(detail["candidate_signal"].sum()),
            "candidate_signal_pct": round(float(detail["candidate_signal"].mean() * 100), 2) if len(detail) else 0,
        }, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
