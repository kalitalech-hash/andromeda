# Etap 3b: rozszerzone scalenie semantyczne i usunięcie `editorial`

## Dane wejściowe

Plik: `app_keywords_long_polish_semantic.csv`  
Liczba rekordów keyword-long: 2737

## Decyzje

1. Usunięto całą kategorię `editorial`, obejmującą rekordy oznaczone wcześniej jako `exclude_candidate_editorial`.
2. Zastosowano mniej konserwatywne automatyczne scalenie semantyczne.
3. Szerokie scalenia kliniczne i pojęciowe oznaczono flagą `review_broad_merge`, aby zachować audytowalność.

## Wyniki

- Usunięte rekordy `editorial`: 88
- Rekordy keyword-long po usunięciu `editorial`: 2649
- Artykuły z co najmniej jednym keywordem po czyszczeniu: 686
- Liczba pojęć przed rozszerzonym scalaniem: 1644
- Liczba pojęć po rozszerzonym scalaniu: 1477
- Redukcja liczby pojęć: 167
- Liczba grup scalających więcej niż jedno pojęcie wejściowe: 38
- Rekordy objęte szerokim scaleniem do audytu: 545

## Główny plik wynikowy

`app_keywords_long_polish_semantic_expanded_no_editorial.csv`

## Uwagi audytowe

Ten wariant jest mniej konserwatywny niż poprzednia warstwa `app_keywords_long_polish_semantic.csv`.
Łączy m.in. warianty historyczne i klinicznie bliskie, np. `alcohol dependence`, `alcoholism`, `alcohol abuse`
do `alcohol use disorder`, a także różne formy depresji do szerszego pojęcia `depression/depressive disorders`.
Takie scalenia zwiększają czytelność trendów tematycznych, ale mogą ukrywać różnice między podtypami.
Dlatego zachowano osobny log oraz flagę `review_broad_merge`.
