# Psychoanalytic core — semantic change, journal/global dynamics, and pluralism think-tank report

**Date:** 2026-05-31  
**Project:** Andromeda Nowicka / `data_psychoanalytic_core`  
**Stage covered:** from Stage 3 comparison (`3e`) through Stage 4a–4b and new theoretical think-tank integration  
**Status:** semantic-change indices and journal-vs-global diagnostics completed; journal-balanced robustness check prepared but not yet run

---

## 1. Purpose

This report documents the work completed after the previous Stage 3 preliminary semantic mapping report.

The project moved from a refined semantic-family layer toward a broader analysis of psychoanalytic discourse change. The central goal was to avoid reducing the interpretation to a single “relational shift” claim and instead model a wider historical transformation:

```text
drive/conflict/defense dominance
→ relational / intersubjective / field language
→ social, cultural, ethical, trauma-regulatory, and narrative-contextual vocabularies
```

The interpretive frame was also expanded through a new set of theoretical articles concerning:

```text
pluralism
common ground
incommensurability
useful fictions
regional dialects
clinical and empirical evidence
psychoanalytic theory as changing narrative redescription
```

The main methodological development was the construction of semantic-change indices and journal/global comparison diagnostics.

---

## 2. Work completed since the previous report

The following components were completed:

```text
3e_compare_initial_vs_refined_semantics.py
4a_semantic_change_indices.py
4b_journal_vs_global_semantic_change.py
theoretical think-tank integration of pluralism/common-ground articles
```

The next script, `4c_journal_balanced_semantic_change.py`, has been prepared but not yet executed at the time of this report.

---

## 3. Stage 3e — initial vs refined semantic comparison

### 3.1 Purpose

`3e_compare_initial_vs_refined_semantics.py` formally compared two Stage 3 layers:

```text
semantic_application/   initial broad lexical model
semantic_refined/       marker-strength refined model
```

The comparison was intended to document the conservative effect of marker-strength correction.

### 3.2 Key result

Script output:

```text
global_family_rows: 17
journal_family_rows: 85
period_family_rows: 85
journal_period_family_rows: 289
pct_initial_any_hit: 96.539
pct_refined_hit: 89.9951
largest_drop_family: history_theory_schools
largest_drop_pct_points: 23.2654
```

### 3.3 Interpretation

The refined model preserved high corpus coverage while reducing overconfidence caused by broad or name-only markers.

The strongest drop was in:

```text
history_theory_schools
```

This was expected and methodologically healthy. The initial version of this family was strongly affected by name markers and broad historical-theoretical terms, especially names such as `Freud`.

### 3.4 Methodological consequence

The refined model became the main interpretive model. The initial model remains useful as:

```text
a sensitivity layer
a documentation of overbroad lexical capture
a comparison baseline showing why marker-strength correction was necessary
```

The project can now say that its key semantic trends are not simply artifacts of broad word matching.

---

## 4. Stage 4a — semantic change indices

### 4.1 Purpose

`4a_semantic_change_indices.py` widened the analytical frame beyond the relational shift. It constructed multiple semantic-change indices from the refined family coverage tables.

The aim was to model psychoanalytic discourse change as a multi-axis process.

### 4.2 Main outputs

```text
data/title_abstract/semantic_change/psychoanalytic_core_semantic_change_family_inputs.csv
data/title_abstract/semantic_change/psychoanalytic_core_semantic_change_indices_global.csv
data/title_abstract/semantic_change/psychoanalytic_core_semantic_change_indices_by_period.csv
data/title_abstract/semantic_change/psychoanalytic_core_semantic_change_indices_by_journal.csv
data/title_abstract/semantic_change/psychoanalytic_core_semantic_change_indices_by_journal_period.csv
data/title_abstract/semantic_change/psychoanalytic_core_semantic_change_journal_vs_global_period.csv
data/title_abstract/semantic_change/psychoanalytic_core_semantic_change_journal_distinctiveness.csv
data/title_abstract/semantic_change/psychoanalytic_core_semantic_change_narrative_table.csv
data/title_abstract/semantic_change/psychoanalytic_core_semantic_change_summary.json
```

### 4.3 Indices computed

The script computed the following families of indices:

```text
classical_drive_conflict_index
classical_metapsychology_index
object_relations_tradition_index
relational_shift_index
relational_process_index
contemporary_contextualization_index
social_ethical_turn_index
trauma_affect_regulation_index
clinical_severity_continuity_index
developmental_attachment_index
body_sexuality_gender_index
language_narrative_index
narrative_reframing_index
research_psychology_index
```

These are exploratory indicators rather than final psychometric scales.

### 4.4 Key result

Script output:

```text
n_period_rows: 5
n_journal_rows: 5
n_journal_period_rows: 17
relational_shift_index_change: 44.2983
drive_conflict_defense_change: -19.3414
narrative_reframing_index_change: 56.0184
```

### 4.5 Interpretation

The global diachronic signal is strong.

The corpus shows:

```text
strong increase in relational_shift_index
strong decrease in drive_conflict_defense
strong increase in narrative_reframing_index
```

This suggests not merely a rise in relational language but a broader transformation in the narrative grammar of psychoanalysis.

### 4.6 Period-level interpretation

The period-level structure can be summarized as:

```text
1920–1945      classical drive/conflict dominance
1946–1969      high classical/metapsychological consolidation
1970–1989      late classical dominance / transitional build-up
1990–2009      mixed transitional profile
2010–2025      relational-contextual narrative profile
```

The strongest shift occurs after 1990.

### 4.7 Broader interpretive frame

The result is not:

```text
drive theory disappears
```

A better formulation is:

```text
classical drive/conflict/defense language remains present,
but loses its earlier monopoly as the organizing grammar of psychoanalytic discourse.
```

The project is therefore not simply documenting the rise of relational psychoanalysis. It is documenting a broader reorganization of psychoanalytic ways of narrating clinical reality.

---

## 5. Stage 4b — journal vs global semantic change

### 5.1 Purpose

`4b_journal_vs_global_semantic_change.py` tested whether the global semantic trend could be reduced to changing journal composition.

The key question was:

```text
Is the observed change corpus-wide,
or is it driven mainly by the entry and influence of specific journals?
```

### 5.2 Main outputs

```text
data/title_abstract/semantic_change_journal_global/psychoanalytic_core_journal_vs_global_index_deviations.csv
data/title_abstract/semantic_change_journal_global/psychoanalytic_core_within_journal_temporal_change.csv
data/title_abstract/semantic_change_journal_global/psychoanalytic_core_direction_consistency_by_index.csv
data/title_abstract/semantic_change_journal_global/psychoanalytic_core_journal_period_distinctiveness_ranked.csv
data/title_abstract/semantic_change_journal_global/psychoanalytic_core_journal_contribution_diagnostics.csv
data/title_abstract/semantic_change_journal_global/psychoanalytic_core_journal_trajectory_summary.csv
data/title_abstract/semantic_change_journal_global/psychoanalytic_core_global_vs_journal_semantic_change_summary.json
```

### 5.3 Key finding

The major directions of change are consistent across journals.

In all five journals:

```text
relational_shift_index increases
classical_drive_conflict_index decreases
contemporary_contextualization_index increases
social_ethical_turn_index increases
trauma_affect_regulation_index increases
narrative_reframing_index increases
```

This is a strong robustness signal.

### 5.4 Interpretation

The global trend cannot be dismissed as merely:

```text
the appearance of Psychoanalytic Dialogues
or
a simple change in the composition of the corpus
```

Psychoanalytic Dialogues strongly amplifies and condenses the relational-contextual trend, but it does not create the trend alone.

### 5.5 Journal profiles

#### IJPA

IJPA is the most important long-historical test. It spans all five periods and still shows:

```text
relational_shift_index increase
classical_drive_conflict_index decrease
contemporary_contextualization_index increase
narrative_reframing_index increase
```

This is crucial because IJPA is the strongest evidence that the shift is not only caused by newer journals.

#### JAPA

JAPA shows a strong decline in classical metapsychological dominance and a substantial increase in narrative reframing. It may represent a more dramatic American trajectory away from classical metapsychology than IJPA.

#### Psychoanalytic Dialogues

Psychoanalytic Dialogues remains the most distinctive journal. It is not merely “more relational”; it is structurally different from the global period profile. It strongly intensifies:

```text
relational_shift_index
contemporary_contextualization_index
narrative_reframing_index
```

#### Psychoanalytic Psychology

Psychoanalytic Psychology combines relational/contextual change with a stronger empirical/research/psychology profile.

#### Psychoanalytic Psychotherapy

