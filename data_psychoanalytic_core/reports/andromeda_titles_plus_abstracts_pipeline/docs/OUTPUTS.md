# Output inventory

## `outputs/raw/`

Initial ingested metadata. May contain source abstracts and should be treated according to rights status.

## `outputs/qa/`

QA checks, duplicate logs, removed records, and `articles_deduplicated.csv`.

## `outputs/normalized/`

Technically normalized title and abstract fields. Public sharing depends on rights status of source text.

## `outputs/terms/`

Candidate term assignments and vocabulary. These are derived features, but still review before publication when source restrictions apply.

## `outputs/semantic/`

Human-in-the-loop semantic map application outputs:

- `terms_semantic_final.csv`
- `semantic_audit_queue.csv`
- `semantic_excluded_records.csv`
- `semantic_concept_counts.csv`

## `outputs/periodized/`

Article and term records with analytical periods.

## `outputs/analyses/`

Aggregate, publication-oriented outputs: trends, top concepts, co-occurrence edges, network nodes, communities, summary JSON, draft methods note.
