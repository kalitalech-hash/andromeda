# Andromeda Nowicka — version history

This document describes the development of Andromeda Nowicka as a human-in-the-loop research agent and reproducible toolkit for bibliometric and discourse analysis of psychotherapy, psychiatry, psychoanalysis, and adjacent scientific literature.

The version history is methodological rather than purely technical. Successive versions mark changes in research workflow, data-layer discipline, auditability, source acquisition policy, and the scope of reusable analytical pipelines.

---

## Versioning principle

Andromeda uses lightweight methodological versioning:

```text
v0.x = developmental versions before full methodological stabilization
```

Version numbers do not yet imply a stable public API. They indicate successive levels of research maturity, including:

- new reference corpora,
- new pipeline layers,
- new audit rules,
- new ethical metadata-acquisition rules,
- new methodological distinctions,
- new documentation standards.

---

## v0.1 — agent and repository establishment

**Status:** initial version  
**Primary function:** establishment of Andromeda as an identifiable research support agent

Version `v0.1` established Andromeda Nowicka as a research support agent and created the basic repository identity.

The key methodological decision was to define Andromeda as a **human-in-the-loop research support system**, not as an autonomous author or independent scientific interpreter.

Main elements:

- creation of the project repository;
- establishment of the name and identity: **Andromeda Nowicka**;
- creation of the DID identity layer;
- definition of the role as a system supporting bibliometric and discourse-analysis research;
- adoption of the principle that interpretation remains the responsibility of the human researcher;
- initial documentation of the relation between the agent, controller, and repository.

Version `v0.1` was primarily constitutive: it defined what Andromeda is, who supervises it, what it is for, and what its limits are.

---

## v0.2 — keyword-based pipeline after the “Psychoterapia” corpus

**Status:** first operational bibliometric pipeline  
**Reference corpus:** *Psychoterapia*  
**Primary function:** creation of the core workflow for keyword-based bibliometric analysis

Version `v0.2` emerged from work on the journal *Psychoterapia*. It was the first major stage in which Andromeda moved from general research identity to a reproducible analytical workflow.

Main elements:

- acquisition and organization of article metadata;
- creation of a `keyword-long` format;
- QA of article and keyword records;
- record deduplication;
- technical normalization of keywords;
- initial semantic merging rules;
- Polish-language concept normalization;
- periodization;
- trend analyses;
- top-concept tables;
- rising, falling, emergent, and persistent topic analyses;
- initial co-occurrence networks.

The key methodological lesson of `v0.2` was the distinction between a raw keyword and an analytical concept. This version established the principle that keyword analysis maps author/editorial self-description rather than the full intellectual content of articles.

---

## v0.3 — expanded keyword pipeline after the “Psychiatria Polska” corpus

**Status:** extended and more auditable keyword-based pipeline  
**Reference corpus:** *Psychiatria Polska*  
**Primary function:** stabilization of QA, normalization, and trend-analysis procedures in a larger psychiatric corpus

Version `v0.3` developed the pipeline through work on the *Psychiatria Polska* corpus.

Compared with `v0.2`, the pipeline was tested on a different type of journal, with a different clinical, linguistic, and thematic profile. This made it possible to distinguish corpus-specific procedures from reusable workflow elements.

Main elements:

- stronger QA and completeness checks;
- more detailed deduplication logging;
- better reporting of articles without keywords;
- more consistent separation of data layers;
- improved technical normalization;
- more systematic semantic aggregation;
- more developed trend tables and percentage-based period comparisons;
- stronger documentation of the limits of keyword-based analysis;
- more cautious interpretive style.

Version `v0.3` shifted Andromeda from being primarily a result generator toward becoming a quality-control and audit system for transformation decisions.

---

## v0.4 — generalized metadata-first governance after “Archives of Psychiatry and Psychotherapy”

**Status:** previous methodological base  
**Reference corpus:** *Archives of Psychiatry and Psychotherapy*  
**Primary function:** generalization of the pipeline, separation of reusable pipelines and applied corpora, and stronger metadata-first governance

Version `v0.4` was developed after work on the *Archives of Psychiatry and Psychotherapy* corpus.

Main elements:

- clear distinction between reusable analytical pipelines and applied journal corpora;
- treatment of corpus directories as auditable research workspaces;
- stronger layered data model:

```text
raw data
→ QA and deduplication
→ technical normalization
→ semantic normalization / translation
→ audit
→ periodization
→ final analyses
→ interpretation
```

- explicit **metadata-first** principle;
- no-PDF-mirroring default;
- more careful scraping and crawler-identification rules;
- standard transformation documentation;
- obligation to preserve quality-control files and logs;
- conservative interpretation rules;
- distinction between keyword-based and title-based discourse mapping;
- preparation for international and multi-journal corpora.

