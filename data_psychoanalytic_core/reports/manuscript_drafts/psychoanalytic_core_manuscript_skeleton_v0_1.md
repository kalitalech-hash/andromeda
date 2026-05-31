# Manuscript skeleton v0.1

**Project:** Psychoanalytic core / Andromeda Nowicka  
**Generated:** 2026-05-31T12:00:19.997576+00:00  
**Script:** `5c_generate_manuscript_skeleton.py`  
**Status:** drafting scaffold, not final manuscript

---

## 0. Working title variants

1. **Changing Narratives of Psychoanalytic Clinical Reality: A Century of Title-and-Abstract Discourse Across Core Journals**
2. **From Drive-Conflict Narratives to Relational-Contextual Vocabularies: A Corpus Study of Psychoanalytic Journals**
3. **Regional Dialects of Psychoanalysis: Semantic Change, Pluralism, and Journal Cultures in a Century-Scale Corpus**
4. **Useful Fictions in Motion: A Bibliometric Discourse History of Psychoanalytic Concepts**
5. **The Relational-Contextual Turn in Psychoanalytic Journal Discourse: A Title-and-Abstract Corpus Analysis**

Preferred current working title:

> **Changing Narratives of Psychoanalytic Clinical Reality: A Century of Title-and-Abstract Discourse Across Core Journals**

---

## 1. Provisional abstract structure

### Background

Psychoanalysis has often been described as a pluralistic field of competing theories, regional dialects, useful fictions, and partially overlapping clinical languages. These claims are usually argued theoretically or clinically, but rarely tested through large-scale historical corpus evidence.

### Aim

This study examines whether the public discourse of core psychoanalytic journals shows measurable semantic change over the last century, especially in relation to drive/conflict/defense language, relational/intersubjective language, contextual and social-ethical vocabularies, and narrative reframing.

### Methods

We analyze an ART-only title-and-abstract corpus from five psychoanalytic journals. After metadata QA, article-type filtering, title/abstract cleaning, candidate term extraction, semantic-family mapping, marker-strength correction, and journal-balanced robustness checks, we compute semantic-change indices globally, by journal, by period, and by journal × period.

### Results

The corpus shows a substantial increase in `relational_shift_index` (44.2983), a decline in `drive_conflict_defense` (-19.3414), and a strong increase in `narrative_reframing_index` (56.0184) and `contemporary_contextualization_index` (49.5929). The main direction of change is visible globally, within journals, and under equal-journal-weight and balanced-panel checks.

### Conclusions

The results support a cautious interpretation of psychoanalytic journal discourse as undergoing a century-scale semantic transformation: not the disappearance of classical language, but a loss of its monopoly and the rise of relational, contextual, trauma-regulatory, social-ethical, and narrative-redescriptive vocabularies.

---

## 2. Core claims matrix

- **C1:** The psychoanalytic_core corpus shows a century-scale semantic transformation from drive/conflict/defense-centered discourse toward relational, contextual, trauma-regulatory, social-ethical, and narrative-reframing vocabularies.  
  _Primary evidence:_ Figure 1; Table 3.  
  _Caveat:_ Title-and-abstract evidence; not direct evidence of clinical practice change.
- **C2:** The main semantic pattern survives conservative marker-strength correction, reducing the risk that results are driven by broad weak terms or name-only markers.  
  _Primary evidence:_ Table 1; Figure 6.  
  _Caveat:_ Marker-strength model remains rule-based and provisional.
- **C3:** The transformation is visible within journal trajectories and is not reducible to simple journal-composition effects.  
  _Primary evidence:_ Figure 5; Table 5.  
  _Caveat:_ Balanced diagnostics reduce but do not fully eliminate all composition concerns.
- **C4:** Psychoanalytic Dialogues intensifies and condenses the relational-contextual transformation but does not create it alone.  
  _Primary evidence:_ Figure 4; Table 4.  
  _Caveat:_ Journal start dates and period coverage remain uneven.
