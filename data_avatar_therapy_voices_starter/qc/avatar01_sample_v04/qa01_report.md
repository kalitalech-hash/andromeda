# QA-01 — automatyczna kontrola próbki AVATAR v0.4

Źródło: `data_avatar_therapy_voices_starter/outputs/raw/avatar01_sample_v04/raw_candidates.csv` (GitHub commit `52818eb`, blob `8ad57dd03da35e5fc4c656c5d0f1baf9480a709e`). Kontrola na poziomie publicznej warstwy metadanych; bez przetwarzania pełnych tekstów.

## Wyniki techniczne

- Rekordy: **122**; lata 2009–2026.
- Brak tytułu: 0; brak roku: 0; brak abstraktu: **24** (19.7%); brak DOI: **2**.
- Duplikaty: OpenAlex ID 0, DOI 0, znormalizowany tytuł+rok 0.
- Typy publikacji: article 99; review 17; conference-abstract 3; conference-paper 1; book-review 2.

## Wstępne sygnały tematyczne (nie finalne kwalifikacje)

- A — AVATAR / dialog z awatarem: **9**.
- B — psychologiczne / relacyjne podejścia do głosów: **59**.
- C — inne technologie VR w psychozach: **12**.
- Nierozstrzygnięte: **42**.

Reguły mają charakter heurystyczny, są oparte na tytułach i dostępnych abstraktach. Mogą zawierać błędy klasyfikacji; żaden rekord nie został automatycznie ostatecznie włączony ani wykluczony. Publikacje typu conference-abstract, conference-paper i book-review są jawnie flagowane do osobnej kontroli. Brak abstraktu nie stanowi samodzielnego kryterium wykluczenia.

## Następna decyzja HITL

Zweryfikować 9 kandydatów A i kolejkę niejednoznacznych rekordów; następnie ocenić, czy próbka z limitami zapytań wystarczająco pokrywa literaturę AVATAR. Dopiero potem uruchomić większą akwizycję i finalną normalizację semantyczną.

Pliki są pochodnymi QA i nie zawierają abstraktów. Surowy rekord pozostaje niezmieniony.
