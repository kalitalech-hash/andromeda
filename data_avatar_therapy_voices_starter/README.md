# Andromeda — AVATAR / voices / VR: strict harvest and QA v0.5

**Nie podmieniaj działającego `01_acquire_candidates.py` v0.4.** On already supports `--full`, checkpoints and resume. We add `02_strict_qa.py` and `03_descriptives.py`, preserving the original `02_qa_screen.py` and all raw data.

Copy the two scripts into `data_avatar_therapy_voices_starter/scripts/`.

From `data_avatar_therapy_voices_starter/` in PowerShell:

```powershell
python scripts/01_acquire_candidates.py --full --require-all-five --contact-email "REAL_EMAIL"
python scripts/02_strict_qa.py --input outputs/raw/avatar01_full_v04/raw_candidates.csv --output-dir outputs/qa/avatar01_full_strict_v05
python scripts/03_descriptives.py --input outputs/qa/avatar01_full_strict_v05/analysis_corpus_ABC.csv --output-dir outputs/analyses/avatar01_full_strict_v05
```

To exclude conference-only records and book reviews *in addition to* user-approved topical exclusion, add `--exclude-nonresearch-types` to stage 02. Otherwise they are flagged, not automatically removed.

Stage 02 output: `analysis_corpus_ABC.csv`, `screening_all_audited.csv`, `excluded_records.csv`, `duplicates.csv`, `qa_summary.json`, `transformation_log.json`, `methodological_note.md`. All outputs are **new layers**. Stage 03 output: `journal_layer_counts.csv`, `year_layer_counts.csv`, `type_layer_counts.csv`, `analysis_summary.json`, `methods_note.md`.

## Important limitations

- `--full` on 01 v0.4 means a **configured page-capped harvest**: 5 journals × 6 queries × at most 2 pages × 50 items. This is not exhaustive and cannot justify claiming a systematic literature search.
- `02_strict_qa.py` implements **conservative deterministic** rules using title+available abstract. A = avatar + voices + therapy; B = voices + relational/dialogue term; C = VR + psychosis + therapy. First matching wins A > B > C. Everything else is automatically excluded **from analysis**, but not deleted.
- This operationalizes the user's instruction to remove `manual_review`. It prioritizes precision over recall, potentially missing relevant papers (especially records without abstracts). You may want a later sensitivity/recall audit before submission.
- 'Relating to voices' is not identical to all psychological treatments of hallucinations. Rely on the explicit rule definitions in method descriptions.
- Stage 03 is a quick **descriptive sanity check**, not a final semantic network or discourse interpretation. Existing `andromeda_titles_plus_abstracts_pipeline` remains the correct downstream method.
- Keep `outputs/` out of public Git unless license / metadata redistribution rights are confirmed; share aggregate QC and derived features if possible.
