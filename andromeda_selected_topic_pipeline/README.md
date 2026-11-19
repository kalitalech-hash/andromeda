# Andromeda Selected Topic Pipeline

**Reusable, researcher-led selected-topic corpus construction and discourse analysis**  
Andromeda Nowicka (v0.5) · human-in-the-loop research support agent

## Purpose and position in the toolkit

This pipeline builds a **problem-defined bibliometric corpus**: the starting point is a research question and an explicit selection protocol, **not** an entire journal or field taken as a reference population.

- `andromeda_keywords_pipeline/` maps the author/editorial keyword layer of a defined corpus.
- `andromeda_titles_pipeline/` maps the public-facing discourse of titles.
- `andromeda_titles_plus_abstracts_pipeline/` maps the richer, still metadata-bounded title/abstract layer.
- **`andromeda_selected_topic_pipeline/`** defines **which publications belong to a researcher-selected problem** through source discovery, bounded OpenAlex sampling/harvesting and conservative, auditable eligibility screening. It **hands off** an approved corpus to one of the analytical pipelines above; it does not replace their semantic-normalization procedures.

A selected-topic corpus maps terminology and publication patterns **within the retrieved and operationally selected metadata records**. It does not measure the prevalence of a topic across all scholarship unless coverage has been independently validated.

## Governance: explicit human decisions

Before acquisition the researcher approves a versioned `topic_protocol.json` recording:

1. research question, operational boundaries and conceptual subtopics;
2. time span, languages and eligible publication types;
3. source universe (named journals, database scope, or a justified wider search) and OpenAlex source IDs when applicable;
4. search families and exact strings, including controlled synonyms and negative controls;
5. metadata fields and the intended analytical layer;
6. inclusion, exclusion and uncertainty rules, with precedence and planned sensitivity checks;
7. sampling caps, stopping criteria and acceptable coverage claims;
8. publication/redistribution boundaries and human sign-off.

Do **not** infer approval from ambiguous discovery exports. Source matching, field mapping and excluded sources require an audit trail. The illustrative template is in `config/topic_protocol.example.json`.

## Workflow

```text
0. researcher-defined topic protocol and source reconnaissance
   ↓
1. OpenAlex pilot / stratified sampling (journal × query × period, when justified)
   ↓
1b. pilot QA, query-yield and coverage assessment; researcher decision gate
   ↓
2. bounded or otherwise documented metadata harvest; checkpoint/resume
   ↓
3. technical QA / deduplication / article-type audit
   ↓
4. conservative topical screening, exclusion log, uncertainty queue
   ↓
5. corpus freeze + versioned analytical cohort (topic × article type × layer)
   ↓
6. hand-off to keywords, titles or titles+abstracts pipeline
   ↓
7. trends / co-presence / cross-journal comparisons + expert interpretation
```

Stages 0–5 are the contribution of this pipeline. Stages 6–7 reuse established Andromeda workflows. See `docs/ACQUISITION_PROTOCOL.md` and `docs/QA_AND_SELECTION.md`.

## Acquisition strategy

**Metadata-first; pilot before expansion.** Prefer structured exports and legal APIs. For OpenAlex:

- Resolve/validate source IDs; distinguish `primary_location.source.id` from other possible publication locations.
- Record exact `search` expressions and filters; OpenAlex general search **must not be represented as title/abstract-only matching**.
- Begin with a small bounded pilot across the declared strata, not just one globally ranked list.
- Inspect per-query counts, overlap, missing abstracts, search noise and retrieval of known relevant 'sentinel' publications.
- Proceed only after a documented researcher decision; save configuration fingerprint and checkpoint every successful page.
- Never use `--full` as evidence of exhaustive coverage: if a page cap or top-ranked search is used, label the result **bounded harvest**.
- Document potential ranking, indexing, language, source and temporal biases. Report unsuccessful attempts separately from completed records.

The generic pipeline is a **methodological framework and configuration contract**. The present repository's operational OpenAlex harvester is a corpus-specific adapter in `data_avatar_therapy_voices_starter/scripts/01_acquire_candidates.py`; it is **not yet a generalized executable for arbitrary topics**. Reusing it requires a corpus-specific configuration and code audit, especially for source scope and output paths. No live queries are executed by this new folder.

