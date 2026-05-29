# Raport uzupełniający — decyzje metodologiczne dotyczące Crossref i `llm_assigned_keywords`

**Data:** 2026-05-28  
**Projekt:** `data_psychoanalytic_core`  
**Powiązany raport:** `2026-05-28_pep_web_recon_report.md`  
**Zakres prac:** doprecyzowanie strategii użycia Crossref oraz koncepcji przypisywania pojęć do abstraktów w rekordach bez oryginalnych keywordów.  
**Tryb pracy:** human-in-the-loop; decyzje badawcze po stronie Lecha Kality, wsparcie projektowo-metodologiczne po stronie Andromedy Nowickiej.

---

## 1. Cel uzupełnienia

Celem tej notatki jest udokumentowanie krótkiej rozmowy metodologicznej po rekonesansie PEP-Web. Rozmowa dotyczyła dwóch kwestii wynikających bezpośrednio z raportu dziennego:

```text
1. Czy warto wykonywać dodatkową akwizycję Crossref, jeśli PEP-Web dostarcza zasadniczo komplet interesujących metadanych?

2. Czy dla historycznych rekordów posiadających abstrakty, ale pozbawionych oryginalnych keywordów, można utworzyć osobną warstwę llm_assigned_keywords?
```

Punktem wyjścia była obserwacja z rekonesansu IJPA, że warstwa article-level z PEP-Web jest stabilna, natomiast keywordy są technicznie wydobywalne, ale historycznie i ilościowo niestabilne. W próbce IJPA keywordy wystąpiły tylko w 3 z 120 rekordów i wyłącznie w najnowszej części próby.

---

## 2. Decyzja robocza dotycząca Crossref

Ustalono, że Crossref nie powinien być traktowany jako równoległe główne źródło korpusu, jeśli PEP-Web dostarcza pełniejsze i bardziej bezpośrednio przydatne metadane dla analizowanego zbioru.

Crossref może jednak zostać użyty jako **warstwa kontrolna i wzbogacająca**, a nie jako osobny pipeline akwizycji.

Rekomendowane funkcje Crossref:

```text
- walidacja DOI;
- wykrywanie literówek lub niespójności w DOI;
- uzupełnianie brakujących pól, jeśli są istotne analitycznie;
- kontrola kompletności korpusu;
- identyfikacja rekordów widocznych w Crossref, a nieobecnych w lokalnym zbiorze PEP;
- porównanie metadanych bibliograficznych tam, gdzie istnieją rozbieżności.
```

Nie rekomenduje się budowania pełnego równoległego korpusu Crossref, ponieważ mogłoby to zwiększyć liczbę kolizji metadanych i obciążyć projekt dodatkowymi decyzjami QA bez proporcjonalnego zysku metodologicznego.

Robocza zasada:

```text
PEP-Web = źródło główne
Crossref = warstwa kontrolna / enrichment / DOI audit
```

Proponowane pliki dla ewentualnego modułu Crossref:

```text
data/source_recon/pep_crossref_doi_check.csv
data/source_recon/pep_crossref_missing_in_pep.csv
data/source_recon/pep_crossref_metadata_differences.csv
data/logs/pep_crossref_enrichment_log.csv
data/source_recon/pep_crossref_check_summary.json
```

---

## 3. Problem historycznego braku keywordów

Raport dzienny wykazał, że dla IJPA keywordy są dostępne tylko w bardzo ograniczonej części próbki. Oznacza to, że klasyczna analiza keyword-based nie może być podstawową metodą dla pełnego historycznego korpusu psychoanalitycznego.

Jednocześnie PEP-Web zawiera warstwę abstraktów, która może stać się podstawą bardziej stabilnego, historycznego mapowania pojęciowego. W związku z tym rozważono utworzenie osobnej warstwy:

```text
llm_assigned_keywords
```

Po dyskusji doprecyzowano, że precyzyjniejsza nazwa robocza powinna brzmieć:

```text
llm_assigned_from_abstract_controlled_vocab
```

