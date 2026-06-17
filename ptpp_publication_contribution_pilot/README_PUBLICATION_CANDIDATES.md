# PTPP publication-candidate search

Ten dodatek do `ptpp_publication_contribution_pilot/` uruchamia metadata-first wyszukiwanie kandydatów publikacyjnych dla osób z publicznego snapshotu PTPP.

## Co robi

Skrypt czyta:

```text
data_raw/ptpp_members_snapshot_reconstructed_2026-06-17.csv
```

i zapisuje:

```text
data_intermediate/publication_candidates_raw.csv
data_intermediate/authorship_candidates_raw.csv
data_intermediate/person_source_summary.csv
logs/publication_candidate_search_log.csv
docs/publication_candidate_search_summary.json
data_intermediate/raw_api_json/*.json
```

To są **kandydaci**, nie finalnie zweryfikowany dorobek. Finalne rekordy powinny powstać po ręcznym audycie homonimii i dopasowań autorów.

## Instalacja

Wystarczy standardowe środowisko Python 3.10+:

```bash
pip install requests
```

## Uruchomienie z repo

Z katalogu repo:

```bash
cd ptpp_publication_contribution_pilot

python scripts/search_ptpp_publication_candidates.py   --members-csv data_raw/ptpp_members_snapshot_reconstructed_2026-06-17.csv   --output-dir .   --email TWOJ_EMAIL@example.org   --sources crossref openalex pubmed   --max-results-per-source 20   --sleep 0.35
```

Test na pierwszych 10 osobach:

```bash
python scripts/search_ptpp_publication_candidates.py   --members-csv data_raw/ptpp_members_snapshot_reconstructed_2026-06-17.csv   --output-dir .   --email TWOJ_EMAIL@example.org   --sources crossref openalex pubmed   --limit-persons 10   --max-results-per-source 10   --sleep 0.35
```

## Źródła

Domyślnie:

- Crossref REST API
- OpenAlex API
- PubMed / NCBI E-utilities

Opcjonalnie:

- ORCID expanded search, jeśli ustawisz `ORCID_TOKEN`.

```bash
export ORCID_TOKEN="..."
python scripts/search_ptpp_publication_candidates.py ... --sources crossref openalex pubmed orcid
```

## Dlaczego nie PBN/CEJSH/BazHum w tej wersji?

Ta wersja celowo zaczyna od stabilnych publicznych API. PBN, CEJSH i BazHum są bardzo wartościowe, ale wymagają osobnych adapterów i osobnego rozpoznania warunków/endpointów. Nie należy ich włączać przez niestabilny scraping wyników wyszukiwania, jeśli nie mamy bezpiecznego eksportu lub publicznego API.

## Reguła interpretacyjna

Piszemy:

> kandydaci publikacyjni przypisani do osób widocznych w publicznym snapshotcie PTPP

a nie:

> publikacje PTPP

ani:

> zweryfikowany dorobek członków PTPP

dopóki `authorship_candidates_raw.csv` nie przejdzie ręcznego audytu.
