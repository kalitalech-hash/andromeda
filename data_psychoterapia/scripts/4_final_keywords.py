#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
01_prepare_long_semantic_psychoterapia.py

Ramowy skrypt przygotowania warstwy keyword-long dla korpusu czasopisma "Psychoterapia".
Skrypt zakłada, że scraping artykułów i ekstrakcja słów kluczowych zostały wykonane osobno.

WEJŚCIE
-------
Plik CSV w formacie keyword-long, np.:
- year
- issue_label
- item_type
- title
- url
- keyword

WYJŚCIE
-------
- keywords_long_polish_semantic_generated.csv
- psychoterapia_keyword_transform_log.csv

CO ROBI SKRYPT
--------------
1. normalizuje formalnie słowa kluczowe,
2. polonizuje wybrane terminy angielskie,
3. mapuje warianty ortograficzne i terminologiczne,
4. tworzy warstwę konceptualną / semantyczną,
5. zapisuje log transformacji.

UWAGA
-----
`raw_articles.csv` zawiera wyłącznie metadane artykułów i nie pozwala samodzielnie odtworzyć
warstwy keyword-long bez osobnego etapu scrapingu/ekstrakcji słów kluczowych.
"""

from __future__ import annotations

import argparse
import re
import unicodedata
from typing import Dict, List, Tuple

import pandas as pd


DROP_TERMS = {
    "",
    "keywords",
    "keyword",
    "słowa kluczowe",
    "slowa kluczowe",
    "brak",
    "none",
    "unknown",
}

EXACT_TRANSLATIONS: Dict[str, str] = {
    "psychotherapy": "psychoterapia",
    "psychodynamic psychotherapy": "psychoterapia psychodynamiczna",
    "cognitive behavioral therapy": "cbt",
    "cbt": "cbt",
    "couples therapy": "terapia par",
    "couple therapy": "terapia par",
    "borderline personality disorder": "borderline",
    "anxiety": "lęk",
    "depression": "depresja",
    "trauma": "trauma",
    "attachment": "przywiązanie",
    "therapeutic relationship": "relacja terapeutyczna",
    "supervision": "superwizja",
    "online psychotherapy": "psychoterapia online",
    "teletherapy": "psychoterapia online",
    "developmental perspective": "perspektywa rozwojowa",
    "schema therapy": "terapia schematów",
    "posttraumatic growth": "wzrost potraumatyczny",
    "case study": "studium przypadku",
    "covid-19": "covid-19",
}

EXACT_CONCEPT_MAP: Dict[str, str] = {
    "psychodynamic psychotherapy": "psychoterapia psychodynamiczna",
    "psychoterapia psychodynamiczna": "psychoterapia psychodynamiczna",
    "cognitive behavioral therapy": "cbt",
    "cbt": "cbt",
    "cognitive-behavioral therapy": "cbt",
    "terapia poznawczo behawioralna": "cbt",
    "terapia poznawczo-behawioralna": "cbt",
    "psychotherapy process": "proces psychoterapii (ogólnie)",
    "psychotherapy": "proces psychoterapii (ogólnie)",
    "psychoterapia": "proces psychoterapii (ogólnie)",
    "psychotherapy online": "psychoterapia online",
    "online psychotherapy": "psychoterapia online",
    "teletherapy": "psychoterapia online",
    "couples therapy": "terapia par",
    "couple therapy": "terapia par",
    "terapia par": "terapia par",
    "depression": "depresja",
    "depresja": "depresja",
    "anxiety": "lęk",
    "lek": "lęk",
    "lęk": "lęk",
    "borderline personality disorder": "borderline",
    "borderline": "borderline",
    "personality disorders": "zaburzenia osobowości",
    "personality disorder": "zaburzenia osobowości",
    "zaburzenia osobowosci": "zaburzenia osobowości",
    "zaburzenia osobowości": "zaburzenia osobowości",
    "developmental perspective": "perspektywa rozwojowa",
    "perspektywa rozwojowa": "perspektywa rozwojowa",
    "trauma": "trauma",
    "attachment": "przywiązanie",
    "therapeutic relationship": "relacja terapeutyczna",
    "supervision": "superwizja",
    "schema therapy": "terapia schematów",
    "posttraumatic growth": "wzrost potraumatyczny",
    "case study": "studium przypadku",
    "covid 19": "covid-19",
    "covid-19": "covid-19",
}

REGEX_RULES: List[Tuple[str, str]] = [
    (r"\bpsychodynamic", "psychoterapia psychodynamiczna"),
    (r"\bcognitive[- ]?behavior", "cbt"),
    (r"\bcbt\b", "cbt"),
    (r"\bcouple|couples", "terapia par"),
    (r"\bborderline\b", "borderline"),
    (r"\bpersonality disorder", "zaburzenia osobowości"),
    (r"\banxiety\b|\blek\b|\blekowy\b", "lęk"),
    (r"\bdepress", "depresja"),
    (r"\btrauma", "trauma"),
    (r"\battachment", "przywiązanie"),
    (r"\btherapeutic relationship", "relacja terapeutyczna"),
    (r"\bsupervision", "superwizja"),
    (r"\bonline psychotherapy\b|\bteletherap", "psychoterapia online"),
    (r"\bdevelopmental", "perspektywa rozwojowa"),
    (r"\bschema therap", "terapia schematów"),
    (r"\bposttraumatic growth", "wzrost potraumatyczny"),
    (r"\bcase stud", "studium przypadku"),
    (r"\bcovid", "covid-19"),
]


def strip_accents(text: str) -> str:
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))


def normalize_keyword(text: str) -> str:
    if pd.isna(text):
        return ""
    text = str(text).strip().lower()
    text = text.replace("/", " ")
    text = text.replace("&", " i ")
    text = re.sub(r"[_–—-]+", " ", text)
    text = re.sub(r"[^\w\sąćęłńóśźż-]", " ", text, flags=re.UNICODE)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def translate_keyword(text: str) -> Tuple[str, str]:
    if text in EXACT_TRANSLATIONS:
        return EXACT_TRANSLATIONS[text], "exact_translation"
    return text, "no_exact_translation"


def semantic_map(text: str) -> Tuple[str, str]:
    if text in EXACT_CONCEPT_MAP:
        return EXACT_CONCEPT_MAP[text], "exact_concept_map"

    ascii_text = strip_accents(text)
    for pattern, replacement in REGEX_RULES:
        if re.search(pattern, ascii_text, flags=re.IGNORECASE):
            return replacement, f"regex:{pattern}"

    return text, "identity"


def process_keyword(raw_keyword: str):
    steps = []

    keyword_raw = str(raw_keyword) if not pd.isna(raw_keyword) else ""
    keyword_norm = normalize_keyword(keyword_raw)
    steps.append(f"normalize:{keyword_norm}")

    if keyword_norm in DROP_TERMS:
        return {
            "keyword_raw": keyword_raw,
            "keyword_norm": keyword_norm,
            "keyword_final": "",
            "keyword_pl": "",
            "keyword_norm_auto": "",
            "keyword_concept_auto": "",
            "keyword_semantic_auto": "",
            "steps": steps + ["drop_term"],
        }

    keyword_pl, step1 = translate_keyword(keyword_norm)
    steps.append(step1)

    keyword_final = normalize_keyword(keyword_pl)
    keyword_concept_auto, step2 = semantic_map(keyword_final)
    steps.append(step2)

    keyword_semantic_auto = normalize_keyword(keyword_concept_auto)

    if keyword_semantic_auto in DROP_TERMS:
        keyword_semantic_auto = ""

    return {
        "keyword_raw": keyword_raw,
        "keyword_norm": keyword_norm,
        "keyword_final": keyword_final,
        "keyword_pl": keyword_pl,
        "keyword_norm_auto": keyword_final,
        "keyword_concept_auto": keyword_concept_auto,
        "keyword_semantic_auto": keyword_semantic_auto,
        "steps": steps,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="keywords_long_raw.csv")
    parser.add_argument("--output", default="keywords_long_polish_semantic_generated.csv")
    parser.add_argument("--log", default="psychoterapia_keyword_transform_log.csv")
    args = parser.parse_args()

    df = pd.read_csv(args.input)

    required = {"year", "issue_label", "item_type", "title", "url", "keyword"}
    if not required.issubset(df.columns):
        raise ValueError(f"Brak wymaganych kolumn: {required - set(df.columns)}")

    rows = []
    logs = []

    for idx, row in df.iterrows():
        res = process_keyword(row["keyword"])

        rows.append({
            "year": row["year"],
            "issue_label": row["issue_label"],
            "item_type": row["item_type"],
            "title": row["title"],
            "url": row["url"],
            "keyword": row["keyword"],
            "keyword_raw": res["keyword_raw"],
            "keyword_norm": res["keyword_norm"],
            "keyword_final": res["keyword_final"],
            "keyword_pl": res["keyword_pl"],
            "keyword_norm_auto": res["keyword_norm_auto"],
            "keyword_concept_auto": res["keyword_concept_auto"],
            "keyword_semantic_auto": res["keyword_semantic_auto"],
        })

        logs.append({
            "row_id": idx,
            "url": row["url"],
            "title": row["title"],
            "keyword_input": row["keyword"],
            "keyword_output": res["keyword_semantic_auto"],
            "transform_steps": " | ".join(res["steps"]),
        })

    out = pd.DataFrame(rows)
    out = out[out["keyword_semantic_auto"].astype(str).str.strip() != ""].copy()
    out["year"] = pd.to_numeric(out["year"], errors="coerce")
    out = out.dropna(subset=["year"])
    out["year"] = out["year"].astype(int)
    out = out.drop_duplicates(subset=["url", "keyword_semantic_auto"]).reset_index(drop=True)

    log_df = pd.DataFrame(logs)

    out.to_csv(args.output, index=False, encoding="utf-8-sig")
    log_df.to_csv(args.log, index=False, encoding="utf-8-sig")

    print(f"Zapisano: {args.output}")
    print(f"Zapisano log: {args.log}")
    print(f"Liczba rekordów finalnych: {len(out)}")
    print(f"Liczba unikalnych terminów semantycznych: {out['keyword_semantic_auto'].nunique()}")
    print(f"Liczba artykułów: {out['url'].nunique()}")


if __name__ == "__main__":
    main()