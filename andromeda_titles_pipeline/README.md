# Andromeda Titles Pipeline

Universal human-in-the-loop pipeline for title-based bibliometric discourse mapping.

This module is intended for corpora where titles are the most stable and comparable metadata layer, especially when author keywords are unavailable or inconsistently exposed.

## Stages

1. `1a_qa_deduplicate_titles.py` — corpus QA and deduplication.
2. `2_clean_titles.py` — title cleaning and technical normalization.
3. `3_extract_title_terms.py` — candidate term and n-gram extraction.
4. `4_semantic_map_title_terms.py` — human-in-the-loop semantic mapping.
5. `5_periodize_title_terms.py` — analytical period assignment.
6. `6_analyze_title_discourse.py` — title-based trend and co-occurrence analyses.

## Principle

Title-based mapping does not reconstruct full article content. It maps the public self-presentation of articles through their titles.
