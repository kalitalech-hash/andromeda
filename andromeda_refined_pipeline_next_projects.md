# Andromeda Nowicka — refined pipeline dla kolejnych projektów bibliometrycznych

Wersja robocza po analizach korpusów: **Psychoterapia**, **Psychiatria Polska** oraz **Archives of Psychiatry and Psychotherapy**.

Dokument jest przeznaczony jako wewnętrzna instrukcja operacyjna dla kolejnych projektów bibliometrycznych i dyskursywnych. Opisuje sprawdzony, audytowalny pipeline: od scrapingu metadanych i słów kluczowych, przez normalizację oraz agregację semantyczną, po analizy trendów, współwystępowania i przygotowanie opisu wyników.

---

## 0. Założenia ogólne

Każdy projekt powinien być prowadzony jako sekwencja jawnych warstw danych. Nie należy nadpisywać wcześniejszych plików, lecz tworzyć kolejne wersje transformacji. Każdy etap powinien zostawiać:

- główny plik wynikowy,
- pliki kontrolne,
- log transformacji,
- krótką notkę metodologiczną do dokumentacji,
- podsumowanie JSON lub CSV z kluczowymi statystykami.

Podstawowa zasada: **surowe dane → dane po QA → normalizacja techniczna → polonizacja i semantyka → audyt → periodyzacja → analizy końcowe → interpretacja**.

---

## 1. Etap 1 — scraping i pozyskanie danych

### Cel

Pozyskać z czasopisma metadane artykułów oraz słowa kluczowe w formacie umożliwiającym dalszą analizę.

### Minimalne pliki wyjściowe

```text
<journal>_issues.csv
<journal>_articles.csv
<journal>_keywords_long.csv
<journal>_scrape_log.csv
```

### Rekomendowane pola w tabeli artykułów

```text
article_id
article_url
source_issue_url
source_issue_label
year
volume
issue_number
title
authors
citation
pages
doi
pdf_url
publication_date
online_publication_date
article_type
abstract_text
n_keywords
```

### Rekomendowane pola w keyword-long

```text
article_id
article_url
year
volume
issue_number
title
keyword_order
keyword_raw
keyword_url
```

### Reguły praktyczne

1. Najpierw rozpoznać strukturę strony:
   - archiwum roczników,
   - strony numerów,
   - strony artykułów,
   - miejsce występowania słów kluczowych,
   - format URL-i,
   - obecność sekcji „online first”, „related”, „latest”, „recommended”.

2. Nie parsować PDF-ów, jeśli keywordy są dostępne w HTML.

3. `Online first` trzymać osobno albo pobierać flagą, ponieważ takie rekordy mogą nie mieć stabilnego roku, tomu lub numeru.

4. Scraper powinien być ostrożny:
   - opóźnienie między zapytaniami,
   - jawny user-agent,
   - log błędów,
   - możliwość ograniczenia zakresu lat.

5. Po scrapingu nie ufać od razu liczbie rekordów. Strony często zawierają globalne linki, które prowadzą do powtórzeń artykułów.

---

## 1a. Etap 1a — QA i deduplikacja

### Cel

Oddzielić właściwy korpus artykułów od powtórzeń, rekordów technicznych i danych spoza zakresu.

### Kontrole obowiązkowe

```text
liczba numerów
liczba rekordów artykułów
liczba unikalnych article_id
liczba unikalnych URL-i
liczba rekordów keyword-long
zakres lat
rekordy poza zakresem
duplikaty article_id
duplikaty article_url
artykuły bez keywordów
top surowych keywordów
rozkład artykułów po latach
```

### Typowe decyzje

- Deduplication key: zwykle `article_id`; awaryjnie `article_url`.
- Rekordy spoza przyjętego zakresu lat wyłączyć z głównego korpusu.
- Artykuły bez keywordów zachować w tabeli artykułów, ale odnotować osobno.
- Jeżeli duplikaty różnią się tylko `source_issue_url` lub `source_issue_label`, deduplikacja po `article_id` jest bezpieczna.

### Minimalne pliki wyjściowe

