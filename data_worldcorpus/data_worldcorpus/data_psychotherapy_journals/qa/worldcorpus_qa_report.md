# World corpus — QA and title-corpus extraction report

## Purpose

This report documents the extraction of a title-based analytical corpus from an immutable raw bibliographic scrape.

## Input

- Raw directory: `data_psychotherapy_journals\raw_full_v05`
- Article files detected: 11
- Scrape-log files detected: 11
- Scrape-summary files detected: 11
- Keyword-long files detected: 11

## Main counts

- Raw article rows: 32190
- Deduplicated article rows: 16095
- Duplicate rows flagged: 32190
- Deduplication strategy: `doi_norm`
- Deduplication columns: `['doi_norm']`

## Title-corpus output

- In-scope title rows: 15979
- Articles without title: 0
- Articles missing year: 0
- Articles outside requested year scope: 116
- Year range in title corpus: 2005–2025
- Journals represented: 10
- DOI coverage: 100.0%
- Abstract coverage: 23.49%

## Keyword status

Total rows found in raw keyword-long files: 0

If this value is zero or near zero, the dataset should not be interpreted as an author-keyword corpus. It should be treated as a bibliographic/title corpus unless additional keyword metadata are obtained from a reliable external export.

## Main output files

QA layer:

- `worldcorpus_articles_raw_combined.csv`
- `worldcorpus_articles_dedup.csv`
- `worldcorpus_articles_duplicates.csv`
- `worldcorpus_articles_without_title.csv`
- `worldcorpus_articles_missing_year.csv`
- `worldcorpus_articles_out_of_scope.csv`
- `worldcorpus_articles_by_journal_year.csv`
- `worldcorpus_journal_summary.csv`
- `worldcorpus_keyword_files_summary.csv`
- `worldcorpus_qa_summary.json`

Title-pipeline input:

- `worldcorpus_titles_input.csv`

## Methodological note

The raw layer is preserved as an immutable source layer. This script creates a derived title-corpus input table for downstream title-based discourse mapping. Article titles are treated as standardized, consistently available indicators of article self-presentation, not as substitutes for full-text discourse analysis.
