#!/usr/bin/env python3
"""
Andromeda World Corpus — keyword source audit (stage 1b)

Purpose
-------
After a full Crossref/landing-page scrape yields article metadata but zero author keywords,
this diagnostic script samples article landing pages and reports where keyword-like metadata
might actually live.

It does NOT download PDFs, bypass paywalls, or store full HTML by default.
It stores short snippets and metadata-field inventories for adapter development.

Inputs
------
A folder containing *_articles.csv files, e.g.
data_worldcorpus/data_psychotherapy_journals/raw_full_2005_2025_v05

Outputs
-------
<outdir>/keyword_source_audit_samples.csv
<outdir>/keyword_source_audit_summary.csv
<outdir>/keyword_source_audit_snippets.csv

Example
-------
python 1b_keyword_source_audit_worldcorpus.py ^
  --raw-dir data_worldcorpus/data_psychotherapy_journals/raw_full_2005_2025_v05 ^
  --outdir data_worldcorpus/data_psychotherapy_journals/qa_keyword_audit ^
  --samples-per-journal 8 ^
  --mailto your.email@example.org
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd
import requests
from bs4 import BeautifulSoup


KEY_PATTERNS = [
    r"keyword",
    r"key\s*word",
    r"author\s+keyword",
    r"\bkwd\b",
    r"kwd-group",
    r"article-keyword",
    r"subject",
    r"index\s+term",
    r"thesaurus",
    r"mesh",
    r"psycinfo",
]

META_KEY_CANDIDATES = [
    "citation_keywords",
    "dc.subject",
    "dc.Subject",
    "dcterms.subject",
    "keywords",
    "news_keywords",
    "article:tag",
    "parsely-tags",
    "prism.keyword",
]

USER_AGENT_TEMPLATE = (
    "AndromedaNowickaKeywordAudit/0.1 "
    "(mailto:{mailto}; human-in-the-loop bibliometric research; polite diagnostic sampling)"
)


def norm(s: Any) -> str:
    if s is None:
        return ""
    return re.sub(r"\s+", " ", str(s)).strip()


def safe_join(values: Iterable[Any], sep: str = " | ", max_len: int = 5000) -> str:
    out = sep.join(norm(v) for v in values if norm(v))
    return out[:max_len]


def read_articles(raw_dir: Path) -> pd.DataFrame:
    files = sorted(raw_dir.glob("*_articles.csv"))
    if not files:
        raise FileNotFoundError(f"No *_articles.csv files found in {raw_dir}")
    frames = []
    for p in files:
        try:
            df = pd.read_csv(p)
        except Exception as e:
            print(f"[WARN] Could not read {p}: {e}", file=sys.stderr)
            continue
        df["source_file"] = p.name
        frames.append(df)
    if not frames:
        raise RuntimeError("No readable article files.")
    articles = pd.concat(frames, ignore_index=True)
    for col in articles.columns:
        if articles[col].dtype == "object":
            articles[col] = articles[col].astype("string").str.strip()
    return articles


def sample_articles(df: pd.DataFrame, samples_per_journal: int, seed: int) -> pd.DataFrame:
    random.seed(seed)
    if "journal_key" not in df.columns:
        df["journal_key"] = "unknown_journal"

    # Prefer records with DOI/article_url and spread across recent and older years.
    df = df.copy()
    df["year_num"] = pd.to_numeric(df.get("year"), errors="coerce")

    sampled = []
    for journal, g in df.groupby("journal_key", dropna=False):
        g = g.dropna(subset=["article_url"]) if "article_url" in g.columns else g
        if g.empty:
            continue

        # Stratify lightly by period to avoid sampling only early years.
        bins = [
            g[g["year_num"].between(2005, 2009, inclusive="both")],
            g[g["year_num"].between(2010, 2014, inclusive="both")],
            g[g["year_num"].between(2015, 2019, inclusive="both")],
            g[g["year_num"].between(2020, 2026, inclusive="both")],
        ]
        picks = []
        quota_each = max(1, samples_per_journal // 4)
        for b in bins:
            if not b.empty:
                picks.append(b.sample(n=min(quota_each, len(b)), random_state=seed))
        if picks:
            picked = pd.concat(picks).drop_duplicates(subset=["article_id"] if "article_id" in g.columns else None)
        else:
            picked = g.sample(n=min(samples_per_journal, len(g)), random_state=seed)

        if len(picked) < min(samples_per_journal, len(g)):
            remaining = g[~g.index.isin(picked.index)]
            if not remaining.empty:
                extra = remaining.sample(
                    n=min(samples_per_journal - len(picked), len(remaining)),
                    random_state=seed + 1,
                )
                picked = pd.concat([picked, extra])
        sampled.append(picked.head(samples_per_journal))

    return pd.concat(sampled, ignore_index=True) if sampled else pd.DataFrame()


def make_session(mailto: str) -> requests.Session:
    s = requests.Session()
    s.headers.update({
        "User-Agent": USER_AGENT_TEMPLATE.format(mailto=mailto),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    })
    return s


def fetch(session: requests.Session, url: str, timeout: Tuple[int, int], retries: int, delay: float) -> Tuple[int, str, str, str]:
    last_err = ""
    for attempt in range(1, retries + 1):
        try:
            r = session.get(url, timeout=timeout, allow_redirects=True)
            return r.status_code, r.url, r.text or "", ""
        except Exception as e:
            last_err = f"{type(e).__name__}: {e}"
            if attempt < retries:
                time.sleep(delay * attempt)
    return 0, url, "", last_err


def extract_meta_inventory(soup: BeautifulSoup) -> Tuple[Counter, Dict[str, List[str]]]:
    names = Counter()
    candidate_values: Dict[str, List[str]] = defaultdict(list)
    for tag in soup.find_all("meta"):
        name = norm(tag.get("name") or tag.get("property") or tag.get("itemprop") or "")
        content = norm(tag.get("content") or "")
        if not name:
            continue
        names[name] += 1
        lname = name.lower()
        if any(k.lower() == lname for k in META_KEY_CANDIDATES) or re.search("|".join(KEY_PATTERNS), lname, re.I):
            if content:
                candidate_values[name].append(content[:1000])
    return names, dict(candidate_values)


def extract_jsonld_inventory(soup: BeautifulSoup) -> Tuple[int, List[str], List[str]]:
    n = 0
    key_paths = []
    snippets = []

    def walk(obj: Any, path: str = "$"):
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_path = f"{path}.{k}"
                if re.search("|".join(KEY_PATTERNS), str(k), re.I) or k in ("keywords", "about", "genre"):
                    key_paths.append(new_path)
                    snippets.append(norm(json.dumps(v, ensure_ascii=False))[:1000])
                walk(v, new_path)
        elif isinstance(obj, list):
            for i, v in enumerate(obj[:50]):
                walk(v, f"{path}[{i}]")

    for script in soup.find_all("script", attrs={"type": re.compile(r"ld\+json", re.I)}):
        raw = script.string or script.get_text() or ""
        if not raw.strip():
            continue
        n += 1
        try:
            data = json.loads(raw)
        except Exception:
            # Some sites put multiple JSON-LD blocks in one script or invalid trailing data.
            snippets.append(norm(raw)[:500])
            continue
        walk(data)
    return n, sorted(set(key_paths)), snippets[:20]


def extract_keyword_snippets(html: str, soup: BeautifulSoup) -> List[str]:
    snippets = []

    # Visible text snippets around keyword-like strings.
    text = soup.get_text(" ")
    text = norm(text)
    for m in re.finditer("|".join(KEY_PATTERNS), text, flags=re.I):
        start = max(0, m.start() - 180)
        end = min(len(text), m.end() + 400)
        snippets.append(text[start:end])

    # Raw HTML snippets catch hidden JSON/app state names.
    for m in re.finditer("|".join(KEY_PATTERNS), html, flags=re.I):
        start = max(0, m.start() - 180)
        end = min(len(html), m.end() + 600)
        sn = re.sub(r"\s+", " ", html[start:end])
        snippets.append(sn)

    # Deduplicate, cap.
    out = []
    seen = set()
    for s in snippets:
        s = norm(s)
        if s and s not in seen:
            out.append(s[:1200])
            seen.add(s)
        if len(out) >= 30:
            break
    return out


def class_id_inventory(soup: BeautifulSoup) -> Counter:
    inv = Counter()
    for tag in soup.find_all(True):
        for attr in ("class", "id", "data-testid", "data-test", "aria-label"):
            val = tag.get(attr)
            if not val:
                continue
            vals = val if isinstance(val, list) else [val]
            for v in vals:
                v = norm(v)
                if re.search("|".join(KEY_PATTERNS), v, re.I):
                    inv[f"{attr}:{v}"] += 1
    return inv


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw-dir", required=True, type=Path)
    ap.add_argument("--outdir", required=True, type=Path)
    ap.add_argument("--samples-per-journal", type=int, default=8)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--mailto", required=True)
    ap.add_argument("--delay", type=float, default=0.8)
    ap.add_argument("--retries", type=int, default=2)
    ap.add_argument("--save-html", action="store_true", help="Save sampled full HTML pages for local debugging. Use cautiously.")
    args = ap.parse_args(argv)

    args.outdir.mkdir(parents=True, exist_ok=True)
    html_dir = args.outdir / "html_samples"
    if args.save_html:
        html_dir.mkdir(exist_ok=True)

    articles = read_articles(args.raw_dir)
    samples = sample_articles(articles, args.samples_per_journal, args.seed)

    if samples.empty:
        raise RuntimeError("No samples selected.")

    session = make_session(args.mailto)
    sample_rows = []
    snippet_rows = []
    summary_counter = Counter()

    for i, row in samples.iterrows():
        url = norm(row.get("article_url"))
        doi = norm(row.get("doi"))
        article_id = norm(row.get("article_id"))
        journal_key = norm(row.get("journal_key"))
        title = norm(row.get("title"))
        year = norm(row.get("year"))

        if not url and doi:
            url = "https://doi.org/" + doi

        print(f"[{i+1}/{len(samples)}] {journal_key} {year} {doi or article_id}", flush=True)
        status, final_url, html, error = fetch(session, url, timeout=(10, 30), retries=args.retries, delay=args.delay)
        time.sleep(args.delay)

        soup = BeautifulSoup(html, "lxml") if html else BeautifulSoup("", "lxml")
        meta_names, meta_candidates = extract_meta_inventory(soup)
        n_jsonld, jsonld_paths, jsonld_snippets = extract_jsonld_inventory(soup)
        snippets = extract_keyword_snippets(html, soup)
        class_ids = class_id_inventory(soup)

        has_candidate = bool(meta_candidates or jsonld_paths or snippets or class_ids)

        if status:
            summary_counter[f"http_{status}"] += 1
        if error:
            summary_counter["fetch_error"] += 1
        if has_candidate:
            summary_counter["keyword_candidate_signal"] += 1
        else:
            summary_counter["no_keyword_signal"] += 1

        if args.save_html and html:
            safe = re.sub(r"[^a-zA-Z0-9._-]+", "_", doi or article_id or str(i))[:120]
            (html_dir / f"{journal_key}_{safe}.html").write_text(html, encoding="utf-8", errors="ignore")

        sample_rows.append({
            "journal_key": journal_key,
            "year": year,
            "doi": doi,
            "article_id": article_id,
            "title": title,
            "source_article_url": url,
            "http_status": status,
            "final_url": final_url,
            "html_length": len(html),
            "fetch_error": error,
            "has_keyword_candidate_signal": has_candidate,
            "meta_names_top": safe_join([f"{k}:{v}" for k, v in meta_names.most_common(30)]),
            "meta_keyword_candidate_fields": safe_join(meta_candidates.keys()),
            "meta_keyword_candidate_values": safe_join([f"{k}={safe_join(v, '; ')}" for k, v in meta_candidates.items()], max_len=5000),
            "n_jsonld_blocks": n_jsonld,
            "jsonld_keyword_paths": safe_join(jsonld_paths),
            "jsonld_keyword_snippets": safe_join(jsonld_snippets, max_len=5000),
            "keyword_like_class_id_inventory": safe_join([f"{k}:{v}" for k, v in class_ids.most_common(50)]),
            "n_keyword_like_snippets": len(snippets),
        })

        for j, snip in enumerate(snippets, start=1):
            snippet_rows.append({
                "journal_key": journal_key,
                "year": year,
                "doi": doi,
                "article_id": article_id,
                "snippet_order": j,
                "snippet": snip,
            })

    pd.DataFrame(sample_rows).to_csv(args.outdir / "keyword_source_audit_samples.csv", index=False)
    pd.DataFrame(snippet_rows).to_csv(args.outdir / "keyword_source_audit_snippets.csv", index=False)

    by_journal = pd.DataFrame(sample_rows).groupby("journal_key").agg(
        n_sampled=("article_id", "count"),
        n_http_200=("http_status", lambda x: int((x == 200).sum())),
        n_with_candidate_signal=("has_keyword_candidate_signal", lambda x: int(x.sum())),
        median_html_length=("html_length", "median"),
    ).reset_index()
    by_journal["candidate_signal_pct"] = (by_journal["n_with_candidate_signal"] / by_journal["n_sampled"] * 100).round(2)
    by_journal.to_csv(args.outdir / "keyword_source_audit_summary_by_journal.csv", index=False)

    with open(args.outdir / "keyword_source_audit_summary.json", "w", encoding="utf-8") as f:
        json.dump({
            "raw_dir": str(args.raw_dir),
            "n_articles_available": int(len(articles)),
            "n_articles_sampled": int(len(samples)),
            "summary_counts": dict(summary_counter),
            "outputs": [
                "keyword_source_audit_samples.csv",
                "keyword_source_audit_snippets.csv",
                "keyword_source_audit_summary_by_journal.csv",
            ],
        }, f, ensure_ascii=False, indent=2)

    print("\nSummary:")
    print(by_journal.to_string(index=False))
    print(f"\nWrote: {args.outdir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
