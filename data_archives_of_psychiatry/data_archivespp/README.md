# data_archivespp — etap 1: scraping

Roboczy moduł dla czasopisma **Archives of Psychiatry and Psychotherapy**.

## Pliki wyjściowe

Po uruchomieniu skryptu:

```bash
cd data_archivespp/scripts
python 1_scrape_archivespp.py --start-year 2005 --end-year 2025
```

powinny powstać:

- `../data/app_issues.csv` — lista numerów czasopisma,
- `../data/app_articles.csv` — metadane artykułów,
- `../data/app_keywords_long.csv` — długi format słów kluczowych,
- `../data/app_scrape_log.csv` — log pobierania i parsowania.

## Uwagi audytowe

- Keywordy są pobierane ze stron abstraktów artykułów, z bloku `KEYWORDS`.
- Skrypt nie parsuje PDF-ów.
- `Online first` jest domyślnie pomijane, aby uniknąć mieszania rekordów bez stabilnego rocznika/numeru. Można je dodać flagą `--include-online-first`.
- Dalszy etap powinien obejmować walidację rekordów bez keywordów oraz kontrolę typów publikacji.