```text
<journal>_articles_dedup_<years>.csv
<journal>_keywords_long_dedup_<years>.csv
<journal>_article_deduplication_log.csv
<journal>_articles_removed_duplicate_rows.csv
<journal>_keywords_removed_duplicate_rows.csv
<journal>_articles_removed_out_of_scope.csv
<journal>_articles_without_keywords.csv
<journal>_qa_report.md
<journal>_qa_summary.json
```

### Notatka metodologiczna

W dokumentacji należy krótko opisać:
- ile było rekordów surowych,
- ile zostało po deduplikacji,
- jakie kryterium deduplikacji zastosowano,
- ile artykułów bez keywordów zidentyfikowano,
- czy usunięto rekordy spoza zakresu.

---

## 2. Etap 2 — normalizacja techniczna keywordów

### Cel

Ujednolicić zapis słów kluczowych bez wchodzenia jeszcze w interpretację semantyczną.

### Wejście

```text
<journal>_keywords_long_dedup_<years>.csv
```

### Główne operacje

- lowercase,
- normalizacja Unicode,
- trimowanie spacji,
- redukcja wielokrotnych spacji,
- ujednolicenie myślników,
- ujednolicenie ukośników,
- usunięcie końcowej interpunkcji,
- zamiana `&` na `and`,
- zachowanie oryginalnego `keyword_raw`.

### Czego nie robić na tym etapie

- nie tłumaczyć,
- nie polonizować,
- nie scalać szerokich synonimów,
- nie usuwać kategorii merytorycznych ani redakcyjnych bez decyzji audytowej.

### Minimalne kolumny

```text
keyword_raw
keyword_norm
normalization_action
normalization_notes
```

### Minimalne pliki wyjściowe

```text
<journal>_keywords_long_normalized.csv
<journal>_keyword_normalization_map.csv
<journal>_keyword_normalization_collisions.csv
<journal>_keyword_top30_normalized.csv
<journal>_keyword_candidate_merges_for_review.csv
<journal>_keyword_suspicious_after_normalization.csv
<journal>_normalization_report.md
<journal>_normalization_summary.json
```

### Kontrola jakości

Porównać:
- liczbę surowych unikalnych keywordów,
- liczbę keywordów po normalizacji,
- liczbę wariantów połączonych technicznie,
- puste wartości po normalizacji.

---

## 3. Etap 3 — polonizacja i scalenie semantyczne

### Cel

Przekształcić technicznie znormalizowane keywordy w polskie pojęcia analityczne.

Etap 3 powinien być iteracyjny. Zalecana struktura:

```text
3a — konserwatywna polonizacja i oczywiste scalenia
3b — usunięcie kategorii redakcyjnych i szersze scalenia
3c — pełniejsza polonizacja oraz automatyzacja średniego audytu
3d — szeroka agregacja do rodzin tematycznych
3e — decyzje ręcznego audytu i finalizacja
```

---

### 3a. Konserwatywna polonizacja

Scalać automatycznie:

- warianty liczby pojedynczej i mnogiej,
- warianty brytyjsko-amerykańskie,
- skróty jednoznaczne,
- różnice interpunkcyjne,
- różnice zapisu z dywizem,
- jednoznaczne równoważniki kliniczne.

Przykłady:

```text
CBT / cognitive-behavioral therapy / cognitive behavioural therapy
→ terapia poznawczo-behawioralna

PTSD / post-traumatic stress disorder
→ zespół stresu pourazowego

OCD / obsessive-compulsive disorder
→ zaburzenie obsesyjno-kompulsyjne
```

Nie scalać jeszcze pojęć bliskich, ale klinicznie nierównoważnych, chyba że projekt wymaga wyższego poziomu agregacji.

---

### 3b. Usuwanie kategorii redakcyjnych i szersze scalenia

Typowa kategoria do wyłączenia:

```text
editorial
editorial 1
editorial 2
editorial 3
```

Decyzja powinna być jawna i zapisana jako osobny etap, np.:

```text
exclude_candidate_editorial → excluded
```

W tym etapie można scalać większe rodziny:

```text
depression, depressive disorder, depressive symptoms
→ depresja i zaburzenia depresyjne

anxiety, anxiety disorder, generalized anxiety disorder
→ lęk i zaburzenia lękowe

suicide, suicidal ideation, suicide attempt
→ samobójczość
```

---

