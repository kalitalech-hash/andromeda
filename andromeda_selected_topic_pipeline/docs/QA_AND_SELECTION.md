# Conservative QA and selected-topic screening

## Separate three decisions

**A. Technical record QA:** presence and consistency of ID, DOI, title, year, source, type, language, abstracts; Unicode/whitespace fixes recorded in derived columns while preserving originals.

**B. Deduplication:** exact OpenAlex IDs and normalized DOI, followed by candidate duplicate pairs based on title + year + authors/venue when available. Retain provenance of all query matches. A title-year match can refer to different reports or records; flag it for verification rather than silently merging unless the approved rule explicitly permits it.

**C. Eligibility:** source/time/type constraints and relevance to *researcher-defined topic*. Term hits in indexed metadata are candidate signals, not evidence of topical or clinical relevance.

## Default selection policy (conservative)

```text
INCLUDE_PROVISIONAL : satisfies a documented high-specificity criterion
EXCLUDE_CONFIRMED   : explicit mismatch under approved rule
UNCERTAIN           : unclear or incomplete evidence; human audit required
DUPLICATE_CANDIDATE : unresolved record linkage
```

By default, *absence of an abstract is not a reason to exclude*. The research lead validates ambiguous selections and semantic merges. Automated classifiers/regex can prioritize review and propose categories, but do not silently convert low-confidence cases into firm exclusions.

A researcher may approve **strict automatic exclusion** of unmatched records for a precision-oriented question. This must be marked `automatic_unmatched_exclusion_opt_in=true`, specify pattern version and rule hierarchy, retain every excluded record/reason, and report a false-negative risk. Include a sensitivity sample from excluded/uncertain records; if sensitivity is not assessed, say so.

Article-type filtering must be separately versioned. `OpenAlex type == article` supports an **article-labelled** cohort; it does not prove peer review or that the work is an original study. Reviews and non-article records should be placed in an exclusion table, not erased. If the researcher intends original empirical studies only, this requires another justified design screen beyond the type label.

## Canonical audit schema

`screening_all_audited.csv` should include:
```text
record_id,doi,journal,year,title,source_id,query_matches,
publication_type_raw,missing_abstract,technical_flags,
topic_rule_version,suggested_topic_layer,match_evidence_field,
match_rule_id,classification_confidence,eligibility_status,
exclusion_reason,decision_actor,decision_timestamp,decision_note
```
Store minimal text features in published audit files if raw abstract redistribution is not permitted.

Additional outputs:
- `duplicate_candidates.csv` — record pair, keys and resolution;
- `missing_metadata.csv` — field and record-level missingness;
- `excluded_records.csv` — all exclusions, explicit reasons;
- `uncertain_review_queue.csv` — unresolved semantic and linkage cases;
- `qa_summary.json` — denominators, reasons, counts, coverage limits;
- `transformation_log.json` — hashes, exact rules and versions, dates;
- `methodological_note.md` — publishable, corpus-bound description.

Always reconcile `raw → unique → included + excluded + uncertain` for each stage. Where deduplication precedes screening, report duplicates separately from topical exclusions and preserve source hit provenance.

## Corpus freeze

Create a versioned `corpus_manifest.json` with:
- source raw SHA and protocol SHA / version;
- analytical layer and eligibility rules;
- explicit included IDs, counts by layer/source/year/type;
- unresolved cases and decisions;
- acquisition mode and truncated-query flags;
- date and approving researcher;
- limitations and permission constraints.

Only after a freeze should the cohort be passed to downstream term extraction, semantic normalization, trend and co-occurrence analysis.

## Interpretation safeguards

Distinguish retrieval yield, *within-corpus* topic proportions, and prevalence in a larger scientific field. A higher count can reflect journal coverage, ranked API hits, query design, indexing and abstract availability rather than intellectual change.

Suggested language: "Wśród publikacji zakwalifikowanych na podstawie publicznej warstwy tytułów i abstraktów..." / "In the metadata-bounded selected-topic corpus...".

Do not infer treatment efficacy, mechanisms or clinical validity from frequencies alone.
