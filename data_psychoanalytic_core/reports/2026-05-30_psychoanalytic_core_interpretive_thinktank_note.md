# Psychoanalytic core — think-tank note on interpretive framing

**Date:** 2026-05-30  
**Project:** Andromeda Nowicka / `data_psychoanalytic_core`  
**Stage:** interpretive think-tank after full metadata harvest and QA  
**Status:** working conceptual note for later periodization, semantic mapping, and article framing

---

## 1. Purpose

This note records a short interpretive think-tank session conducted after the successful full PEP-Web metadata harvest and global QA build for the `psychoanalytic_core` corpus.

The purpose of the session was not to analyze the harvested data yet, but to define a preliminary conceptual frame for later stages:

```text
periodization
title/abstract semantic mapping
keyword-window diagnostics
interpretation of discourse shifts
article framing
```

The session established three main reference points:

```text
1. Lech Kalita’s historical map of psychoanalytic theories of early states of mind.
2. Donna Orange’s reflection on psychoanalytic language, tradition, and responsibility.
3. Roy Schafer’s account of clinical facts as narratively and theoretically conceptualized.
```

These references will be used as interpretive scaffolding, not as a substitute for empirical analysis.

---

## 2. Context

The think-tank followed completion of the first global build of the five-journal `psychoanalytic_core` corpus.

The current main analytical corpus is:

```text
data_psychoanalytic_core/data/qa/global/psychoanalytic_core_articles_ART_only.csv
```

The corpus contains:

```text
24,393 raw article-level metadata records
12,164 ART-only article records
12,229 non-ART records retained in audit/exclusion layers
14,348 keyword-long rows
```

The working methodological decision is:

```text
full historical corpus:
    ART-only + title + abstract

supplementary keyword corpus:
    ART-only + keywords where available,
    with an empirically defined cutoff window
```

This note helps frame why title, abstract, and keyword language can be treated as meaningful historical evidence rather than merely as surface metadata.

---

## 3. Reference 1 — Lech Kalita’s historical map of early states of mind

The first reference text was Lech Kalita’s chapter from *Rytmy otchłani*, focused on psychoanalytic theories of early states of mind and situated within the broader history of psychoanalytic thought.

The chapter provides a human-authored historical and theoretical map of the development of psychoanalytic discourse. It is especially important for later interpretation because it identifies major conceptual tensions and transitions in psychoanalytic thinking.

Key interpretive axes extracted from the chapter:

```text
intrapsychic → interpersonal / relational
drive and conflict → relation, environment, care, responsiveness
regressive understanding of early states → developmental/progressive understanding
psychopathology → developmental continuum of states of mind
one-person psychology → relational and intersubjective field
internal objects → lived experience with actual others
representation → experience, affect, regulation, relation
primitive/autistic states → early states of mind as broader developmental phenomena
```

A particularly important working point is that “early states of mind” should not be understood only as pathological, regressive, primitive, or psychotic. They may also be understood developmentally, relationally, and as forms of experience that remain active in adult psychic life.

For later empirical work, this chapter suggests that the corpus should be read for long-term shifts between different psychoanalytic grammars:

```text
classical drive/conflict grammar
ego-psychological grammar
Kleinian/Bionian grammar
object-relations grammar
attachment/developmental grammar
self-psychological grammar
relational/intersubjective grammar
trauma/affect-regulation grammar
```

The chapter will serve as a historically informed interpretive frame against which corpus-level findings can be compared.

---

## 4. Reference 2 — Donna Orange on psychoanalytic language

The second reference was Donna Orange’s article:

```text
Orange, D. (2003). Why Language Matters to Psychoanalysis.
Psychoanalytic Dialogues, 13(1), 77–103.
```

Orange’s article is important for the project because it offers a philosophical and clinical justification for taking psychoanalytic language seriously.

The key idea for the corpus project is:

```text
psychoanalytic terms are not neutral labels;
they carry traditions, assumptions, histories, and clinical attitudes.
```

Orange argues that many psychoanalytic terms remain embedded in earlier discourses or “language-games.” Even when terms are redefined for contemporary use, their older connotations and theoretical assumptions may remain active.

For the present project, this gives a strong rationale for treating titles, abstracts, and keywords as traces of historically changing psychoanalytic language-worlds.