### 3c. Pełniejsza polonizacja i akceptacja średniego audytu

Jeżeli wcześniejszy audyt potwierdza jakość reguł, można zaufać średnio ryzykownym scaleniom i pozostawiać do ręcznego przeglądu tylko przypadki mocno problematyczne.

Kolumny rekomendowane:

```text
keyword_concept_en_final
keyword_concept_polish_final
keyword_semantic_id
semantic_action
semantic_confidence
polish_translation_method
review_flag
```

---

### 3d. Szeroka agregacja do rodzin tematycznych

Ten etap jest potrzebny, gdy liczba pojęć jest zbyt duża do stabilnych analiz trendów i sieci.

Ważna zasada: to nie jest już tylko scalanie synonimów, ale **mapowanie do rodzin tematycznych**.

Przykłady rodzin:

```text
schizofrenia i zaburzenia psychotyczne
depresja i zaburzenia depresyjne
lęk i zaburzenia lękowe
trauma, PTSD i zaburzenia stresowe
zaburzenia osobowości i cechy osobowości
psychoterapia i proces terapeutyczny
interwencje terapeutyczne i rehabilitacja
ocena kliniczna, psychometria i narzędzia pomiarowe
metodologia badań i projekt badawczy
choroby somatyczne i współchorobowość medyczna
COVID-19 i pandemia
dzieci, adolescenci i rodzina
funkcjonowanie społeczne i wsparcie społeczne
emocje, afekt i regulacja emocji
```

W praktyce dobrym celem jest redukcja do około **500–600 pojęć analitycznych**, jeśli korpus startuje z około 1500–2000 surowych wariantów.

Nie tworzyć jednej wielkiej kategorii „inne”, bo ukrywa heterogeniczność danych.

---

### 3e. Audyt końcowy

Po automatycznych etapach zostawić tylko małą kolejkę pojęć wymagających mocnego audytu.

Typowe decyzje audytowe:

```text
keep      = zostaw bez zmian
merge     = scal z istniejącą kategorią
rename    = popraw nazwę
exclude   = usuń z analiz
```

Decyzje audytowe aplikować jako osobną warstwę, np.:

```text
<journal>_keywords_long_polish_semantic_final.csv
```

Kolumna główna do analiz:

```text
keyword_concept_polish_analysis
```

### Minimalne pliki wyjściowe etapu 3

```text
<journal>_keywords_long_polish_semantic_final.csv
<journal>_semantic_map.csv
<journal>_semantic_merges_log.csv
<journal>_semantic_concept_counts.csv
<journal>_semantic_audit_queue.csv
<journal>_semantic_excluded_records.csv
<journal>_semantic_summary.json
<journal>_semantic_report.md
```

### Główne miary do raportowania

```text
surowe unikalne keywordy
unikalne keywordy po normalizacji
pojęcia po konserwatywnym scaleniu
pojęcia po szerokiej agregacji
pojęcia po audycie
liczba wyłączonych rekordów
liczba wyłączonych pojęć
finalna liczba pojęć analitycznych
procent redukcji
```

---

## 4. Etap 4 — podział na okresy analityczne

### Cel

Przygotować dane do analiz trendów.

### Zasada

Okresy muszą być spójne z celem porównawczym projektu. Dla analiz analogicznych do korpusu „Psychoterapii” stosować:

```text
2005–2009
2010–2014
2015–2019
2020–2025
```

### Kolumny

```text
analysis_period
analysis_period_order
```

### Kontrole

- liczba rekordów keyword-long po okresach,
- liczba artykułów po okresach,
- liczba unikalnych pojęć po okresach,
- rekordy bez roku,
- rekordy poza zakresem.

### Minimalne pliki wyjściowe

```text
<journal>_keywords_long_periodized.csv
<journal>_period_summary.csv
<journal>_year_summary.csv
<journal>_concept_period_counts.csv
<journal>_top30_concepts_by_period.csv
<journal>_article_period_summary.csv
<journal>_periodization_report.md
<journal>_periodization_summary.json
```

---

## 5. Etap 5 — analizy końcowe

### Cel

Wytworzyć zestaw tabel, trendów, sieci i figur do interpretacji wyników.

### Analizy obowiązkowe

