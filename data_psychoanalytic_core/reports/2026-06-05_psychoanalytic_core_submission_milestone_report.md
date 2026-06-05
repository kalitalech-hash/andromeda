# Psychoanalytic core — manuscript submission milestone report

**Date:** 2026-06-05  
**Project:** `data_psychoanalytic_core`  
**Milestone:** first blinded manuscript submission  
**Manuscript title:** *Changing Narratives of Psychoanalytic Clinical Reality: A Century of Title-and-Abstract Discourse Across Core Psychoanalytic Journals*  
**Status:** submitted / milestone closed  
**Prepared by:** Andromeda Nowicka (v0.4), HITL research-support agent  
**Human scholarly responsibility:** Lech Kalita  

---

## 1. Purpose of this report

This report closes the current `data_psychoanalytic_core` manuscript-preparation milestone. It documents the transition from a reproducible title-and-abstract semantic-mapping workflow to a first submitted blinded manuscript.

The submitted manuscript uses a corpus-derived, psychoanalytically informed, audit-controlled semantic mapping procedure to examine diachronic changes in the public conceptual vocabulary of five psychoanalytic journals.

The report is intended for placement in the project `reports` directory and should function as a compact audit note for future revisions, responses to reviewers, release notes, or a later Andromeda-methods paper.

---

## 2. Final manuscript submitted in this milestone

The submitted blinded manuscript is:

```text
Changing Narratives of Psychoanalytic Clinical Reality:
A Century of Title-and-Abstract Discourse Across Core Psychoanalytic Journals
```

The manuscript includes: Abstract, Introduction, Theoretical frame, Materials and methods, Results, Discussion, Limitations, Conclusion, Acknowledgment and data note, and References.

The final submitted abstract reports the core empirical findings:

```text
n = 12,164 article-level title-and-abstract records
5 psychoanalytic journals
17 working semantic families
relational shift index change: +44.30 points
drive/conflict/defense coverage change: -19.34 points
narrative reframing index change: +56.02 points
contemporary contextualization index change: +49.59 points
```

The main interpretive formulation is that the findings do not indicate the disappearance of classical psychoanalytic language, but rather the loss of its earlier organizing monopoly and the rise of relational, contextual, trauma-regulatory, social-ethical, and narrative-redescriptive vocabularies.

---

## 3. Corpus and data layer summarized in the manuscript

The analytic corpus was restricted to ART-level original article records.

```text
Initial consolidated metadata layer: 24,393 records
Final analytic corpus: 12,164 ART-level title-and-abstract records
Excluded non-ART records: reviews, commentaries, abstracts, reports, announcements, supplements, errata, and other non-ART material
```

Journals included:

```text
The International Journal of Psychoanalysis
Journal of the American Psychoanalytic Association
Psychoanalytic Dialogues
Psychoanalytic Psychology
Psychoanalytic Psychotherapy
```

Rationale for journal selection:

```text
IJPA:
  central international and historically oldest psychoanalytic journal

JAPA:
  major American institutional psychoanalytic journal

Psychoanalytic Dialogues:
  key voice of the relational turn

Psychoanalytic Psychology:
  bridge between psychoanalysis, psychology, and empirical/research-facing discourse

Psychoanalytic Psychotherapy:
  contemporary applied psychoanalytic therapy venue
```

The manuscript explicitly frames the data layer as a public layer of psychoanalytic self-description, not as a proxy for full clinical practice or complete article content.

---

## 4. Data acquisition and ethical framing

The manuscript uses a metadata-first acquisition model.

Current submitted formulation:

```text
Article metadata were obtained from PEP-Web’s metadata/API layer through authorized access.
The acquired fields included article identifiers, journal, year, article type, title, abstract, and related bibliographic metadata.
The project followed a metadata-first acquisition model.
The analysis used article metadata, titles, abstracts, article types, and publicly available metadata layers rather than a local full-text or PDF corpus.
No claims are made about full-text interpretation.
```

For blinded review, the repository URL is withheld. The manuscript states that project documentation, scripts, semantic maps, derived analytical tables, figures, and methodological reports are available in a public repository, with the URL to be supplied after acceptance.

