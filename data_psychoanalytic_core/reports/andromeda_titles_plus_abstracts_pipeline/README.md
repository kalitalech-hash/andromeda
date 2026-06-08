# andromeda_titles_plus_abstracts_pipeline

Reusable pipeline for **title + abstract discourse mapping** in Andromeda Nowicka (v0.4).

This pipeline extends the existing title-based workflow toward a richer but still metadata-first layer: article titles and openly available or otherwise lawfully accessible abstracts. It was prepared for psychoanalytic / psychotherapy bibliometric work inspired by the PEP-Web project, but it is intentionally corpus-agnostic and should be copied or imported into applied workspaces such as `data_<corpus>/`.

## Methodological position

The pipeline maps the discourse visible in **titles and abstracts**. It does not reconstruct the full intellectual content of articles and it should not be interpreted as full-text mining.

Default acquisition and storage rules:

```text
metadata first
abstracts only when openly displayed, exported under permitted terms, or otherwise lawfully available
no PDF mirroring
no full-text mirroring
derived analytical features preferred over redistributable source text
```

For PEP-Web-style sources this distinction is important: the reusable pipeline can process a legally obtained metadata export, but the repository should not contain restricted abstracts, full-text records, PDFs, access tokens, cookies, or session-specific material.

## Recommended workflow

```text
0 corpus definition
→ 1 metadata ingestion
→ 1a QA and deduplication
→ 2 technical text normalization
→ 3 candidate term extraction
→ 4 semantic normalization and audit
→ 5 periodization
→ 6 final analyses
→ 7 methods/report note
```

## Expected input

A CSV or JSONL file with at least:

```text
article_id
title
year
```

Recommended fields:

```text
article_id
article_url
source
journal
year
volume
issue
pages
doi
authors
title
abstract
publication_type
language
source_collection
rights_note
acquisition_date
```

## Main analytical outputs

The final stage produces:

```text
outputs/analyses/stage6_period_descriptives.csv
outputs/analyses/stage6_top_terms_overall.csv
outputs/analyses/stage6_term_period_trends.csv
outputs/analyses/stage6_rising_terms.csv
outputs/analyses/stage6_falling_terms.csv
outputs/analyses/stage6_emerging_terms.csv
outputs/analyses/stage6_persistent_terms.csv
outputs/analyses/stage6_cooccurrence_edges_filtered.csv
outputs/analyses/stage6_network_nodes.csv
outputs/analyses/stage6_network_communities.csv
outputs/analyses/stage6_summary.json
```

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Minimal run

```bash
python scripts/1_ingest_metadata.py \
  --input data/raw/pepweb_metadata_export.csv \
  --output outputs/raw/articles_raw.csv \
  --config config/default_config.json

python scripts/1a_qa_deduplicate.py \
  --input outputs/raw/articles_raw.csv \
  --output-dir outputs/qa \
  --config config/default_config.json

python scripts/2_normalize_text.py \
  --input outputs/qa/articles_deduplicated.csv \
  --output-dir outputs/normalized \
  --config config/default_config.json

python scripts/3_extract_candidate_terms.py \
  --input outputs/normalized/articles_text_normalized.csv \
  --output-dir outputs/terms \
  --config config/default_config.json

python scripts/4_apply_semantic_map.py \
  --terms outputs/terms/candidate_terms_long.csv \
  --map templates/semantic_map_template.csv \
  --output-dir outputs/semantic

python scripts/5_periodize.py \
  --articles outputs/normalized/articles_text_normalized.csv \
  --terms outputs/semantic/terms_semantic_final.csv \
  --output-dir outputs/periodized \
  --config config/default_config.json

python scripts/6_final_analyses.py \
  --articles outputs/periodized/articles_periodized.csv \
  --terms outputs/periodized/terms_periodized.csv \
  --output-dir outputs/analyses \
  --config config/default_config.json

python scripts/7_generate_methods_note.py \
  --summary outputs/analyses/stage6_summary.json \
  --output outputs/analyses/methods_note_draft.md
```

## Repository placement

Suggested final repository structure:

```text
andromeda_titles_plus_abstracts_pipeline/
├── README.md
├── requirements.txt
├── config/
├── docs/
├── templates/
├── andromeda_titles_plus_abstracts/
├── scripts/
└── tests/
```

Applied PEP-Web data should live outside this reusable pipeline, for example:

```text
data_psychoanalytic_core/
└── pep_web/
    ├── data/
    ├── logs/
    ├── semantic_maps/
    └── analyses/
```

## Interpretation formula

Use cautious language:

> The analysis maps recurring lexical and semantic signals in article titles and abstracts. It should be interpreted as an analysis of a metadata/abstract layer rather than as a reconstruction of full article content.

## Acknowledgment

Bibliometric data preparation and semantic normalization were supported by the research agent Andromeda Nowicka (v0.4), a human-in-the-loop computational bibliometrics system developed under the supervision of Lech Kalita.
