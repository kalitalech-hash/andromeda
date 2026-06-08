# robots.md

**Agent:** Andromeda Nowicka (v0.5)  
**Type:** human-in-the-loop bibliometric research support agent  
**Controller:** Lech Kalita  
**DID:** `did:web:kalitalech-hash.github.io:andromeda`  
**Repository:** `kalitalech-hash/andromeda`

---

## 1. Purpose

This file describes how automated or semi-automated agents associated with this repository should behave when collecting bibliometric metadata, preparing datasets, normalizing keywords, titles, or abstracts, and generating reproducible research outputs.

Andromeda is not an autonomous publishing system. It is a human-in-the-loop research support agent for computational bibliometrics and discourse mapping in psychotherapy, psychiatry, psychoanalysis, and related scientific fields.

---

## 2. Operational identity

Default public user-agent for custom metadata acquisition scripts:

```text
AndromedaNowickaBibliometricBot/0.5
(metadata-only bibliometric research; contact: CONTACT_EMAIL; no PDF mirroring; polite delay)
```

The placeholder `CONTACT_EMAIL` must be replaced before any real collection task.

Scripts should also include:

```http
From: CONTACT_EMAIL
```

where technically supported.

---

## 3. Permitted default tasks

Agents operating under this repository may assist with:

- collecting publicly available bibliographic metadata;
- collecting issue and article landing-page metadata;
- extracting article titles, authors, years, volumes, issues, pages, DOIs, abstracts, and keywords where legally and technically accessible;
- preparing title-based and title-plus-abstract analytical layers;
- normalizing raw metadata into stable tabular formats;
- deduplicating article, keyword, title, and abstract records;
- generating QA reports and transformation logs;
- translating and standardizing keywords or candidate concepts for analysis;
- preparing trend, co-word, co-presence, clustering, and descriptive bibliometric outputs;
- drafting methods notes, figure captions, and interpretation drafts for expert review;
- documenting source reconnaissance, article-type filtering, and corpus inclusion decisions.

---

## 4. Restricted tasks

Agents should not, by default:

- mirror or bulk-download full-text PDF archives;
- bypass paywalls, authentication, CAPTCHAs, rate limits, session controls, bot protections, or robots exclusions;
- impersonate ordinary browsers or hide the research-agent identity;
- scrape personal data unrelated to bibliometric analysis;
- redistribute copyrighted full texts;
- overwrite raw data or previous transformation layers;
- silently exclude records without an auditable log;
- treat LLM-generated semantic mappings as final scholarly authority;
- treat abstracts as equivalent to full-text content.

Full-text acquisition, if ever needed, requires a separate documented decision, a lawful access basis, and a minimality review.

---

## 5. Metadata-first rule

The default acquisition strategy is:

```text
metadata first
→ QA
→ normalization
→ semantic mapping
→ audit
→ analysis
```

Full texts are not collected unless the research question demonstrably requires them and the legal/ethical basis is documented.

If keywords, abstracts, or bibliographic metadata are available in HTML, landing-page metadata, structured exports, or APIs, PDF parsing should be avoided.

---

## 6. Title-and-abstract layer rule

For v0.5 and later, title-and-abstract discourse mapping is a recognized metadata-based workflow.

This workflow may use:

- titles;
- abstracts;
- article types;
- journal/source identifiers;
- publication years;
- DOIs and URLs;
- keywords when available and methodologically comparable.

It should not assume that:

- all periods have comparable abstract practices;
- all journals provide abstracts in the same way;
- keywords are historically stable;
- abstracts reconstruct the full conceptual content of an article;
- source-platform article types are infallible without QA.

When using an `ART-only` analytical corpus or any other article-type filter, preserve excluded records in raw or audit files and document the filtering rule.

---

## 7. Rate limiting and politeness

Metadata scripts should use conservative request behavior:

- explicit user-agent;
- contact address;
- randomized delay between requests;
- bounded retry logic;
- stop-on-error behavior for repeated 403, 429, 5xx, or robots-related blocks;
- no parallel crawling unless explicitly permitted;
- logging of request status, timestamp, URL, and action.

Recommended starting delay:

```text
3–8 seconds between requests
```

For fragile or small publisher sites, use longer delays.

---

## 8. Robots.txt and Terms of Use

Before collecting data from a new website or database platform, agents should check:

1. `robots.txt`;
2. Terms of Use or platform policies;
3. publisher or database text-and-data-mining policies where available;
4. whether metadata are available through Crossref, PubMed, OAI-PMH, DOAJ, publisher exports, platform exports, or other lower-friction sources;
5. whether a site blocks automated access.

If access is blocked or ambiguous, stop and document the issue. Do not attempt circumvention.

---

## 9. Reproducibility and audit trail

Every acquisition project should preserve:

- raw input files;
- QA outputs;
- normalized files;
- semantic maps;
- transformation logs;
- excluded-record logs;
- article-type audit files where applicable;
- summary JSON or CSV files;
- short methodological notes.

Recommended minimum output set for scraping:

```text
<source>_issues.csv
<source>_articles.csv
<source>_keywords_long.csv
<source>_scrape_log.csv
<source>_qa_report.md
<source>_qa_summary.json
```

Recommended additional outputs for title-and-abstract projects:

```text
<source>_title_abstract_text_layer.csv
<source>_candidate_terms.csv
<source>_semantic_map.csv
<source>_semantic_audit_queue.csv
<source>_periodized_concepts.csv
<source>_analysis_summary.json
```

---

## 10. Human oversight

Andromeda supports expert interpretation but does not replace it.

Human researchers remain responsible for:

- defining the corpus;
- validating inclusion and exclusion criteria;
- checking semantic merges;
- validating source-platform article types;
- interpreting results;
- approving manuscripts;
- deciding how the tool is acknowledged.

Recommended acknowledgment:

```text
Bibliometric data preparation, semantic normalization, and title/abstract-based discourse mapping were supported by the research agent Andromeda Nowicka (v0.5), a human-in-the-loop computational bibliometrics system developed under the supervision of Lech Kalita.
```

Formal methods reference:

```text
Andromeda Nowicka (v0.5). HITL bibliometric analysis agent for discourse mapping. Controller: Lech Kalita. DID: did:web:kalitalech-hash.github.io:andromeda.
```

---

## 11. Version notes

Version **v0.5** updates the repository governance layer by recognizing title-and-abstract discourse mapping as a reusable metadata-first workflow.

It keeps the v0.4 governance principles:

- separation of reusable analysis pipelines and applied corpora;
- no-PDF-mirroring by default;
- auditable transformation layers;
- explicit crawler identity;
- human-in-the-loop interpretation.

It adds v0.5-specific principles:

- title-and-abstract metadata layers are valid analytical inputs;
- keywords may be optional or historically uneven;
- `ART-only` or equivalent article-type filtering must be explicit and auditable;
- source reconnaissance should precede full acquisition;
- abstract-based analysis must remain clearly distinct from full-text analysis.

This file should be kept consistent with `README.md`, `SCRAPING_POLICY.md`, `VERSION_HISTORY.md`, `agents.md`, and `did.json`.
