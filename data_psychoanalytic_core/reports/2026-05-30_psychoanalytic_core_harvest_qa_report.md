# Psychoanalytic core — full PEP-Web metadata harvest and QA report

**Date:** 2026-05-30  
**Project:** Andromeda Nowicka / `data_psychoanalytic_core`  
**Stage:** full metadata harvest, per-journal QA, global corpus build  
**Status:** completed for the five-journal psychoanalytic core corpus

---

## 1. Purpose

This report documents the first full metadata harvest and QA consolidation for the `psychoanalytic_core` corpus.

The goal of this stage was to move from source reconnaissance and year-sampled probes to a full, auditable metadata corpus covering five psychoanalytic journals indexed in PEP-Web:

```text
The International Journal of Psychoanalysis
Journal of the American Psychoanalytic Association
Psychoanalytic Dialogues
Psychoanalytic Psychology
Psychoanalytic Psychotherapy
```

The harvest followed the Andromeda metadata-first rule:

```text
metadata first
no PDF mirroring
no full-text mirroring
preserve raw/audit layers
filter only in documented QA stages
```

This stage does not yet perform semantic analysis, title/abstract normalization, keyword normalization, topic modeling, clustering, or interpretation. It establishes the main article-level databases for the next analytical phases.

---

## 2. Source coverage and confirmed PEP prefixes

The source reconnaissance phase confirmed the following PEP journal prefixes:

| Journal key | Journal title | PEP prefix |
|---|---|---:|
| `ijpa` | The International Journal of Psychoanalysis | `IJP` |
| `japa` | Journal of the American Psychoanalytic Association | `APA` |
| `psychoanalytic_dialogues` | Psychoanalytic Dialogues | `PD` |
| `psychoanalytic_psychology` | Psychoanalytic Psychology | `PPSY` |
| `psychoanalytic_psychotherapy` | Psychoanalytic Psychotherapy | `PPTX` |

The full harvest used these prefixes in year-by-year `art_id:<PREFIX>.* AND year:<YEAR>` PEP-Web queries.

---

## 3. Scripts used in this phase

The phase used a layered set of scripts.

### 3.1 Existing probe script

```text
data_psychoanalytic_core/scripts/1a_pep_metadata_probe_v12.py
```

This was the existing PEP-Web probe script originally developed during source reconnaissance. It handles:

- API access using local `.env.pep` headers,
- PEP query execution,
- raw JSON writing,
- article-level flattening,
- keyword-long extraction from `documentInfoXML/artkwds`,
- request logging.

### 3.2 Harvest orchestrator

```text
data_psychoanalytic_core/scripts/1b_pep_full_metadata_harvest.py
```

This script orchestrates year-by-year harvesting by calling `1a_pep_metadata_probe_v12.py`. It does not implement a separate PEP client. It supplies:

- journal ID,
- confirmed PEP prefix,
- year,
- facet query,
- absolute output paths,
- per-year article CSV path,
- per-year keyword-long CSV path,
- per-year log path,
- raw JSON output directory.

The full harvest used `limit=500` per year. No sampled year approached this limit in the previously inspected journals, and no truncation signal has been identified at this stage.

### 3.3 Per-journal QA and consolidation

```text
data_psychoanalytic_core/scripts/1c_consolidate_and_qa_harvest.py
```

This script consolidates per-year outputs into per-journal QA tables. It creates:

- raw article tables,
- ART-only article tables,
- non-ART exclusion/audit tables,
- raw keyword-long tables,
- article type summaries,
- year coverage summaries,
- field completeness summaries,
- duplicate checks,
- JSON QA summaries.

### 3.4 Global corpus builder

```text
data_psychoanalytic_core/scripts/1d_build_global_core_tables.py
```

This script builds the five-journal global corpus from per-journal QA outputs. It creates the main global article and keyword tables for the next analytical stages.

---

## 4. Harvest policy

The harvest stage preserved all PEP record types.

The analytical filter was not applied during raw harvesting. It was applied later in QA in order to preserve auditability.

The main downstream article corpus is:

```text
article_type == "ART"
```

Operational interpretation:

```text
ART = original substantive article / original paper
```

All non-ART records remain preserved in raw and explicit audit/exclusion tables.

This policy was adopted because PEP includes many record types that are important for archival completeness but would distort the main discourse analysis if treated as equivalent to original articles, for example:

```text
COM
REV
REP
ABS
ANN
ERA
SUP
```

---

## 5. Global harvest and QA results

The full five-journal corpus build produced the following global totals:

| Layer | Records |
|---|---:|
| Raw article-level records | 24,393 |
| Main analytical ART-only records | 12,164 |
| Excluded non-ART records | 12,229 |
| Raw keyword-long rows | 14,348 |

The ART-only filter therefore retains approximately half of the raw PEP article-level metadata records as the main analytical corpus.