- **C5:** The narrative_reframing_index suggests a change in the narrative grammar through which psychoanalytic clinical reality is described.  
  _Primary evidence:_ Figure 2; Table 3.  
  _Caveat:_ The index is interpretive and composite; it requires careful theoretical framing.
- **C6:** The contemporary corpus shows a strong contextualization pattern, combining relational, social-ethical, and trauma-regulatory vocabularies.  
  _Primary evidence:_ Figure 3; Table 3.  
  _Caveat:_ Composite index should be interpreted as exploratory, not as a validated scale.
- **C7:** Journals function as distinct psychoanalytic discourse dialects, shaping the tempo, intensity, and vocabulary of the broader transformation.  
  _Primary evidence:_ Table 4; Table 7.  
  _Caveat:_ Distinctiveness is based on selected semantic indices; further cluster/network analysis may refine this claim.
- **C8:** Equal-journal-weight and balanced-panel checks preserve the main directions of semantic change.  
  _Primary evidence:_ Figure 5; Table 5.  
  _Caveat:_ This is a robustness diagnostic rather than a full causal decomposition.

---

## 3. Recommended main figures and tables

### 3.1 Main-text figure candidates

- **Figure 1. Relational/intersubjective versus drive/conflict/defense vocabulary by period**  
  File: `publication_figure_01_relational_vs_drive_by_period.png`  
  Role: `main_text_core_result`  
  Supports: C1 | C2.
- **Figure 5. Article-weighted versus equal-journal-weight relational shift trajectory**  
  File: `publication_figure_05_equal_weight_vs_global_relational_shift.png`  
  Role: `main_text_methods_results_bridge`  
  Supports: C3 | C8.
- **Figure 4. Journal trajectories of the relational shift index**  
  File: `publication_figure_04_journal_relational_shift_trajectories.png`  
  Role: `main_text_core_result`  
  Supports: C3 | C4 | C7.

### 3.2 Table candidates

- **Table 1. Semantic coverage and marker-strength counts**  
  File: `publication_table_01_corpus_semantic_coverage.csv`  
  Role: `methods`  
  Supports: C2.
- **Table 2. Refined semantic-family coverage**  
  File: `publication_table_02_semantic_family_counts_refined.csv`  
  Role: `results_or_supplement`  
  Supports: C1 | C2.
- **Table 3. Semantic change indices by period**  
  File: `publication_table_03_semantic_indices_by_period.csv`  
  Role: `main_text_core_result`  
  Supports: C1 | C5 | C6.
- **Table 4. Journal-level semantic trajectories**  
  File: `publication_table_04_journal_trajectories.csv`  
  Role: `main_text_core_result`  
  Supports: C3 | C4 | C7.
- **Table 5. Direction consistency under balanced panels**  
  File: `publication_table_05_balanced_direction_consistency.csv`  
  Role: `main_text_or_supplement`  
  Supports: C3 | C8.
- **Table 6. Initial versus refined marker-strength impact**  
  File: `publication_table_06_initial_vs_refined_impact.csv`  
  Role: `methods_or_supplement`  
  Supports: C2.
- **Table 7. Journal distinctiveness**  
  File: `publication_table_07_journal_distinctiveness.csv`  
  Role: `results_or_supplement`  
  Supports: C4 | C7.
- **Table 8. Period-level narrative interpretation table**  
  File: `publication_table_08_narrative_table.csv`  
  Role: `discussion_or_supplement`  
  Supports: C1 | C5 | C6.

---

## 4. Introduction skeleton

### 4.1 Opening problem

- Psychoanalysis has never been a single unified metapsychological system.
- Its history can be read as a series of theoretical languages, clinical dialects, and redescriptions of suffering, subjectivity, conflict, relation, and meaning.
- The literature on pluralism, common ground, incommensurability, and useful fictions has conceptualized this problem, but mostly without large-scale diachronic corpus data.

### 4.2 Theoretical frame

Potential anchors:

