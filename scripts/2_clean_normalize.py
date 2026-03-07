import os
import re
import pandas as pd
from rapidfuzz import fuzz

IN = "output/keywords_long.csv"
OUT = "output/keywords_long_normalized.csv"

# ręczne mapowania (tu możesz dopisywać)
MANUAL_MAP = {
    # "internet": "Internet",
    # "zaburzenia osobowości typu borderline": "borderline",
}

def normalize_basic(s: str) -> str:
    s = s.strip()
    s = re.sub(r"\s+", " ", s)
    return s

def build_fuzzy_map(values: list[str], threshold: int = 94) -> dict[str, str]:
    """
    Zwraca mapę {wariant -> reprezentant}.
    Prosta wersja: idziemy po wartościach w kolejności częstotliwości
    i podpinamy podobne do wcześniejszego reprezentanta.
    """
    rep = []
    mapping = {}
    for v in values:
        if v in mapping:
            continue
        best = None
        for r in rep:
            if fuzz.ratio(v, r) >= threshold:
                best = r
                break
        if best is None:
            rep.append(v)
            mapping[v] = v
        else:
            mapping[v] = best
    return mapping

def main():
    os.makedirs("output", exist_ok=True)
    df = pd.read_csv(IN)

    df["keyword_raw"] = df["keyword"].astype(str)
    df["keyword_norm"] = df["keyword_raw"].map(normalize_basic)

    # manual map (ma pierwszeństwo)
    df["keyword_norm"] = df["keyword_norm"].apply(lambda x: MANUAL_MAP.get(x, x))

    # fuzzy map dla reszty
    freq = df["keyword_norm"].value_counts()
    ordered = list(freq.index)

    fuzzy_map = build_fuzzy_map(ordered, threshold=95)
    df["keyword_final"] = df["keyword_norm"].map(lambda x: fuzzy_map.get(x, x))

    df.to_csv(OUT, index=False, encoding="utf-8")
    print("Zapisano:", OUT)
    print("Unikalne keywords (raw/norm/final):",
          df["keyword_raw"].nunique(), df["keyword_norm"].nunique(), df["keyword_final"].nunique())

if __name__ == "__main__":
    main()