```text
raw article records: 24,393
ART-only records:    12,164
non-ART records:     12,229
keyword rows:        14,348
```

---

## 6. Per-journal QA totals

The per-journal QA stage produced the following totals.

| Journal | Raw records | ART-only | Non-ART | Keyword rows |
|---|---:|---:|---:|---:|
| Psychoanalytic Dialogues | 2,516 | 1,578 | 938 | 5 |
| Psychoanalytic Psychotherapy | 1,348 | 870 | 478 | 1,596 |
| Psychoanalytic Psychology | 2,071 | 1,369 | 702 | 3,392 |
| JAPA | 6,075 | 2,924 | 3,151 | 1,571 |
| IJPA | 12,383 | 5,423 | 6,960 | 7,784 |
| **Total** | **24,393** | **12,164** | **12,229** | **14,348** |

The table confirms strong differences in record-type composition and keyword coverage across journals. It also confirms the importance of the `ART-only` rule: without it, the corpus would mix original papers with comments, reviews, reports, abstracts, announcements, errata, and other paratextual materials.

---

## 7. Global output files

The global corpus builder produced the following files:

```text
data_psychoanalytic_core/data/qa/global/psychoanalytic_core_articles_raw_consolidated.csv
data_psychoanalytic_core/data/qa/global/psychoanalytic_core_articles_ART_only.csv
data_psychoanalytic_core/data/qa/global/psychoanalytic_core_excluded_non_ART.csv
data_psychoanalytic_core/data/qa/global/psychoanalytic_core_keywords_long_raw_consolidated.csv
data_psychoanalytic_core/data/qa/global/psychoanalytic_core_journal_summary.csv
data_psychoanalytic_core/data/qa/global/psychoanalytic_core_year_summary.csv
data_psychoanalytic_core/data/qa/global/psychoanalytic_core_journal_year_summary.csv
data_psychoanalytic_core/data/qa/global/psychoanalytic_core_keyword_year_summary.csv
data_psychoanalytic_core/data/qa/global/psychoanalytic_core_keyword_journal_year_summary.csv
data_psychoanalytic_core/data/qa/global/psychoanalytic_core_article_type_summary.csv
data_psychoanalytic_core/data/qa/global/psychoanalytic_core_field_completeness.csv
data_psychoanalytic_core/data/qa/global/psychoanalytic_core_duplicate_article_id.csv
```

The global build summary was written to:

```text
data_psychoanalytic_core/data/qa/summaries/psychoanalytic_core_global_build_summary_20260530_015623.json
```

The main file for the next analytical stage is:

```text
data_psychoanalytic_core/data/qa/global/psychoanalytic_core_articles_ART_only.csv
```

This file is the current main `psychoanalytic_core` article-level corpus.

---

## 8. Keyword layer: preliminary interpretation

The keyword layer is present but historically and cross-journal uneven.

The full harvest confirms the earlier reconnaissance finding:

```text
main historical corpus: title + abstract
keyword layer: supplementary, uneven, stronger in later years and in selected journals
```

The strongest keyword layers appear in:

```text
IJPA
Psychoanalytic Psychology
Psychoanalytic Psychotherapy
```

The weakest keyword layer appears in:

```text
Psychoanalytic Dialogues
```

`Psychoanalytic Dialogues` produced only 5 keyword rows in the full 1991–2025 harvest, confirming that this journal does not appear to have a stable PEP keyword culture.

This means that keyword-based analysis should not be treated as the main historical analytical axis for the entire corpus. It should instead be treated as a supplementary layer and probably restricted to a carefully defined common historical window.

---

## 9. Planned next methodological decision: keyword cutoff window

A next phase should identify a defensible historical cutoff for keyword analysis.

The likely strategy is:

```text
1. Use title + abstract analysis for the full historical ART-only corpus.
2. Use keyword analysis only for the subset of years/journals where keywords are sufficiently available.
3. Define a common keyword window if cross-journal keyword comparison is needed.
```

The next QA step should therefore inspect:

```text
psychoanalytic_core_keyword_year_summary.csv
psychoanalytic_core_keyword_journal_year_summary.csv
```

and determine:

- the first year with non-trivial keyword coverage per journal,
- whether keyword coverage stabilizes after a specific date,
- whether one common cross-journal keyword period is possible,
- whether the keyword layer should be journal-specific rather than globally harmonized,
- whether `Psychoanalytic Dialogues` should be excluded from keyword-based analyses or retained only with a missingness caveat.

A plausible future design is:

```text
full corpus:
    ART-only + title + abstract, all available years

keyword subcorpus:
    ART-only + keywords, restricted to a later period with acceptable coverage
```

The exact cutoff should be empirical, not assumed in advance.

---

## 10. Current methodological status