Psychoanalytic Psychotherapy shows a clinical-practical and research/process-oriented variant of the broader transformation.

### 5.6 Working conclusion from 4b

The best current formulation is:

```text
The corpus shows a broad field-level semantic transformation,
but each journal narrates this transformation in a distinct dialect.
```

Or more compactly:

```text
The global shift is real, but journal cultures shape its tempo, intensity, and vocabulary.
```

---

## 6. Theoretical think-tank integration

A new set of articles was added to the interpretive think tank.

These texts are strongly aligned with the project, but they are primarily theoretical, epistemological, and programmatic. Their limitation is that they do not provide a large-scale diachronic corpus test.

The current project can contribute precisely this missing empirical layer.

### 6.1 Claudia Lament — “Useful Untruths”

Lament develops the idea of psychoanalytic theories as useful fictions or useful untruths. Her argument supports the view that theories do not simply mirror clinical reality. They organize attention, shape what can be seen, and help clinicians act under conditions of complexity.

Relevance to the corpus:

```text
Our semantic families can be interpreted as historically changing useful fictions:
ways of making clinical material intelligible at different moments in psychoanalytic history.
```

### 6.2 Jiménez and Altimir — “Beyond the hermeneutic/scientific controversy”

Jiménez and Altimir argue for an empirically sensitive research paradigm that goes beyond the sterile opposition between hermeneutics and science. They emphasize:

```text
interdisciplinary dialogue
empirical research
dyadic construction of experience
implicit and explicit levels of the analytic relationship
intersubjective process
```

Relevance to the corpus:

```text
Our work is an example of an empirically sensitive, metadata-first, discourse-level method
that does not reduce psychoanalysis to simple measurement but also does not remain purely speculative.
```

### 6.3 Alan Karbelnig — “Chasing Infinity”

Karbelnig argues that psychoanalysis cannot be unified by a single overarching metapsychology. He proposes a structured clinical pluralism in which psychoanalytic theories function as:

```text
theoretical metaphors
controlling fictions
useful untruths
regional dialects
```

Relevance to the corpus:

```text
Our journal profiles can be interpreted as empirical traces of regional dialects:
different journals organize psychoanalytic discourse through different semantic emphases.
```

### 6.4 Leopoldo Fulgencio — “Incommensurability between paradigms”

Fulgencio uses Kuhnian paradigm theory to analyze psychoanalytic theoretical systems. His key point for this project is that different theories may redescribe similar phenomena in different conceptual languages.

Relevance to the corpus:

```text
This is one of the strongest theoretical supports for our Schafer-adjacent hypothesis:
the clinical object may remain partly continuous, while the narrative and conceptual redescription changes.
```

### 6.5 Ricardo Bernardi — “A Common Ground in Clinical Discussion Groups”

Bernardi argues for a partial and dynamic clinical common ground. Agreement is more plausible at the level of clinical resonance and observation than at the level of abstract metapsychology.

Relevance to the corpus:

```text
Our project can be read as a macro-level complement to this idea:
even when journals differ theoretically, their discourses may orbit a shared clinical field,
while narrating it through different semantic systems.
```

### 6.6 Ricardo Bernardi — “What Kind of Discipline is Psychoanalysis?”

Bernardi argues for methodological pluralism, triangulation, consilience, and the use of multiple kinds of evidence.

Relevance to the corpus:

```text
This provides methodological legitimacy for Andromeda’s approach:
corpus-level title/abstract evidence does not replace clinical interpretation,
but adds a new evidentiary layer to psychoanalytic self-understanding.
```

---

## 7. What these articles lack — and what the project adds

The uploaded articles provide strong theoretical arguments about:

```text
pluralism
fragmentation
incommensurability
common ground
useful fictions
clinical dialects
research and hermeneutics
```

But they largely lack:

```text
large-scale historical data
journal-level comparison
diachronic measurement
auditable semantic mapping
corpus-wide evidence for shifts in theoretical vocabulary
```

The `psychoanalytic_core` project adds:

```text
12,164 ART-only title+abstract records
five psychoanalytic journals
approximately one century of historical coverage
refined semantic-family mapping
marker-strength correction
period, journal, and journal-period analysis
semantic-change indices
journal/global comparison diagnostics
```

Therefore the relationship is:

```text
The think-tank texts supply the theoretical vocabulary.
The corpus supplies empirical diachronic evidence.
```

