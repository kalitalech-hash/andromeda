# Psychoanalytic core — Stage 3 preliminary semantic mapping report

**Date:** 2026-05-31  
**Project:** Andromeda Nowicka / `data_psychoanalytic_core`  
**Stage:** Stage 3 — preliminary semantic family mapping and refined article-level application  
**Status:** preliminary semantic layer completed; interpretive use requires further audit

---

## 1. Purpose

This report documents the first semantic mapping stage of the `psychoanalytic_core` corpus.

After Stage 2 produced a cleaned and audited title+abstract vocabulary, Stage 3 created a first semantic-family map and applied it to the full `ART-only` title+abstract corpus.

The aim was not to produce a final ontology. The aim was to test whether broad psychoanalytic semantic families can detect meaningful differences:

```text
between journals
between historical periods
between initial broad lexical mapping and more conservative refined mapping
```

The central preliminary finding is that the corpus shows a robust diachronic pattern consistent with a **relational shift in psychoanalysis**.

This phrase is used cautiously. At this stage it means:

```text
a measurable title+abstract-level increase in relational / intersubjective / field-oriented semantic markers,
especially after 1990 and especially in Psychoanalytic Dialogues,
together with a relative decline in drive/conflict/defense markers after the postwar and late-20th-century periods.
```

---

## 2. Interpretive backbone added to the think tank

For the interpretive frame of the relational shift, the project added:

```text
Beebe, B. & Lachmann, F. (2003).
The Relational Turn in Psychoanalysis: A Dyadic Systems View from Infant Research.
Contemporary Psychoanalysis, 39(3), 379–409.
```

This article is not treated as a data source for the corpus counts. It is treated as a theoretical backbone for later interpretation.

The article is especially useful for the project because it frames the relational turn not merely as a change in clinical attitude or technique, but as a broader theoretical reorganization around:

```text
interaction
dyadic systems
self- and interactive regulation
co-construction
infant research
implicit procedural-emotional knowing
integration of inner and relational processes
```

This is closely aligned with what the refined semantic mapping is beginning to show empirically at the metadata/title+abstract level.

---

## 3. Main data inputs

The Stage 3 scripts used the following core inputs:

```text
data/title_abstract/keyness_final/psychoanalytic_core_discriminative_candidate_terms_final.csv
data/title_abstract/global/psychoanalytic_core_ART_title_abstract_clean.csv
```

The article-level corpus contains:

```text
12,164 ART-only records
title_clean
abstract_clean
text_for_analysis
journal_key
period
```

The periodization used at this stage remained:

```text
1920–1945
1946–1969
1970–1989
1990–2009
2010–2025
```

---

## 4. Scripts used in Stage 3

### 4.1 `3a_build_initial_semantic_families.py`

Purpose:

```text
build an initial semantic family map from final candidate terms
assign candidate terms to broad psychoanalytic semantic families
create review and unmapped queues
```

Main outputs:

```text
data/title_abstract/semantic/psychoanalytic_core_initial_semantic_map.csv
data/title_abstract/semantic/psychoanalytic_core_initial_semantic_map_review_queue.csv
data/title_abstract/semantic/psychoanalytic_core_unmapped_candidate_terms.csv
```

Important diagnostic result:

```text
initial map rows: 1,718 candidate terms
mapped terms: 310
unmapped terms: 1,408
```

Interpretation:

```text
The first semantic map was useful as a scaffold, but it was intentionally broad and incomplete.
The large unmapped queue shows that the ontology remains preliminary.
```

### 4.2 `3b_apply_semantic_map_to_articles.py`

Purpose:

```text
apply the initial semantic map to article-level title+abstract text
produce article-level semantic-family hit tables
summarize semantic family counts by journal and period
```

Key result:

```text
n_articles: 12,164
n_articles_with_any_semantic_family_hit: 11,743
pct_articles_with_any_semantic_family_hit: 96.539%
n_article_family_hit_rows: 52,187
n_families_with_terms: 17
```