## QA position: conservative by default

QA first checks record integrity and metadata completeness; topical screening is a **separate, documented decision**. Preserve raw records and never silently delete exclusions.

Default policy:
- missing abstract/DOI → flag, **not automatic topical exclusion**;
- duplicate OpenAlex ID/DOI → deterministic key and audit, with title-year near-duplicates flagged for validation;
- incompatible article type/year/language → exclude only under *researcher-approved* rule, with reason;
- ambiguous relevance → `UNCERTAIN` / human review (default), not guessed inclusion or exclusion;
- strict automated exclusion of unmatched records is an **opt-in precision-oriented protocol**, with an explicit false-negative risk, preserved exclusions and a sensitivity sample.

Source platform `type=article` is a **metadata label**, not independent proof of peer review. Avoid conflating articles, reviews, conference abstracts or trial reports with independent studies.

## Required project outputs

```text
data_<topic>/
  config/topic_protocol.json
  data/raw/                          # permissions and redistribution controls
  outputs/source_reconnaissance.csv
  outputs/sample/pilot_candidates.csv
  outputs/sample/pilot_qa_summary.json
  outputs/harvest/run_manifest.json
  outputs/harvest/checkpoints/
  outputs/harvest/acquisition_log.csv
  outputs/harvest/candidates_raw.csv
  outputs/qa/deduplication_audit.csv
  outputs/qa/missing_metadata.csv
  outputs/qa/screening_all_audited.csv
  outputs/qa/excluded_records.csv
  outputs/qa/uncertain_review_queue.csv
  outputs/qa/qa_summary.json
  outputs/qa/transformation_log.json
  outputs/qa/methodological_note.md
  outputs/cohorts/selected_topic_articles.csv
  outputs/cohorts/corpus_manifest.json
  outputs/analyses/                      # downstream analytical pipeline
```

The structure is a **recommended output contract**, not a claim that all stages are already implemented. A stage should emit an output, QC file(s), machine-readable summary, transformation log and a short methods note where applicable. Preserve previous runs; use hashes, run IDs, source/API dates and explicit cohort versions.

## Example application: AVATAR / voices / VR

The applied workspace is `data_avatar_therapy_voices_starter/`. A researcher-approved five-journal OpenAlex search generated a pilot (122 records) and a **bounded** larger harvest (1047 raw candidates). Strict A/B/C rules retained 266 metadata candidates, then an `article` type filter retained **209** (A=12, B=184, C=13) for the derivative cohort as recorded in that workspace. These counts are *corpus-specific* and do not define universal defaults.

The AVATAR project deliberately auto-excludes records outside A/B/C; **that is a signed-off special case**, not this pipeline's general conservative default. OpenAlex general search, page caps and regex inclusion introduce potential omissions. The cohort should not be called exhaustive or human-validated on this basis alone.

## Methodological interpretation

Suggested wording:

> We constructed a researcher-defined, selected-topic corpus from a documented public bibliographic metadata layer. Source selection, OpenAlex retrieval, sampling limits, deduplication, type filtering and topical screening were versioned and audited. Reported topic patterns refer to the resulting bounded and operationally selected corpus, rather than to all publications on the subject. Semantic interpretation was performed separately using the relevant metadata-discourse pipeline.

## Ethics and credit

Follow `../SCRAPING_POLICY.md` and `../robots.md`: real crawler contact, considerate delays (initially 3–8 s), halt on 401/403/429 and persistent 5xx, obey API quotas, no CAPTCHA/paywall circumvention, no PDF/full-text mirroring by default. Use environment variables for API keys; never commit tokens, cookies, raw authorization headers or unrestricted third-party content.

Andromeda is a **research support agent**, not a co-author. Researcher decisions, validation of ambiguous selections and interpretation remain human-led. Code/documentation follow repository MIT terms; rights to third-party metadata and abstracts remain separate.

**Status:** v0.1 documentation-first reusable methodology and templates; the AVATAR scripts are the initial reference implementation, not a certified topic-agnostic engine.
