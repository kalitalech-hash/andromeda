# PEP-Web metadata probe — psychoanalytic_core

Ten katalog zawiera czysty, rekonesansowy skrypt do sprawdzania metadanych w PEP-Web API.

## Najważniejsze zasady

- Nie zapisujemy sekretów w kodzie.
- Nie commitujemy `.env.pep`.
- Nie pobieramy PDF-ów.
- Nie tworzymy lokalnego mirrora pełnych tekstów.
- Zaczynamy od małych próbek roczników i zapisujemy log.

## Pliki

```text
scripts/1a_pep_metadata_probe.py
.env.pep.example
.gitignore
data/raw_pep_metadata/probe/
data/logs/pep_metadata_probe_log.csv
data/source_recon/psychoanalytic_core_metadata_probe_results.csv
```

## Jak uruchomić najbezpieczniej — tryb suchy

Tryb suchy pokazuje planowane zapytania, ale nie łączy się z API:

```bash
python scripts/1a_pep_metadata_probe.py --dry-run --journal ijpa --year 1920
```

## Jak przygotować dane dostępowe

Skopiuj przykład:

```bash
cp .env.pep.example .env.pep
```

Następnie wpisz dane dostępowe lokalnie w `.env.pep`.

Ten plik jest ignorowany przez Git i nie powinien trafić do repozytorium.

## Pierwsze właściwe uruchomienie

Po uzupełnieniu `.env.pep` zacznij od jednego czasopisma i jednego rocznika:

```bash
python scripts/1a_pep_metadata_probe.py --journal ijpa --year 1920 --limit 10 --delay 3
```

Jeżeli wynik wygląda poprawnie, można uruchomić próbkę dla kilku lat:

```bash
python scripts/1a_pep_metadata_probe.py --journal ijpa --limit 10 --delay 3
```

## Wyniki

Skrypt zapisuje:

- surowe odpowiedzi JSON do `data/raw_pep_metadata/probe/`,
- log zapytań do `data/logs/pep_metadata_probe_log.csv`,
- spłaszczoną tabelę metadanych do `data/source_recon/psychoanalytic_core_metadata_probe_results.csv`.

## Uwaga

Składnia `facetquery` może wymagać korekty po pierwszym realnym teście API. To normalne na etapie rekonesansu.


## v7 keyword extraction

Version v7 extracts IJPA article keywords from PEP Search API records.

Confirmed control case:

```text
art_id = IJP.101.0013A
expected keywords =
Paradigms; incommensurability; common ground; communication; redescription
```

PEP Search API does not expose these values in a simple `keywords` field.
Instead, v7 checks:

```text
documentInfoXML / artkwds / impx[@type="KEYWORD"]
abstract HTML / div.artkwds
```

Run the control case:

```powershell
python scripts/1a_pep_metadata_probe.py --journal ijpa --year 2020 --limit 10 --delay 3 --facetquery "art_id:IJP.101.0013A"
```

Expected flattened result:

```text
has_keywords = True
n_keywords = 5
keyword_source = documentInfoXML/artkwds
keywords_joined = Paradigms; incommensurability; common ground; communication; redescription
```


## v8 fix: keyword parser plus `--facetquery`

Version v8 restores the manual `--facetquery` override while keeping v7 keyword extraction.

Control run:

```powershell
python scripts/1a_pep_metadata_probe.py --journal ijpa --year 2020 --limit 10 --delay 3 --facetquery "art_id:IJP.101.0013A"
```

Expected result:

```text
Flattened records: 1
has_keywords = True
n_keywords = 5
keyword_source = documentInfoXML/artkwds
```


## v9 consolidated probe

Version v9 consolidates the previous fixes:

- confirmed default facetquery: `art_id:<PEP_PREFIX>.* AND year:<YYYY>`;
- manual `--facetquery` override for one-article tests;
- safe `--diagnose` output;
- keyword extraction from `documentInfoXML/artkwds`;
- fallback extraction from `abstract` HTML `div.artkwds`;
- append/per-run CSV options.

Control command:

```powershell
python scripts/1a_pep_metadata_probe_v9.py --journal ijpa --year 2020 --limit 10 --delay 3 --diagnose --facetquery "art_id:IJP.101.0013A"
```

Expected result:

```text
status_code = 200
Flattened records = 1
n_keywords = 5
keyword_source = documentInfoXML/artkwds
```


## v10 clean consolidated version

Version v10 is a clean rewrite of the probe script after v7/v8/v9 drift.

It includes:

- PEP-specific headers from `.env.pep`;
- confirmed default facetquery: `art_id:<PEP_PREFIX>.* AND year:<YYYY>`;
- manual `--facetquery` override;
- safe `--diagnose` output;
- keyword extraction from `documentInfoXML/artkwds`;
- fallback keyword extraction from `abstract` HTML `div.artkwds`;
- append and per-run CSV support.

Control test:

```powershell
python scripts/1a_pep_metadata_probe_v10.py --journal ijpa --year 2020 --limit 10 --delay 3 --diagnose --facetquery "art_id:IJP.101.0013A"
```

Expected diagnostics:

```text
sends_client_id_header = true
sends_client_session_header = true
sends_x_api_authorize_header = true
sends_x_pep_auth_header = true
status_code = 200
Flattened records = 1
```

Expected CSV:

```text
has_keywords = True
n_keywords = 5
keyword_source = documentInfoXML/artkwds
keywords_joined = Paradigms; incommensurability; common ground; communication; redescription
```
