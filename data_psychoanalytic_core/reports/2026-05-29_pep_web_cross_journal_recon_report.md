# Raport dzienny — zbiorczy rekonesans PEP-Web dla `data_psychoanalytic_core`

**Data:** 2026-05-29  
**Projekt:** `data_psychoanalytic_core`  
**Zakres prac:** domknięcie rekonesansu źródłowego PEP-Web dla pięciu czasopism korpusu psychoanalitycznego.  
**Tryb akwizycji:** metadata-first; bez pobierania PDF-ów i bez mirroringu pełnego tekstu.  
**Status:** rekonesans próbkujący zakończony; rekomendowane przejście do przygotowania pełniejszego harvestingu metadanych `ART-only`.

---

## 1. Cel sesji

Celem sesji było rozszerzenie wcześniejszego rekonesansu PEP-Web, rozpoczętego od *The International Journal of Psychoanalysis* (`ijpa`, prefiks `IJP`), na pozostałe tytuły roboczego korpusu psychoanalitycznego:

```text
japa                         Journal of the American Psychoanalytic Association
psychoanalytic_dialogues     Psychoanalytic Dialogues
psychoanalytic_psychology    Psychoanalytic Psychology
psychoanalytic_psychotherapy Psychoanalytic Psychotherapy
```

Praca miała charakter rekonesansowy. Celem nie było jeszcze pełne pobranie korpusu, lecz potwierdzenie:

```text
- poprawnych prefiksów PEP;
- działania Search API dla kolejnych tytułów;
- stabilności warstwy article-level metadata;
- dostępności abstraktów;
- dostępności keywordów;
- rozkładu article_type;
- zasadności filtra ART-only dla głównego korpusu analitycznego.
```

---

## 2. Ustalony korpus i potwierdzone prefiksy PEP

Po obecnym etapie pięć podstawowych czasopism ma następujący status:

| journal_id | Tytuł | Prefiks PEP | Status |
|---|---|---:|---|
| `ijpa` | *The International Journal of Psychoanalysis* | `IJP` | potwierdzony wcześniej |
| `japa` | *Journal of the American Psychoanalytic Association* | `APA` | potwierdzony w tej sesji |
| `psychoanalytic_dialogues` | *Psychoanalytic Dialogues* | `PD` | potwierdzony w tej sesji |
| `psychoanalytic_psychology` | *Psychoanalytic Psychology* | `PPSY` | potwierdzony w tej sesji |
| `psychoanalytic_psychotherapy` | *Psychoanalytic Psychotherapy* | `PPTX` | potwierdzony w tej sesji |

Dla wszystkich tytułów potwierdzono, że właściwą logiką filtrowania czasopisma w PEP Search API jest prefiks `art_id`, np.:

```text
art_id:APA.* AND year:2020
art_id:PD.* AND year:2024
art_id:PPSY.* AND year:2024
art_id:PPTX.* AND year:2024
```

---

## 3. Skrypty i rozwiązania techniczne

### 3.1. Skrypt bazowy

Podstawą pozostał istniejący skrypt:

```text
data_psychoanalytic_core/scripts/1a_pep_metadata_probe_v12.py
```

Nie tworzono osobnego klienta PEP API. Dla kolejnych czasopism przygotowano cienkie wrappery, które:

```text
- wywołują `1a_pep_metadata_probe_v12.py`;
- ustawiają właściwy `--journal` albo jawny `--facetquery`;
- zapisują outputy do standardowych katalogów repo;
- przekazują ścieżki absolutne, aby uniknąć błędu `raw_path.relative_to(PROJECT_ROOT)` na Windowsie;
- nie pobierają PDF-ów;
- nie mirrorują pełnych tekstów.
```

### 3.2. Wrappery przygotowane podczas sesji

```text
data_psychoanalytic_core/scripts/1a_pep_japa_probe.py
data_psychoanalytic_core/scripts/1a_pep_psychoanalytic_dialogues_probe.py
data_psychoanalytic_core/scripts/1a_pep_psychoanalytic_psychology_probe.py
data_psychoanalytic_core/scripts/1a_pep_psychoanalytic_psychotherapy_probe.py
```

