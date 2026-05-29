# Andromeda Nowicka — historia wersji

Ten dokument opisuje rozwój Andromedy Nowickiej jako human-in-the-loop research agent oraz reproducible toolkit dla bibliometrycznej i dyskursywnej analizy literatury z zakresu psychoterapii, psychiatrii, psychoanalizy i pól pokrewnych.

Historia wersji ma charakter metodologiczny, nie wyłącznie techniczny. Kolejne wersje oznaczają nie tylko zmiany w kodzie, lecz także dojrzewanie zasad pracy z korpusami: od pierwszego ustanowienia tożsamości agentki i repozytorium, przez rozwój pipeline’ów keyword-based, aż po obecny model metadanych, audytu, rekonesansu źródeł i analizy wielokorpusowej.

---

## Zasada wersjonowania

Andromeda używa lekkiego wersjonowania semantyczno-metodologicznego:

```text
v0.x = wersje rozwojowe przed pełną stabilizacją metodologiczną
```

Numery wersji nie oznaczają jeszcze stabilnego API. Oznaczają raczej kolejne progi dojrzałości badawczej:

- nowe korpusy referencyjne,
- nowe warstwy pipeline’u,
- nowe reguły audytu,
- nowe zasady etycznego pozyskiwania metadanych,
- nowe rozróżnienia metodologiczne,
- nowe standardy dokumentacji.

---

## v0.1 — ustanowienie agentki i repozytorium

**Status:** wersja inicjalna  
**Główna funkcja:** powołanie Andromedy jako identyfikowalnego narzędzia wsparcia badawczego

Wersja `v0.1` obejmowała powołanie Andromedy Nowickiej jako research support agent oraz utworzenie podstaw repozytorium. Na tym etapie kluczowe było zdefiniowanie tożsamości systemu jako narzędzia human-in-the-loop, a nie autonomicznego autora ani samodzielnego interpretatora naukowego.

Najważniejsze elementy wersji:

- utworzenie repozytorium projektu,
- ustanowienie nazwy i tożsamości agentki: **Andromeda Nowicka**,
- utworzenie identyfikatora DID,
- określenie roli jako systemu wspierającego badania bibliometryczne i dyskursywne,
- przyjęcie zasady, że interpretacja wyników pozostaje decyzją badacza,
- rozpoczęcie dokumentowania relacji między agentką, kontrolerem i repozytorium.

Wersja `v0.1` była przede wszystkim warstwą konstytutywną: definiowała, czym Andromeda jest, kto ją nadzoruje, do czego służy i w jakich granicach powinna być używana.

---

## v0.2 — pipeline keyword-based z pracy nad korpusem „Psychoterapia”

**Status:** pierwsza wersja operacyjnego pipeline’u bibliometrycznego  
**Korpus referencyjny:** „Psychoterapia”  
**Główna funkcja:** budowa podstawowego workflow dla analizy słów kluczowych

Wersja `v0.2` wyłoniła się z pracy nad korpusem czasopisma „Psychoterapia”. Był to pierwszy duży etap, w którym Andromeda przeszła od ogólnej tożsamości badawczej do konkretnego, powtarzalnego pipeline’u analitycznego.

Najważniejsze elementy wersji:

- pozyskiwanie i porządkowanie metadanych artykułów,
- utworzenie formatu `keyword-long`,
- QA rekordów artykułów i słów kluczowych,
- deduplikacja rekordów,
- techniczna normalizacja słów kluczowych,
- pierwsze reguły semantycznego scalania pojęć,
- polonizacja keywordów,
- periodyzacja danych,
- analizy trendów,
- tabele top pojęć,
- analiza tematów rosnących, malejących, emergentnych i trwałych,
- pierwsze sieci współwystępowania pojęć.

Najważniejsza lekcja metodologiczna `v0.2` polegała na rozróżnieniu między surowym keywordem a pojęciem analitycznym. W tej wersji ukształtowała się zasada, że analiza słów kluczowych nie rekonstruuje pełnej treści artykułów, lecz mapuje ich samoopis autorsko-redakcyjny.

---

## v0.3 — rozwinięcie pipeline’u w pracy nad korpusem „Psychiatria Polska”

**Status:** rozszerzona i bardziej audytowalna wersja pipeline’u keyword-based  
**Korpus referencyjny:** „Psychiatria Polska”  
**Główna funkcja:** stabilizacja procedur QA, normalizacji i analizy trendów w większym korpusie psychiatrycznym

