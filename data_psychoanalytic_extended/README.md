# Psychoanalytic extended — additional journal layer

**Status:** research workspace; metadata-based, human-in-the-loop.  
**Analysis interval:** 1970–2025.  
**Renamed:** 2026-11-19 from `data_gaming_mind_extension/`.

## Corpus definition

This directory holds the **eight additional PEP-Web journals**, previously gathered for Gaming Mind. It is **not a physical copy of all 13 journals**. The extended 13-journal analytical corpus is defined as:

```text
data_psychoanalytic_core/          # existing five journals, unchanged
+ data_psychoanalytic_extended/     # eight additional journals (this workspace)
= extended 13-journal analysis layer, after deduplication and QC
```

The extension journals are: Contemporary Psychoanalysis; British Journal of Psychotherapy; Modern Psychoanalysis; Journal of Child Psychotherapy; Neuropsychoanalysis; Psychoanalysis, Culture & Society; Psychoanalytic Inquiry; and The Psychoanalytic Quarterly. The source configuration is `gaming_mind_extension_bundle/journals.json`.

The physical data layout in `data/` retains raw PEP metadata, probe and harvest manifests, QA exports, and source audit materials. No raw or derived records were altered by this directory rename.

## Snapshot and unresolved coverage

The existing `data/qa/summary.json` records an audit generated 2026-11-13 (UTC). It reports:

- 21,734 incoming metadata records and 10,617 ART-eligible records.
- 361 verified journal-years out of 362 expected.
- **One unresolved metadata gap:** Modern Psychoanalysis, 2018; HTTP 200 with zero returned records is **not** proof of zero publications.
- `coverage_complete: false`. The corpus must not be described as exhaustively harvested for 1970–2025.

These numbers describe **eight additional journals only**, not the 13-journal union. Title/abstract screening candidates for games are not validated conceptual codes. Expert audit is required before publication-level claims.

## Rename and reproducibility

The previous path was `data_gaming_mind_extension/`. Historical outputs may contain this string in `manifest.csv`, `summary.json`, or audit logs, sometimes as absolute Windows paths. Those fields are preserved **unchanged as provenance**, not rewritten to claim a new harvest; do not interpret them as current, portable executable file paths.

To locate files today, use the present directory tree and the year/journal identifiers. Code for source acquisition, checkpoint verification, QA, and the separate topical gaming screening remains in `gaming_mind_extension_bundle/`; its configured output now points to this workspace. Re-audit only after a human review of source permissions and existing artefacts. Do not overwrite existing raw or QA layers.

## Rights and release preparation

This repository is public, but the repository's MIT license **does not confer redistribution rights** over third-party PEP-Web content. Review the existing tracked raw/abstract-bearing datasets, source conditions, and Git history before any Zenodo archival snapshot or broader release. No license clearance or data removal is implied by this rename.
