# Psychoanalytic core — Stage 4 semantic change and robustness report

**Date:** 2026-05-31  
**Project:** Andromeda Nowicka / `data_psychoanalytic_core`  
**Stage covered:** Stage 4a–4c  
**Status:** semantic-change indices, journal/global diagnostics, and journal-balanced robustness checks completed

---

## 1. Purpose

This report summarizes Stage 4 of the `psychoanalytic_core` project.

Stage 3 produced a refined semantic-family layer. Stage 4 moved from semantic-family coverage to higher-level semantic-change diagnostics.

The guiding question was:

```text
Has psychoanalytic discourse changed over the last century,
and if so, is this change visible across journals rather than reducible to
journal composition effects?
```

The project deliberately avoided reducing the result to a simple “relational shift” narrative. Instead, Stage 4 examined several linked axes:

```text
decline of drive/conflict/defense dominance
rise of relational/intersubjective/field language
rise of contextual, social, ethical, trauma-regulatory, and narrative vocabularies
journal-specific dialects of psychoanalytic discourse
global corpus change versus journal-level change
robustness of the observed trend under balanced comparisons
```

---

## 2. Scripts included in this stage

Stage 4 currently includes:

```text
4a_semantic_change_indices.py
4b_journal_vs_global_semantic_change.py
4c_journal_balanced_semantic_change.py
```

The scripts use the refined semantic layer produced by Stage 3:

```text
data/title_abstract/semantic_refined/
```

and produce the following directories:

```text
data/title_abstract/semantic_change/
data/title_abstract/semantic_change_journal_global/
data/title_abstract/semantic_change_balanced/
```

---

## 3. Stage 4a — semantic change indices

### 3.1 Purpose

`4a_semantic_change_indices.py` created a set of exploratory semantic-change indices.

The aim was to translate refined semantic-family percentages into interpretable indicators of discourse change.

### 3.2 Core indices

The script computed, among others:

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

These indices are exploratory composites, not final psychometric constructs.

### 3.3 Key output

The script returned:

```text
n_period_rows: 5
n_journal_rows: 5
n_journal_period_rows: 17
relational_shift_index_change: 44.2983
drive_conflict_defense_change: -19.3414
narrative_reframing_index_change: 56.0184
```

### 3.4 Interpretation

The global corpus shows a strong semantic transformation:

```text
relational_shift_index strongly increases
drive_conflict_defense substantially decreases
narrative_reframing_index strongly increases
```

The change is not merely “more relational language.” It looks more like a broader change in the grammar of psychoanalytic discourse:

```text
from drive/conflict/defense-centered narration
toward relational, contextual, trauma-regulatory, social-ethical,
and narrative-symbolic modes of description
```

### 3.5 Period-level interpretation

The period-level pattern can be summarized as:

```text
1920–1945      classical drive/conflict dominance
1946–1969      high classical/metapsychological consolidation
1970–1989      late classical dominance with transitional build-up
1990–2009      mixed transitional profile
2010–2025      relational-contextual narrative profile
```

The strongest historical transition appears after 1990.

---

## 4. Stage 4b — journal vs global semantic change

### 4.1 Purpose

`4b_journal_vs_global_semantic_change.py` tested whether the global pattern might be reducible to changing journal composition.

The key question was:

```text
Is the semantic transformation visible within journals,
or only in the aggregate corpus?
```

### 4.2 Main outputs

```text
data/title_abstract/semantic_change_journal_global/psychoanalytic_core_journal_vs_global_index_deviations.csv
data/title_abstract/semantic_change_journal_global/psychoanalytic_core_within_journal_temporal_change.csv
data/title_abstract/semantic_change_journal_global/psychoanalytic_core_direction_consistency_by_index.csv
data/title_abstract/semantic_change_journal_global/psychoanalytic_core_journal_period_distinctiveness_ranked.csv
data/title_abstract/semantic_change_journal_global/psychoanalytic_core_journal_contribution_diagnostics.csv
data/title_abstract/semantic_change_journal_global/psychoanalytic_core_journal_trajectory_summary.csv
data/title_abstract/semantic_change_journal_global/psychoanalytic_core_global_vs_journal_semantic_change_summary.json
```

