# Andromeda Keywords Pipeline

Universal human-in-the-loop pipeline for author-keyword-based bibliometric and discourse mapping.

This module is intended for corpora in which author keywords are available from journal pages, publisher metadata, Crossref-adjacent records, database exports, or manually curated metadata.

## Stages

1. `0_scrape_crossref_landing_pages.py` — optional metadata acquisition from Crossref and public landing pages.
2. `0b_keyword_source_audit.py` — audit whether keywords are actually exposed in public HTML/meta/JSON-LD.
3. `1a_qa_deduplicate_keywords.py` — corpus QA and deduplication.
4. `2_normalize_keywords.py` — technical normalization of keyword strings.
5. `3_semantic_map_keywords.py` — human-in-the-loop semantic mapping.
6. `4_periodize_keywords.py` — analytical period assignment.
7. `5_analyze_keyword_trends.py` — descriptive trends and co-occurrence-ready outputs.

## Principle

The scraper is a data acquisition helper, not an analytical result. Always run QA before interpretation.
