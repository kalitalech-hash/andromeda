# PTPP publication contribution pilot

Project date: 2026-06-17

## Purpose

Pilot bibliometric project for mapping the publication output of people listed in public PTPP membership/certification pages.

Working formulation:

> publication output of persons publicly listed by PTPP, not institutional publications of PTPP as an organization.

## Analytical scope

Primary object: person-publication links.

Primary data layers:
1. Public PTPP membership/certification snapshot.
2. Bibliographic metadata from open/public scholarly databases.
3. Manual disambiguation and audit.
4. Topic/concept extraction from titles, abstracts and keywords where available.

## Default source order

1. PTPP public membership pages.
2. PBN / Polska Bibliografia Naukowa.
3. ORCID where available.
4. Crossref REST API.
5. CEJSH / BazHum / CEEOL / PubMed as auxiliary sources.
6. Manual validation.

## Exclusions

- No patient data.
- No private therapist-profile enrichment unless explicitly justified.
- No PDF mirroring.
- No full-text corpus by default.
- No paywall or access-control circumvention.

## Core tables

- data_raw/ptpp_members_snapshot.csv
- data_intermediate/persons_disambiguation.csv
- data_intermediate/publication_candidates.csv
- data_intermediate/authorship_candidates.csv
- data_final/persons.csv
- data_final/publications.csv
- data_final/authorships.csv
- semantic_maps/concepts.csv
- logs/acquisition_log.csv
- logs/audit_log.csv

## Pilot rule

Start with 20-30 people from one membership category. Use conservative matching:
- high: ORCID/PBN profile or strong full-name + affiliation/topic consistency
- medium: full name + field consistency, no unique ID
- low: possible but ambiguous
- reject: likely different person

Only high and manually accepted medium matches enter the final analytical layer.