### 4.3 Key result

The main directions of change were consistent across all five journals:

```text
relational_shift_index increases
classical_drive_conflict_index decreases
contemporary_contextualization_index increases
social_ethical_turn_index increases
trauma_affect_regulation_index increases
narrative_reframing_index increases
```

### 4.4 Interpretation

This result strongly weakens the simple composition-effect objection.

The pattern is not adequately explained by saying:

```text
Psychoanalytic Dialogues appears, therefore the corpus becomes relational.
```

A better formulation is:

```text
Psychoanalytic Dialogues intensifies and condenses the relational-contextual shift,
but the broader direction of change is visible across the journal field.
```

### 4.5 Journal-specific trajectories

#### IJPA

IJPA is crucial because it spans the longest historical range. It shows the same broad direction of change, although more gradually than the aggregate corpus.

Working interpretation:

```text
IJPA confirms that semantic change is visible even inside the long classical archive.
```

#### JAPA

JAPA shows a strong decline in classical metapsychological dominance and a substantial increase in narrative reframing.

Working interpretation:

```text
JAPA may represent a more dramatic American transition away from classical metapsychological dominance.
```

#### Psychoanalytic Dialogues

Psychoanalytic Dialogues remains the most distinctive journal and the strongest carrier of relational-contextual discourse.

Working interpretation:

```text
PD does not create the global trend alone, but radicalizes and crystallizes it.
```

#### Psychoanalytic Psychology

Psychoanalytic Psychology combines relational/contextual language with empirical, research, and psychology-facing vocabulary.

#### Psychoanalytic Psychotherapy

Psychoanalytic Psychotherapy shows a clinical-practical, process-oriented, and research-sensitive variant of the broader shift.

---

## 5. Stage 4c — journal-balanced robustness checks

### 5.1 Purpose

`4c_journal_balanced_semantic_change.py` provided a stricter test of the main semantic-change claim.

The question was:

```text
Does the observed semantic change survive when we partially control for journal composition?
```

The script created several robustness views:

```text
equal-journal-weight period trajectory
long-journal panel
common-period panel
post-1990 multi-journal panel
paired within-journal changes
direction consistency under balanced or partially balanced conditions
```

### 5.2 Main outputs

```text
data/title_abstract/semantic_change_balanced/psychoanalytic_core_balanced_equal_journal_weight_by_period.csv
data/title_abstract/semantic_change_balanced/psychoanalytic_core_balanced_global_vs_equal_weight.csv
data/title_abstract/semantic_change_balanced/psychoanalytic_core_balanced_long_journal_panel.csv
data/title_abstract/semantic_change_balanced/psychoanalytic_core_balanced_common_period_panel.csv
data/title_abstract/semantic_change_balanced/psychoanalytic_core_balanced_post1990_panel.csv
data/title_abstract/semantic_change_balanced/psychoanalytic_core_balanced_paired_period_changes.csv
data/title_abstract/semantic_change_balanced/psychoanalytic_core_balanced_direction_consistency.csv
data/title_abstract/semantic_change_balanced/psychoanalytic_core_balanced_semantic_change_summary.json
```

### 5.3 Equal-journal-weight result

The equal-journal-weight trajectory preserved the major global trends:

```text
relational_shift_change_equal_weight: +44.846
drive_conflict_change_equal_weight: -20.2778
narrative_reframing_change_equal_weight: +54.8227
```

This is very close to the global article-weighted result from 4a:

```text
relational_shift_index_change: +44.2983
drive_conflict_defense_change: -19.3414
narrative_reframing_index_change: +56.0184
```

Interpretation:

```text
The major semantic-change pattern does not depend strongly on article-weighted journal composition.
```

### 5.4 Long-journal panel

The long-journal panel included the journals with sufficient historical depth:

```text
IJPA
JAPA
```

