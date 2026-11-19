# D03 — zatwierdzona mapa pojęć i analizy dyskursu głosów

## Podstawa decyzji HITL

Badacz potwierdził w rozmowie, że ręcznie przejrzał i zaakceptował wszystkie kandydackie pojęcia D02. W tej warstwie uznano za zatwierdzone **23 identyfikatory pojęć oraz 89 przyporządkowań fraz do pojęć**. Zachowano dokładnie granice i identyfikatory z D02; bez nowego scalania ani przypisywania przez model. Akceptacja słownika **nie jest** potwierdzeniem trafności kontekstowej wszystkich 414 dopasowań do artykułów ani walidacją pełnotekstową.

## Korpus i mianowniki

209 publikacji oznaczonych jako `article` w A/B/C (A=12, B=184, C=13); 192 publikacje z ≥1 rozpoznanym pojęciem i 17 bez dopasowań. Braki dopasowania nie powodują wykluczenia z mianowników. 12 publikacji nie ma abstraktu, więc analizowano ich tytuły. Analiza wyłącznie na dostępnej warstwie tytułów i abstraktów.

## Metoda

Deterministyczne dopasowanie zatwierdzonych fraz: binarna obecność pojęcia na publikację po scaleniu wariantów (`article_id,concept_id` unikatowe). Współobecność oznacza obecność obu pojęć **w jednej publikacji**, a nie bezpośrednią relację interpretacyjną. Obok surowej liczby współobecności raportowano cosine i lift obliczane z częstości dokumentowych; dla rzadkich pojęć miary te są niestabilne i nie stanowią dowodu asocjacji klinicznej.

Okresy 2009–2015 (n=42), 2016–2020 (n=60), 2021–2026 (n=107; 2026 rok niepełny). Osobno zliczono źródło i kategorię A/B/C; wartości procentowe zawsze odnoszą się do liczby artykułów w danej grupie.

## Wyniki empiryczne

Najczęstsze zatwierdzone w tym korpusie pojęcia: `VOICE_HEARING` 108/209, `VOICE_AUDITORY_HALLUCINATIONS` 87/209, `QUALITATIVE_METHOD` 35/209, `VOICE_DISTRESS` 31/209. Współobecność `VOICE_HEARING` × `VOICE_AUDITORY_HALLUCINATIONS`: 32 artykuły; `QUALITATIVE_METHOD` × `VOICE_HEARING`: 26; `VOICE_DISTRESS` × `VOICE_HEARING`: 23. Metody badań (np. `QUALITATIVE_METHOD`, `CONTROLLED_TRIAL`) należy interpretować osobno od tematów badawczych.

## Ostrożna interpretacja / hipoteza

Wśród wybranych rekordów widoczne są równoległe sposoby nazywania fenomenu — `voice hearing` i `auditory hallucinations`. Ich współobecność sugeruje częściowe nakładanie się języków, niekoniecznie konflikt szkół. Frazy `VOICE_RELATING`, `VOICE_DIALOGUE` i `AVATAR_THERAPY` są rzadkie przy konserwatywnych kryteriach dopasowania; brak wąskiej frazy nie dowodzi braku relacyjnego ujęcia w publikacji. Interpretacja temporalna pozostaje ograniczona przez dobór czasopism, ranking API i maksymalną liczbę stron wyszukiwania.

## Co NIE jest dowiedzione

Nie wnioskujemy o zmianie częstości tych idei w całej literaturze, skuteczności AVATAR ani o hierarchii dowodów. Wybrane słowa nie oznaczają, że tekst w całości reprezentuje dany paradygmat. Wykluczenia i brakujące abstrakty stanowią możliwe źródło błędów klasyfikacji. Następna kontrola powinna obejmować sensitivity audit artykułów bez dopasowań i podział języka tytułów od języka abstraktów.
