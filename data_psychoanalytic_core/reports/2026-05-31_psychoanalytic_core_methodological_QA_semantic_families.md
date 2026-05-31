# Psychoanalytic core — methodological Q&A note on semantic families and marker assignment

**Date:** 2026-05-31  
**Project:** Andromeda Nowicka / `data_psychoanalytic_core`  
**Purpose:** internal manuscript-support note  
**Status:** methodological drafting aid for article writing

---

## 1. Purpose

This note summarizes a methodological discussion about likely reader or reviewer questions concerning the semantic-family model used in the `psychoanalytic_core` title-and-abstract analysis.

It addresses:

```text
How were abstracts assigned to semantic families?
How were markers prepared?
Which terms were considered characteristic, and why?
Who assigned terms to families?
Who decided which semantic families should exist?
Why was no external expert-rater panel used?
How should the human–agent collaboration be described?
```

The note is intended for use when writing the article’s Methods, Limitations, Discussion, and response-to-reviewer sections.

---

## 2. Core formulation

The most compact formulation is:

```text
The vocabulary was corpus-derived;
the semantic architecture was psychoanalytically informed;
the mapping workflow was computationally implemented and audit-controlled.
```

Or:

```text
Terms were corpus-derived.
Semantic families were expert-designed working categories.
Term-to-family assignments were audit-controlled.
```

Expanded version:

> Candidate terms were derived from the cleaned title-and-abstract corpus. Semantic families, by contrast, were theory-informed working categories designed to capture major historically and clinically recognizable domains of psychoanalytic discourse. The assignment of corpus-derived terms to these families was performed through an explicit rule-based semantic map within a human-in-the-loop workflow, and was subsequently audited through marker-strength correction, high-risk term review, and sensitivity analyses.

---

## 3. How were abstracts assigned to semantic families?

We did not ask an algorithm to “understand” the whole abstract in the way a human analyst would. Instead, we used controlled lexical-semantic mapping.

Each article had a combined title-and-abstract field. This field was searched for previously defined psychoanalytic markers. Each marker belonged to a semantic family. If a title or abstract contained markers from a given family, the article received a hit for that family, subject to marker-strength rules.

Examples:

```text
drive, conflict, defense, resistance
→ drive_conflict_defense

relational, intersubjective, mutual, dialogue, recognition
→ relational_intersubjective_field

trauma, dissociation, affect, regulation
→ trauma_dissociation_affect_regulation
```

Suggested Methods wording:

> Assignment of articles to semantic families was performed at the article level using the combined title-and-abstract field. We first constructed a rule-based semantic map in which candidate terms were assigned to broader psychoanalytic semantic families. The cleaned title-and-abstract text of each article was then searched for these mapped terms. An article was counted as associated with a given semantic family when its title-and-abstract field contained one or more terms mapped to that family, subject to marker-strength rules. Strong and medium markers counted as full family evidence. Weak markers or name markers alone were retained as signals but did not count as full family hits unless combined with additional evidence. This procedure produced an auditable article × semantic-family matrix.

Suggested limitation wording:

> A semantic-family hit indicates that an article’s title and abstract use vocabulary associated with a given semantic field. It does not imply that the full article belongs exclusively to that theoretical school, nor that the semantic family exhausts the article’s clinical or conceptual content.

Key distinction:

```text
controlled lexical-semantic mapping
```

not:

```text
automated interpretation of full clinical meaning
```

---

## 4. How were markers prepared?

Markers were not imported as a closed external ontology and were not simply invented. They were derived from the corpus and then organized psychoanalytically.

Process:

```text
clean title+abstract corpus
→ candidate term extraction
→ technical filtering
→ removal/down-weighting of artifacts and generic terms
→ theory-informed semantic-family mapping
→ article-level application
→ QA of family inflation
→ marker-strength correction
→ refined semantic layer
```

Suggested Methods wording:

> Candidate markers were derived from the cleaned title-and-abstract corpus rather than imposed as a closed external vocabulary. After technical filtering, candidate terms were assigned to psychoanalytic semantic families using a transparent rule-based semantic map. The map was subsequently audited by examining top contributing terms per family, single-term family inflation, and high-risk broad markers. This QA step led to a marker-strength model distinguishing strong, medium, weak, and name markers.

Key formulation:

```text
The marker set was corpus-derived, theory-informed, and QA-controlled.
```

This avoids two misleading claims:

```text
1. that the terms were purely subjective inventions;
2. that the semantic families were automatically discovered as objective natural classes.
```

The terms came from the corpus. The family architecture came from psychoanalytic knowledge. The mapping was then tested and documented.

---

## 5. Which terms were considered characteristic, and why?

“Characteristic” does not mean simply “most frequent.” In a psychoanalytic corpus, the most frequent words may be generic or tautological, such as:

```text
psychoanalytic
patient
clinical
analysis
```

Such words may name the domain but not differentiate meaningful semantic tendencies inside it.

Suggested Methods wording:

> Candidate terms were treated as characteristic when they were sufficiently frequent and/or discriminative in the cleaned title-and-abstract corpus and when they carried interpretable psychoanalytic semantic information. We did not equate raw frequency with interpretive importance: very frequent but generic words were filtered, down-weighted, or treated as weak markers. Terms were retained as analytically characteristic when they helped identify a semantic field, distinguish journals or periods, or functioned as theoretically meaningful markers of psychoanalytic discourse.

Practical criteria:

```text
1. empirical presence
   the term appeared in the cleaned title-and-abstract corpus

2. analytic informativeness
   the term carried recognizable psychoanalytic meaning

3. discriminative usefulness
   the term helped differentiate semantic families, journals, or periods

4. QA robustness
   the term did not inflate a family disproportionately, unless treated as strong/medium
```

Some terms were psychoanalytically important but too broad to count as full evidence when appearing alone:

```text
self
object
mother
relationship
Freud
```

These were retained as signals but assigned weaker status:

```text
weak
name_marker
```

Suggested wording:

> Broad but meaningful terms were retained as signals but did not count as full family evidence when they appeared alone.

---

## 6. Who assigned terms to families?

The semantic-family framework was developed in a human-in-the-loop workflow combining psychoanalytic domain expertise with computational data-analysis support.

```text
Lech Kalita:
  psychoanalytic domain expertise
  interpretive supervision
  theory-informed semantic-family design
  final scholarly responsibility

Andromeda Nowicka:
  corpus processing
  candidate-term extraction
  rule-based semantic mapping
  QA and marker-strength refinement
  robustness analyses
  publication tables and figures
```

Suggested formal wording:

> The semantic-family framework was developed in a human-in-the-loop workflow combining psychoanalytic domain expertise with computational data-analysis support. Psychoanalytic interpretation, family design, and final methodological decisions were supervised by Lech Kalita. Andromeda Nowicka supported corpus processing, candidate-term extraction, rule-based semantic mapping, quality control, marker-strength refinement, sensitivity analyses, and publication-output preparation.

Compact description:

```text
Lech = psychoanalytic expert / domain interpreter
Andromeda = data-analysis agent / reproducible workflow engine
```

For manuscript language, avoid excessive anthropomorphism. Use:

```text
human-in-the-loop workflow
computational data-analysis support
psychoanalytic domain supervision
```

---

## 7. Who decided that these should be the semantic families?

The semantic families were not discovered automatically as definitive categories. They were designed as working analytical categories.

Their purpose was not to create an ultimate taxonomy of psychoanalysis. Their purpose was to create a broad, historically and clinically interpretable map of discourse fields that could be followed across time and journals.

Criteria for family design:

```text
1. historical recognizability in psychoanalysis
2. clinical interpretability
3. presence in the title-and-abstract corpus
4. usefulness for diachronic comparison
5. usefulness for journal comparison
6. sufficient breadth for statistical stability
7. sufficient specificity to avoid being empty labels
```