In this panel:

```text
relational_shift_index increases
classical_drive_conflict_index decreases
narrative_reframing_index increases
contemporary_contextualization_index increases
```

in both journals.

Interpretation:

```text
The shift is visible in the long classical archive and not only in recently added journals.
```

### 5.5 Common-period panel

The common-period panel covered:

```text
1970–1989
1990–2009
2010–2025
```

and included all five journals.

The direction of change remained consistent:

```text
relational_shift_index increases in 5/5 journals
classical_drive_conflict_index decreases in 5/5 journals
narrative_reframing_index increases in 5/5 journals
contemporary_contextualization_index increases in 5/5 journals
```

Interpretation:

```text
The trend remains visible under a more comparable multi-journal structure.
```

### 5.6 Post-1990 panel

The post-1990 panel compared:

```text
1990–2009
2010–2025
```

In this contemporary multi-journal panel, all five journals showed:

```text
relational_shift_index increase
classical_drive_conflict_index decrease
narrative_reframing_index increase
contemporary_contextualization_index increase
social_ethical_turn_index increase
```

Interpretation:

```text
The semantic transformation continues within the contemporary multi-journal era.
```

This is important because it suggests that the change is not exhausted by the entry of newer journals into the corpus.

---

## 6. What 4c strengthens

Stage 4c strengthens the claim that the semantic transformation is not reducible to journal composition.

A cautious formulation:

```text
Journal composition contributes to the observed field-level pattern,
but balanced and within-journal diagnostics indicate that the main direction
of change is also visible within journal trajectories.
```

A stronger working formulation:

```text
The semantic transformation is field-level, but journal cultures shape its dialects.
```

---

## 7. What remains less stable

Not all indices behave as cleanly as the main axes.

Less stable or more heterogeneous indices include:

```text
object_relations_tradition_index
developmental_attachment_index
body_sexuality_gender_index
research_psychology_index
relational_process_index
```

This is theoretically useful. It suggests that the field is not simply moving from one homogeneous vocabulary to another.

For example:

```text
relational_shift_index increases,
but relational_process_index does not always move in the same direction.
```

This indicates that the shift is not just “more clinical process language.” It is a more specific movement toward relational, intersubjective, contextual, and narrative reframing.

---

## 8. Main empirical argument after 4a–4c

The strongest current empirical argument is:

```text
In a century-scale corpus of psychoanalytic journal articles,
there is a robust semantic transformation from drive/conflict/defense-centered
discourse toward relational, contextual, trauma-regulatory, and narrative-reframing vocabularies.

This transformation is visible globally, within journals, and under partially balanced
journal-composition checks.

Psychoanalytic Dialogues intensifies the transformation, but does not produce it alone.
```

---

## 9. Relation to the theoretical think tank

The Stage 4 findings align strongly with the think-tank frame.

### 9.1 Beebe and Lachmann

Beebe and Lachmann support the relational/dyadic systems side of the interpretation.

Our data suggest:

```text
the relational turn is visible not only as a theoretical proposition,
but as a measurable semantic shift in the journal corpus.
```

### 9.2 Orange

Orange supports the ethical, hermeneutic, contextual, and intersubjective expansion of psychoanalysis.

Our data suggest:

```text
the later corpus increasingly speaks in contextual, social, ethical,
and relational terms.
```

### 9.3 Schafer

Schafer supports the narrative-reframing interpretation.

Our data suggest:

```text
the clinical object of psychoanalysis may remain recognizably continuous,
but the preferred narrative grammar used to describe it changes substantially.
```

### 9.4 Pluralism / common ground / incommensurability literature

The newly integrated articles by Lament, Jiménez and Altimir, Karbelnig, Fulgencio, and Bernardi support the broader epistemological frame.

They theorize:

```text
useful fictions
regional dialects
pluralism
common ground
incommensurability
clinical and empirical evidence
```

The corpus adds:

```text
diachronic evidence for how these dialects and redescription patterns change over time.
```

---