Ta warstwa nie oznacza rekonstrukcji oryginalnych historycznych keywordów. Oznacza wtórne przypisanie pojęć analitycznych do abstraktów przy użyciu kontrolowanego słownika zbudowanego na podstawie istniejących keywordów i map semantycznych.

---

## 4. Decyzja robocza dotycząca `llm_assigned_keywords`

Ustalono, że metodologicznie dopuszczalne jest przypisywanie pojęć do abstraktów z użyciem LLM, ale tylko pod warunkiem zachowania czterech zasad:

```text
1. Nie traktować przypisań LLM jako oryginalnych keywordów autorskich lub redakcyjnych.

2. Utworzyć osobną warstwę danych z jednoznacznym keyword_source.

3. Ograniczyć model do kontrolowanego słownika pojęć.

4. Zachować audytowalność: confidence, evidence span, prompt version, model name, vocabulary version i audit decision.
```

Rekomendowana wartość pola `keyword_source`:

```text
llm_assigned_from_abstract_controlled_vocab
```

Dla porównania oryginalne keywordy powinny zachować osobne źródło:

```text
author_keywords
editorial_keywords
pep_extracted_keywords
```

Dzięki temu późniejsze analizy mogą być prowadzone w trzech wariantach:

```text
A. tylko oryginalne keywordy;
B. tylko pojęcia przypisane z abstraktów;
C. warstwa połączona, ale z zachowaniem pola keyword_source.
```

---

## 5. Kontrolowany słownik jako baza wiedzy

Za najlepszy wariant uznano nie swobodne generowanie keywordów z abstraktów, lecz przypisywanie pojęć z kontrolowanego słownika.

Słownik powinien zostać zbudowany na podstawie istniejących keywordów, ale po przejściu przez warstwy normalizacji:

```text
raw extracted keywords
→ technical normalization
→ semantic normalization
→ controlled analytical vocabulary
```

Rekomendowane kolumny słownika:

```text
concept_id
concept_label
concept_label_en
concept_label_pl
source_keyword_variants
scope_note
examples
do_not_use_for
semantic_family
vocabulary_version
review_status
```

Przykładowy rekord słownika:

```text
concept_id: PSYCHOANALYSIS_THEORY_001
concept_label: psychoanalytic theory
scope_note: use for abstracts centrally concerned with psychoanalytic concepts, theory-building, metapsychology, or theoretical development
examples: psychoanalytic theory; metapsychology; theory of psychoanalysis
do_not_use_for: purely clinical case reports without explicit theoretical focus
```

Model LLM powinien wybierać pojęcia wyłącznie z takiego słownika. Ewentualne nowe kategorie mogą być zapisywane tylko jako propozycje do audytu:

```text
candidate_new_concept
```

i nie powinny automatycznie trafiać do głównej warstwy analitycznej.

---

## 6. Proponowany pipeline dla warstwy abstraktowej

Dla rekordów historycznych bez keywordów proponuje się następujący pipeline:

```text
raw PEP abstract HTML
→ abstract parsing and cleaning
→ abstract QA
→ controlled vocabulary construction
→ LLM-assisted concept assignment
→ assignment QA
→ manual audit queue
→ accepted llm_assigned_from_abstract_controlled_vocab layer
→ periodization
→ trend and co-occurrence analyses
```

Warstwa ta pozostaje metodologicznie odrębna od klasycznej warstwy keywordów.

Proponowane pliki:

```text
data/abstracts/pep_abstracts_cleaned.csv
data/semantic/controlled_keyword_vocabulary.csv
data/semantic/llm_assignment_prompt_v1.txt
data/semantic/abstracts_without_keywords_input.csv
data/semantic/llm_assigned_keywords_long.csv
data/semantic/llm_assignment_audit_queue.csv
data/semantic/llm_assignment_validation_report.md
data/semantic/llm_assignment_summary.json
```

---

## 7. Rekomendowane kolumny dla `llm_assigned_keywords_long.csv`

```text
article_id
document_id
pep_code
journal_id
year
title
abstract_text_hash
assigned_concept_id
assigned_concept_label
assignment_rank
assignment_confidence
evidence_span
keyword_source
assignment_method
controlled_vocabulary_version
prompt_version
model_name
review_flag
audit_decision
audit_notes
```