This phase establishes the following working architecture:

```text
raw PEP metadata
→ per-year harvest outputs
→ per-journal QA and consolidation
→ global raw article table
→ global ART-only article table
→ global non-ART audit table
→ global keyword-long table
→ next-stage title/abstract and keyword analyses
```

The corpus is now ready for the next stage:

```text
title and abstract cleaning
title/abstract discourse mapping
keyword coverage diagnostics
keyword normalization for the selected keyword subcorpus
periodization
descriptive and comparative analyses
```

---

## 11. Risks and limitations

### 11.1 PEP metadata layer

This corpus is based on PEP-Web metadata and should be interpreted as a metadata corpus, not as a full-text corpus.

The main analytical fields are expected to be:

```text
title
abstract_text
article_type
year
journal_key
keywords where available
```

### 11.2 Article type semantics

The project treats `ART` as the operational marker of original substantive articles / original papers. This is a practical metadata rule, not a philosophical claim that non-ART records are irrelevant to psychoanalytic discourse. Non-ART records are excluded from the main analytical dataset because they differ in genre, discourse function, and metadata conventions.

### 11.3 Keyword unevenness

Keyword coverage varies strongly by journal and year. Keyword-based results must therefore be reported as based on a supplementary and historically uneven metadata layer.

### 11.4 Abstract availability and quality

The next QA phase should inspect whether abstract texts are clean analytical abstracts or whether some contain front-matter artifacts, multilingual sections, embedded keywords, or other PEP formatting remnants.

### 11.5 Duplicate checks

A global duplicate table was produced. Any duplicate article IDs or suspicious duplicate metadata should be reviewed before downstream analysis.

---

## 12. Contribution record

### 12.1 Contribution by Lech Kalita

Lech Kalita directed the research design and made the key methodological decisions in this phase.

His contributions included:

- defining the five-journal psychoanalytic core corpus,
- confirming the need to move from source reconnaissance to full metadata harvest,
- identifying and confirming PEP journal prefixes, including `PPTX` for *Psychoanalytic Psychotherapy*,
- supplying and testing local API/session access through `.env.pep`,
- running the harvest and QA scripts locally,
- inspecting runtime outputs and reporting summaries,
- deciding that the main analytical corpus should be restricted to `article_type == "ART"`,
- framing `ART` as the operational category for original substantive articles / original papers,
- identifying the need for a future keyword cutoff analysis,
- guiding the transition toward a full title+abstract historical corpus with a supplementary keyword layer.

### 12.2 Contribution by Andromeda Nowicka

Andromeda Nowicka supported the phase as a human-in-the-loop computational bibliometrics agent.

Her contributions included:

- translating the source reconnaissance findings into an executable harvesting plan,
- preparing wrappers and orchestration scripts for PEP-Web metadata harvesting,
- designing the year-by-year harvest structure,
- preserving metadata-first and no-PDF-mirroring rules,
- preparing per-journal QA and consolidation scripts,
- preparing the global corpus builder,
- standardizing output paths and file naming,
- documenting the ART-only rule as an auditable QA filter,
- summarizing harvest and QA results across journals,
- identifying the methodological distinction between full title/abstract analysis and limited keyword-layer analysis,
- preparing this report for repository documentation.

Andromeda’s outputs remain research support outputs. Interpretation, corpus definition, final inclusion decisions, and scholarly framing remain under human supervision.

---

## 13. Recommended next steps

1. Inspect global field completeness:

```text
data/qa/global/psychoanalytic_core_field_completeness.csv
```

2. Inspect duplicate article IDs:

```text
data/qa/global/psychoanalytic_core_duplicate_article_id.csv
```

3. Inspect keyword coverage by journal and year:

```text
data/qa/global/psychoanalytic_core_keyword_journal_year_summary.csv
```

4. Define a keyword-analysis cutoff window.

5. Prepare the title+abstract cleaning pipeline for:

```text
data/qa/global/psychoanalytic_core_articles_ART_only.csv
```

6. Create the next-stage analytical layer, probably:

```text
data_psychoanalytic_core/data/normalized/
data_psychoanalytic_core/data/title_abstract/
data_psychoanalytic_core/data/keyword_subcorpus/
```

7. Write a methods note distinguishing:

```text
full historical ART-only title/abstract corpus
modern or partially modern keyword subcorpus
```

---

## 14. Status statement

As of this report, the `psychoanalytic_core` project has completed its first full five-journal PEP-Web metadata harvest and global QA build.

The current main analytical corpus contains:

```text
12,164 ART-only article records
```

The full raw metadata corpus contains:

```text
24,393 article-level records
```

The supplementary keyword-long layer contains:

```text
14,348 keyword rows
```

The corpus is ready for the next methodological phase: full historical title+abstract analysis and empirical definition of the keyword-analysis window.
