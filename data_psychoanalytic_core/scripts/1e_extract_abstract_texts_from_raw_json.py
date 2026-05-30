#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
1e_extract_abstract_texts_from_raw_json.py

Andromeda Nowicka v0.4/v0.5-pre
Recover abstract text from already harvested PEP raw JSON files.

Purpose
-------
The global ART-only table currently contains `has_abstract` but not actual
abstract text. This script attempts to recover abstract text from local raw JSON
responses saved during full harvest:

    data_psychoanalytic_core/data/raw_pep_metadata/<journal>/<year>/*.json

It does NOT call PEP-Web and does NOT download anything.

Outputs
-------
- data/qa/global/psychoanalytic_core_abstract_texts_extracted.csv
- data/qa/global/psychoanalytic_core_articles_ART_only_with_abstracts.csv
- data/qa/global/psychoanalytic_core_abstract_extraction_field_candidates.csv
- data/qa/global/psychoanalytic_core_abstract_extraction_samples.csv
- data/qa/global/psychoanalytic_core_abstract_extraction_summary.json

Run
---
Put this file in:

    data_psychoanalytic_core/scripts/

Run:

    cd data_psychoanalytic_core/scripts
    python 1e_extract_abstract_texts_from_raw_json.py

Notes
-----
This is deliberately diagnostic and conservative. It searches recursively for
article-like records and abstract-like fields. It preserves extraction source
paths so that parser decisions can be audited.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import pandas as pd


SCRIPT_VERSION = "v0.1.0"

JOURNALS = [
    "ijpa",
    "japa",
    "psychoanalytic_dialogues",
    "psychoanalytic_psychology",
    "psychoanalytic_psychotherapy",
]

ABSTRACT_KEY_HINTS = [
    "abstract",
    "abs",
    "summary",
    "synopsis",
]

ARTICLE_ID_KEYS = [
    "article_id",
    "document_id",
    "documentID",
    "documentId",
    "art_id",
    "artID",
    "artId",
    "id",
    "pepCode",
    "PEPCode",
    "pep_code",
]

TITLE_KEYS = [
    "title",
    "articleTitle",
    "article_title",
    "art_title",
]

YEAR_KEYS = [
    "year",
    "publicationYear",
    "pubYear",
    "year_record",
]


def utc_now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def get_paths() -> Dict[str, Path]:
    scripts_dir = Path(__file__).resolve().parent
    project_root = scripts_dir.parent
    return {
        "scripts_dir": scripts_dir,
        "project_root": project_root,
        "raw_root": project_root / "data" / "raw_pep_metadata",
        "global_root": project_root / "data" / "qa" / "global",
        "summaries": project_root / "data" / "qa" / "summaries",
    }


def clean_html_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False)
    text = str(value)
    if not text:
        return ""

    text = html.unescape(text)

    # Remove obvious keyword blocks if embedded in abstract HTML.
    text = re.sub(
        r"<div[^>]+class=[\"'][^\"']*artkwds[^\"']*[\"'][^>]*>.*?</div>",
        " ",
        text,
        flags=re.I | re.S,
    )

    # Remove scripts/styles if any.
    text = re.sub(r"<script\b[^>]*>.*?</script>", " ", text, flags=re.I | re.S)
    text = re.sub(r"<style\b[^>]*>.*?</style>", " ", text, flags=re.I | re.S)

    # Replace common block separators before stripping tags.
    text = re.sub(r"</(p|div|br|li|section|abstract)>", " ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)

    # Strip recurring PEP/copyright noise if it leaks in.
    text = re.sub(r"Copyrighted Material\..*$", " ", text, flags=re.I | re.S)
    text = re.sub(r"For use only by .*?PEP terms.*$", " ", text, flags=re.I | re.S)

    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_plausible_abstract(text: str) -> bool:
    if not text:
        return False
    t = text.strip()
    low = t.lower()

    # Avoid boolean flags and labels.
    if low in {"true", "false", "yes", "no", "0", "1", "none", "null"}:
        return False

    # Abstracts can be short, but most real ones are at least sentence-like.
    if len(t) < 40:
        return False

    # Avoid raw JSON/XML blobs being mistaken as abstract.
    if t.startswith("{") and len(t) > 40:
        return False

    # A plausible abstract should contain spaces and at least one vowel-rich word.
    if " " not in t:
        return False

    return True


def as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(as_text(x) for x in value if as_text(x))
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).strip()


def first_present(record: Dict[str, Any], keys: Iterable[str]) -> str:
    lower = {k.lower(): k for k in record.keys()}
    for key in keys:
        if key in record and record[key] not in (None, "", []):
            return as_text(record[key])
        real = lower.get(key.lower())
        if real and record[real] not in (None, "", []):
            return as_text(record[real])
    return ""


def normalized_article_id(value: str) -> str:
    return str(value or "").strip()


def looks_like_article_record(d: Dict[str, Any]) -> bool:
    keys_norm = {k.lower() for k in d.keys()}
    has_id = any(k.lower() in keys_norm for k in ARTICLE_ID_KEYS)
    has_title = any(k.lower() in keys_norm for k in TITLE_KEYS)
    has_year = any(k.lower() in keys_norm for k in YEAR_KEYS)
    has_pep_like = any("art" in k.lower() and "id" in k.lower() for k in d.keys())
    return has_id or (has_title and has_year) or has_pep_like


def iter_records(obj: Any, path: str = "$") -> Iterable[Tuple[str, Dict[str, Any]]]:
    if isinstance(obj, dict):
        if looks_like_article_record(obj):
            yield path, obj
        for k, v in obj.items():
            yield from iter_records(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            yield from iter_records(item, f"{path}[{i}]")


def find_abstract_candidates(record: Dict[str, Any], base_path: str) -> List[Dict[str, Any]]:
    candidates = []

    def walk(obj: Any, path: str) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                k_low = str(k).lower()
                child_path = f"{path}.{k}"
                if any(h in k_low for h in ABSTRACT_KEY_HINTS):
                    cleaned = clean_html_text(v)
                    candidates.append({
                        "field_path": child_path,
                        "field_name": str(k),
                        "raw_type": type(v).__name__,
                        "text": cleaned,
                        "text_length": len(cleaned),
                        "plausible": is_plausible_abstract(cleaned),
                    })
                walk(v, child_path)
        elif isinstance(obj, list):
            for i, item in enumerate(obj):
                walk(item, f"{path}[{i}]")

    walk(record, base_path)
    return candidates


def pick_best_abstract(candidates: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    plausible = [c for c in candidates if c.get("plausible")]
    if not plausible:
        return None

    def score(c: Dict[str, Any]) -> Tuple[int, int]:
        path = str(c.get("field_path", "")).lower()
        name = str(c.get("field_name", "")).lower()
        text_len = int(c.get("text_length") or 0)

        s = 0
        if name in {"abstract", "abstracttext", "abstract_text"}:
            s += 50
        if "abstract" in name:
            s += 30
        if "html" in name:
            s += 5
        if "has_abstract" in name or name.startswith("has"):
            s -= 100
        if "responseinfo" in path:
            s -= 100
        return (s, text_len)

    plausible.sort(key=score, reverse=True)
    return plausible[0]


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def list_raw_json_files(raw_root: Path, journals: List[str]) -> List[Path]:
    files = []
    for journal in journals:
        d = raw_root / journal
        if not d.exists():
            continue
        files.extend(sorted(d.rglob("*.json")))
    return sorted(files)


def read_csv_safe(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    except UnicodeDecodeError:
        return pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8")


def choose_col(df: pd.DataFrame, candidates: Iterable[str]) -> Optional[str]:
    lower = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c in df.columns:
            return c
        real = lower.get(c.lower())
        if real:
            return real
    return None


def extract_all(raw_files: List[Path], project_root: Path) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Any]]:
    rows = []
    candidate_rows = []
    errors = []

    for idx, path in enumerate(raw_files, start=1):
        try:
            payload = read_json(path)
        except Exception as exc:
            errors.append({"path": str(path), "error": repr(exc)})
            continue

        # Infer journal/year from path if possible.
        parts = path.parts
        journal_guess = ""
        year_guess = ""
        for j in JOURNALS:
            if j in parts:
                journal_guess = j
                try:
                    pos = parts.index(j)
                    if pos + 1 < len(parts) and re.fullmatch(r"\d{4}", parts[pos + 1]):
                        year_guess = parts[pos + 1]
                except Exception:
                    pass

        for rec_path, record in iter_records(payload):
            article_id = normalized_article_id(first_present(record, ARTICLE_ID_KEYS))
            title = clean_html_text(first_present(record, TITLE_KEYS))
            year = first_present(record, YEAR_KEYS) or year_guess

            candidates = find_abstract_candidates(record, rec_path)
            for c in candidates:
                candidate_rows.append({
                    "raw_json_file": str(path.relative_to(project_root)) if path.is_relative_to(project_root) else str(path),
                    "journal_key_guess": journal_guess,
                    "year_guess": year_guess,
                    "record_path": rec_path,
                    "article_id": article_id,
                    "title": title[:300],
                    "field_path": c["field_path"],
                    "field_name": c["field_name"],
                    "raw_type": c["raw_type"],
                    "text_length": c["text_length"],
                    "plausible": c["plausible"],
                    "text_preview": c["text"][:500],
                })

            best = pick_best_abstract(candidates)
            if best is None:
                continue

            rows.append({
                "article_id": article_id,
                "journal_key_guess": journal_guess,
                "year_guess": year_guess,
                "year_record": year,
                "title_from_raw": title,
                "abstract_text": best["text"],
                "abstract_text_length": len(best["text"]),
                "abstract_extraction_field_path": best["field_path"],
                "abstract_extraction_field_name": best["field_name"],
                "raw_json_file": str(path.relative_to(project_root)) if path.is_relative_to(project_root) else str(path),
                "record_path": rec_path,
            })

    extracted = pd.DataFrame(rows).fillna("")
    candidates_df = pd.DataFrame(candidate_rows).fillna("")

    # Deduplicate by article_id, preferring longest abstract.
    if not extracted.empty and "article_id" in extracted.columns:
        extracted["_len"] = pd.to_numeric(extracted["abstract_text_length"], errors="coerce").fillna(0)
        extracted = extracted.sort_values(["article_id", "_len"], ascending=[True, False])
        extracted = extracted.drop_duplicates(subset=["article_id"], keep="first")
        extracted = extracted.drop(columns=["_len"])

    stats = {
        "raw_json_files_seen": len(raw_files),
        "raw_json_errors": len(errors),
        "errors": errors[:20],
        "extracted_abstract_rows": int(len(extracted)),
        "candidate_field_rows": int(len(candidates_df)),
    }
    return extracted, candidates_df, stats


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--articles-art",
        default="../data/qa/global/psychoanalytic_core_articles_ART_only.csv",
        help="Global ART-only table to enrich.",
    )
    parser.add_argument(
        "--raw-root",
        default="../data/raw_pep_metadata",
        help="Root directory with raw PEP JSON files.",
    )
    parser.add_argument(
        "--journals",
        default="all",
        help="Comma-separated journal keys or all.",
    )
    parser.add_argument(
        "--out-dir",
        default="../data/qa/global",
    )
    args = parser.parse_args()

    paths = get_paths()
    project_root = paths["project_root"]

    articles_path = Path(args.articles_art)
    if not articles_path.is_absolute():
        articles_path = (paths["scripts_dir"] / articles_path).resolve()

    raw_root = Path(args.raw_root)
    if not raw_root.is_absolute():
        raw_root = (paths["scripts_dir"] / raw_root).resolve()

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = (paths["scripts_dir"] / out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    journals = JOURNALS if args.journals == "all" else [x.strip() for x in args.journals.split(",") if x.strip()]

    if not articles_path.exists():
        raise SystemExit(f"ERROR: ART-only table not found: {articles_path}")
    if not raw_root.exists():
        raise SystemExit(f"ERROR: raw root not found: {raw_root}")

    raw_files = list_raw_json_files(raw_root, journals)
    extracted, candidates_df, stats = extract_all(raw_files, project_root)

    extracted_path = out_dir / "psychoanalytic_core_abstract_texts_extracted.csv"
    candidates_path = out_dir / "psychoanalytic_core_abstract_extraction_field_candidates.csv"
    samples_path = out_dir / "psychoanalytic_core_abstract_extraction_samples.csv"
    enriched_path = out_dir / "psychoanalytic_core_articles_ART_only_with_abstracts.csv"
    summary_path = out_dir / "psychoanalytic_core_abstract_extraction_summary.json"

    extracted.to_csv(extracted_path, index=False, encoding="utf-8-sig")
    candidates_df.to_csv(candidates_path, index=False, encoding="utf-8-sig")

    if not extracted.empty:
        samples = extracted.sort_values("abstract_text_length", ascending=False).head(50).copy()
    else:
        samples = pd.DataFrame()
    samples.to_csv(samples_path, index=False, encoding="utf-8-sig")

    articles = read_csv_safe(articles_path)
    article_id_col = choose_col(articles, ["article_id", "document_id", "pep_document_id", "id"])

    if article_id_col is None:
        raise SystemExit("ERROR: Could not identify article_id column in ART-only table.")

    # Remove any stale abstract_text columns before merge if they are empty/flag-like.
    merge_cols = [
        "article_id",
        "abstract_text",
        "abstract_text_length",
        "abstract_extraction_field_path",
        "abstract_extraction_field_name",
        "raw_json_file",
        "record_path",
    ]
    if extracted.empty:
        enriched = articles.copy()
        enriched["abstract_text"] = ""
        enriched["abstract_text_length"] = ""
        enriched["abstract_extraction_status"] = "not_extracted"
    else:
        enriched = articles.merge(
            extracted[merge_cols],
            left_on=article_id_col,
            right_on="article_id",
            how="left",
            suffixes=("", "_extracted"),
        )
        if article_id_col != "article_id" and "article_id_extracted" in enriched.columns:
            pass
        enriched["abstract_text"] = enriched["abstract_text"].fillna("")
        enriched["abstract_text_length"] = enriched["abstract_text_length"].fillna("")
        enriched["abstract_extraction_status"] = enriched["abstract_text"].astype(str).str.strip().ne("").map(
            {True: "extracted", False: "missing"}
        )

    enriched.to_csv(enriched_path, index=False, encoding="utf-8-sig")

    n_articles = len(articles)
    n_enriched = int(enriched["abstract_text"].fillna("").astype(str).str.strip().ne("").sum()) if "abstract_text" in enriched.columns else 0

    by_journal = []
    if "journal_key" in enriched.columns:
        tmp = enriched.copy()
        tmp["_has_abstract_text"] = tmp["abstract_text"].fillna("").astype(str).str.strip().ne("")
        by_journal = (
            tmp.groupby("journal_key", dropna=False)
            .agg(n_records=("_has_abstract_text", "size"), n_with_abstract_text=("_has_abstract_text", "sum"))
            .reset_index()
        )
        by_journal["pct_with_abstract_text"] = (by_journal["n_with_abstract_text"] / by_journal["n_records"] * 100).round(2)
        by_journal = by_journal.to_dict(orient="records")

    summary = {
        "script_version": SCRIPT_VERSION,
        "created_at_utc": utc_now_iso(),
        "policy": {
            "no_api_calls": True,
            "no_pdf_downloads": True,
            "source": "local raw PEP JSON files",
        },
        "inputs": {
            "articles_ART_only": str(articles_path),
            "raw_root": str(raw_root),
            "journals": journals,
        },
        "raw_json_files": stats["raw_json_files_seen"],
        "raw_json_errors": stats["raw_json_errors"],
        "candidate_field_rows": stats["candidate_field_rows"],
        "extracted_abstract_rows_unique_article_id": stats["extracted_abstract_rows"],
        "ART_only_rows": int(n_articles),
        "ART_only_rows_with_abstract_text_after_merge": n_enriched,
        "ART_only_pct_with_abstract_text_after_merge": round(n_enriched / max(n_articles, 1) * 100, 2),
        "by_journal": by_journal,
        "outputs": {
            "abstract_texts_extracted": str(extracted_path),
            "field_candidates": str(candidates_path),
            "samples": str(samples_path),
            "ART_only_with_abstracts": str(enriched_path),
            "summary_json": str(summary_path),
        },
        "errors_preview": stats["errors"],
    }

    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