1. Statystyki opisowe po okresach:
   - liczba artykułów,
   - liczba przypisań artykuł–pojęcie,
   - średnia i mediana liczby pojęć na artykuł,
   - liczba unikalnych pojęć.

2. Top pojęcia ogółem:
   - liczba artykułów,
   - udział procentowy artykułów.

3. Top pojęcia po okresach.

4. Macierz trendów:
   - liczba artykułów z pojęciem w każdym okresie,
   - udział procentowy w okresie,
   - zmiana między pierwszym i ostatnim okresem,
   - okres szczytowy,
   - liczba okresów, w których pojęcie występuje.

5. Tematy rosnące:
   - sortowane po wzroście udziału procentowego.

6. Tematy malejące:
   - sortowane po spadku udziału procentowego.

7. Tematy emergentne:
   - nieobecne w pierwszym okresie,
   - obecne w ostatnim okresie.

8. Tematy trwałe:
   - obecne we wszystkich okresach.

9. Współwystępowanie:
   - na poziomie artykułów,
   - dwa pojęcia łączone, jeśli występują w tym samym artykule.

10. Sieć filtrowana:
   - rekomendowany próg początkowy: waga >= 3,
   - raportować liczbę krawędzi, węzłów i klastrów.

11. Klasteryzacja:
   - np. greedy modularity communities,
   - opisać top pojęcia w klastrach.

### Minimalne pliki wyjściowe

```text
<journal>_stage5_period_descriptives.csv
<journal>_stage5_top_concepts_overall.csv
<journal>_stage5_concept_period_counts.csv
<journal>_stage5_concept_trends_wide.csv
<journal>_stage5_rising_topics.csv
<journal>_stage5_falling_topics.csv
<journal>_stage5_emerging_topics.csv
<journal>_stage5_persistent_topics.csv
<journal>_stage5_article_concepts.csv
<journal>_stage5_cooccurrence_edges_all.csv
<journal>_stage5_cooccurrence_edges_filtered.csv
<journal>_stage5_network_nodes.csv
<journal>_stage5_network_communities.csv
<journal>_stage5_final_analysis_report.md
<journal>_stage5_summary.json
```

### Figury rekomendowane

```text
fig1_articles_by_period.png
fig2_top20_overall.png
fig3_top25_period_heatmap.png
fig4_rising_topics.png
fig5_falling_topics.png
fig6_cooccurrence_network_top40.png
```

### Uwaga interpretacyjna

Przy trendach używać udziałów procentowych w okresach, nie tylko surowych liczebności, bo liczba artykułów w kolejnych okresach zwykle rośnie.

---

## 6. Etap 6 — raport wyników i wstępna interpretacja

### Cel

Przygotować opis wyników w stylu artykułowym, bez jeszcze przechodzenia do analizy porównawczej, chyba że taki jest cel projektu.

### Struktura opisu

1. Krótki opis korpusu:
   - zakres lat,
   - liczba artykułów,
   - liczba pojęć,
   - sposób agregacji.

2. Dominujące osie tematyczne:
   - top kategorie,
   - ich udział w korpusie,
   - znaczenie dla profilu czasopisma.

3. Trendy wzrostowe:
   - nowe i rosnące tematy,
   - możliwe czynniki historyczne lub kliniczne.

4. Trendy spadkowe:
   - ostrożna interpretacja spadku udziału,
   - podkreślenie, że spadek procentowy nie oznacza zaniku tematu.

5. Złożoność tematyczna:
   - liczba pojęć na artykuł,
   - wzrost heterogeniczności,
   - poszerzanie pola problemowego.

6. Sieć współwystępowania:
   - czy dyskurs jest rozproszony czy zorganizowany,
   - liczba klastrów,
   - ogólne osie organizujące.

7. Wnioski robocze:
   - profil czasopisma,
   - przesunięcia tematyczne,
   - kwestie do dalszej analizy.

### Ton

- ostrożny,
- interpretacyjny, ale nie nadmiernie kategoryczny,
- jawnie oparty na słowach kluczowych,
- świadomy ograniczeń metod keyword-based analysis.

---

## 7. Standard dokumentacji projektu

Po każdym etapie tworzyć krótką notkę do dokumentacji. Notka powinna zawierać:

