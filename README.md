# Andromeda

**Andromeda Nowicka (v0.5)** — human-in-the-loop research agent and reproducible toolkit for bibliometric and discourse analysis of psychotherapy, psychiatry, psychoanalysis, and adjacent scientific literature.

Controller: **Lech Kalita**  
DID: `did:web:kalitalech-hash.github.io:andromeda`  
Repository: `kalitalech-hash/andromeda`

---

## Purpose

This repository contains research code, documentation, and project datasets used to map the evolution of scientific discourse in psychotherapy, psychiatry, psychoanalysis, and adjacent fields.

The project focuses on transparent, reproducible, and auditable bibliometric workflows, including:

- journal and database metadata acquisition,
- keyword extraction and cleaning,
- title-based discourse mapping,
- title-and-abstract semantic mapping,
- semantic normalization and merging,
- co-word, co-occurrence, and term co-presence analysis,
- temporal trend analysis,
- thematic clustering,
- multi-corpus and multi-journal comparison,
- preparation of publication-ready tables, figures, and methods descriptions.

Andromeda is a **research support agent**, not an autonomous author and not a substitute for expert scholarly interpretation. All analytical outputs are intended to support human-led research decisions.

---

## Repository structure

The repository separates **reusable analytical pipelines** from **applied journal or database corpora**.

### Reusable pipelines

```text
andromeda_keywords_pipeline/
```

Pipeline for keyword-based bibliometric analysis. It supports metadata acquisition, keyword QA, technical normalization, semantic merging, periodization, trend analysis, and co-word network construction. It is most appropriate when keywords are consistently available across the selected corpus.

```text
andromeda_titles_pipeline/
```

Pipeline for title-based discourse mapping. It is intended for cases where titles are the primary public metadata layer or where title-level comparison is methodologically appropriate.

```text
andromeda_titles_plus_abstracts_pipeline/
```

Pipeline for title-and-abstract discourse mapping. It supports corpora where titles and abstracts form the main analyzable metadata layer, while keywords are absent, unevenly available, historically unstable, or methodologically secondary. It was introduced in v0.5 after the PEP-Web / psychoanalytic core project and is designed for conservative, auditable semantic analysis without full-text or PDF mirroring.

### Applied corpora

```text
data_psychoterapia/
data_psychiatria_polska/
data_archives_of_psychiatry/
data_worldcorpus/
data_psychoanalytic_core/
```

Project-specific data directories contain corpus-specific scripts, intermediate outputs, quality-control files, transformation logs, semantic mappings, audit files, and analysis results.

Applied corpora should be treated as research workspaces. Raw data, cleaned data, semantic mappings, and analytical outputs should be stored as separate layers rather than overwritten.

---

## Core methodological principle

Each project should move through explicit data layers:

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

Each stage should produce:

- a main output file,
- quality-control files,
- a transformation log,
- a short methodological note,
- a machine-readable summary where useful, for example JSON or CSV.

The pipeline prioritizes reproducibility, auditability, and conservative interpretation. Keyword-based analysis maps the self-description of publications through author/editorial metadata; title-based analysis maps the public-facing language of titles; title-and-abstract analysis maps a richer but still metadata-bounded discourse layer. None of these layers should be treated as a substitute for full-text scholarly interpretation.

---

## Typical workflow

1. **Corpus definition**
   - journal, database, or source platform,
   - time span,
   - language,
   - article types,
   - metadata fields,
   - inclusion and exclusion rules,
   - decision whether the primary analytical layer is keywords, titles, titles plus abstracts, or another documented layer.

2. **Metadata acquisition**
   - preferably from structured exports, APIs, Crossref, landing pages, public issue tables, or other public metadata layers,
   - with explicit logging and source attribution,
   - without unnecessary full-text or PDF mirroring.

3. **QA and deduplication**
   - duplicated article IDs, URLs, and DOIs,
   - records outside the selected time span,
   - missing title, year, abstract, keywords, DOI, or article type,
   - source and article-type inconsistencies,
   - corpus-specific inclusion filters such as `ART-only` where justified.

4. **Technical normalization**
   - Unicode normalization,
   - whitespace cleanup,
   - lowercase handling where appropriate,
   - punctuation and hyphen harmonization,
   - preservation of raw metadata values.

5. **Semantic normalization**
   - conservative translation and synonym merging,
   - explicit semantic IDs,
   - confidence flags,
   - manual audit queue for ambiguous cases,
   - clear distinction between technical normalization, semantic merging, and broader thematic aggregation.

6. **Periodization**
   - analytically justified time windows,
   - article and concept counts by period,
   - missing-year checks,
   - transparent handling of uneven journal histories in multi-journal corpora.

7. **Final analyses**
   - descriptive statistics,
   - top concepts,
   - trends,
   - rising/falling/emergent/persistent topics,
   - co-occurrence or co-presence networks,
   - clustering and community summaries,
   - journal-level and period-level comparisons where applicable.

8. **Interpretation**
   - cautious, corpus-bound interpretation,
   - explicit limitation to the available metadata layer,
   - documentation of methodological decisions and possible bias,
   - human expert review before publication use.

---

## Ethical metadata acquisition

The default acquisition model is **metadata-first**.

Andromeda workflows should not assume that temporary free access, institutional access, browser-readable content, or personal research access grants permission for mass downloading, PDF mirroring, redistribution, or unrestricted full-text mining.

The default approach is:

```text
metadata first
abstracts and keywords only where openly or lawfully available
full text only if necessary, permitted, and documented
PDF mirroring avoided unless explicitly licensed or otherwise permitted
```

For detailed acquisition rules, see:

```text
SCRAPING_POLICY.md
robots.md
```

Recommended transparent user agent for project-specific crawlers:

```text
AndromedaNowickaBibliometricBot/0.5
(metadata-only bibliometric research; contact: CONTACT_EMAIL; no PDF mirroring; polite delay)
```

---

## Version identity

Current research-agent identity:

```text
Andromeda Nowicka (v0.5)
HITL bibliometric analysis agent for discourse mapping
Controller: Lech Kalita
DID: did:web:kalitalech-hash.github.io:andromeda
```

Version **v0.5** marks the transition from a primarily keyword/title toolkit to a broader metadata-discourse toolkit that includes reusable title-and-abstract analysis. It formalizes lessons from the PEP-Web / psychoanalytic core project: multi-source source reconnaissance, ART-only analytical filtering, historically uneven metadata layers, and conservative abstract-based semantic mapping without full-text or PDF mirroring.

---

## Acknowledgment guidance

When this system supports scholarly work, it should be acknowledged as a research support agent rather than listed as a co-author.

Recommended acknowledgment:

```text
Bibliometric data preparation, semantic normalization, and title/abstract-based discourse mapping were supported by the research agent Andromeda Nowicka (v0.5), a human-in-the-loop computational bibliometrics system developed under the supervision of Lech Kalita.
```

Formal methods reference, if needed:

```text
Andromeda Nowicka (v0.5). HITL bibliometric analysis agent for discourse mapping. Controller: Lech Kalita. DID: did:web:kalitalech-hash.github.io:andromeda.
```

---

## Tools

Primary language:

```text
Python
```

Common libraries:

```text
pandas
numpy
requests
beautifulsoup4
lxml
scikit-learn
networkx
matplotlib
```

Additional dependencies may be declared inside individual pipeline or corpus directories.

---

## License

MIT License, unless otherwise noted in a specific data source, corpus directory, or third-party dependency.

The license applies to repository code and documentation. It does not grant rights to redistribute third-party journal content, publisher metadata beyond permitted uses, PDFs, full-text article corpora, restricted database content, or access-controlled material.
