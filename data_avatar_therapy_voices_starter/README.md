# Andromeda v0.5 — avatar therapy / voice-hearing: corpus reconnaissance

**Purpose:** narrow, auditable journal-scoped candidate search supporting a theoretical section of a clinical pilot article (78 participants). Not a systematic review and not a completed discourse map.

## Scope and safeguards

Five journals: *Schizophrenia Bulletin*, *Schizophrenia Research*, *Psychology and Psychotherapy: Theory, Research and Practice*, *Schizophrenia Bulletin Open*, *Psychosis*. They are a purposive ISPS-oriented sample, not the entirety of the AVATAR literature. Record major eligible works from other journals in a separate supplementary register. SJR/JCR quartiles need separate timestamped verification; they are not stored as verified facts here.

Working layers: A = avatar-mediated voice dialogue; B = psychological/relational approaches to hearing voices; C = broader VR and psychosis context. A and B should not be conflated. Text-based avatar systems and immersive VR are different modalities and require separate human coding. Do not infer effectiveness from discourse frequencies.

**Source:** OpenAlex works and source metadata only; no journal HTML crawling, full text, or PDF mirroring. Work-search may use indexing beyond title/abstract; therefore lexical relevance must be assessed from retrieved title/abstract and manually screened. The OpenAlex abstract field may be absent. Confirm API terms and reuse permissions before redistributing abstracts; do not commit raw third-party abstracts without permission.

## Usage

From project root:

```bash
python -m pip install -r requirements.txt
export ANDROMEDA_CONTACT_EMAIL='research-team@example.org' # replace with a real monitored address
python scripts/00_discover_sources.py --config config/corpus.json
```

Inspect `outputs/source_candidates.csv`; compare journal names and ISSNs to official sources. Insert five **verified** source IDs into `config/corpus.json` and set `source_ids_confirmed` to `true`. The script intentionally refuses collection until this review is done.

```bash
python scripts/01_acquire_candidates.py --config config/corpus.json
# Substitute the actual timestamped output filename:
python scripts/02_qa_screen.py --input outputs/raw/raw_candidates_YYYYMMDDTHHMMSSZ.csv
```

**Default initial limit:** 2 pages × 50 records per keyword per journal (not exhaustive). Dates 2009–2026 are provisional. The source IDs are left blank on purpose. Runs save new timestamped raw files/logs; do not overwrite older outputs. QA files should be saved in a separate run directory on repeated runs (`--output-dir`). Fetch rate is 3–8 seconds between calls and halts on HTTP 401/403/429/5xx. No retries on barriers. Do not use `example.org` as a real contact email.

Outputs: candidates, acquisition logs, source-review table, deduplicated candidate/review queue, duplicates log, missingness log, summary JSON and stage note. No statistics or network outputs until human inclusion, publication-type assessment, and source audit are complete. Later: feed approved metadata to `andromeda_titles_plus_abstracts_pipeline/` after mapping its expected fields.

## Screening decisions to capture

Record `human_include` (yes/no/uncertain), `human_layer` (A/B/C/out-of-scope), exclusion reason, relation to voice-hearing, technology modality (immersive VR versus screen avatar), publication type, trial/study ID, and confidence. Protocols, trial reports, follow-ups and reviews should remain individually identifiable rather than being interpreted as independent clinical trials.

## Reproducibility

Record date, source IDs and ISSNs, source API details, search terms, time window, page limits, total reported counts (future extension), missingness and decisions. Preserve raw files, QA, normalized metadata, mappings and analyses as separate layers. Methods should say 'in titles and abstracts of a purposively selected journal corpus'.