- **Beebe and Lachmann:** relational turn, dyadic systems, self- and interactive regulation.
- **Orange:** ethical, hermeneutic, contextual, intersubjective expansion.
- **Schafer:** psychoanalysis as narrative redescription; changing ways of telling clinical reality.
- **Bernardi:** common ground, triangulation, multiple evidence sources.
- **Fulgencio:** paradigms, incommensurability, redescriptions of phenomena.
- **Karbelnig / Lament:** theoretical metaphors, useful untruths, regional dialects.

### 4.3 Gap

Existing theoretical discussions claim that psychoanalysis has become more plural, relational, contextual, and epistemologically self-aware. What is missing is a corpus-level, historical, journal-comparative test of whether these shifts are visible in published psychoanalytic discourse.

### 4.4 Research questions

1. Does psychoanalytic journal discourse show a measurable decline in drive/conflict/defense dominance?
2. Does relational/intersubjective/field language increase over time?
3. Do social-ethical, trauma-regulatory, contextual, and narrative-symbolic vocabularies increase?
4. Are the observed changes global, or driven mainly by journal composition?
5. Do journals function as distinct psychoanalytic discourse dialects?

---

## 5. Corpus and methods skeleton

### 5.1 Corpus

- Five journals:
  - IJPA
  - JAPA
  - Psychoanalytic Dialogues
  - Psychoanalytic Psychology
  - Psychoanalytic Psychotherapy
- ART-only records.
- Title and abstract metadata.
- No PDF mirroring.
- Metadata-first acquisition policy.

### 5.2 Article-type filtering

- Only article type `ART` was treated as original article material.
- Non-ART material was retained for QA/exclusion documentation but not used in the semantic core.

### 5.3 Text layer

- `title_clean`
- `abstract_clean`
- `text_for_analysis`

### 5.4 Candidate term extraction

- Title+abstract candidate terms.
- Global and journal-specific extraction.
- Stopword and artifact cleaning.
- Discriminative candidate terms.

### 5.5 Semantic-family mapping

- Initial broad semantic map.
- QA of high-risk broad markers.
- Marker-strength refinement:
  - strong
  - medium
  - weak
  - name_marker
  - unmapped

### 5.6 Refined semantic application

- Weak-only and name-only hits did not count as full family hits.
- Two or more weak markers could count as provisional.
- Refined model used for interpretation.

### 5.7 Semantic-change indices

Mention formulas or refer to table:

- `relational_shift_index`
- `classical_drive_conflict_index`
- `classical_metapsychology_index`
- `contemporary_contextualization_index`
- `narrative_reframing_index`

### 5.8 Robustness checks

- Initial vs refined comparison.
- Journal-vs-global diagnostics.
- Equal-journal-weight trajectories.
- Long-journal panel.
- Common-period panel.
- Post-1990 panel.
- Direction consistency across journals.

---

## 6. Results skeleton

### 6.1 Semantic coverage and marker-strength correction

Use:

- Table 1
- Table 2
- Table 6
- Figure 6

Claim:

> The refined semantic model preserved broad corpus coverage while reducing overconfident family assignment caused by broad weak markers and name-only markers.

### 6.2 Global semantic transformation by period

Use:

- Figure 1
- Figure 2
- Figure 3
- Table 3
- Table 8

Key numbers:

```text
relational_shift_index_change: 44.2983
drive_conflict_defense_change: -19.3414
narrative_reframing_index_change: 56.0184
contemporary_contextualization_index_change: 49.5929
```

Claim:

> The corpus shows a shift from drive/conflict/defense-centered discourse toward relational, contextual, trauma-regulatory, social-ethical, and narrative-reframing vocabularies.

### 6.3 Journal trajectories and dialects

Use:

- Figure 4
- Table 4
- Table 7

Claim:

> Journals differ in semantic profile and trajectory. Psychoanalytic Dialogues is the strongest relational-contextual pole, but long journals such as IJPA and JAPA also show the broader historical direction of change.

### 6.4 Robustness against journal composition

Use:

- Figure 5
- Table 5

Claim:

> Equal-journal-weight and balanced-panel diagnostics preserve the major directions of change, indicating that the result is not reducible to journal composition.

### 6.5 Summary of empirical pattern

Working formulation:

> Classical language remains present, but loses its earlier organizing monopoly. The later corpus is more relational, contextual, trauma-regulatory, social-ethical, and narrative-redescriptive.

---

## 7. Discussion skeleton

### 7.1 From replacement to reconfiguration

Avoid saying:

```text
drive theory disappears
```

Prefer:

```text
drive/conflict/defense language remains part of psychoanalytic discourse,
but no longer dominates the published vocabulary in the same way.
```

### 7.2 Relational-contextual transformation

Connect to Beebe and Lachmann, Orange, and relational traditions.

### 7.3 Narrative redescription

Connect to Schafer and Fulgencio:

- clinical phenomena may persist,
- theoretical languages redescribe them,
- journal cultures provide dialects of redescription.

### 7.4 Pluralism and common ground

Connect to Bernardi, Karbelnig, Lament:

- pluralism is visible not only as theoretical claim,
- journal profiles show structured dialects,
- common ground may be clinical while discourse varies.

### 7.5 Journal cultures

Interpret journals as discourse ecologies:

- IJPA: long classical archive undergoing gradual transformation.
- JAPA: American classical-to-plural shift.
- Psychoanalytic Dialogues: relational-contextual intensification.
- Psychoanalytic Psychology: relational/research/psychology-facing translation.
- Psychoanalytic Psychotherapy: clinical-practical and process/research orientation.

---

## 8. Limitations skeleton

- Title/abstract layer is not full text.
- Semantic mapping is rule-based and provisional.
- Indices are exploratory composites.
- Article abstracts and keywords vary by journal and period.
- Journal coverage is historically uneven.
- Balanced checks reduce but do not eliminate composition effects.
- Clinical continuity is inferred indirectly from discourse, not directly observed.
- The corpus maps public article self-description, not full intellectual content.

---

## 9. Conclusion skeleton

Working conclusion:

> This study provides corpus-level evidence that psychoanalytic journal discourse has undergone a broad semantic transformation over the last century. The change is visible as a decline in drive/conflict/defense dominance and an increase in relational, contextual, trauma-regulatory, social-ethical, and narrative-reframing vocabularies. The transformation is not uniform: journals function as distinct discourse dialects. However, balanced diagnostics indicate that the main direction of change is visible across journal trajectories rather than being reducible to journal composition.

---

## 10. Figure and table placement plan

### Main text, likely essential

- Figure 1: relational vs drive by period
- Figure 5: equal-weight vs article-weighted relational shift
- Table 3: semantic indices by period
- Table 4: journal trajectories
- Table 5: balanced direction consistency

### Main text or supplement

- Figure 2: narrative reframing by period
- Figure 3: contextualization vs classical metapsychology
- Figure 4: journal relational trajectories

### Methods or supplement

- Figure 6: initial vs refined family drop
- Table 1: semantic coverage
- Table 2: refined family counts
- Table 6: initial vs refined impact
- Table 7: journal distinctiveness
- Table 8: narrative table

---

## 11. Citation placeholders

Insert citations for:

- Beebe & Lachmann — relational turn / dyadic systems
- Orange — ethics, hermeneutics, contextual psychoanalysis
- Schafer — narrative psychoanalysis / action language
- Bernardi — common ground, triangulation, discipline status
- Fulgencio — paradigms and incommensurability
- Karbelnig — structured clinical pluralism
- Lament — useful untruths
- Jiménez & Altimir — empirical research paradigm

---

## 12. Acknowledgment language

Recommended acknowledgment:

> Bibliometric data preparation, semantic keyword normalization, and computational discourse-analysis support were provided by Andromeda Nowicka (v0.5-pre), a human-in-the-loop computational bibliometrics system developed under the supervision of Lech Kalita.

Alternative project-style acknowledgment:

> The computational workflow was supported by Andromeda Nowicka, a human-in-the-loop research agent for reproducible bibliometric and discourse analysis. Final scholarly interpretation remained under human supervision.

---

## 13. Andromeda / Lech contribution note for internal repo

### Lech Kalita

