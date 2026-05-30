# Psychoanalytic core — title/abstract reconnaissance and vocabulary audit report

**Date:** 2026-05-30 / 2026-05-31  
**Project:** Andromeda Nowicka / `data_psychoanalytic_core`  
**Stage:** Stage 2 — title/abstract text QA, vocabulary reconnaissance, and candidate-term audit  
**Status:** completed as a preliminary semantic-readiness layer

---

## 1. Purpose

This report documents the second major stage of the `psychoanalytic_core` project.

After the five-journal PEP-Web metadata harvest, global QA build, and abstract recovery, the project had a full `ART-only` title+abstract corpus. Stage 2 was designed to prepare this corpus for semantic analysis without yet imposing a final ontology.

The goal was to move from:

```text
article-level metadata with title and abstract
```

to:

```text
clean title/abstract text
→ vocabulary reconnaissance
→ term audit
→ discriminative vocabulary/keyness
→ refined candidate queue for semantic mapping
```

This stage is exploratory and diagnostic. It does not yet define final semantic families, interpret historical trends, or perform topic modeling.

---

## 2. Main input

The main input was the post-recovery ART-only title+abstract corpus:

```text
data_psychoanalytic_core/data/qa/global/psychoanalytic_core_articles_ART_only_with_abstracts.csv
```

This file contains:

```text
12,164 ART-only article records
100% recovered abstract_text coverage
five PEP-Web psychoanalytic journals
```

The five journals are:

```text
ijpa
japa
psychoanalytic_dialogues
psychoanalytic_psychology
psychoanalytic_psychotherapy
```

---

## 3. Conceptual role of Stage 2

Stage 2 was deliberately conservative.

It was not intended to decide the final semantic structure of the corpus. Instead, it was intended to answer the following questions:

```text
Is the title+abstract text usable?
Are there HTML, PEP, copyright, or layout artifacts?
What terms dominate the corpus globally?
Which terms are merely tautological background for a psychoanalytic corpus?
Which terms are technical artifacts or metadata noise?
Which terms distinguish journals?
Which terms distinguish periods?
Which terms should enter the first human-led semantic mapping stage?
```

The stage therefore separates three layers:

```text
raw or near-raw vocabulary evidence
audit decisions
candidate semantic queue
```

This keeps the pipeline auditable and avoids silently deleting terms.

---

## 4. Scripts used

Stage 2 consisted of five scripts.

### 4.1 `2a_title_abstract_recon.py`

Purpose:

```text
initial title/abstract cleaning
text QA
global vocabulary reconnaissance
per-journal vocabulary reconnaissance
period-based vocabulary reconnaissance
candidate-term queue
```

Main input:

```text
data/qa/global/psychoanalytic_core_articles_ART_only_with_abstracts.csv
```

Main outputs:

```text
data/title_abstract/global/psychoanalytic_core_ART_title_abstract_clean.csv
data/title_abstract/global/psychoanalytic_core_text_quality_summary.csv
data/title_abstract/global/psychoanalytic_core_text_quality_by_journal.csv
data/title_abstract/global/psychoanalytic_core_top_terms_global.csv
data/title_abstract/global/psychoanalytic_core_top_terms_by_journal.csv
data/title_abstract/global/psychoanalytic_core_candidate_terms_for_semantic_map.csv
data/title_abstract/by_journal/<journal_key>/
```

This script worked both globally and separately for each journal.

### 4.2 `2b_recon_audit_terms.py`

Purpose:

```text
first audit of high-frequency candidate terms
classification of obvious background and artifact terms
creation of explicit audit map
```

This stage marked terms such as:

```text
runninghead → technical_artifact
psychoanalytic / patient / clinical / treatment → background_domain_term
```

It did not modify raw `2a` outputs. It created a separate audit layer.

Main outputs:

```text
data/title_abstract/audit/term_recon_audit_map.csv
data/title_abstract/audit/psychoanalytic_core_candidate_terms_for_semantic_map_audited.csv
data/title_abstract/audit/psychoanalytic_core_candidate_terms_for_semantic_map_filtered.csv
data/title_abstract/audit/term_recon_background_terms.csv
data/title_abstract/audit/term_recon_artifacts.csv
data/title_abstract/audit/by_journal/<journal_key>/
```