Wersja `v0.3` została rozwinięta w pracy nad korpusem „Psychiatria Polska”. W porównaniu z `v0.2` pipeline został przetestowany na innym typie czasopisma, o innym profilu klinicznym, językowym i tematycznym. Pozwoliło to odróżnić elementy specyficzne dla jednego korpusu od procedur nadających się do ponownego użycia.

Najważniejsze elementy wersji:

- mocniejsze procedury QA i kontroli kompletności,
- dokładniejsze logowanie deduplikacji,
- lepsze raportowanie artykułów bez keywordów,
- rozwinięcie reguł technicznej normalizacji,
- bardziej konsekwentne rozdzielenie warstw danych,
- dopracowanie semantycznej agregacji pojęć,
- rozwinięcie tabel trendów i udziałów procentowych,
- mocniejsze podkreślenie, że trendy należy liczyć względem liczby artykułów w okresie,
- lepsza dokumentacja ograniczeń keyword-based analysis,
- bardziej ostrożny styl interpretacji wyników.

Wersja `v0.3` przyniosła ważne przesunięcie: Andromeda zaczęła działać nie tylko jako generator wyników, lecz jako system kontroli jakości i audytu decyzji transformacyjnych.

---

## v0.4 — uogólniony pipeline po pracy nad „Archives of Psychiatry and Psychotherapy”

**Status:** aktualna baza metodologiczna  
**Korpus referencyjny:** „Archives of Psychiatry and Psychotherapy”  
**Główna funkcja:** uogólnienie pipeline’u, rozdzielenie reusable pipelines i applied corpora, wzmocnienie zasad metadata-first

Wersja `v0.4` powstała po pracy nad korpusem „Archives of Psychiatry and Psychotherapy” i stanowi obecną bazę metodologiczną projektu. To wersja, na której opiera się aktualny rozwój `data_psychoanalytic_core`.

Najważniejsze elementy wersji:

- wyraźne rozdzielenie reusable analytical pipelines od applied journal corpora,
- ujęcie katalogów korpusowych jako audytowalnych research workspaces,
- wprowadzenie silniejszej zasady warstw danych:

```text
raw data
→ QA and deduplication
→ technical normalization
→ semantic normalization / translation
→ audit
→ periodization
→ final analyses
→ interpretation
```

- doprecyzowanie zasady **metadata-first**,
- domyślne unikanie PDF mirroringu,
- ostrożniejsze reguły scrapingu i identyfikacji crawlera,
- standard dokumentowania transformacji,
- obowiązek zachowywania plików kontrolnych i logów,
- konserwatywne podejście do interpretacji,
- rozróżnienie między keyword-based i title-based discourse mapping,
- przygotowanie podstaw do pracy na korpusach międzynarodowych i wieloczasopismowych.

Wersja `v0.4` przesuwa Andromedę z poziomu pojedynczych projektów keywordowych w stronę pełniejszego ekosystemu narzędzi: pipeline’ów, korpusów, dokumentacji, reguł etycznych i spójnego stylu raportowania.

---

## v0.5 — planowana wersja po rekonesansie `psychoanalytic_core`

**Status:** planowana / robocza  
**Korpus referencyjny:** `data_psychoanalytic_core`  
**Główna funkcja:** obsługa wieloczasopismowego korpusu psychoanalitycznego opartego głównie na tytułach i abstraktach

Wersja `v0.5` może zostać wydzielona po zakończeniu etapu rekonesansu i przygotowaniu stabilnego pipeline’u dla `data_psychoanalytic_core`.

Prawdopodobne elementy wersji:

- obsługa wieloczasopismowego korpusu psychoanalitycznego,
- praca na pięciu źródłach PEP-Web:

```text
The International Journal of Psychoanalysis
Journal of the American Psychoanalytic Association
Psychoanalytic Dialogues
Psychoanalytic Psychology
Psychoanalytic Psychotherapy
```

- potwierdzenie prefiksów PEP:

```text
IJP
APA
PD
PPSY
PPTX
```