Suggested Methods wording:

> Semantic families were constructed as working analytical categories rather than as a definitive ontology of psychoanalysis. Their initial design was theory-informed: families were chosen to capture major historically and clinically recognizable domains of psychoanalytic discourse, including drive/conflict/defense, dreams and fantasy, object relations, transference and technique, relational/intersubjective language, trauma and affect regulation, culture and ethics, empirical research, and theoretical schools. Candidate terms extracted from the cleaned title-and-abstract corpus were then assigned to these families through a transparent rule-based mapping procedure implemented by Andromeda Nowicka and reviewed within a human-in-the-loop workflow under the supervision of Lech Kalita. The mapping was subsequently audited by examining top contributing terms, family concentration, high-risk broad markers, and the effect of marker-strength correction.

Do not claim:

```text
These 17 families are the true structure of psychoanalysis.
```

Claim instead:

```text
These 17 families are a working analytical instrument for diachronic discourse mapping.
```

Suggested wording:

> The families should be read as an analytical instrument for diachronic discourse mapping, not as a definitive taxonomy of psychoanalytic theory.

---

## 8. How was arbitrariness reduced?

The project did not eliminate interpretation. It made interpretation explicit and auditable.

Main controls:

```text
1. explicit semantic map
   every mapped term has a documented family assignment

2. working definitions
   each family has a documented interpretive definition

3. marker-strength model
   terms were marked strong, medium, weak, or name_marker

4. QA of high-risk terms
   broad terms that inflated families were identified

5. top-term reporting
   top contributing terms per family were exported

6. initial-vs-refined comparison
   effects of conservative marker-strength correction were measured

7. journal/global and balanced-panel checks
   main findings were tested against composition effects
```

Reviewer-facing wording:

> Yes, semantic-family construction involves interpretive judgment. This is unavoidable in psychoanalytic discourse analysis. We addressed this not by pretending that classification can be fully neutral, but by making the classification explicit, reproducible, and auditable. The semantic map, marker-strength decisions, top contributing terms, and high-risk terms were all preserved as separate outputs.

---

## 9. Why was there no external expert-rater panel?

No independent expert-rater panel was used in this phase. This is a real limitation.

However, the purpose of this stage was not to validate a final psychoanalytic taxonomy. The purpose was to build and test an explicit, reproducible semantic instrument for diachronic discourse mapping.

Suggested reviewer-facing answer:

> We did not use an external expert-rater panel in this phase because the purpose was not to validate a final psychoanalytic taxonomy, but to develop an explicit, reproducible semantic instrument for diachronic discourse mapping. To reduce arbitrariness, all semantic assignments were preserved in inspectable mapping files, marker-strength decisions were documented, high-risk broad markers were reported, and the main findings were tested against refined, journal-level, and balanced-panel sensitivity analyses. We agree that independent expert rating would be a valuable future validation step.

Suggested limitation wording:

> We did not include an independent expert-rater validation panel for semantic-family assignments. This limits claims about inter-rater reliability and external validity of the semantic taxonomy. However, the study was designed as an auditable corpus-based discourse analysis rather than a definitive taxonomy-building exercise. The full semantic map, marker-strength distinctions, top contributing terms, high-risk markers, and sensitivity checks are reported to make the interpretive layer inspectable and reproducible.

Theoretical nuance:

> In a pluralistic psychoanalytic field, external expert ratings would themselves be theory-positioned rather than neutral. For this reason, we prioritized explicitness and auditability over the appearance of theory-free classification.

Use this carefully. It should supplement, not replace, the limitation.

Suggested future-work wording:

> Future work should evaluate the semantic-family map through independent expert review, ideally including raters representing different psychoanalytic traditions. Such a study could assess agreement on family assignments, identify school-specific disagreements, and refine the marker-strength model. In the present study, we treat the semantic families as working analytical categories whose credibility depends on transparency, inspectability, and robustness checks rather than on claims of final classificatory validity.

---

## 10. Where the semantic-family content is documented

