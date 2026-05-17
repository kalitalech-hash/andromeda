# Etap 3: polonizacja i scalenie semantyczne keywordów — Archives of Psychiatry and Psychotherapy

## Dane wejściowe

Plik wejściowy: `app_keywords_long_normalized.csv`

Liczba rekordów keyword-long: **2737**  
Liczba artykułów z keywordami: **714**  
Liczba unikalnych surowych keywordów: **1743**  
Liczba unikalnych keywordów po normalizacji technicznej: **1699**

## Zakres operacji

Wykonano konserwatywne scalenie semantyczne oraz automatyczną polonizację etykiet. Automatycznie scalano przede wszystkim:

- oczywiste warianty pisowni i literówki,
- warianty brytyjskie/amerykańskie,
- zapisy z dywizem i bez dywizu,
- jednoznaczne skróty, np. `CBT`, `PTSD`, `OCD`,
- wybrane warianty liczby pojedynczej/mnogiej, jeżeli oznaczały ten sam typ pojęcia,
- warianty redakcyjne `editorial 1`, `editorial 2`, `editorial 3` do pojęcia `editorial`.

Nie scalano automatycznie synonimów klinicznie lub historycznie niejednoznacznych, np. `alcohol dependence` z `alcohol use disorder`, ani szerokich powiązań typu `coronavirus` z `covid-19`.

## Wyniki

Liczba finalnych pojęć semantycznych: **1645**  
Liczba wariantów technicznie znormalizowanych połączonych przez etap semantyczny: **54**  
Liczba pojęć mających więcej niż jeden wariant wejściowy: **43**  
Liczba pozycji w kolejce do przeglądu: **1303**  
Liczba wariantów wymagających przeglądu tłumaczenia: **1222**  
Liczba wariantów z tłumaczeniem bez flagi przeglądu: **477**

## Pliki wynikowe

- `app_keywords_long_polish_semantic.csv` — główna warstwa keyword-long po polonizacji i scaleniu semantycznym.
- `app_keyword_semantic_polish_map.csv` — mapa przejścia od `keyword_norm` do pojęcia finalnego.
- `app_keyword_semantic_concept_counts.csv` — częstości finalnych pojęć semantycznych.
- `app_semantic_merges_log.csv` — log połączeń semantycznych.
- `app_semantic_review_queue.csv` — kolejka pozycji wymagających kontroli eksperckiej.
- `app_semantic_polish_summary.json` — metryki etapu.

## Decyzje audytowe

1. `editorial`, `editorial 1`, `editorial 2`, `editorial 3` i podobne warianty scalono do pojęcia `editorial`, ale oznaczono jako kandydat do wyłączenia z analiz merytorycznych.
2. Zastosowano scalenia konserwatywne. Terminy potencjalnie bliskie znaczeniowo, ale nierównoważne klinicznie, pozostawiono jako osobne pojęcia.
3. Tłumaczenia oznaczone jako `translation_review` wymagają weryfikacji przed użyciem w finalnym artykule.
4. Plik `app_keywords_long_polish_semantic.csv` nadaje się do wstępnych analiz ilościowych; przed publikacją należy przejrzeć kolejkę `app_semantic_review_queue.csv`, zaczynając od pojęć o najwyższej częstości.