Dla `psychoanalytic_psychotherapy` zastosowano jawny `--facetquery` z prefiksem `PPTX`, ponieważ prefiks został potwierdzony w toku rekonesansu, a wcześniejsze mapowanie w `v12` mogło być jeszcze placeholderem.

---

## 4. Globalna decyzja metodologiczna: `ART-only`

W tej sesji przyjęto globalną zasadę dla głównego korpusu psychoanalitycznego:

```text
article_type == "ART" → główny korpus analityczny
article_type != "ART" → raw/audit layer, wyłączone z głównej analizy
```

W PEP metadata typ `ART` traktowany jest operacyjnie jako marker właściwych artykułów merytorycznych / original papers. Inne typy rekordów, takie jak `REV`, `COM`, `REP`, `ABS`, `ANN`, `ERA`, `SUP` i inne materiały redakcyjne lub paratekstowe, powinny zostać zachowane w warstwach raw i audit, ale wyłączone z głównego datasetu analitycznego.

Decyzja ta ma trzy uzasadnienia:

```text
1. poprawia porównywalność między czasopismami;
2. ogranicza wpływ recenzji, komentarzy, sprawozdań i materiałów redakcyjnych;
3. stabilizuje interpretację title-based i abstract-based discourse mapping.
```

Filtr nie powinien być stosowany przez ciche kasowanie rekordów. Każdy pełny harvesting powinien zapisywać:

```text
<journal>_articles_raw.csv
<journal>_articles_ART_only.csv
<journal>_articles_excluded_non_ART.csv
<journal>_article_type_summary.csv
```

---

## 5. Wyniki zbiorcze próbkowania

| Tytuł | Prefiks | Lata próby | Rekordy | Abstracts | DOI | Artykuły z keywordami | Keyword rows | ART-only |
|---|---:|---|---:|---:|---:|---:|---:|---:|
| *The International Journal of Psychoanalysis* | `IJP` | 1920, 1950, 1970, 1990, 2005, 2020 | 120 | stabilne w próbie | 20/120 | 3/120 | 12 | do przeliczenia w QA |
| *Journal of the American Psychoanalytic Association* | `APA` | 1953, 1970, 1990, 2005, 2020 | 100 | 100/100 | 18/100 | 2/100 | 19 | 43/100 |
| *Psychoanalytic Dialogues* | `PD` | 1991, 2000, 2010, 2020, 2024 | 100 | 100/100 | 60/100 | 0/100 | 0 | 59/100 |
| *Psychoanalytic Psychology* | `PPSY` | 1984, 1995, 2005, 2015, 2024 | 100 | 100/100 | 36/100 | 27/100 | 120 | 55/100 |
| *Psychoanalytic Psychotherapy* | `PPTX` | 1987, 1995, 2005, 2015, 2024 | 91 | 91/91 | 47/91 | 29/91 | 141 | 61/91 |

Uwaga: dla IJPA dane liczbowe pochodzą z wcześniejszego raportu rekonesansu. W obecnej sesji nie przeliczano jeszcze rozkładu `ART` vs non-ART dla IJPA w takim samym trybie jak dla pozostałych tytułów.

---

## 6. Wyniki per journal

### 6.1. JAPA — *Journal of the American Psychoanalytic Association*

**Prefiks PEP:** `APA`  
**Artykuł kontrolny:** `APA.068.0583A`  
**Status prefiksu:** potwierdzony.

Najpierw wykonano test kontrolny na artykule:

```text
APA.068.0583A
Allannah Furlong
“Consenting and Assenting to Psychoanalytic Work”
2020, JAPA 68(4):583–613
```

Test kontrolny zakończył się powodzeniem:

```text
flattened records: 1
flattened keyword rows: 5
```

Następnie wykonano próbkę rocznikową po 20 rekordów dla lat:

```text
1953, 1970, 1990, 2005, 2020
```

Wynik:

```text
article-level records: 100
unique document_id: 100
abstracts: 100/100
authors: 92/100
DOI: 18/100
articles with keywords: 2/100
keyword rows: 19
ART-only: 43/100
article_type distribution: ART 43; REV 30; REP 9; COM 6; ABS 6; ERA 2; ANN 2; SUP 2
```

