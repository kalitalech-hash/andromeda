#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
01_clean_keywords_pp.py

Ramowy skrypt przygotowania danych dla korpusu "Psychiatria Polska".

Wejście:
    pp_keywords_cleaned.csv
        kolumny oczekiwane:
        - url
        - year
        - volume
        - issue
        - doi
        - keyword_raw
        - keyword_norm

Wyjście:
    pp_keywords_final_clean_generated.csv
    pp_keyword_transform_log.csv
"""

from __future__ import annotations

import argparse
import re
import unicodedata
from typing import Dict, Tuple, List

import pandas as pd


DROP_TERMS = {
    "",
    "brak",
    "bez slow kluczowych",
    "bez słów kluczowych",
    "keywords",
    "keyword",
    "slowa kluczowe",
    "słowa kluczowe",
    "od redakcji",
    "editorial",
}

EXACT_TRANSLATIONS: Dict[str, str] = {
    "child and adolescent psychiatry": "psychiatria dzieci i młodzieży",
    "adolescent psychiatry": "psychiatria dzieci i młodzieży",
    "child psychiatry": "psychiatria dzieci i młodzieży",
    "neuropsychology": "neuropsychologia",
    "neuropsychiatry": "neuropsychiatria",
    "pharmacotherapy": "farmakoterapia",
    "psychotherapy": "psychoterapia",
    "schizophrenia": "schizofrenia",
    "depression": "depresja",
    "suicide": "samobójstwo",
    "suicidality": "samobójstwo",
    "substance use disorders": "uzależnienia",
    "addiction": "uzależnienia",
    "ptsd": "ptsd",
    "trauma": "trauma",
    "autism": "autyzm",
    "adhd": "adhd",
    "psychometrics": "psychometria",
    "genetics": "genetyka",
    "neurobiology": "neurobiologia",
    "eating disorders": "zaburzenia odżywiania",
    "mental health": "zdrowie psychiczne",
    "speech therapy": "logopedia",
    "law and psychiatry": "prawo i psychiatria",
    "youth": "młodzież",
    "adolescents": "młodzież",
    "coping": "radzenie sobie ze stresem",
    "stress coping": "radzenie sobie ze stresem",
}

REGEX_RULES: List[Tuple[str, str]] = [
    (r"\b(child|children|adolescent|adolescence|youth).*(psychiatry|mental health)\b", "psychiatria dzieci i młodzieży"),
    (r"\bpsychiatria dzieci i mlodziezy\b", "psychiatria dzieci i młodzieży"),
    (r"\bneuropsycholog(y|ia|ical)\b", "neuropsychologia"),
    (r"\bneuropsychiatr(y|ia)\b", "neuropsychiatria"),
    (r"\bpharmacotherap(y|ia)\b", "farmakoterapia"),
    (r"\bpsychotherap(y|ia)\b", "psychoterapia"),
    (r"\bschizophreni(a|c)\b", "schizofrenia"),
    (r"\bdepress(ion|ive|ja)\b", "depresja"),
    (r"\bsuicid(e|al|ality)\b", "samobójstwo"),
    (r"\bsubstance use\b|\baddiction\b|\buzaleznieni", "uzależnienia"),
    (r"\bautis(m|tic)\b", "autyzm"),
    (r"\badhd\b|\battention deficit", "adhd"),
    (r"\bptsd\b|\bpost[- ]traumatic", "ptsd"),
    (r"\btraum(a|atic)\b", "trauma"),
    (r"\bpsychometr", "psychometria"),
    (r"\bneurobiolog", "neurobiologia"),
    (r"\bgenetic", "genetyka"),
    (r"\beating disorder", "zaburzenia odżywiania"),
    (r"\bbody image\b", "zaburzenia odżywiania"),
    (r"\bspeech therap", "logopedia"),
    (r"\bmental health\b", "zdrowie psychiczne"),
    (r"\blaw and psychiatry\b|\bforensic\b", "prawo i psychiatria"),
    (r"\bcoping\b", "radzenie sobie ze stresem"),
]

EXACT_SEMANTIC_MAP: Dict[str, str] = {
    "cbt": "terapia poznawczo-behawioralna",
    "cognitive behavioral therapy": "terapia poznawczo-behawioralna",
    "terapia poznawczo behawioralna": "terapia poznawczo-behawioralna",
    "neuropsychologia i neuropsychiatria": "neuropsychologia",
    "psychiatria dziecieca": "psychiatria dzieci i młodzieży",
    "psychiatria dzieci i mlodziezy": "psychiatria dzieci i młodzieży",
    "dzieci i mlodziez": "młodzież",
    "mniejszosci seksualne": "mniejszości seksualne",
    "plci kulturowa": "płeć kulturowa",
    "plciowosc": "seksualność",
    "seksualnosc": "seksualność",
}


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


def translate_or_map_exact(text: str):
    if text in EXACT_TRANSLATIONS:
        return EXACT_TRANSLATIONS[text], "exact_translation"
    if text in EXACT_SEMANTIC_MAP:
        return EXACT_SEMANTIC_MAP[text], "exact_semantic_map"
    return text, "identity"


def apply_regex_rules(text: str):
    ascii_text = strip_accents(text)
    for pattern, replacement in REGEX_RULES:
        if re.search(pattern, ascii_text, flags=re.IGNORECASE):
            return replacement, f"regex:{pattern}"
    return text, "no_regex_match"


def clean_one_keyword(text: str):
    steps = []

    norm = normalize_keyword(text)
    steps.append(f"normalize:{norm}")

    if norm in DROP_TERMS:
        return "", steps + ["drop_term"]

    mapped, step1 = translate_or_map_exact(norm)
    steps.append(step1)

    mapped2, step2 = apply_regex_rules(mapped)
    steps.append(step2)

    final = normalize_keyword(mapped2)
    final = final.replace("mlodziezy", "młodzieży").replace("mlodziez", "młodzież")
    final = final.replace("uzaleznienia", "uzależnienia")
    final = final.strip()

    if final in DROP_TERMS:
        return "", steps + ["drop_after_mapping"]

    return final, steps


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="pp_keywords_cleaned.csv")
    parser.add_argument("--output", default="pp_keywords_final_clean_generated.csv")
    parser.add_argument("--log", default="pp_keyword_transform_log.csv")
    args = parser.parse_args()

    df = pd.read_csv(args.input)

    required = {"url", "year", "volume", "issue", "doi"}
    if not required.issubset(df.columns):
        raise ValueError(f"Brak wymaganych kolumn: {required - set(df.columns)}")

    source_col = "keyword_norm" if "keyword_norm" in df.columns else "keyword_raw"
    if source_col not in df.columns:
        raise ValueError("Nie znaleziono kolumny keyword_norm ani keyword_raw.")

    work = df.copy()
    work["keyword_source"] = work[source_col].fillna("").astype(str)

    finals = []
    logs = []

    for idx, row in work.iterrows():
        final_kw, steps = clean_one_keyword(row["keyword_source"])
        finals.append(final_kw)
        logs.append({
            "row_id": idx,
            "url": row["url"],
            "doi": row["doi"],
            "keyword_raw": row.get("keyword_raw", ""),
            "keyword_norm": row.get("keyword_norm", ""),
            "keyword_final_polish": final_kw,
            "transform_steps": " | ".join(steps),
        })

    work["keyword_final_polish"] = finals
    log_df = pd.DataFrame(logs)

    out = work[work["keyword_final_polish"].astype(str).str.strip() != ""].copy()
    out["year"] = pd.to_numeric(out["year"], errors="coerce")
    out = out.dropna(subset=["year"])
    out["year"] = out["year"].astype(int)

    out = out[["url", "year", "volume", "issue", "doi", "keyword_final_polish"]]
    out = out.drop_duplicates(subset=["url", "keyword_final_polish"]).reset_index(drop=True)

    out.to_csv(args.output, index=False, encoding="utf-8-sig")
    log_df.to_csv(args.log, index=False, encoding="utf-8-sig")

    print(f"Zapisano: {args.output}")
    print(f"Zapisano log: {args.log}")
    print(f"Liczba rekordów finalnych: {len(out)}")
    print(f"Liczba unikalnych keywordów finalnych: {out['keyword_final_polish'].nunique()}")
    print(f"Liczba artykułów: {out['url'].nunique()}")


if __name__ == "__main__":
    main()