- rozwinięcie pipeline’u source reconnaissance,
- standaryzacja próbkowania źródeł przed pełnym harvestingiem,
- reguła głównego korpusu `ART-only`,
- traktowanie `article_type == "ART"` jako operacyjnego markera original substantive articles / original papers,
- zachowanie non-ART w warstwach raw/audit,
- rozpoznanie, że dla historycznego korpusu psychoanalitycznego główną osią jest title/abstract-based analysis,
- potraktowanie keywordów jako nowoczesnej, nierównej historycznie warstwy pomocniczej,
- przygotowanie pipeline’u do analizy abstraktów, a nie tylko keywordów.

Najważniejszą zmianą metodologiczną `v0.5` byłoby przejście od klasycznego keyword-first corpus do modelu, w którym główny materiał analityczny stanowią tytuły i abstrakty, a keywordy są wykorzystywane selektywnie i z wyraźnym opisem braków historycznych.

---

## v0.6 — możliwa większa aktualizacja po pełnym opracowaniu `psychoanalytic_core`

**Status:** możliwa wersja docelowa po zakończeniu pełnego korpusu psychoanalitycznego  
**Korpus referencyjny:** pełny `psychoanalytic_core`  
**Główna funkcja:** stabilizacja makropipeline’u wieloczasopismowego i porównawczego

Wersja `v0.6` może być uzasadniona, jeżeli po rekonesansie `psychoanalytic_core` powstanie pełny, działający pipeline dla wieloczasopismowej analizy psychoanalitycznej. Byłaby to większa aktualizacja niż `v0.5`, ponieważ nie dotyczyłaby tylko rekonesansu źródeł, ale całego makroprzepływu: od pozyskania metadanych, przez filtr `ART-only`, po analizy porównawcze i interpretację historyczną.

Prawdopodobne elementy wersji:

- pełny harvesting metadanych PEP-Web dla wybranych czasopism,
- deduplikacja i QA na poziomie wieloczasopismowym,
- jednolity model `article_id`, `journal_key`, `year`, `article_type`, `title`, `abstract_text`, `keywords`,
- korpus główny `ART-only`,
- osobny korpus raw/audit z wszystkimi typami rekordów,
- title-based discourse mapping,
- abstract-based semantic mapping,
- opcjonalna warstwa keyword-based dla nowszych rekordów,
- porównywalna periodyzacja między czasopismami,
- analiza trendów po journalach i okresach,
- analiza wspólnych oraz specyficznych osi dyskursu psychoanalitycznego,
- metody porównywania czasopism o różnej długości historii i różnej kulturze metadanych,
- dokumentacja ograniczeń wynikających z nierównej obecności DOI, keywordów i typów rekordów,
- przygotowanie publikowalnych tabel i figur dla makroanalizy psychoanalytic core.

Wersja `v0.6` mogłaby oznaczać przejście Andromedy od pipeline’u pojedynczego czasopisma do stabilnego modelu **comparative multi-journal discourse analysis**.

---

## Relacja między wersjami

Rozwój Andromedy można streścić następująco:

```text
v0.1
tożsamość agentki, repozytorium, DID

v0.2
pierwszy keyword-based pipeline na korpusie „Psychoterapia”

v0.3
rozszerzony i bardziej audytowalny pipeline na korpusie „Psychiatria Polska”

v0.4
uogólniony, metadata-first pipeline po pracy nad „Archives of Psychiatry and Psychotherapy”

v0.5
planowany source reconnaissance i title/abstract-based pipeline dla psychoanalytic_core

v0.6
możliwy pełny multi-journal comparative pipeline po zakończeniu psychoanalytic_core
```

---

## Zasada interpretacyjna

Każda wersja Andromedy powinna zachowywać podstawową zasadę projektu:

> Andromeda Nowicka wspiera przygotowanie danych, audyt, normalizację, analizę i dokumentację, ale nie zastępuje eksperckiej interpretacji naukowej.

Wyniki generowane przez pipeline powinny być traktowane jako uporządkowane, audytowalne wsparcie dla badacza. Decyzje interpretacyjne, dobór ram teoretycznych i końcowe wnioski pozostają częścią human-in-the-loop research process.

---

## Proponowana polityka aktualizacji

Dla przyszłych wersji zaleca się, aby każda aktualizacja wersji zawierała:

1. krótki opis celu wersji,
2. wskazanie korpusu lub pipeline’u referencyjnego,
3. listę głównych zmian metodologicznych,
4. listę głównych zmian technicznych,
5. opis nowych ograniczeń lub ryzyk,
6. rekomendację, jak cytować lub opisywać daną wersję w pracach naukowych.

