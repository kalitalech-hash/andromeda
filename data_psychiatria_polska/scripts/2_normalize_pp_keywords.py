# 2_normalize_pp_keywords.py
# -*- coding: utf-8 -*-

import os
import re
import unicodedata
import pandas as pd

IN_PATH = os.path.join("output", "pp_keywords_long.csv")
OUT_PATH = os.path.join("output", "pp_keywords_long_normalized.csv")

def strip_accents(s: str) -> str:
    # usuń diakrytyki (opcjonalnie) – tu zostawiamy POLSKIE znaki,
    # ale normalizujemy unicode (NFKC), bo bywają „dziwne” cudzysłowy itd.
    return unicodedata.normalize("NFKC", s)

def normalize_keyword(s: str) -> str:
    if s is None:
        return ""
    s = strip_accents(str(s)).strip().lower()

    # ujednolicenie cudzysłowów i myślników
    s = s.replace("„", "\"").replace("”", "\"").replace("’", "'").replace("–", "-").replace("−", "-")

    # usuń zbędne spacje
    s = re.sub(r"\s+", " ", s)

    # usuń końcowe kropki/średniki itp.
    s = s.strip(" .;,:/\\|")

    return s

def main() -> None:
    df = pd.read_csv(IN_PATH)
    df["keyword_norm"] = df["keyword_raw"].astype(str).map(normalize_keyword)

    # usuń puste
    df = df[df["keyword_norm"].str.len() > 0].copy()

    df.to_csv(OUT_PATH, index=False, encoding="utf-8")
    print(f"[DONE] Wrote {OUT_PATH} rows={len(df)}")

if __name__ == "__main__":
    main()