The family content is documented in the `5d` publication outputs:

```text
publication_table_09_semantic_family_definitions_and_top_terms.csv
publication_table_10_semantic_family_marker_strength_examples.csv
publication_table_11_semantic_family_top_terms_long.csv
publication_table_12_semantic_family_high_risk_terms.csv
publication_table_13_semantic_family_content_audit_summary.csv
publication_figure_07_semantic_family_content_heatmap.png
publication_figure_08_marker_strength_by_family.png
```

These outputs answer reviewer questions such as:

```text
What terms make up each family?
Which terms were strong, medium, weak, or name markers?
Which terms contributed most to article-level family hits?
Which terms were considered high-risk for family inflation?
How broad or narrow were the families?
```

Recommended main/supplement division:

```text
Main text:
  publication_table_09_semantic_family_definitions_and_top_terms.csv

Supplement:
  publication_table_10_semantic_family_marker_strength_examples.csv
  publication_table_11_semantic_family_top_terms_long.csv
  publication_table_12_semantic_family_high_risk_terms.csv
  publication_table_13_semantic_family_content_audit_summary.csv
  publication_figure_07_semantic_family_content_heatmap.png
  publication_figure_08_marker_strength_by_family.png
```

---

## 11. Best one-paragraph Methods version

> Candidate terms were derived from the cleaned title-and-abstract corpus. Semantic families were expert-designed working categories intended to capture major historically and clinically recognizable domains of psychoanalytic discourse, not a definitive taxonomy of psychoanalytic theory. Corpus-derived terms were assigned to these families through an explicit rule-based semantic map in a human-in-the-loop workflow combining psychoanalytic domain expertise with computational data-analysis support. Article-level family assignment was then performed by searching each combined title-and-abstract field for mapped terms. To reduce overinterpretation, the initial semantic map was audited for family inflation, broad markers, and name-only effects. We introduced marker-strength categories—strong, medium, weak, and name_marker—so that broad terms could be retained as signals without automatically counting as full family evidence when appearing alone. The full semantic map, marker-strength examples, high-risk terms, and top contributing terms were preserved as auditable outputs.

---

## 12. Best one-paragraph Limitations version

> The semantic-family model involves interpretive judgment and was not validated by an independent expert-rater panel. Therefore, the families should be read as working analytical categories rather than final psychoanalytic taxa. This limits claims about inter-rater reliability and external validity of the taxonomy. The study addresses this limitation through transparency and sensitivity analysis: all term-to-family assignments were preserved in explicit mapping files; broad or potentially inflationary terms were identified; marker-strength correction was applied; and the main findings were evaluated under refined, journal-level, and balanced-panel robustness checks. Future work should test the map through independent expert review, ideally including raters from different psychoanalytic traditions.

---

## 13. Best short conference-style answer

> The terms came from the corpus; the family architecture came from psychoanalytic expertise; and the mapping was implemented computationally, documented explicitly, and stress-tested through QA and robustness checks. We are not claiming a final taxonomy of psychoanalysis. We are using an auditable semantic instrument to track how psychoanalytic journals changed their public conceptual vocabulary over time.

---

## 14. Internal contribution note

### Lech Kalita

Lech contributed:

```text
psychoanalytic domain expertise
knowledge of psychoanalytic history and clinical-theoretical meaning
design and evaluation of semantic family architecture
interpretive supervision
final scholarly responsibility
```

### Andromeda Nowicka

Andromeda contributed:

```text
candidate-term extraction
corpus processing
rule-based semantic mapping
QA diagnostics
marker-strength correction
sensitivity and robustness analyses
publication tables and figures
methodological documentation
```

Suggested neutral formulation:

> The semantic framework was developed in a human-in-the-loop workflow combining psychoanalytic expertise and computational data-analysis support.

---

## 15. Working mantra

```text
Corpus-derived vocabulary.
Psychoanalytically informed semantic architecture.
Audit-controlled mapping.
Conservative interpretation.
```
