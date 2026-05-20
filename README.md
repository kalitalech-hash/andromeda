# Andromeda

**Andromeda Nowicka (v0.4)** — human-in-the-loop research agent and reproducible toolkit for bibliometric and discourse analysis of psychotherapy, psychiatry, and related scientific literature.

Controller: **Lech Kalita**  
DID: `did:web:kalitalech-hash.github.io:andromeda`  
Repository: `kalitalech-hash/andromeda`

---

## Purpose

This repository contains research code, documentation, and project datasets used to map the evolution of scientific discourse in psychotherapy, psychiatry, and adjacent fields.

The project focuses on transparent, reproducible, and auditable bibliometric workflows, including:

- journal metadata acquisition,
- keyword extraction and cleaning,
- title-based discourse mapping,
- semantic normalization and merging,
- co-word and co-occurrence analysis,
- temporal trend analysis,
- thematic clustering,
- preparation of publication-ready tables, figures, and methods descriptions.

Andromeda is a **research support agent**, not an autonomous author and not a substitute for expert scholarly interpretation. All analytical outputs are intended to support human-led research decisions.

---

## Repository structure

The repository separates **reusable analytical pipelines** from **applied journal corpora**.

### Reusable pipelines

```text
andromeda_keywords_pipeline/
```

Pipeline for keyword-based bibliometric analysis. It supports metadata acquisition, keyword QA, technical normalization, semantic merging, periodization, trend analysis, and co-word network construction.

```text
andromeda_titles_pipeline/
```

Pipeline for title-based discourse mapping. It is intended for cases where titles are the primary public metadata layer or where title-level comparison is methodologically appropriate.

### Applied corpora

```text
data_psychoterapia/
data_psychiatria_polska/
data_archives_of_psychiatry/
data_worldcorpus/
```

Project-specific data directories containing corpus-specific scripts, intermediate outputs, quality-control files, transformation logs, and analysis results.

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

The pipeline prioritizes reproducibility, auditability, and conservative interpretation. Keyword-based analysis maps the self-description of publications through author/editorial metadata; it does not reconstruct the full intellectual content of articles.

---

## Typical workflow

1. **Corpus definition**
   - journal or database,
   - time span,
   - language,
   - article types,
   - metadata fields,
   - inclusion and exclusion rules.

2. **Metadata acquisition**
   - preferably from HTML metadata, Crossref, landing pages, or other public metadata layers,
   - with explicit logging and source attribution,
   - without unnecessary full-text or PDF mirroring.

3. **QA and deduplication**
   - duplicated article IDs and URLs,
   - records outside the selected time span,
   - missing metadata,
   - missing keywords,
   - article-type inconsistencies.

4. **Technical normalization**
   - Unicode normalization,
   - whitespace cleanup,
   - lowercase handling,
   - punctuation and hyphen harmonization,
   - preservation of raw keyword values.

5. **Semantic normalization**
   - conservative translation and synonym merging,
   - explicit semantic IDs,
   - confidence flags,
   - manual audit queue for ambiguous cases.

6. **Periodization**
   - analytically justified time windows,
   - article and keyword counts by period,
   - missing-year checks.

7. **Final analyses**
   - descriptive statistics,
   - top concepts,
   - trends,
   - rising/falling/emergent/persistent topics,
   - co-occurrence networks,
   - clustering and community summaries.

8. **Interpretation**
   - cautious, corpus-bound interpretation,
   - explicit limitation to the available metadata layer,
   - documentation of methodological decisions and possible bias.

---

## Ethical metadata acquisition

The default acquisition model is **metadata-first**.

Andromeda workflows should not assume that temporary free access, institutional access, or browser-readable content grants permission for mass downloading, PDF mirroring, redistribution, or unrestricted full-text mining.

The default approach is:

```text
metadata first
full text only if necessary
PDF mirroring avoided unless explicitly licensed or otherwise permitted
```

For detailed acquisition rules, see:

```text
SCRAPING_POLICY.md
```

Recommended transparent user agent for project-specific crawlers:

```text
AndromedaNowickaBibliometricBot/0.4
(metadata-only bibliometric research; contact: CONTACT_EMAIL; no PDF mirroring; polite delay)
```

---

## Version identity

Current research-agent identity:

```text
Andromeda Nowicka (v0.4)
HITL bibliometric analysis agent for discourse mapping
Controller: Lech Kalita
DID: did:web:kalitalech-hash.github.io:andromeda
```

Version v0.4 marks a governance and documentation update: clearer distinction between reusable pipelines and applied corpora, explicit metadata-acquisition policy, and stronger framing of Andromeda as a human-in-the-loop research support system.

---

## Acknowledgment guidance

When this system supports scholarly work, it should be acknowledged as a research support agent rather than listed as a co-author.

Recommended acknowledgment:

```text
Bibliometric data preparation and semantic keyword normalization were supported by the research agent Andromeda Nowicka (v0.4), a human-in-the-loop computational bibliometrics system developed under the supervision of Lech Kalita.
```

Formal methods reference, if needed:

```text
Andromeda Nowicka (v0.4). HITL bibliometric analysis agent for discourse mapping. Controller: Lech Kalita. DID: did:web:kalitalech-hash.github.io:andromeda.
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

The license applies to repository code and documentation. It does not grant rights to redistribute third-party journal content, publisher metadata beyond permitted uses, PDFs, or full-text article corpora.
