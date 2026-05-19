# World corpus title-corpus builder

Ten mini-moduł wyprowadza korpus tytułowy z zamrożonej warstwy surowej `raw_full_v05`.

## Cel

Skrypt tworzy audytowalną warstwę pochodną:

1. scala wszystkie pliki `*_articles.csv`,
2. scala logi i summary, jeśli istnieją,
3. kontroluje puste lub brakujące pliki keywordów,
4. deduplikuje artykuły,
5. sprawdza braki tytułów, roku, DOI i abstraktów,
6. generuje raport QA,
7. zapisuje plik wejściowy do title-pipeline.

## Zasada

Katalog `raw_full_v05` pozostaje niemodyfikowany. Wszystkie wyniki trafiają do osobnych katalogów QA i title-pipeline.

## Przykładowe uruchomienie PowerShell

```powershell
python scripts/1a_build_title_corpus_from_raw.py `
  --raw-dir data_worldcorpus/data_psychotherapy_journals/raw_full_v05 `
  --qa-dir data_worldcorpus/data_psychotherapy_journals/qa `
  --title-dir data_worldcorpus/title_pipeline/input `
  --from-year 2005 `
  --to-year 2025
```

## Główne wyjście

```text
data_worldcorpus/title_pipeline/input/worldcorpus_titles_input.csv
```

## Najważniejsze pliki QA

```text
data_worldcorpus/data_psychotherapy_journals/qa/worldcorpus_qa_summary.json
data_worldcorpus/data_psychotherapy_journals/qa/worldcorpus_qa_report.md
data_worldcorpus/data_psychotherapy_journals/qa/worldcorpus_journal_summary.csv
data_worldcorpus/data_psychotherapy_journals/qa/worldcorpus_articles_by_journal_year.csv
```

## Interpretacja

Jeśli `total_keyword_rows_in_raw_keyword_files` wynosi 0, korpus nie powinien być raportowany jako author-keyword corpus. W takim przypadku właściwym opisem jest title-based bibliometric discourse mapping.