Minimalna wartość `assignment_method`:

```text
llm_controlled_vocab_from_abstract
```

Minimalne wartości `review_flag`:

```text
none
low_confidence
ambiguous_assignment
possible_new_concept
manual_review_needed
```

Minimalne wartości `audit_decision`:

```text
accepted
rejected
modified
merge_required
pending
```

---

## 8. Walidacja procedury

Ustalono, że przed zastosowaniem procedury do pełnego korpusu historycznego należy ją przetestować na artykułach, które posiadają zarówno abstrakty, jak i oryginalne keywordy.

Proponowany test:

```text
1. Wybrać rekordy z abstraktem i oryginalnymi keywordami.
2. Ukryć keywordy przed modelem.
3. Przypisać pojęcia z kontrolowanego słownika na podstawie abstraktu.
4. Porównać przypisania LLM z pojęciami wynikającymi z oryginalnych keywordów.
5. Ocenić zgodność na poziomie rodzin semantycznych, nie tylko literalnych keywordów.
```

Celem walidacji nie jest pełne odtworzenie autorskich keywordów, lecz sprawdzenie, czy procedura daje stabilne, sensowne i audytowalne przypisania pojęciowe.

Proponowane miary:

```text
- exact concept match;
- semantic family match;
- average number of assigned concepts per article;
- proportion of low-confidence assignments;
- proportion of assignments requiring manual review;
- false-positive themes identified in audit;
- missing major themes identified in audit.
```

---

## 9. Konsekwencje metodologiczne

Przyjęta decyzja wzmacnia trzywarstwowy model z raportu dziennego:

```text
1. title-based historical mapping
2. abstract-based discourse mapping
3. keyword-based concept mapping
```

Po tej rozmowie warstwę abstraktową można doprecyzować jako potencjalnie najważniejszą dla historycznego mapowania pojęciowego:

```text
abstract-based controlled concept assignment
```

Natomiast keywordy pozostają warstwą pomocniczą i empirycznie nierównomierną. Oryginalne keywordy są nadal cenne, ale nie powinny wyznaczać pełnego zakresu historycznego dyskursu, ponieważ ich brak w starszych rekordach jest cechą źródła, a nie dowodem braku tematów.

Robocza interpretacja:

```text
- title-based layer: najbardziej kompletna historycznie;
- abstract-based layer: najbardziej obiecująca dla kontrolowanego mapowania tematów;
- original keyword layer: wartościowa, ale niepełna i głównie nowoczesna;
- llm_assigned layer: wtórna, kontrolowana, audytowalna warstwa analityczna.
```

---

## 10. Wkład Lecha Kality

Lech Kalita wniósł komponent badawczy, decyzyjny i koncepcyjny:

```text
- sformułował pytanie, czy Crossref ma sens, jeśli PEP-Web zawiera zasadniczo komplet potrzebnych metadanych;
- wskazał praktyczny problem proporcji nakładu pracy do zysku metodologicznego przy dodatkowym Crossref pipeline;
- zaproponował możliwość utworzenia kategorii keywords-llm-assigned dla rekordów historycznych bez oryginalnych keywordów;
- doprecyzował, że bazą wiedzy dla takich przypisań mogłaby być baza istniejących keywordów;
- wskazał potrzebę wykorzystania istniejącego słownika keywordów jako kontrolowanego punktu odniesienia;
- podkreślił, że rozmowa i decyzje powinny zostać zapisane w dokumentacji projektu;
- jednoznacznie zaznaczył konieczność rozdzielenia wkładu Lecha Kality i wkładu Andromedy.
```

Interpretacyjnie Lech Kalita prowadził decyzję badawczą: uznał, że projekt powinien unikać niepotrzebnego mnożenia źródeł metadanych, a jednocześnie szukać sposobu na odpowiedzialne włączenie abstraktów do historycznego mapowania dyskursu.

---

## 11. Wkład Andromedy Nowickiej

Andromeda Nowicka wniosła komponent metodologiczno-operacyjny i dokumentacyjny:

```text
- zarekomendowała traktowanie Crossref jako warstwy kontrolnej, a nie głównego źródła danych;
- zaproponowała funkcje Crossref: DOI audit, enrichment, metadata differences i missing records check;
- wskazała ryzyko tworzenia równoległego korpusu Crossref przy wystarczającej kompletności PEP-Web;
- doprecyzowała, że llm_assigned_keywords nie powinny być traktowane jako oryginalne keywordy;
- zaproponowała nazwę llm_assigned_from_abstract_controlled_vocab;
- zarekomendowała użycie kontrolowanego słownika zamiast swobodnego generowania keywordów przez LLM;
- zaproponowała strukturę controlled vocabulary;
- zaproponowała kolumny dla pliku llm_assigned_keywords_long.csv;
- zaproponowała tryb zamkniętego słownika oraz osobny tryb candidate_new_concept;
- zaproponowała procedurę walidacji na rekordach mających zarówno abstrakty, jak i oryginalne keywordy;
- przygotowała niniejszą notatkę jako raport uzupełniający spójny ze stylem raportu dziennego.
```

Andromeda działała jako human-in-the-loop research support agent: wspierała konceptualizację, projektowanie pipeline’u, nazewnictwo warstw danych, audytowalność i dokumentację. Decyzje badawcze oraz kierunek interpretacyjny pozostały po stronie Lecha Kality.

---

## 12. Ryzyka i ograniczenia

```text
- LLM-assigned concepts mogą odzwierciedlać współczesną strukturę słownika, a nie historyczny język epoki.
- Abstrakty mogą być nierównomiernie dostępne lub różnie sformatowane w różnych okresach i czasopismach.
- Model może nadmiernie uogólniać tematy albo przypisywać pojęcia bardziej standardowe niż rzeczywisty język artykułu.
- Kontrolowany słownik zbudowany na podstawie nowszych keywordów może niedoreprezentować starsze pojęcia psychoanalityczne.
- Evidence span i manual audit są konieczne, aby ograniczyć arbitralność przypisań.
- Warstwa llm_assigned nie może być mieszana z author/editorial keywords bez zachowania keyword_source.
```

---

## 13. Rekomendowane następne kroki

```text
1. Zachować PEP-Web jako główne źródło metadanych dla data_psychoanalytic_core.
2. Zaprojektować lekki moduł Crossref DOI audit, bez budowania równoległego korpusu Crossref.
3. Przygotować parser czystych abstraktów z pola abstract HTML.
4. Wydobyć wszystkie dostępne oryginalne keywordy z PEP-Web dla testowego zakresu.
5. Zbudować pierwszą wersję controlled_keyword_vocabulary.csv.
6. Przygotować prompt v1 dla LLM-assisted controlled vocabulary assignment.
7. Przeprowadzić walidację na rekordach mających zarówno abstrakty, jak i keywordy.
8. Dopiero po walidacji zdecydować, czy warstwa llm_assigned_from_abstract_controlled_vocab może wejść do pełnego pipeline’u.
```

---

## 14. Krótkie podsumowanie

Rozmowa uzupełniająca doprowadziła do dwóch decyzji roboczych.

Po pierwsze, Crossref nie będzie traktowany jako główna równoległa ścieżka akwizycji, lecz jako lekka warstwa kontrolna dla DOI, braków i rozbieżności metadanych.

Po drugie, dla historycznych rekordów bez oryginalnych keywordów można rozważyć utworzenie warstwy `llm_assigned_from_abstract_controlled_vocab`, ale wyłącznie jako osobnej, wtórnej i audytowalnej warstwy analitycznej. Model LLM nie powinien swobodnie generować keywordów, lecz przypisywać pojęcia z kontrolowanego słownika zbudowanego na bazie istniejących keywordów i ich semantycznej normalizacji.

Najważniejsza zasada dokumentacyjna: w całym projekcie należy konsekwentnie rozdzielać wkład badawczy Lecha Kality od wkładu Andromedy Nowickiej jako narzędzia human-in-the-loop wspierającego projektowanie, kodowanie, QA i dokumentację.
