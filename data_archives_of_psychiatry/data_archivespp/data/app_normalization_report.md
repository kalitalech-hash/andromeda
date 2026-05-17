# Etap 2 — normalizacja techniczna keywordów APP

## Wejście

- Plik artykułów: `app_articles_dedup_2005_2025.csv`
- Plik keyword-long: `app_keywords_long_dedup_2005_2025.csv`
- Zakres: 2005–2025
- Artykuły wejściowe: 730
- Rekordy keyword-long wejściowe: 2737
- Unikalne surowe warianty keywordów: 1743

## Zakres normalizacji

Zastosowano konserwatywną normalizację techniczną:

1. normalizacja Unicode NFKC,
2. usunięcie nadmiarowych spacji i znaków niewidocznych,
3. obniżenie rejestru liter,
4. ujednolicenie cudzysłowów, apostrofów i myślników,
5. ujednolicenie spacji wokół ukośników i dywizów,
6. zamiana `&` na `and`,
7. usunięcie końcowej interpunkcji technicznej,
8. nadanie stabilnego identyfikatora `keyword_norm_id`.

Nie wykonywano jeszcze scalania semantycznego, lematyzacji ani tłumaczenia na język polski.

## Wynik

- Rekordy keyword-long po normalizacji: 2737
- Unikalne formy znormalizowane: 1699
- Liczba wariantów połączonych przez normalizację techniczną: 44
- Formy znormalizowane mające więcej niż jeden wariant surowy: 40
- Puste keywordy po normalizacji: 0
- Artykuły bez keywordów po normalizacji: 16
- Pary kandydackie do ręcznego przeglądu semantycznego: 300

## Decyzja audytowa

Warstwą wyjściową etapu 2 jest `app_keywords_long_normalized.csv`. Kolumna `keyword_raw` pozostaje nienaruszona, a kolumna `keyword_norm` zawiera wyłącznie efekt normalizacji technicznej. Dalsze scalanie, np. `depression` z `depressive disorder`, `schizophrenia` ze złożonymi wariantami klinicznymi albo wariantów pisowni brytyjskiej i amerykańskiej, powinno zostać wykonane w osobnym etapie semantycznym i zapisane w logu decyzji.

## Pliki wynikowe

- `app_keywords_long_normalized.csv`
- `app_keyword_normalization_map.csv`
- `app_keyword_top30_normalized.csv`
- `app_keyword_normalization_collisions.csv`
- `app_keyword_candidate_merges_for_review.csv`
- `app_keyword_suspicious_after_normalization.csv`
- `app_articles_without_keywords_after_normalization.csv`
- `app_normalization_summary.json`