Interpretation:

```text
The first lexical semantic map was broad enough to touch nearly the whole corpus.
However, because it counted broad terms such as self, object, mother, relationship, and Freud as full family hits, it required QA before interpretation.
```

### 4.3 `3c_semantic_family_QA.py`

Purpose:

```text
inspect which terms inflate broad semantic families
identify high-risk family markers
create a refinement queue
```

Key result:

```text
n_articles: 12,164
n_article_family_hit_rows: 52,187
n_term_hit_rows_exploded: 85,111
n_high_risk_term_rows: 43
n_refinement_queue_rows: 43
```

The QA identified broad or potentially inflationary terms such as:

```text
self
object
mother
relationship
social
early
Freud
```

Interpretation:

```text
These terms are not noise. They are psychoanalytically meaningful.
However, they should not by themselves carry the same evidentiary weight as more specific markers.
```

### 4.4 `3d_refine_semantic_map_marker_strength.py`

Purpose:

```text
add marker-strength distinctions to the semantic map
reapply the semantic map using stronger counting rules
separate weak-only and name-only marker hits from refined family hits
```

Marker classes:

```text
strong
medium
weak
name_marker
unmapped
```

Rules:

```text
strong marker alone → refined family hit
medium marker alone → refined family hit
weak marker alone → weak-only marker, not a refined family hit
2+ weak markers → provisional refined family hit
weak + name marker → provisional refined family hit
name marker alone → name-only marker, not a refined family hit
```

Key result:

```text
n_articles: 12,164
n_articles_with_refined_semantic_family_hit: 10,947
pct_articles_with_refined_semantic_family_hit: 89.9951%
n_articles_with_any_marker_hit: 11,743
pct_articles_with_any_marker_hit: 96.539%
```

Marker-strength map:

```text
unmapped: 1,408
strong: 200
medium: 61
weak: 44
name_marker: 5
```

Interpretation:

```text
The refined model remains broad enough to cover approximately 90% of the corpus,
but it no longer allows broad weak terms or name markers to inflate semantic families by themselves.
```

---

## 5. Semantic families used

The preliminary semantic families were:

```text
drive_conflict_defense
dream_fantasy_unconscious
ego_self_narcissism
object_relations
kleinian_bionian
winnicottian_environment_holding
attachment_development_infant
transference_countertransference
technique_interpretation_process
relational_intersubjective_field
trauma_dissociation_affect_regulation
psychosis_borderline_primitive_states
body_sexuality_gender
language_narrative_symbolization
culture_race_social_ethics
empirical_research_measurement
history_theory_schools
```

These families are not final. They are working categories used to test corpus-level and journal-level structure.

---

## 6. Initial versus refined semantic application

The initial application showed very high coverage:

```text
any initial family marker: 96.539%
```

The refined application produced more conservative coverage:

```text
refined family hit: 89.9951%
```

The reduction is methodologically important. It indicates that approximately:

```text
796 articles
```

had only weak or name-only semantic markers under the refined rules.

This is not a loss of data. It is a reduction of false certainty.

---

## 7. Differences between journals

The refined semantic application preserves strong journal differentiation.

### 7.1 IJPA

`IJPA` remains the most classical and historically deep journal profile.

Prominent families include:

```text
drive_conflict_defense
object_relations
dream_fantasy_unconscious
technique_interpretation_process
transference_countertransference
kleinian_bionian
```

Working interpretation:

```text
IJPA appears as the strongest carrier of classical, object-relational, technical,
and historically layered psychoanalytic vocabulary.
```

### 7.2 JAPA

`JAPA` preserves a classical core but is less strongly Klein/Bion-coded than IJPA.

Prominent families include:

```text
drive_conflict_defense
technique_interpretation_process
dream_fantasy_unconscious
ego_self_narcissism
attachment_development_infant
```