Or, more strongly:

```text
They theorize pluralism.
We can measure its historical traces.
```

---

## 8. Emerging article argument

The emerging argument is broader than a simple “relational shift.”

A possible formulation:

```text
Over the last century, psychoanalytic journals show a measurable transformation
from a drive/conflict/defense-centered narrative grammar toward a plural,
relational, contextual, trauma-regulatory, and narrative-hermeneutic discourse.
This transformation is not uniform: journals preserve distinct dialects,
but the broad direction of change is visible across the field.
```

A Schafer-adjacent version:

```text
The clinical object of psychoanalysis remains recognizably continuous,
but the preferred narrative grammar through which it is described changes substantially.
```

A pluralism/common-ground version:

```text
Psychoanalysis appears not as one unified metapsychology,
but as a field of historically changing dialects organized around overlapping clinical concerns.
```

A methodological version:

```text
Corpus-based semantic analysis can give empirical form to debates that have usually remained theoretical:
pluralism, common ground, incommensurability, and the changing status of psychoanalytic theory.
```

---

## 9. Current state of the empirical evidence

At this stage the strongest evidence is:

```text
1. refined semantic-family coverage remains high after marker-strength correction
2. relational_shift_index increases strongly across the full period range
3. drive_conflict_defense decreases substantially
4. narrative_reframing_index increases strongly
5. contemporary_contextualization_index increases strongly
6. the direction of change is consistent across all five journals
7. Psychoanalytic Dialogues strongly intensifies but does not solely produce the shift
8. IJPA confirms that the shift is visible even in the long classical archive
```

The strongest methodological vulnerability remains:

```text
journal composition effects
```

This is why the next step is `4c_journal_balanced_semantic_change.py`.

---

## 10. Prepared next step: 4c

`4c_journal_balanced_semantic_change.py` has been prepared.

Its purpose is to run stricter robustness checks by comparing:

```text
equal-journal-weight period trajectories
long-journal panel
common-period panel
post-1990 multi-journal panel
paired within-journal changes
direction consistency under balanced or partially balanced conditions
```

Expected interpretive question:

```text
Does the semantic change survive when journal composition is partially controlled?
```

This is the next major empirical test before moving to publication-oriented figures and tables.

---

## 11. Contribution record

### 11.1 Contribution by Lech Kalita

Lech Kalita directed the theoretical expansion of the project after the Stage 3 report.

His contributions included:

- correcting the interpretive frame so that the project does not reduce itself to “relational shift”;
- emphasizing the importance of drive/conflict/defense decline;
- foregrounding the distinction between whole-corpus dynamics and journal-specific trajectories;
- introducing Orange and Schafer as additional interpretive anchors beyond Beebe and Lachmann;
- formulating the key idea that psychoanalysis may retain a relatively stable pool of clinical facts while radically changing the narratives used to describe them;
- supplying additional think-tank articles on pluralism, common ground, incommensurability, and psychoanalytic theory;
- directing the move toward journal-balanced robustness testing.

### 11.2 Contribution by Andromeda Nowicka

Andromeda Nowicka supported the project as a human-in-the-loop computational bibliometrics and discourse-analysis agent.

Her contributions included:

- preparing `3e_compare_initial_vs_refined_semantics.py`;
- interpreting the conservative effect of marker-strength correction;
- preparing `4a_semantic_change_indices.py`;
- designing multi-axis semantic-change indices beyond the relational-shift frame;
- preparing `4b_journal_vs_global_semantic_change.py`;
- interpreting journal/global diagnostics;
- preparing `4c_journal_balanced_semantic_change.py`;
- reading and integrating the newly supplied think-tank articles into the project frame;
- preparing this report for repository documentation.

Andromeda’s role remains research support. Final psychoanalytic interpretation and scholarly argument remain under human supervision.

---

## 12. Status statement

The project now has:

```text
a refined semantic-family layer
a formal initial-vs-refined comparison
multi-axis semantic-change indices
journal-vs-global semantic diagnostics
a strengthened theoretical think-tank around pluralism and narrative redescription
a prepared journal-balanced robustness script
```

The next empirical step is:

```text
python 4c_journal_balanced_semantic_change.py
```

The next interpretive question is:

```text
Does the broad semantic transformation remain visible after journal-balanced robustness checks?
```