Important boundary:

```text
Raw PEP-Web records, full texts, and PDFs are not redistributed.
The repository should contain scripts, semantic maps, aggregate/derived analytical outputs, figures, and reports only where permitted.
```

---

## 5. Semantic mapping approach

The semantic procedure is summarized in the manuscript as:

```text
clean title-and-abstract layer
→ candidate term extraction
→ psychoanalytically informed semantic-family design
→ term-to-family mapping
→ article-level semantic-family hits
→ QA for broad-marker inflation
→ marker-strength refinement
→ semantic-change indices
→ journal-level and balanced-panel robustness checks
```

The methodological formulation developed during this stage was:

```text
The vocabulary was corpus-derived.
The semantic architecture was psychoanalytically informed.
The mapping workflow was computationally implemented and audit-controlled.
```

The submitted manuscript presents semantic families as working analytical instruments, not as a final ontology of psychoanalytic theory.

---

## 6. Marker-strength model

The initial semantic map achieved very high coverage, but broad terms created inflation risk. The refined model introduced marker-strength categories:

```text
strong
medium
weak
name_marker
```

Broad but meaningful terms such as `self`, `object`, `mother`, `relationship`, and `Freud` were treated as signals but not allowed to count alone as full family evidence when their marker strength did not justify it.

Coverage reported in the manuscript:

```text
Initial semantic application: 11,743 / 12,164 articles = 96.54%
Refined semantic application: 10,947 / 12,164 articles = 90.00%
Any marker hit after refinement layer: 11,743 / 12,164 articles = 96.54%
```

Marker-strength count reported:

```text
unmapped: 1,408
strong: 200
medium: 61
weak: 44
name_marker: 5
```

The refined model is the primary interpretive layer.

---

## 7. Semantic families documented in the manuscript

The submitted manuscript reports 17 working semantic families:

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

The manuscript includes a compact table with example terms and global refined coverage. This table serves as the main transparency mechanism for readers asking what the semantic families contain.

---

## 8. Diachronic periods

The submitted manuscript groups articles into five historical periods:

```text
1920–1945
1946–1969
1970–1989
1990–2009
2010–2025
```

Rationale:

```text
balance historical interpretability with sufficient corpus size
separate early/classical consolidation
postwar and mid-century development
late twentieth-century transition
contemporary multi-journal period
```

Trend analyses use percentages relative to the number of ART records in each period rather than raw counts alone.

---

## 9. Main empirical findings

### 9.1 Global transformation

The core global result:

```text
drive/conflict/defense:
  43.44% in 1920–1945
  24.10% in 2010–2025
  change: -19.34 percentage points

relational/intersubjective/field:
  5.69% in 1920–1945
  30.64% in 2010–2025
```

The relational family overtakes drive/conflict/defense in the final period.

Composite index changes:

```text
relational shift index:
  -37.76 → +6.54
  change: +44.30 index points

narrative reframing index:
  -17.06 → +38.96
  change: +56.02 index points

contemporary contextualization index:
  18.95 → 68.54
  change: +49.59 index points
```

Interpretive conclusion:

```text
not disappearance of classical psychoanalytic language
not simple replacement
rather: reconfiguration of the semantic field
```

### 9.2 Periodization of the shift

The results support a three-phase interpretation:

```text
1920–1989:
  classical drive/conflict/defense and metapsychological dominance

1990–2009:
  transitional phase
  drive/conflict declines
  relational language rises
  narrative reframing index becomes positive

2010–2025:
  relational-contextual phase
  relational coverage exceeds drive/conflict/defense
  culture/social/ethics and trauma/affect/regulation rise substantially
```

### 9.3 Journal trajectories

All five journals show:

```text
increase in relational shift index
decrease in drive/conflict/defense
increase in narrative reframing
increase in contemporary contextualization
```

Journal-specific interpretation included in the manuscript:

```text
IJPA:
  long classical archive with gradual relational-contextual movement

JAPA:
  larger relational shift and stronger decline in classical metapsychology

Psychoanalytic Dialogues:
  most distinctive relational-contextual journal
  enters corpus already strongly relational

Psychoanalytic Psychology:
  relational-contextual change combined with research/psychology-facing profile

Psychoanalytic Psychotherapy:
  applied psychotherapy-process register with strong contextualization and narrative reframing
```

### 9.4 Robustness checks

Robustness diagnostics included:

```text
journal-vs-global diagnostics
within-journal first-to-last changes
equal-journal-weight trajectories
long-journal panel
common-period panel
post-1990 panel
direction-consistency checks across journals
```

Main conclusion:

```text
journal composition does not fully explain the result
the dominant directions persist across balanced and partially balanced comparisons
```

---

## 10. Theoretical framing used in the submitted manuscript

The theoretical frame combines:

```text
Roy Schafer:
  clinical facts as conceptualized within narratives and metanarratives
  multiple histories
  critique of common ground as mere shared terminology

Donna Orange:
  psychoanalytic language as historically burdened and ethically consequential
  responsibility for the language through which clinicians understand suffering

Wallerstein / Green / Bernardi:
  common ground, pluralism, and the debate over whether psychoanalysis can share a clinical language

Lament:
  useful untruths and the partiality of theoretical models

Karbelnig:
  pluralism as a structured clinical method and future condition of psychoanalytic vitality

Fulgencio:
  paradigms, incommensurability, redescription, and terminological ethics

Beebe & Lachmann:
  relational turn interpreted through dyadic systems and co-constructed inner-relational processes

Britton & Steiner:
  selected fact vs overvalued idea, used as a clinical counterpoint to simple constructivism
```

The main theoretical bridge:

```text
If clinical facts are narratively conceptualized,
and psychoanalytic words carry historical and ethical implications,
and traditions function as partially overlapping dialects,
then changes in published psychoanalytic vocabulary are not superficial.
They are part of how the discipline publicly reorganizes what it takes itself to be seeing, treating, and explaining.
```

---

## 11. Discussion-level interpretation

The submitted discussion emphasizes six points:

```text
1. No disappearance narrative:
   classical vocabulary remains strongly present; classical conflict language loses its earlier monopoly.

2. Relational-contextual turn:
   trauma/affect regulation, culture/ethics, and narrative-symbolic vocabularies rise alongside relational vocabulary.

3. Changing public metanarratives:
   the clinical object may remain recognizably continuous while the way it is made speakable changes substantially.

4. Language constructs and finds clinical facts:
   the manuscript avoids simple constructivism and asks both what language constructs and what language helps analysts find or crystallize.

5. Journals as discourse dialects:
   the field changes through journals, and journals change with the field.

6. Relevance of psychoanalysis:
   the findings support internal redescription rather than erosion of psychoanalytic identity.
```

---

## 12. Limitations documented in the manuscript

The submitted manuscript explicitly notes:

```text
title-and-abstract layer only
no full-text interpretation
semantic-family hits do not imply school membership
semantic families are working analytical categories, not final taxa
no independent expert-rater panel in this phase
journal composition reduced but not eliminated as a concern
changes in abstracting practices and editorial policies may affect results
continuity of clinical facts is a theoretical inference, not directly measured
```

Future work named:

```text
independent expert review of semantic family assignments
raters from different psychoanalytic traditions
further causal decomposition of journal composition effects
```

---

## 13. Figures and tables in the submitted manuscript

The submitted manuscript includes:

```text
Table 1:
  corpus semantic coverage and marker-strength counts

Table 2:
  working semantic families, example terms, and global refined coverage

Table 3:
  selected semantic-family coverage and semantic-change indices by period

Table 4:
  within-journal semantic trajectories

Table 5:
  direction consistency in balanced and partially balanced panels

Figure 1:
  drive/conflict/defense and relational/intersubjective/field vocabulary by period

Figure 2:
  narrative reframing and contemporary contextualization indices by period

Figure 3:
  semantic families most affected by marker-strength correction

Figure 4:
  within-journal changes in core semantic indices

Figure 5:
  journal distinctiveness from global period profile

Figure 6:
  refined global coverage of semantic families
```