Important implications for the corpus:

```text
changing vocabulary may signal changing clinical attitudes;
old terms may survive with transformed or contested meanings;
new terms may signal new ethical, relational, or epistemological commitments;
language may preserve assumptions even when theories claim to have moved beyond them;
semantic mapping must avoid assuming that identical terms have identical meanings across periods.
```

Orange’s text also supports an ethical and hermeneutic framing of the article:

```text
to study psychoanalytic language is to study how psychoanalysis takes responsibility
for the assumptions embedded in its own clinical and theoretical vocabulary.
```

---

## 5. Reference 3 — Roy Schafer on clinical facts and narratives

The third reference was Roy Schafer’s article:

```text
Schafer, R. (1994). The Conceptualisation of Clinical Facts.
International Journal of Psychoanalysis, 75, 1023–1030.
```

Schafer’s text adds a crucial methodological point:

```text
clinical facts are not simply found;
they become clinical facts through symbolization, conceptualization,
narration, dialogue, and theoretical framing.
```

In Schafer’s account, details of the clinical situation are not yet clinical facts. They become clinically meaningful when situated within interrelated clinical narratives and psychoanalytic metanarratives. Different schools of psychoanalytic thought may therefore construct different clinical facts from similar clinical material.

For the corpus project, this provides a powerful interpretive bridge:

```text
psychoanalytic journals do not merely report clinical facts;
they organize clinical facts into historically changing narratives.
```

This helps frame the project not simply as a count of words, but as a study of changing narrative conditions under which something becomes psychoanalytically visible, meaningful, and reportable.

Potential Schafer-inspired categories for later semantic analysis:

```text
clinical fact
narrative
retelling
dialogue
reconceptualization
psychic reality
transference-countertransference enactment
metanarrative
clinical construction
facticity in flux
```

---

## 6. Combined interpretive frame

Taken together, the three references suggest the following frame for the future article:

```text
Kalita:
    provides a historically informed map of major psychoanalytic theoretical shifts,
    especially around early states of mind and the movement from intrapsychic
    to relational-developmental understandings.

Orange:
    shows why psychoanalytic language itself matters and why terms carry
    historical, philosophical, and ethical assumptions.

Schafer:
    shows that clinical facts are narratively and theoretically constituted,
    not merely observed and reported.
```

This gives the project a strong psychoanalytic and hermeneutic rationale.

The article can therefore be framed around the question:

```text
How have leading psychoanalytic journals changed the language through which
psychoanalysis narrates clinical reality, psychic life, early states of mind,
relationality, subjectivity, trauma, development, and therapeutic action?
```

A compact formulation:

```text
We are not only mapping changing topics in psychoanalysis.
We are mapping changing narrative and conceptual conditions under which
clinical experience becomes psychoanalytic discourse.
```

---

## 7. Implications for periodization

The think-tank suggests that periodization should not be only mechanical or decade-based.

Several possible periodization strategies should be compared:

### 7.1 Simple chronological periods

Useful for descriptive stability:

```text
1920–1945
1946–1969
1970–1989
1990–2009
2010–2025
```

### 7.2 Theory-informed periods

Potentially more interpretive:

```text
early classical / interwar institutional formation
postwar ego psychology and object relations expansion
Kleinian, Bionian, Winnicottian, and British object-relations consolidation
self psychology, attachment, developmental, and infant research expansion
relational, intersubjective, trauma, affect-regulation, and pluralist period
```

### 7.3 Empirically derived periods

To be defined after exploratory analysis of title/abstract vocabulary:

```text
periods based on shifts in term frequencies
periods based on topic-model or embedding changes
periods based on journal-specific change points
periods based on keyword availability thresholds
```

Recommended approach:

```text
Use simple chronological periods for primary descriptive analyses,
then compare them with theoretically informed periods in interpretation.
```

---

## 8. Implications for semantic mapping

The next title/abstract semantic stage should prepare concept families that can capture both classical and contemporary psychoanalytic languages.

Preliminary families to consider:

```text
drive, instinct, libido, aggression
conflict, defense, repression, resistance
ego, superego, id, ego functions
object, internal object, object relations
fantasy, unconscious fantasy, phantasy
transference, countertransference, enactment
projection, projective identification, splitting
psychosis, borderline states, primitive states
self, selfobject, narcissism
attachment, separation, loss, dependency
infant, child, mother, caregiver, development
environment, holding, containment, responsiveness
affect, affect regulation, emotion
trauma, dissociation, shame
mentalization, representation, symbolization
intersubjectivity, relationality, field
body, corporeality, sexuality, gender
language, narrative, meaning, interpretation
therapy process, technique, clinical action
culture, race, social world, ethics
```

Important methodological warning:

```text
The same term may not mean the same thing across periods or journals.
Semantic mapping must preserve historical ambiguity and should avoid premature
collapsing of theoretically distinct terms.
```

---

## 9. Implications for keyword-window diagnostics

The think-tank also confirms that keyword analysis should not be treated as equivalent to the full title/abstract corpus.

Current working position:

```text
title + abstract:
    main historical layer for all ART-only records

keywords:
    supplementary layer,
    useful only after empirical coverage diagnostics
```

Next empirical task:

```text
inspect psychoanalytic_core_keyword_journal_year_summary.csv
identify when keyword coverage becomes non-trivial per journal
define whether a shared keyword window is possible
decide whether Psychoanalytic Dialogues should be excluded from keyword analyses
or retained only with a strong missingness caveat
```

Potential criterion to test:

```text
a journal-year is keyword-usable when a meaningful proportion of ART records has keywords
```

The exact threshold should be decided after inspecting coverage distributions.

---

## 10. Article framing

The project should avoid presenting itself as “bibliometrics for bibliometrics’ sake.”

A stronger framing is:

```text
a metadata-based historical study of psychoanalytic language,
narrative frameworks, and changing forms of clinical-theoretical salience
across five leading psychoanalytic journals.
```

Possible working title:

```text
Mapping a Century of Psychoanalytic Discourse:
A Metadata-Based Study of Titles and Abstracts in Five PEP-Web Journals, 1920–2025
```

Alternative more interpretive title:

```text
How Psychoanalysis Narrates Its Clinical World:
A Century of Titles and Abstracts Across Five Psychoanalytic Journals
```

Possible central claim:

```text
The long history of psychoanalytic journals can be studied as a history of
changing clinical narratives: not only what psychoanalysis studies, but how it
makes experience speak psychoanalytically.
```

---

## 11. Contribution record

### 11.1 Contribution by Lech Kalita

Lech Kalita contributed the human interpretive and psychoanalytic frame for this session.

His contributions included:

- supplying the chapter from *Rytmy otchłani* as a historical-theoretical map of psychoanalytic ideas,
- identifying theories of early states of mind as a key reference point for later interpretation,
- proposing Donna Orange as a major reference for thinking about psychoanalytic language,
- proposing Roy Schafer as an additional reference for thinking about clinical facts and narratives,
- articulating the importance of journals as different narrative systems organizing similar clinical realities,
- framing the project as human–non-human cooperation: computational analysis supported by human psychoanalytic interpretation,
- directing the project toward a future article that remains psychoanalytically meaningful rather than merely technical.

### 11.2 Contribution by Andromeda Nowicka

Andromeda Nowicka supported the session as a human-in-the-loop bibliometric and discourse-analysis agent.

Her contributions included:

- extracting methodological implications from the three reference texts,
- translating them into a working interpretive frame for the corpus,
- identifying implications for periodization,
- proposing preliminary semantic concept families,
- clarifying the relation between title/abstract analysis and keyword analysis,
- formulating a possible article frame around language, tradition, clinical facts, and narrative,
- preparing this repository note for future use in the `psychoanalytic_core` pipeline.

Andromeda’s role remains that of research support. Theoretical judgment, psychoanalytic interpretation, and final scholarly framing remain under human supervision.

---

## 12. Status statement

This think-tank note should be treated as a working interpretive scaffold.

It does not predetermine the empirical results. Instead, it records the conceptual expectations and hermeneutic questions that will guide later stages.

The next empirical phase should test, complicate, or revise this map using the harvested corpus.

Working principle:

```text
The theoretical map guides the questions.
The corpus constrains the answers.
Human interpretation gives the findings psychoanalytic meaning.
```
