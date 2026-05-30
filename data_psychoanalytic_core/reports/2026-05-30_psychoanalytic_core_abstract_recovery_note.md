# Psychoanalytic core — abstract text recovery technical note

**Date:** 2026-05-30  
**Project:** Andromeda Nowicka / `data_psychoanalytic_core`  
**Stage:** post-harvest technical correction / abstract text recovery  
**Status:** completed

---

## 1. Purpose

This technical note documents a post-harvest correction in the `psychoanalytic_core` pipeline.

After the global `ART-only` corpus had been built, a diagnostic check showed that the main article table contained only an abstract availability flag, not the actual abstract text.

The affected file was:

```text
data_psychoanalytic_core/data/qa/global/psychoanalytic_core_articles_ART_only.csv
```

It contained:

```text
has_abstract
```

but did not contain:

```text
abstract_text
```

Because the next analytical phase requires a full title+abstract corpus, an additional recovery step was performed using the locally preserved raw PEP-Web JSON files.

No new API calls were made. No PDFs were downloaded. No full text was mirrored.

---

## 2. Diagnostic finding

A diagnostic script was run to inspect the global `ART-only` table for abstract-like fields.

The diagnostic found:

```text
n_rows: 12,164
abstract_like_columns: has_abstract
n_nonempty has_abstract: 12,164
median_length: 4
probably_flag_column: true
likely_contains_abstract_text: false
```

Conclusion:

```text
The global ART-only table preserved abstract availability but not abstract text.
```

This did not invalidate the harvest. It indicated that the abstract text had not been included in the flattened CSV layer even though raw PEP-Web JSON outputs had been preserved.

---

## 3. Recovery source

The recovery process used local raw JSON files from the full harvest:

```text
data_psychoanalytic_core/data/raw_pep_metadata/<journal>/<year>/*.json
```

The recovery was performed from the already harvested local metadata layer.

Policy flags:

```text
no API calls
no PDF downloads
no full-text mirroring
local raw JSON only
```

---

## 4. Script used

The recovery script was:

```text
data_psychoanalytic_core/scripts/1e_extract_abstract_texts_from_raw_json.py
```

The script recursively searched local raw JSON records for abstract-like fields, extracted plausible abstract text, deduplicated by `article_id`, and merged recovered abstracts into the global `ART-only` article table.

The extraction preserved audit fields:

```text
abstract_extraction_field_path
abstract_extraction_field_name
raw_json_file
record_path
abstract_text_length
abstract_extraction_status
```

---

## 5. Recovery results

The recovery completed successfully.

Summary:

```text
raw_json_files: 295
raw_json_errors: 0
candidate_field_rows: 24,393
extracted_abstract_rows_unique_article_id: 24,393
ART_only_rows: 12,164
ART_only_rows_with_abstract_text_after_merge: 12,164
ART_only_pct_with_abstract_text_after_merge: 100.0
```

Coverage by journal:

| Journal key | ART-only records | Records with abstract text | Coverage |
|---|---:|---:|---:|
| `ijpa` | 5,423 | 5,423 | 100.0% |
| `japa` | 2,924 | 2,924 | 100.0% |
| `psychoanalytic_dialogues` | 1,578 | 1,578 | 100.0% |
| `psychoanalytic_psychology` | 1,369 | 1,369 | 100.0% |
| `psychoanalytic_psychotherapy` | 870 | 870 | 100.0% |
| **Total** | **12,164** | **12,164** | **100.0%** |

---

## 6. Output files

The recovery produced the following files:

```text
data_psychoanalytic_core/data/qa/global/psychoanalytic_core_abstract_texts_extracted.csv
data_psychoanalytic_core/data/qa/global/psychoanalytic_core_articles_ART_only_with_abstracts.csv
data_psychoanalytic_core/data/qa/global/psychoanalytic_core_abstract_extraction_field_candidates.csv
data_psychoanalytic_core/data/qa/global/psychoanalytic_core_abstract_extraction_samples.csv
data_psychoanalytic_core/data/qa/global/psychoanalytic_core_abstract_extraction_summary.json
```

The most important output is:

```text
data_psychoanalytic_core/data/qa/global/psychoanalytic_core_articles_ART_only_with_abstracts.csv
```

This file is now the main input for title+abstract analyses.

---

## 7. Updated main analytical file

Before this correction, the main analytical article file was:

```text
data_psychoanalytic_core/data/qa/global/psychoanalytic_core_articles_ART_only.csv
```

After abstract recovery, the main analytical article file should be treated as:

```text
data_psychoanalytic_core/data/qa/global/psychoanalytic_core_articles_ART_only_with_abstracts.csv
```

This file contains the global `ART-only` corpus plus recovered abstract text.

Working rule for subsequent stages:

```text
Use psychoanalytic_core_articles_ART_only_with_abstracts.csv
for all title+abstract text analysis.
```

---

## 8. Methodological significance

This step confirms that the project now has a full `ART-only` title+abstract corpus:

```text
12,164 original substantive article records
100% recovered abstract text coverage
five PEP-Web psychoanalytic journals
```

This allows the next stage to proceed as planned:

```text
title_clean
abstract_clean
text_for_analysis = title_clean + abstract_clean
text quality QA
vocabulary reconnaissance
periodization
semantic mapping
journal and period comparison
```

The recovery also demonstrates the value of preserving raw JSON outputs. Because the raw metadata layer had been retained, the project could correct the flattened analytical layer without repeating the full harvest.

---

## 9. Risks and next checks

Although abstract coverage is now complete, the next QA step should inspect the quality of the recovered abstract texts.

Recommended checks:

```text
very short abstracts
HTML or XML artifacts
PEP front-matter remnants
embedded keyword blocks
copyright or access text leakage
duplicated abstracts
multilingual abstract segments
journal-specific formatting differences
```

These checks should be performed before semantic analysis.

---

## 10. Contribution record

### 10.1 Contribution by Lech Kalita

Lech Kalita identified the issue by manually inspecting the global `ART-only` CSV and questioning whether the file contained actual abstract text.

His contribution included:

- noticing that the apparent abstract field might be only a flag,
- requesting a diagnostic check,
- running the diagnostic script locally,
- reporting the diagnostic result,
- running the abstract recovery script,
- confirming that the enriched CSV now contains actual abstract texts.

### 10.2 Contribution by Andromeda Nowicka

Andromeda Nowicka supported the correction as a human-in-the-loop bibliometric and pipeline assistant.

Her contribution included:

- diagnosing the distinction between `has_abstract` and `abstract_text`,
- preparing a script to detect abstract-like columns and distinguish flags from text,
- preparing a recovery script to extract abstract text from local raw JSON files,
- defining output paths and audit fields,
- interpreting the successful recovery results,
- preparing this technical note for repository documentation.

---

## 11. Status statement

The abstract recovery step is complete.

The `psychoanalytic_core` project now has a full global `ART-only` title+abstract corpus ready for the next stage of text QA and vocabulary reconnaissance.

Main file for the next phase:

```text
data_psychoanalytic_core/data/qa/global/psychoanalytic_core_articles_ART_only_with_abstracts.csv
```