### 4.3 `2c_discriminative_vocabulary_recon.py`

Purpose:

```text
move beyond raw frequency
identify discriminative terms by journal
identify discriminative terms by period
identify discriminative terms by journal × period
build a richer candidate pool for semantic mapping
```

This script used a simple, auditable keyness logic based on document percentage differences between a group and the rest of the corpus.

It produced global core terms after audit and key terms by journal, period, and journal-period cell.

Main outputs:

```text
data/title_abstract/keyness/psychoanalytic_core_terms_clean_for_keyness.csv
data/title_abstract/keyness/psychoanalytic_core_global_core_terms_after_audit.csv
data/title_abstract/keyness/psychoanalytic_core_global_core_bigrams_after_audit.csv
data/title_abstract/keyness/psychoanalytic_core_key_terms_by_journal.csv
data/title_abstract/keyness/psychoanalytic_core_key_bigrams_by_journal.csv
data/title_abstract/keyness/psychoanalytic_core_key_terms_by_period.csv
data/title_abstract/keyness/psychoanalytic_core_key_bigrams_by_period.csv
data/title_abstract/keyness/psychoanalytic_core_key_terms_by_journal_period.csv
data/title_abstract/keyness/psychoanalytic_core_key_bigrams_by_journal_period.csv
data/title_abstract/keyness/psychoanalytic_core_discriminative_candidate_terms.csv
```

### 4.4 `2d_refine_recon_vocabulary_audit.py`

Purpose:

```text
second-pass audit of the 2c discriminative vocabulary
remove additional generic discourse terms
remove affiliation and metadata noise
remove personal-name noise
protect theoretically meaningful psychoanalytic names
```

This stage responded to the observation that even after `2c`, lists still contained terms such as:

```text
time
study
life
author
concept
way
discussion
role
view
present
faculty
gmail
professor
center
john
robert
david
michael
```

The script introduced more specific audit categories:

```text
candidate_concept
background_domain_term
generic_academic_language
generic_discourse_language
affiliation_or_metadata_noise
personal_name_noise
technical_artifact
non_english_function_word
```

The script also protected theoretically meaningful names such as:

```text
freud
klein
bion
winnicott
lacan
kohut
fairbairn
ferenczi
bowlby
```

Main outputs:

```text
data/title_abstract/keyness_refined/term_refinement_audit_map.csv
data/title_abstract/keyness_refined/term_refinement_excluded_terms.csv
data/title_abstract/keyness_refined/term_refinement_candidate_concepts.csv
data/title_abstract/keyness_refined/psychoanalytic_core_global_core_terms_refined.csv
data/title_abstract/keyness_refined/psychoanalytic_core_key_terms_by_journal_refined.csv
data/title_abstract/keyness_refined/psychoanalytic_core_key_terms_by_period_refined.csv
data/title_abstract/keyness_refined/psychoanalytic_core_discriminative_candidate_terms_refined.csv
data/title_abstract/keyness_refined/psychoanalytic_core_vocabulary_recon_v3_summary.json
```

### 4.5 `2e_final_recon_cleanup.py`

Purpose:

```text
final light cleanup of residual generic/function/discourse terms after 2d
```

This stage targeted remaining low-information items such as:

```text
time
following
after
himself
since
```

and related temporal, connective, and generic terms.

This was not a new keyness calculation. It was a final cleanup layer applied to the already refined `2d` outputs.

Main outputs:

```text
data/title_abstract/keyness_final/term_final_cleanup_audit_map.csv
data/title_abstract/keyness_final/term_final_cleanup_removed_terms.csv
data/title_abstract/keyness_final/term_final_cleanup_candidate_terms.csv
data/title_abstract/keyness_final/psychoanalytic_core_global_core_terms_final.csv
data/title_abstract/keyness_final/psychoanalytic_core_global_core_bigrams_final.csv
data/title_abstract/keyness_final/psychoanalytic_core_key_terms_by_journal_final.csv
data/title_abstract/keyness_final/psychoanalytic_core_key_bigrams_by_journal_final.csv
data/title_abstract/keyness_final/psychoanalytic_core_key_terms_by_period_final.csv
data/title_abstract/keyness_final/psychoanalytic_core_key_bigrams_by_period_final.csv
data/title_abstract/keyness_final/psychoanalytic_core_discriminative_candidate_terms_final.csv
data/title_abstract/keyness_final/psychoanalytic_core_vocabulary_recon_v4_summary.json
```