Wniosek: JAPA jest stabilnym źródłem title/abstract. Keywordy występują w próbce tylko w 2020 roku i powinny być traktowane jako warstwa pomocnicza, nie jako główna oś historycznej analizy.

---

### 6.2. *Psychoanalytic Dialogues*

**Prefiks PEP:** `PD`  
**Status prefiksu:** potwierdzony.

Próba objęła po 20 rekordów dla lat:

```text
1991, 2000, 2010, 2020, 2024
```

Wynik:

```text
article-level records: 100
unique document_id: 100
abstracts: 100/100
authors: 100/100
DOI: 60/100
articles with keywords: 0/100
keyword rows: 0
ART-only: 59/100
article_type distribution: ART 59; COM 31; REP 9; REV 1
```

Wniosek: *Psychoanalytic Dialogues* jest bardzo dobrym źródłem title/abstract, ale w próbie nie wykazało żadnej warstwy keywordowej. Roboczo można przyjąć, że czasopismo nie ma stabilnej kultury keywordów w PEP albo nie eksponuje ich w rozpoznanej warstwie `documentInfoXML/artkwds`.

---

### 6.3. *Psychoanalytic Psychology*

**Prefiks PEP:** `PPSY`  
**Status prefiksu:** potwierdzony.

Próba objęła po 20 rekordów dla lat:

```text
1984, 1995, 2005, 2015, 2024
```

Wynik:

```text
article-level records: 100
unique document_id: 100
abstracts: 100/100
authors: 95/100
DOI: 36/100
articles with keywords: 27/100
keyword rows: 120
ART-only: 55/100
article_type distribution: ART 55; COM 22; REV 16; REP 7
```

Rozkład keywordów był historycznie nierówny:

```text
1984: 0 keyword articles
1995: 0 keyword articles
2005: 2 keyword articles
2015: 10 keyword articles
2024: 15 keyword articles
```

Wniosek: *Psychoanalytic Psychology* jest stabilnym źródłem title/abstract i ma wartościową nowoczesną warstwę keywordową, szczególnie od lat 2010. Keywordy pozostają jednak historycznie nierówne i nie powinny zastąpić title/abstract mapping.

---

### 6.4. *Psychoanalytic Psychotherapy*

**Prefiks PEP:** `PPTX`  
**Status prefiksu:** potwierdzony.

Próba objęła lata:

```text
1987, 1995, 2005, 2015, 2024
```

Dla 1987 PEP zwrócił 11 rekordów, nie 20, co może oznaczać ograniczone pokrycie lub mniejszą liczbę rekordów PEP-indexed w tym roku.

Wynik:

```text
article-level records: 91
unique document_id: 91
abstracts: 91/91
authors: 89/91
DOI: 47/91
articles with keywords: 29/91
keyword rows: 141
ART-only: 61/91
article_type distribution: ART 61; REV 19; COM 9; ERA 1; REP 1
```

Rozkład keywordów:

```text
1987: 0 keyword articles
1995: 0 keyword articles
2005: 0 keyword articles
2015: 12 keyword articles
2024: 17 keyword articles
```

Wniosek: *Psychoanalytic Psychotherapy* jest stabilnym źródłem title/abstract, a od około 2015 roku ma bogatą warstwę keywordową. W pełnym harvestingu należy zaktualizować mapowanie `psychoanalytic_psychotherapy -> PPTX` w skrypcie bazowym, aby uniknąć pomocniczych nazw plików z etykietą `nopep`.

---

## 7. Wniosek metodologiczny dla całego korpusu

Zbiorczy rekonesans potwierdza model trzywarstwowy:

```text
1. title-based historical mapping
   główna warstwa dla pełnej historii czasopism;

2. abstract-based discourse mapping
   główna rozszerzona warstwa semantyczna, ponieważ abstrakty są stabilnie obecne w próbkach;

3. keyword-based concept mapping
   warstwa dodatkowa, technicznie wydobywalna, ale historycznie nierówna.
```

Najważniejsza decyzja: **pełny korpus psychoanalityczny powinien być projektowany jako `ART-only + title/abstract-based`, z keywordami jako warstwą pomocniczą dla nowszych rekordów.**

