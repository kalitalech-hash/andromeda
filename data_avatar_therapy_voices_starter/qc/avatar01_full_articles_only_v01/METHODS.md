# AVATAR strict A/B/C — artykuły naukowe (warstwa pochodna)

Źródło: `data_avatar_therapy_voices_starter/outputs/qa/avatar01_full_strict_v05/analysis_corpus_ABC.csv`, Git blob `11b1e6a4d8a3ae4285f33da3c0956c6ceed6b8bf`.

Kryterium: zachować tylko `publication_type == article` i wcześniej wybraną warstwę A/B/C. **209** rekordów (A 12, B 184, C 13) z 266; **57** innych typów wykluczono z analiz (przeglądy 17, abstrakty konferencyjne 36, redakcyjne 3, recenzje książek 1).

W pliku audytu jawnie zapisano decyzję wobec każdego rekordu. Poprzednich danych i decyzji nie nadpisano. Etykieta OpenAlex `article` nie poświadcza samodzielnie recenzowania naukowego ani trafności tematycznej. Filtr A/B/C jest heurystyczny. Zbiór źródłowy pozostaje ograniczony do 2 stron na zapytanie; analizy nie są systematycznym przeglądem całej literatury.

Do analiz tekstowych korzystaj ze źródłowego `analysis_corpus_ABC.csv` z filtrem `publication_type == article`, a identyfikatory i decyzje weryfikuj w `article_type_audit.csv` — nie duplikujemy abstraktów w nowej publicznej warstwie.