Working interpretation:

```text
JAPA appears as a classical American psychoanalytic profile with strong clinical,
ego/self, developmental, and technique-oriented components, but a weaker
Kleinian/Bionian signal.
```

### 7.3 Psychoanalytic Dialogues

`Psychoanalytic Dialogues` is the clearest relational journal in the corpus.

The strongest distinctive family is:

```text
relational_intersubjective_field
```

Additional strong families include:

```text
trauma_dissociation_affect_regulation
culture_race_social_ethics
```

Working interpretation:

```text
Psychoanalytic Dialogues appears as the clearest journal-level carrier of the relational shift.
Its profile remains robust after weak-marker correction, which is methodologically important.
```

### 7.4 Psychoanalytic Psychology

`Psychoanalytic Psychology` shows a distinct research-oriented and psychology-facing profile.

Prominent families include:

```text
empirical_research_measurement
relational_intersubjective_field
attachment_development_infant
trauma_dissociation_affect_regulation
```

Working interpretation:

```text
Psychoanalytic Psychology appears to connect psychoanalytic discourse with empirical,
developmental, relational, trauma, and psychological research vocabularies.
```

### 7.5 Psychoanalytic Psychotherapy

`Psychoanalytic Psychotherapy` shows a clinical-practice and research-oriented profile.

Prominent families include:

```text
empirical_research_measurement
relational_intersubjective_field
attachment_development_infant
psychosis_borderline_primitive_states
trauma_dissociation_affect_regulation
```

Working interpretation:

```text
Psychoanalytic Psychotherapy appears as a clinically practical and psychotherapy-oriented journal,
with notable attention to research/process language and severe clinical states.
```

---

## 8. Diachronic results: preliminary relational shift

The refined period analysis suggests three major axes of change.

### 8.1 Decline of drive/conflict/defense dominance

`drive_conflict_defense` is strongest before 1990 and declines afterward.

Working interpretation:

```text
The corpus shows a decline in the relative dominance of drive/conflict/defense language
after the postwar and late-20th-century periods.
```

This does not mean the family disappears. It remains a core psychoanalytic vocabulary. But its relative prominence decreases in later periods.

### 8.2 Rise of relational/intersubjective/field language

`relational_intersubjective_field` rises strongly after 1990 and remains high in 2010–2025.

Working interpretation:

```text
This is the clearest quantitative signal of a relational shift.
```

The key point is that this result survives marker-strength refinement. It is not merely the effect of the broad term `relationship`.

### 8.3 Rise of culture/race/social/ethics language

`culture_race_social_ethics` rises strongly in the most recent period.

Working interpretation:

```text
The latest period shows a marked widening of psychoanalytic discourse toward
culture, race, society, ethics, and political context.
```

This may represent a second, later expansion beyond the relational turn itself.

### 8.4 Trauma and affect regulation as sustained and rising vocabulary

`trauma_dissociation_affect_regulation` is not simply a late invention. It appears across periods but becomes more prominent in the most recent period.

Working interpretation:

```text
Trauma, affect, and regulation appear as a sustained strand that becomes more prominent in contemporary psychoanalytic discourse.
```

---

## 9. Relation to Beebe and Lachmann’s dyadic systems view

The empirical Stage 3 signal aligns well with the theoretical frame supplied by Beebe and Lachmann.

Their article describes psychoanalysis as moving toward an expanded theory of interaction and locates the relational turn at the center of that expansion. Their dyadic systems view emphasizes that self-regulation and interactive regulation should be understood together rather than by privileging either inner or relational processes.

For our project, this provides a strong interpretive bridge:

```text
Corpus signal:
  relational_intersubjective_field rises after 1990

Theoretical backbone:
  psychoanalysis increasingly conceptualizes clinical process through co-construction,
  dyadic regulation, interaction, implicit relational knowing, and the integration of
  inner and relational processes
```

