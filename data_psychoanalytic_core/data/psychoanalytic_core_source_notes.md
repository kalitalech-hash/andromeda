# psychoanalytic_core_source_notes

## Cel etapu

Ten plik będzie dokumentował ręczny i automatyczny rekonesans źródeł dla korpusu `data_psychoanalytic_core`.

Na tym etapie nie pobieramy pełnych tekstów ani PDF-ów. Sprawdzamy wyłącznie dostępność metadanych: tytułów, autorów, roczników, tomów, numerów, DOI, abstraktów, słów kluczowych, typów artykułów oraz stabilnych URL-i.

## Zasada robocza

Każdy tytuł sprawdzamy w trzech warstwach:

1. PEP-Web — szczególnie dla ciągłości historycznej.
2. Crossref — szczególnie dla DOI i metadanych współczesnych.
3. Strona wydawcy — walidacja spisów treści, issue TOC, online-first i nowszych metadanych.

## Decyzje do podjęcia po próbie

- Czy pełna historia danego tytułu może być analizowana title-based?
- Od którego roku dostępne są stabilne keywordy?
- Które źródło jest podstawowe dla każdego tytułu?
- Czy potrzebujemy osobnych parserów dla PEP-Web i stron wydawców?
- Czy istnieje embargo, moving wall albo ograniczenie dostępu wpływające na zakres analiz?
