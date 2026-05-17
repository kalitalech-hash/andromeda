# Etap 3c — polonizacja pełna i rozszerzone scalenie semantyczne

## Wejście
- Plik wejściowy: `app_keywords_long_polish_semantic_expanded_no_editorial.csv`
- Rekordy keyword-long: 2649
- Artykuły z co najmniej jednym keywordem: 686

## Transformacje
1. Priorytetem była kolumna `keyword_concept_polish_expanded`.
2. Utworzono finalne kolumny:
   - `keyword_concept_en_final`
   - `keyword_concept_polish_final`
   - `keyword_semantic_3c_id`
   - `semantic_3c_action`
   - `polish_translation_method_3c`
   - `review_flag_3c`
3. Zastosowano mniej konserwatywne scalenia semantyczne dla obszarów wcześniej oznaczonych jako wymagające średniego audytu.
4. Do kolejki audytu pozostawiono tylko przypadki mocno problematyczne: terminy nietematyczne/metadane, ewidentne literówki lub nierozwiązane skróty.

## Wyniki
- Liczba pojęć przed etapem 3c, według `keyword_concept_en_expanded`: 1477
- Liczba finalnych polskich pojęć po etapie 3c: 1232
- Redukcja liczby pojęć względem poprzedniej warstwy EN: 245
- Rekordy objęte dodatkowymi scaleniami: 1093
- Rekordy pozostawione do silnego audytu: 65
- Unikalne pojęcia pozostawione do silnego audytu: 59

## Decyzja audytowa
Flagi audytu średniego z poprzedniego etapu nie są już przenoszone jako wymagające ręcznej decyzji. Uznano, że dotychczasowe reguły scalania są wystarczająco stabilne, aby traktować je jako automatyczną warstwę analityczną. Do ręcznego audytu pozostawiono tylko pojęcia mocno problematyczne.