## 10. Methodological caution

The results are strong but still require caution.

Current limitations:

```text
semantic families are rule-based and provisional
indices are exploratory composites
title+abstract data do not equal full clinical theory
journal composition is reduced but not fully eliminated as a concern
article type, abstract conventions, and editorial practices may affect results
semantic continuity of clinical phenomena is inferred, not directly observed
```

The strongest defensible phrasing is:

```text
The corpus provides title-and-abstract-level evidence for a broad semantic transformation
in psychoanalytic journal discourse.
```

not:

```text
The corpus proves how psychoanalytic clinical practice changed.
```

---

## 11. Publication-oriented implications

The project is now ready to begin publication-facing tables and figures.

Recommended first outputs:

```text
Figure 1. Global semantic change indices by period
Figure 2. Relational shift vs drive/conflict/defense by period
Figure 3. Initial vs refined semantic model comparison
Figure 4. Journal trajectories of relational_shift_index
Figure 5. Equal-journal-weight vs article-weighted global trajectory
Table 1. Corpus composition by journal and period
Table 2. Semantic family definitions and marker-strength rules
Table 3. Stage 4 indices and formulas
Table 4. Direction consistency across journals and balanced panels
```

The most important figure for the article will likely be:

```text
relational_shift_index and drive_conflict_defense by period,
with article-weighted and equal-journal-weight trajectories compared.
```

This would directly show both the substantive finding and the robustness check.

---

## 12. Recommended next step

The next stage should be:

```text
5a_publication_tables_and_figures.py
```

Purpose:

```text
create clean publication-ready CSVs and first figures from 4a–4c outputs
```

Suggested output directory:

```text
data/title_abstract/publication_outputs/
```

Suggested first outputs:

```text
publication_table_semantic_indices_by_period.csv
publication_table_direction_consistency.csv
publication_table_journal_trajectories.csv
publication_figure_semantic_change_by_period.png
publication_figure_relational_vs_drive_conflict.png
publication_figure_journal_relational_trajectories.png
publication_figure_equal_weight_vs_global.png
publication_outputs_summary.json
```

---

## 13. Contribution record

### 13.1 Contribution by Lech Kalita

Lech Kalita directed the conceptual and interpretive expansion of Stage 4.

His contributions included:

- insisting that the project should not be reduced to a single “relational shift” story;
- foregrounding decline of drive/conflict/defense language as equally important;
- emphasizing global corpus versus journal-specific dynamics;
- connecting the empirical results to Orange, Schafer, Beebe and Lachmann, and the pluralism/common-ground literature;
- articulating the key hypothesis that relatively stable clinical realities may be narrated through historically changing psychoanalytic languages;
- deciding to pursue journal-balanced robustness checks before publication-facing visualizations.

### 13.2 Contribution by Andromeda Nowicka

Andromeda Nowicka supported the work as a human-in-the-loop computational bibliometrics and discourse-analysis agent.

Her contributions included:

- preparing `4a_semantic_change_indices.py`;
- preparing `4b_journal_vs_global_semantic_change.py`;
- preparing `4c_journal_balanced_semantic_change.py`;
- interpreting the Stage 4 outputs;
- framing the robustness logic of equal-journal-weight and within-journal comparisons;
- integrating the Stage 4 results with the theoretical think-tank frame;
- preparing this Stage 4 semantic change and robustness report.

Andromeda’s role remains research support. Final psychoanalytic interpretation and scholarly argument remain under human supervision.

---

## 14. Status statement

Stage 4 has produced a strong, multi-layered empirical foundation.

The current best summary is:

```text
The psychoanalytic_core corpus shows a robust, century-scale semantic transformation.
The transformation includes a decline of drive/conflict/defense dominance and a rise of
relational, contextual, trauma-regulatory, social-ethical, and narrative-reframing vocabularies.

This pattern is visible globally, within journals, and under partially balanced
journal-composition checks.

The field changes, but it changes through journal-specific dialects.
```

The project is now ready for first publication-oriented tables and figures.
