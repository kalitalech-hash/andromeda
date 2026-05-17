# QA + deduplikacja — Archives of Psychiatry and Psychotherapy

## Zakres i decyzja

Przetworzono surowe pliki z etapu scrapingu: `app_issues.csv`, `app_articles.csv`, `app_keywords_long.csv` oraz `app_scrape_log.csv`.

Docelowy zakres korpusu ustawiono jako **2005–2025**, zgodnie z parametrami pierwszego uruchomienia scrapera. Jeden rekord z roku 2026 został potraktowany jako wyciek spoza zakresu, ponieważ występował w danych mimo braku odpowiadającego mu numeru w `app_issues.csv`.

## Podsumowanie liczbowe

| Miara | Wartość |
|---|---:|
| Numery czasopisma w `app_issues.csv` | 83 |
| Surowe rekordy artykułów | 1223 |
| Unikalne `article_id` w surowych artykułach | 731 |
| Finalne artykuły po deduplikacji i ograniczeniu do 2005–2025 | 730 |
| Surowe rekordy keyword-long | 4790 |
| Finalne rekordy keyword-long po deduplikacji i ograniczeniu do 2005–2025 | 2737 |
| Usunięte nadmiarowe rekordy artykułów | 492 |
| Usunięte nadmiarowe rekordy keywordów | 1804 |
| Usunięte artykuły spoza zakresu | 1 |
| Artykuły bez keywordów | 16 |
| Unikalne surowe warianty keywordów | 1743 |
| Unikalne warianty po prostym lower+trim | 1700 |

## Rozpoznany problem duplikacji

W danych wystąpiło 6 grup zduplikowanych artykułów. Każda grupa pojawiała się 83 razy, czyli raz przy każdym numerze czasopisma. Wskazuje to na pobranie linków z elementów globalnych strony, np. bloków typu „latest” albo „recommended”, a nie wyłącznie z głównej listy artykułów danego numeru.

Deduplikację wykonano po `article_id`. Dla zduplikowanych grup wybierano rekord kanoniczny przez dopasowanie cytowania artykułu (`year`, `volume`, `issue_number`) do etykiety numeru (`source_issue_label`). Jeśli takie dopasowanie nie było możliwe, stosowano pierwszy napotkany rekord i oznaczano to w logu.

## Pliki wynikowe

- `app_articles_dedup_2005_2025.csv` — finalna tabela artykułów do dalszego pipeline'u.
- `app_keywords_long_dedup_2005_2025.csv` — finalna tabela keyword-long do normalizacji.
- `app_article_deduplication_log.csv` — decyzje deduplikacyjne dla zduplikowanych artykułów.
- `app_articles_removed_duplicate_rows.csv` — usunięte nadmiarowe rekordy artykułów.
- `app_keywords_removed_duplicate_rows.csv` — usunięte nadmiarowe rekordy keywordów.
- `app_articles_removed_out_of_scope.csv` — rekordy artykułów spoza zakresu 2005–2025.
- `app_keywords_removed_out_of_scope.csv` — rekordy keywordów spoza zakresu 2005–2025.
- `app_articles_without_keywords.csv` — artykuły bez słów kluczowych.
- `app_articles_by_year.csv` — rozkład artykułów i keywordów po latach.
- `app_keyword_top30_raw.csv` — surowa lista 30 najczęstszych keywordów.
- `app_qa_summary.json` — maszynowo czytelne podsumowanie QA.

## Braki metadanych po deduplikacji

| Pole | Liczba pustych rekordów |
|---|---:|
| DOI | 266 |
| Abstract | 14 |
| Authors | 0 |
| Citation | 0 |
| Title | 0 |

## Artykuły bez keywordów

Liczba artykułów bez keywordów: **16**. Te rekordy pozostawiono w tabeli artykułów, ale naturalnie nie pojawiają się w tabeli keyword-long. Lista znajduje się w `app_articles_without_keywords.csv`.

## Top 15 surowych keywordów

| keyword_raw | n |
| --- | --- |
| schizophrenia | 71 |
| depression | 59 |
| anxiety | 31 |
| anorexia nervosa | 26 |
| editorial | 26 |
| editorial 2 | 26 |
| psychotherapy | 25 |
| editorial 1 | 25 |
| psychosis | 16 |
| stress | 16 |
| trauma | 14 |
| Psychotherapy | 14 |
| COVID-19 | 14 |
| bipolar disorder | 12 |
| mental health | 12 |

## Rozkład roczny

| year | articles | keyword_rows |
| --- | --- | --- |
| 2005 | 27 | 90 |
| 2006 | 23 | 98 |
| 2007 | 31 | 94 |
| 2008 | 40 | 123 |
| 2009 | 34 | 108 |
| 2010 | 36 | 124 |
| 2011 | 36 | 127 |
| 2012 | 29 | 123 |
| 2013 | 30 | 110 |
| 2014 | 32 | 119 |
| 2015 | 37 | 146 |
| 2016 | 37 | 131 |
| 2017 | 37 | 144 |
| 2018 | 37 | 140 |
| 2019 | 41 | 156 |
| 2020 | 37 | 146 |
| 2021 | 35 | 132 |
| 2022 | 37 | 144 |
| 2023 | 39 | 166 |
| 2024 | 37 | 159 |
| 2025 | 38 | 157 |

## Rekomendacja na kolejny etap

Do etapu 2 należy użyć:

- `app_articles_dedup_2005_2025.csv`
- `app_keywords_long_dedup_2005_2025.csv`

Następny krok to normalizacja techniczna keywordów: czyszczenie spacji, wielkości liter, interpunkcji, wariantów liczby pojedynczej/mnogiej oraz pierwsza identyfikacja wariantów semantycznych do późniejszego scalania.