Keywordy są szczególnie słabe lub nieobecne w:

```text
- historycznych rocznikach IJPA;
- historycznych rocznikach JAPA;
- całej próbie Psychoanalytic Dialogues.
```

Keywordy są bardziej użyteczne w:

```text
- Psychoanalytic Psychology od około 2005/2015;
- Psychoanalytic Psychotherapy od około 2015;
- wybranych nowszych rekordach JAPA i IJPA.
```

---

## 8. Pliki wytworzone podczas sesji

Najważniejsze pliki robocze i wynikowe:

```text
data_psychoanalytic_core/
├── scripts/
│   ├── 1a_pep_japa_probe.py
│   ├── 1a_pep_psychoanalytic_dialogues_probe.py
│   ├── 1a_pep_psychoanalytic_psychology_probe.py
│   └── 1a_pep_psychoanalytic_psychotherapy_probe.py
├── data/
│   ├── source_recon/
│   │   ├── japa_pep_metadata_probe_results.csv
│   │   ├── japa_pep_keywords_probe_long.csv
│   │   ├── psychoanalytic_dialogues_pep_metadata_probe_results.csv
│   │   ├── psychoanalytic_dialogues_pep_keywords_probe_long.csv
│   │   ├── psychoanalytic_psychology_pep_metadata_probe_results.csv
│   │   ├── psychoanalytic_psychology_pep_keywords_probe_long.csv
│   │   ├── psychoanalytic_psychotherapy_pep_metadata_probe_results.csv
│   │   └── psychoanalytic_psychotherapy_pep_keywords_probe_long.csv
│   ├── raw_pep_metadata/
│   │   ├── japa_probe/
│   │   ├── psychoanalytic_dialogues_probe/
│   │   ├── psychoanalytic_psychology_probe/
│   │   └── psychoanalytic_psychotherapy_probe/
│   └── logs/
│       ├── japa_pep_metadata_probe_log.csv
│       ├── psychoanalytic_dialogues_pep_metadata_probe_log.csv
│       ├── psychoanalytic_psychology_pep_metadata_probe_log.csv
│       └── psychoanalytic_psychotherapy_pep_metadata_probe_log.csv
```

---

## 9. Wkład Lecha Kality

Lech Kalita wniósł komponent badawczy, decyzyjny, dostępowy i walidacyjny:

```text
- zdecydował o kontynuacji rekonesansu korpusu psychoanalitycznego po etapie IJPA;
- dostarczył kontrolny PDF JAPA `APA.068.0583A`;
- rozpoznał po nazwie pliku, że JAPA jest kodowane w PEP jako `APA`;
- zasugerował użycie istniejącego skryptu IJPA/v12 zamiast tworzenia nowego klienta API;
- uruchamiał lokalnie wrappery i skrypty PEP z właściwymi nagłówkami `.env.pep`;
- raportował wyniki diagnostyczne z terminala;
- potwierdził działanie absolutnych ścieżek na Windowsie;
- dostarczył pliki wynikowe CSV dla JAPA, Psychoanalytic Dialogues, Psychoanalytic Psychology i Psychoanalytic Psychotherapy;
- wskazał, że Psychoanalytic Dialogues prawdopodobnie nie ma stabilnej kultury keywordów w PEP;
- potwierdził prefiks `PPTX` dla Psychoanalytic Psychotherapy;
- podjął decyzję metodologiczną, że główny korpus ma obejmować tylko `article_type == "ART"`.
```

Interpretacyjnie Lech prowadził decyzje dotyczące zakresu korpusu, kolejności rekonesansu, kryterium włączenia oraz praktycznej walidacji PEP API.

---

## 10. Wkład Andromedy Nowickiej

Andromeda Nowicka wykonała komponent projektowo-techniczny, QA i dokumentacyjny:

```text
- zaktualizowała kontekst projektu na podstawie wcześniejszych raportów repo;
- zinterpretowała PDF JAPA jako rekord kontrolny;
- zaproponowała kontynuację rekonesansu po tytułach: JAPA, Psychoanalytic Dialogues, Psychoanalytic Psychology, Psychoanalytic Psychotherapy;
- początkowo przygotowała osobny skrypt JAPA, następnie — po korekcie Lecha — przeszła na właściwszą strategię cienkich wrapperów wokół `v12`;
- zdiagnozowała błąd Windows/pathlib `raw_path.relative_to(PROJECT_ROOT)`;
- przygotowała wrappery z absolutnymi ścieżkami outputów;
- przygotowała wrappery dla JAPA, Psychoanalytic Dialogues, Psychoanalytic Psychology i Psychoanalytic Psychotherapy;
- podsumowała każdy wynik próbkowania pod kątem rekordów, abstraktów, DOI, keywordów i typów artykułów;
- zaproponowała sformalizowanie reguły `ART-only`;
- przygotowała niniejszy raport zbiorczy;
- utrzymywała zasadę metadata-first, bez mirroringu PDF/full text.
```

Andromeda działała jako human-in-the-loop research support agent: wspierała kodowanie, QA, dokumentację i interpretację metodologiczną, ale decyzje badawcze pozostawały po stronie Lecha Kality.

---

## 11. Ryzyka i ograniczenia

```text
- Wyniki mają charakter próbkujący, nie są jeszcze pełnym harvestingiem.
- Keywordy są nierówne historycznie i czasopiśmienniczo.
- Dla Psychoanalytic Dialogues nie wykryto keywordów w próbie, ale należy to sformułować ostrożnie jako wynik rozpoznanej warstwy PEP.
- Dla IJPA rozkład ART vs non-ART powinien zostać przeliczony w następnym etapie wspólnym skryptem QA.
- Dla Psychoanalytic Psychotherapy należy trwale wpisać prefiks `PPTX` do mapowania w `v12` lub jego następcy.
- Pole `abstract` nadal wymaga parsera czyszczącego front matter / HTML.
- `article_type` pochodzi z PEP metadata i wymaga zachowania jako surowej wartości oraz późniejszej kontroli QA.
- DOI są stabilnie obecne głównie w nowszych rocznikach.
- Lokalne nagłówki `.env.pep` pozostają poza repo i nie mogą zostać commitowane.
```

---

## 12. Rekomendowane następne kroki

```text
1. Zaktualizować mapowanie journal → PEP prefix w skrypcie bazowym:
   - `japa` → `APA`;
   - `psychoanalytic_dialogues` → `PD`;
   - `psychoanalytic_psychology` → `PPSY`;
   - `psychoanalytic_psychotherapy` → `PPTX`.

2. Utworzyć etap QA dla wyników rekonesansu:
   - podsumowanie article_type per journal;
   - ART-only vs excluded non-ART;
   - missing authors;
   - missing DOI;
   - missing abstracts;
   - missing keywords;
   - deduplikacja document_id.

3. Przygotować pełniejszy harvesting metadanych `ART-only` dla każdego tytułu.

4. Zaprojektować parser abstraktów:
   - usunięcie front matter;
   - oddzielenie keywordów, jeśli są osadzone w HTML;
   - zachowanie czystego `abstract_text_clean`;
   - flagowanie rekordów z nietypowym HTML.

5. Ustalić strategię periodyzacji historycznej:
   - osobna dla pełnej historii IJPA/JAPA;
   - porównywalna dla nowszych tytułów;
   - możliwa warstwa wspólna od 1991 lub od 2005.

6. Zaplanować pierwszą analizę właściwą jako:
   - title-based ART-only corpus;
   - abstract-based ART-only corpus;
   - keyword-based supplementary modern layer.
```

---

## 13. Krótkie podsumowanie

Sesja zakończyła rekonesans próbkujący pięciu głównych czasopism korpusu psychoanalitycznego. Potwierdzono prefiksy PEP dla JAPA, Psychoanalytic Dialogues, Psychoanalytic Psychology i Psychoanalytic Psychotherapy oraz sprawdzono stabilność warstw metadanych.

Najważniejszy wynik: **pełny korpus psychoanalityczny powinien być budowany jako `ART-only + title/abstract-based`, z keywordami jako dodatkową, nowoczesną i nierówną warstwą pomocniczą.**

Rekonesans źródłowy można uznać za domknięty. Następny etap powinien przejść od próbki do kontrolowanego harvestingu i QA.