---

## 5. Text quality results

The initial `2a` run completed successfully.

Key quality flags:

```text
n_records: 12,164
n_journals: 5
possible_html_artifact_rows: 0
possible_copyright_artifact_rows: 0
very_short_abstract_lt_80_chars: 10
```

Interpretation:

```text
The title+abstract corpus is technically usable.
No large HTML or copyright artifact problem was detected.
Only a very small number of abstracts are extremely short.
```

The main cleaned text file from this stage is:

```text
data/title_abstract/global/psychoanalytic_core_ART_title_abstract_clean.csv
```

This file contains:

```text
title_clean
abstract_clean
text_for_analysis
period
journal_key
word-count fields
artifact flags
```

---

## 6. Periodization used in Stage 2

The preliminary periodization used in the reconnaissance stage was:

```text
1920–1945
1946–1969
1970–1989
1990–2009
2010–2025
```

This periodization is provisional. It was used to make the first vocabulary comparison possible.

Later stages may compare it with:

```text
decade-based periodization
theory-informed periodization
empirically derived change-point periodization
keyword-coverage-based periodization
```

---

## 7. Important audit decisions

### 7.1 Background domain terms

The first top-frequency results naturally included terms that are true to the corpus but analytically weak as differentiating concepts.

Examples:

```text
psychoanalytic
psychoanalysis
patient
patients
clinical
treatment
therapy
analytic
analysis
analyst
process
```

These terms were not removed from raw output tables. They were flagged as background/domain terms and excluded from later candidate queues.

Rationale:

```text
They describe the corpus itself rather than differentiating its internal semantic structure.
```

### 7.2 Technical artifacts

The term:

```text
runninghead
```

was identified as a layout or extraction artifact and treated as:

```text
technical_artifact
```

### 7.3 Metadata and affiliation noise

Terms such as:

```text
faculty
gmail
professor
center
university
street
suite
london
york
```

were treated as:

```text
affiliation_or_metadata_noise
```

### 7.4 Personal-name noise

Common first names and author-name traces such as:

```text
john
robert
david
michael
```

were treated as:

```text
personal_name_noise
```

However, theoretically meaningful psychoanalytic names were protected and retained as candidate concepts.

Examples:

```text
freud
klein
bion
winnicott
lacan
kohut
fairbairn
ferenczi
bowlby
```

### 7.5 Generic discourse language

Generic terms such as:

```text
time
following
after
since
himself
way
role
view
issue
context
field
general
specific
important
```

were progressively removed from the candidate semantic queue.

Rationale:

```text
They may be linguistically frequent, but they do not yet define psychoanalytic semantic families.
```

---

## 8. Methodological interpretation

Stage 2 shows that raw frequency is insufficient for the next semantic step.

The first global frequency list contained many obvious or tautological terms. These are useful as QA evidence but not as semantic concepts.

The project therefore moved through several increasingly selective layers:

```text
2a: raw vocabulary reconnaissance
2b: first audit of background and artifact terms
2c: discriminative vocabulary/keyness
2d: refined audit of generic, metadata, and name noise
2e: final light cleanup of residual function/discourse terms
```

This sequence keeps the process auditable:

```text
nothing is silently deleted
raw outputs remain available
each exclusion is represented in an audit map
manual override columns are preserved
```

---

## 9. Current main output for Stage 3

The main input for the next semantic mapping stage is:

```text
data_psychoanalytic_core/data/title_abstract/keyness_final/psychoanalytic_core_discriminative_candidate_terms_final.csv
```

Supporting final files include:

```text
data_psychoanalytic_core/data/title_abstract/keyness_final/psychoanalytic_core_global_core_terms_final.csv
data_psychoanalytic_core/data/title_abstract/keyness_final/psychoanalytic_core_global_core_bigrams_final.csv
data_psychoanalytic_core/data/title_abstract/keyness_final/psychoanalytic_core_key_terms_by_journal_final.csv
data_psychoanalytic_core/data/title_abstract/keyness_final/psychoanalytic_core_key_terms_by_period_final.csv
data_psychoanalytic_core/data/title_abstract/keyness_final/psychoanalytic_core_key_terms_by_journal_period_final.csv
data_psychoanalytic_core/data/title_abstract/keyness_final/term_final_cleanup_audit_map.csv
```

---

## 10. Remaining limitations

Although Stage 2 is complete enough to move forward, some minor artifacts may remain.

This is acceptable at this stage because:

```text
the next step is still a human-led initial semantic mapping
remaining artifacts can be caught during family assignment
over-cleaning may remove meaningful psychoanalytic vocabulary
the audit maps preserve manual override paths
```

Known limitation:

```text
some generic words, names, or metadata fragments may still appear in low-frequency candidate lists
```

Planned response:

```text
capture remaining problems during Stage 3 semantic mapping and manual audit
```

---

## 11. Recommended next stage

The next step should be:

```text
3a_build_initial_semantic_families.py
```

Purpose:

```text
build a first auditable semantic family map from the final candidate queue
apply the map to article-level title/abstract text
produce first counts of semantic families by journal and period
create an audit queue for ambiguous or unmapped terms
```

Proposed initial semantic families include:

```text
drive_conflict_defense
ego_self_narcissism
object_relations
kleinian_bionian
winnicottian_environment_holding
attachment_development_infant
transference_countertransference
technique_interpretation_process
relational_intersubjective_field
trauma_dissociation_affect_regulation
body_sexuality_gender
psychosis_borderline_primitive_states
dream_fantasy_unconscious
language_narrative_symbolization
culture_race_social_ethics
empirical_research_measurement
```

Stage 3 should not be treated as final interpretation. It should produce the first explicit semantic map, with confidence flags and manual review fields.

---

## 12. Contribution record

### 12.1 Contribution by Lech Kalita

Lech Kalita directed the human review and audit logic for Stage 2.

His contributions included:

- confirming that the cleaned title+abstract corpus was ready for vocabulary reconnaissance,
- identifying that raw top-frequency terms were dominated by tautological background terms,
- pointing out that terms such as `psychoanalytic`, `patient`, and similar high-frequency words were not analytically informative,
- identifying `runninghead` as a technical artifact,
- noting that the same issue occurred globally and per journal,
- inspecting successive candidate-term files after `2b`, `2c`, and `2d`,
- identifying residual noise such as `time`, `following`, `after`, `himself`, and `since`,
- deciding when the vocabulary was sufficiently clean to stop iterating and move toward semantic mapping,
- preserving the methodological balance between cleaning and not over-cleaning psychoanalytic language.

### 12.2 Contribution by Andromeda Nowicka

Andromeda Nowicka supported Stage 2 as a human-in-the-loop computational bibliometrics and discourse-analysis agent.

Her contributions included:

- preparing the `2a` title/abstract reconnaissance script,
- designing global, per-journal, period, and journal-period output structures,
- preparing the `2b` audit script for background and artifact terms,
- preparing the `2c` discriminative vocabulary/keyness script,
- preparing the `2d` refined audit script for generic, metadata, affiliation, and name noise,
- preparing the `2e` final cleanup script,
- maintaining separate raw, audit, refined, and final layers,
- documenting the methodological distinction between raw frequency, keyness, and semantic mapping,
- preparing this Stage 2 report for repository documentation.

Andromeda’s role remains research support. Final psychoanalytic interpretation and scholarly framing remain under human supervision.

---

## 13. Status statement

Stage 2 is complete.

The project now has:

```text
a clean ART-only title+abstract corpus
global and per-journal vocabulary reconnaissance
period and journal-period keyness tables
audited background and artifact term maps
a refined final candidate queue for semantic mapping
```

The recommended next file for Stage 3 is:

```text
data_psychoanalytic_core/data/title_abstract/keyness_final/psychoanalytic_core_discriminative_candidate_terms_final.csv
```

The project is ready to begin initial semantic family mapping.