A later revision may improve graphic typography, journal styling, or move some tables/figures to supplementary material depending on reviewer/editor feedback.

---

## 14. Acknowledgment and repository note

For the blinded submission, repository identity was withheld.

Submitted logic:

```text
Project documentation, scripts, semantic maps, derived analytical tables, figures, and methodological reports are available in a public repository.
The repository URL has been withheld for anonymous review and will be provided upon acceptance.
```

Andromeda acknowledgment submitted in blinded form:

```text
Bibliometric data preparation, title-and-abstract semantic mapping, and publication-output preparation were supported by the research agent Andromeda Nowicka (v0.4), a human-in-the-loop computational bibliometrics research-support system created by the author of this manuscript using OpenAI’s GPT-5.5 model.
Final scholarly interpretation and manuscript responsibility remain human-led.
```

Note for future non-blinded version:

```text
Replace blinded repository note with:
https://github.com/kalitalech-hash/andromeda
workspace: data_psychoanalytic_core
```

Suggested non-blinded data availability statement:

```text
Project documentation, scripts, semantic maps, derived analytical outputs, figures, and methodological reports are available in the public repository https://github.com/kalitalech-hash/andromeda, under data_psychoanalytic_core. Raw PEP-Web records, full texts, and PDFs are not redistributed because they are subject to source access conditions.
```

---

## 15. Minor issues noticed in the submitted manuscript for future revision

These are not milestone blockers, but should be corrected in a revision or resubmission:

```text
"Probably the weight..." could become "It is partly the weight..."
"Journals, in proposed view..." could become "In the view proposed here, journals..."
"The relational turn found in data..." could become "The relational turn observed in the data..."
"not only psychoanalysis became more relational..." could become "not only that psychoanalysis became more relational..."
"title-and-abstrct" typo in acknowledgment should become "title-and-abstract"
"esearch-support" typo should become "research-support"
Schafer publication year should be checked: manuscript uses Schafer (1995); confirm official year and citation metadata.
```

Decision taken during drafting:

```text
Minor US/UK spelling variation and some non-native stylistic traces were left intentionally for this stage, provided they do not obstruct meaning.
```

---

## 16. Milestone summary

This milestone transformed `data_psychoanalytic_core` from a reproducible analytical corpus into a submitted empirical-theoretical manuscript.

The work completed in this phase includes:

```text
final conceptual framing
integration of Schafer, Orange, pluralism literature, Beebe–Lachmann, and Britton–Steiner
final Methods formulation
metadata/API access description
bibliometric/science-mapping methodological anchoring
semantic-family transparency table
global, journal-level, and robustness result presentation
discussion and limitations
blinded repository/data note
Andromeda acknowledgment
cover letter
submission package preparation
```

The manuscript now functions as the first major publication-facing output of the `data_psychoanalytic_core` workspace.

---

## 17. Suggested next steps after milestone closure

Immediate next steps:

```text
commit this report to reports/
commit final submitted blinded PDF if appropriate and legally/project-wise acceptable
tag current repo state as manuscript-submission milestone
preserve scripts and derived outputs used in the submitted version
do not overwrite semantic maps or publication tables used for submission
```

Likely next scholarly steps:

```text
prepare response-to-reviewer workspace when reviews arrive
create a non-blinded repository/data availability note for accepted version
consider Zenodo DOI for the repo release
prepare Andromeda v0.5 release note after this project
develop a separate methodological paper on HITL semantic bibliometrics / Andromeda workflow
```

---

## 18. Closing note

The central outcome of this milestone is not only a submitted manuscript, but also a reusable demonstration of Andromeda’s intended research model:

```text
metadata-first acquisition
explicit data layers
conservative semantic mapping
human-in-the-loop interpretation
audit-controlled outputs
publication-facing tables and figures
clear distinction between computational support and scholarly responsibility
```

The project began as an exploration of whether psychoanalytic discourse change could be traced empirically at title-and-abstract level. It now has a full submitted manuscript and a reproducible project workspace capable of supporting future revisions, extensions, or methodological publications.