```text
co zrobiono
na jakich plikach pracowano
jakie decyzje podjęto
ile rekordów / pojęć uzyskano
jaki plik przyjęto do kolejnego etapu
jakie ograniczenia lub ryzyka odnotowano
```

Preferowana długość: 1–4 akapity.

---

## 8. Zasady audytowalności

Każda transformacja powinna być odwracalna lub przynajmniej możliwa do odtwórzenia z logów.

W szczególności trzeba zachowywać:

```text
keyword_raw
keyword_norm
keyword_concept_en
keyword_concept_polish
keyword_concept_polish_analysis
semantic_action
semantic_confidence
review_flag
audit_decision
```

Nie usuwać rekordów bez śladu. Każde wyłączenie musi mieć osobny plik:

```text
excluded_records.csv
manual_exclusion_decisions.csv
```

---

## 9. Rekomendowana struktura folderu nowego korpusu

```text
data_<journal>/
├── README.md
├── requirements_<journal>.txt
├── data/
│   ├── raw/
│   ├── qa/
│   ├── normalized/
│   ├── semantic/
│   ├── periodized/
│   └── analyses/
└── scripts/
    ├── 1_scrape_<journal>.py
    ├── 1a_qa_deduplicate_<journal>.py
    ├── 2_normalize_keywords_<journal>.py
    ├── 3_semantic_polonize_<journal>.py
    ├── 3d_broad_semantic_aggregation_<journal>.py
    ├── 4_periodize_<journal>.py
    └── 5_final_analyses_<journal>.py
```

---

## 10. Minimalny zestaw pytań do badacza przed projektem

1. Jakie czasopismo lub baza danych?
2. Jaki zakres lat?
3. Czy uwzględniać online-first?
4. Czy analizujemy tylko artykuły oryginalne, czy także review, case reports, editorials?
5. Czy keywordy mają być analizowane w języku oryginalnym, po polsku, czy dwujęzycznie?
6. Jaki poziom agregacji jest celem:
   - niski: blisko oryginalnych keywordów,
   - średni: synonimy i warianty,
   - wysoki: rodziny tematyczne.
7. Czy projekt będzie porównywany z wcześniejszymi korpusami?
8. Jakie okresy analityczne mają być użyte?

---

## 11. Krytyczne lekcje z dotychczasowych projektów

1. Scraping prawie zawsze wymaga QA, bo strony zawierają powtórzenia, globalne linki i sekcje nietematyczne.
2. Normalizacja techniczna daje niewielką redukcję, ale jest konieczna dla audytowalności.
3. Największa redukcja pojawia się dopiero przy szerokiej agregacji semantycznej.
4. Dla analiz trendów lepsze są rodziny tematyczne niż bardzo drobne keywordy.
5. Należy raportować zarówno liczby rekordów keyword-long, jak i liczby artykułów, bo powtarzające się pojęcia w jednym artykule mogą zaburzać interpretację.
6. Trendy należy interpretować procentowo względem liczby artykułów w okresie.
7. Kategorie redakcyjne typu `editorial` powinny być identyfikowane wcześnie i wyłączane decyzją audytową.
8. Ręczny audyt powinien być mały i celowany, nie powinien obejmować całego słownika.
9. Nie należy tworzyć kategorii „inne”, jeśli można zachować heterogeniczne resztki jako osobne, rzadkie kategorie albo jawnie je wyłączyć.
10. Raport wyników powinien podkreślać, że analiza dotyczy słów kluczowych, a więc mapuje samoopis artykułów, nie pełną treść publikacji.

---

## 12. Domyślna formuła acknowledgment

Jeżeli system jest wykorzystywany w pracy naukowej, rekomendowane jest ujęcie go jako narzędzia wsparcia badawczego, nie jako współautora:

```text
Bibliometric data preparation and semantic keyword normalization were supported by the research agent Andromeda Nowicka (v0.2), a human-in-the-loop computational bibliometrics system developed under the supervision of Lech Kalita.
```

Formalny zapis metodologiczny:

```text
Andromeda Nowicka (v0.2). HITL bibliometric analysis agent for discourse mapping. Controller: Lech Kalita. DID: did:web:kalitalech-hash.github.io:andromeda.
```