Version `v0.4` moved Andromeda from single-project keyword workflows toward a broader ecosystem of pipelines, corpora, documentation, ethical rules, and consistent reporting style.

---

## v0.5 — title-and-abstract discourse mapping after the PEP-Web / psychoanalytic core project

**Status:** current version  
**Reference project:** PEP-Web / `data_psychoanalytic_core`  
**Primary function:** formalization of reusable title-and-abstract discourse mapping for historically deep, multi-source psychoanalytic corpora

Version `v0.5` promotes the previously planned psychoanalytic-core work into the current methodological baseline. It follows source reconnaissance and manuscript-oriented analysis of core psychoanalytic journals using titles and abstracts as the main metadata layer.

The central methodological shift is the move from keyword-first and title-only mapping toward **title-and-abstract discourse analysis**. In this model, keywords may remain useful, but they are treated as optional and historically uneven. Titles and abstracts become the principal analyzable metadata layer when they are more consistently available and methodologically better aligned with the research question.

Main elements:

- introduction of `andromeda_titles_plus_abstracts_pipeline/` as a reusable pipeline;
- support for corpora where abstracts are the main enrichment layer beyond titles;
- multi-source source reconnaissance before full acquisition;
- explicit treatment of PEP-Web-style source identifiers and journal keys;
- `ART-only` analytical filtering where article type is a documented marker of substantive original articles;
- preservation of non-ART records in raw and audit layers;
- clear distinction between:
  - keyword-based self-description,
  - title-based public-facing discourse,
  - title-and-abstract metadata discourse;
- support for historically uneven metadata, especially missing or non-comparable keywords;
- conservative abstract-based semantic normalization and concept mapping;
- periodized analysis across long time spans;
- journal-level and period-level comparison;
- co-presence and co-occurrence analysis based on extracted concepts;
- continued no-PDF-mirroring and metadata-first acquisition rules;
- explicit warning that abstract analysis is richer than title analysis but still not equivalent to full-text interpretation.

Reference PEP-Web journal set used during methodological development:

```text
The International Journal of Psychoanalysis
Journal of the American Psychoanalytic Association
Psychoanalytic Dialogues
Psychoanalytic Psychology
Psychoanalytic Psychotherapy
```

Reference PEP-style short identifiers handled during development:

```text
IJP
APA
PD
PPSY
PPTX
```

The key methodological lesson of `v0.5` is that long-range psychoanalytic discourse can be analyzed through titles and abstracts in a reproducible way, but only if the pipeline preserves source-layer uncertainty, article-type filtering decisions, abstract availability limits, and human audit of semantic mappings.

---

## Possible v0.6 — full comparative multi-journal discourse-analysis stabilization

**Status:** possible future version  
**Reference scope:** completed and generalized multi-journal corpora  
**Primary function:** stabilization of a comparative macro-pipeline across several journals, metadata cultures, and historical periods

Version `v0.6` may be justified if Andromeda moves from the current title-and-abstract pipeline into a fully stabilized comparative multi-journal framework.

Possible elements:

- full reusable support for multi-journal comparative discourse analysis;
- standardized journal-level normalization and weighting;
- more mature handling of unequal journal histories;
- cross-corpus comparison between psychotherapy, psychiatry, and psychoanalysis;
- publication-ready comparative tables and figures;
- stronger package-level test coverage;
- stable command-line interfaces for the main reusable pipelines.

---

## Relationship between versions

The development of Andromeda can be summarized as follows:

```text
v0.1  agent identity, repository, DID
v0.2  first keyword-based pipeline on “Psychoterapia”
v0.3  expanded and more auditable keyword pipeline on “Psychiatria Polska”
v0.4  generalized metadata-first governance after “Archives of Psychiatry and Psychotherapy”
v0.5  title-and-abstract discourse mapping after PEP-Web / psychoanalytic core
v0.6  possible future comparative multi-journal macro-pipeline
```

---

## Interpretive principle

Each version of Andromeda must preserve the basic principle of the project:

> Andromeda Nowicka supports data preparation, audit, normalization, analysis, and documentation, but does not replace expert scholarly interpretation.

Results generated by the pipeline should be treated as structured, auditable support for the researcher. Interpretive decisions, theoretical framing, and final conclusions remain part of the human-in-the-loop research process.

---

## Recommended update policy

Future version updates should include:

1. a short description of the purpose of the version;
2. the reference corpus, pipeline, or project;
3. the main methodological changes;
4. the main technical changes;
5. new limitations or risks;
6. recommended wording for acknowledgment or methods description.