- Defined the psychoanalytic interpretive frame.
- Directed the shift from a narrow relational-turn focus to a broader narrative-redescription model.
- Supplied theoretical think-tank materials.
- Evaluated computational outputs against psychoanalytic meaning.
- Maintained human scholarly responsibility for interpretation.

### Andromeda Nowicka

- Generated reproducible scripts for semantic mapping, refinement, robustness, and publication outputs.
- Produced interpretive summaries and reports.
- Organized claims, figures, tables, and manuscript structure.
- Functioned as HITL computational research support, not autonomous author.

---

## 14. Immediate next tasks

1. Human review of title variants and central claim.
2. Decide journal target and required word count.
3. Add formal citations to theory section.
4. Inspect Figures 1–6 visually and choose final figure set.
5. Prepare `5d_manuscript_intro_methods_draft.py` or manually draft Introduction + Methods.
6. Consider a supplementary methods appendix for semantic-family and marker-strength rules.


---

## 15. Imported 5b core results narrative

# Core results narrative draft

**Status:** working results narrative generated by `5b_publication_figure_audit_and_captions.py`  
**Use:** manuscript planning only; requires human revision.

## Main result

The refined title-and-abstract semantic layer indicates a substantial diachronic transformation in the psychoanalytic journal corpus. The most compact expression of this transformation is the movement from drive/conflict/defense-centered discourse toward relational, contextual, trauma-regulatory, social-ethical, and narrative-reframing vocabularies.

Across the full period range, the key period-level changes are:

```text
relational_shift_index_change: 44.2983
drive_conflict_defense_change: -19.3414
narrative_reframing_index_change: 56.0184
contemporary_contextualization_index_change: 49.5929
```

These results support the interpretation that the corpus does not merely show a rise in relational language. It shows a broader change in the narrative grammar of psychoanalytic discourse.

## Marker-strength correction

The main interpretive layer is the refined semantic model, not the initial broad lexical model. Stage 3 QA showed that some families were inflated by broad weak terms or name-only markers. The marker-strength model therefore treated weak-only and name-only hits conservatively. The purpose was not to remove psychoanalytically meaningful words, but to prevent them from carrying too much interpretive weight when they appeared alone.

This correction supports a central methodological claim: the major trends are not simply artifacts of overbroad lexical matching.

## Journal and corpus dynamics

The field-level transformation is visible globally, but journals differ in how they carry it. Psychoanalytic Dialogues appears as the strongest relational-contextual pole, yet it does not produce the shift alone. Long-archive journals such as IJPA and JAPA also show movement in the same broad direction.

The journal-level results suggest that psychoanalytic journals function as distinct discourse dialects: they participate in the same historical transformation, but with different intensity, timing, and vocabulary.

## Balanced robustness checks

Balanced and partially balanced analyses support the robustness of the main result. In the equal-journal-weight trajectory, the key changes were:

```text
relational_shift_change_equal_weight: 44.846
drive_conflict_change_equal_weight: -20.2778
narrative_reframing_change_equal_weight: 54.8227
```

The similarity between article-weighted and equal-journal-weight trajectories suggests that the result is not reducible to the changing composition of the corpus. Journal composition matters, but it does not fully explain the observed semantic transformation.

## Theoretical interpretation

The empirical pattern is consistent with a broad theoretical frame involving:

```text
Beebe and Lachmann: relational and dyadic-systems transformation
Orange: ethical, contextual, and hermeneutic expansion
Schafer: changing psychoanalytic narratives
Pluralism/common-ground literature: useful fictions, regional dialects, and redescriptions
```

The corpus does not prove how clinical practice changed. It provides title-and-abstract-level evidence for how psychoanalytic authors and journals publicly redescribed their clinical and theoretical world over time.

## Recommended manuscript claim

A cautious central claim is:

> In a century-scale corpus of psychoanalytic journal articles, refined title-and-abstract semantic mapping shows a robust transformation from drive/conflict/defense-centered discourse toward relational, contextual, trauma-regulatory, social-ethical, and narrative-reframing vocabularies. This transformation is visible globally, within journal trajectories, and under partially balanced journal-composition checks, while remaining shaped by distinct journal cultures.