The article is especially valuable because it avoids a simplistic replacement narrative.

It does not say:

```text
inner world disappears
```

Rather, it supports a model in which:

```text
inner and relational processes are simultaneous, reciprocal, and mutually organizing
```

This distinction is crucial for later interpretation of the corpus.

---

## 10. Methodological caution

The current semantic results are still preliminary.

Limitations:

```text
the semantic map is rule-based
many candidate terms remain unmapped
some families are broad
marker strength rules are provisional
article-level hits are lexical, not full interpretive readings
period effects may partly reflect journal composition
journal effects may partly reflect coverage years and editorial cultures
```

Therefore the current results should be framed as:

```text
preliminary title+abstract-level semantic evidence
```

not as final proof of theoretical transformation.

---

## 11. Recommended next steps

### 11.1 Compare initial and refined models formally

Recommended script:

```text
3e_compare_initial_vs_refined_semantics.py
```

Purpose:

```text
quantify how each family changed after marker-strength correction
identify families most affected by weak-marker filtering
document why the refined model is more conservative
```

### 11.2 Refine semantic map manually

Use:

```text
data/title_abstract/semantic_QA/psychoanalytic_core_semantic_QA_map_refinement_queue.csv
data/title_abstract/semantic_refined/psychoanalytic_core_semantic_map_marker_strength.csv
```

Manual review should focus first on:

```text
self
object
mother
relationship
social
early
Freud
```

### 11.3 Add a relational-shift analysis layer

Recommended future analysis:

```text
relational_intersubjective_field by period
relational_intersubjective_field by journal × period
relational vs drive/conflict/defense ratio
relational vs object-relations ratio
relational + culture/ethics combined contemporary expansion
```

Possible derived indicators:

```text
relational_shift_index
classical_conflict_index
contemporary_contextualization_index
```

### 11.4 Test journal-composition effects

Because the journal set is historically uneven, period effects should be checked with:

```text
within-journal temporal trends
journal-balanced period comparisons
IJPA-only long historical trend
post-1990 cross-journal comparison
```

---

## 12. Contribution record

### 12.1 Contribution by Lech Kalita

Lech Kalita directed the interpretive and methodological decisions of Stage 3.

His contributions included:

- recognizing the preliminary semantic results as evidence for a possible relational shift,
- identifying the need to treat broad psychoanalytic terms as meaningful but not sufficient by themselves,
- approving the marker-strength model rather than simply deleting broad terms,
- providing the Beebe and Lachmann article as a theoretical backbone for the relational-shift interpretation,
- framing the next interpretive direction around empirical testing of psychoanalytic discourse history,
- maintaining the distinction between computational signal and psychoanalytic interpretation.

### 12.2 Contribution by Andromeda Nowicka

Andromeda Nowicka supported Stage 3 as a human-in-the-loop computational bibliometrics and discourse-analysis agent.

Her contributions included:

- preparing the initial semantic-family mapping script,
- separating semantic-map construction from article-level application after the first implementation proved too heavy,
- preparing the semantic application script,
- preparing the semantic QA script,
- identifying family inflation by broad terms,
- preparing the marker-strength refinement script,
- interpreting the difference between initial and refined semantic application,
- connecting the refined results to the relational-shift hypothesis,
- preparing this Stage 3 preliminary semantic mapping report.

Andromeda’s role remains research support. Final psychoanalytic interpretation and scholarly argument remain under human supervision.

---

## 13. Status statement

Stage 3 has produced a usable preliminary semantic layer.

The strongest current finding is:

```text
A robust title+abstract-level relational shift signal is visible in the corpus,
especially after 1990 and especially in Psychoanalytic Dialogues.
```

This signal remains visible after marker-strength correction.

The project is now ready for:

```text
formal initial-vs-refined comparison
manual semantic-map refinement
relational-shift index construction
journal-balanced diachronic analysis
```
