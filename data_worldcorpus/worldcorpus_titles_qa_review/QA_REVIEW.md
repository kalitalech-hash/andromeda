# QA review — worldcorpus_titles_input.csv

## Main status

The uploaded title corpus contains **15,979 rows**, covering **10 journals** and years **2005–2025**.

The core identifiers look clean:

- unique `article_id`: 15,979
- unique `doi`: 15,979
- duplicate `article_id` rows: 0
- duplicate DOI rows: 0

This means the file is usable as the canonical raw title-corpus input layer.

## Missingness

- missing titles: 0
- missing years: 0
- missing authors: 1,531
- missing abstracts: 12,226
- abstract coverage: 23.49%
- all `n_keywords` equal zero: True

The corpus should therefore be treated as a **title corpus**, with abstracts as a partial supplementary layer only.

## Important QA issue

There are **763 rows** that duplicate the same `journal_key + year + title_clean_initial` combination. Inspection shows that many are not bibliographic duplicates but repeated technical/editorial titles such as:

- `Book review`
- `Guide for Authors`
- `Notice`
- `Inside front cover / Editorial board`
- `New Books of Potential Interest`

These records should not automatically be removed as DOI duplicates, because the DOI values are unique. However, they should be excluded or separately flagged before title-term extraction.

## Non-research / technical candidate flags

A rule-based screen flagged **1,081 rows** as likely non-research or technical/editorial material.

After conservative exclusion of these candidates, the analysis-candidate title corpus contains **14,898 rows** (93.23% retained).

This should still be treated as an audit candidate, not as a final exclusion decision.

## Recommended next step

Use:

`worldcorpus_titles_input_analysis_candidate.csv`

as the preliminary input for title cleaning and term extraction, while preserving:

`worldcorpus_titles_input.csv`

as the canonical raw title-corpus layer.

Before final analyses, manually inspect:

- `nonresearch_candidate_records.csv`
- `duplicate_title_year_journal_records.csv`
- `short_title_records_lt20.csv`
