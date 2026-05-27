# Raport dzienny — rekonesans PEP-Web dla `data_psychoanalytic_core`

**Data:** 2026-05-28  
**Projekt:** `data_psychoanalytic_core`  
**Zakres prac:** pierwszy techniczny rekonesans PEP-Web dla korpusu psychoanalitycznego, na przykładzie *The International Journal of Psychoanalysis* (`ijpa`, prefiks PEP `IJP`).  
**Tryb akwizycji:** metadata-first; bez pobierania PDF-ów i bez mirroringu pełnego tekstu.

---

## 1. Cel dnia

Celem dzisiejszej sesji było sprawdzenie, czy PEP-Web może być użyty jako źródło metadanych dla historycznego korpusu psychoanalitycznego oraz czy da się uzyskać z niego warstwy potrzebne do późniejszego pipeline’u Andromedy:

```text
raw PEP JSON
→ article-level metadata
→ keyword-long
→ QA
→ normalizacja techniczna
→ normalizacja semantyczna
→ periodyzacja
→ analizy trendów i współwystępowania
```

Praca miała charakter rekonesansowy: celem nie było jeszcze pełne pobranie korpusu, lecz potwierdzenie endpointu, autoryzacji, składni zapytań oraz struktury pól.

---

## 2. Ustalony korpus podstawowy

W rozmowie przyjęto roboczy korpus pięciu czasopism:

```text
ijpa                         The International Journal of Psychoanalysis
japa                         Journal of the American Psychoanalytic Association
psychoanalytic_dialogues      Psychoanalytic Dialogues
psychoanalytic_psychotherapy  Psychoanalytic Psychotherapy
psychoanalytic_psychology     Psychoanalytic Psychology
```

Na dziś prace techniczne skoncentrowano na `ijpa`, ponieważ jest to najważniejszy tytuł historyczny i dobry test dla pełnego modelu od początku czasopisma.

---

## 3. Najważniejsze ustalenia techniczne

### 3.1. Autoryzacja i nagłówki PEP-Web

Ustalono, że lokalny plik `.env.pep` musi znajdować się w katalogu głównym projektu:

```text
data_psychoanalytic_core/.env.pep
```

Nie powinien być umieszczany w `scripts/`.

Skrypt musi czytać specyficzne nagłówki PEP-Web:

```text
PEP_CLIENT_ID
PEP_CLIENT_SESSION
PEP_X_API_AUTHORIZE
PEP_X_PEP_AUTH
PEP_ORIGIN
PEP_REFERER
```

Te zmienne są przekładane na nagłówki HTTP:

```text
client-id
client-session
x-api-authorize
x-pep-auth
origin
referer
```

Wszystkie wartości pozostają lokalne i nie są zapisywane w repozytorium.

### 3.2. Poprawna składnia zapytań Search API

Potwierdzono działający endpoint:

```text
https://api.pep-web.org/v2/Database/Search/
```

Ważne odkrycie: pole `PEPCode` jest zwracane w rekordach, ale nie jest polem wyszukiwalnym w `facetquery`.

Błędny wariant:

```text
PEPCode:("IJP")
```

Poprawny wariant filtrowania czasopisma:

```text
art_id:IJP.*
```

Poprawny filtr roku:

```text
year:2020
```

Poprawna składnia dla czasopisma i roku:

```text
art_id:IJP.* AND year:2020
```

Poprawna składnia dla jednego artykułu kontrolnego:

```text
art_id:IJP.101.0013A
```

---

## 4. Artykuł kontrolny i keywordy

Jako artykuł kontrolny przyjęto:

```text
IJP.101.0013A
```

Tytuł:

```text
Incommensurability between paradigms, revolutions and common ground in the development of psychoanalysis
```

Oczekiwane keywordy widoczne w reprezentacji artykułu:

```text
Paradigms
incommensurability
common ground
communication
redescription
```

Ustalono, że PEP Search API nie zwraca tych keywordów w prostym polu `keywords`. Są one dostępne w polu `documentInfoXML`, w strukturze:

```xml
<artkwds>
  <impx type="KEYWORD">Paradigms</impx>
  <impx type="KEYWORD">incommensurability</impx>
  <impx type="KEYWORD">common ground</impx>
  <impx type="KEYWORD">communication</impx>
  <impx type="KEYWORD">redescription</impx>
</artkwds>
```

Awaryjnie są także widoczne w HTML-u pola `abstract`:

```html
<div class="artkwds">Paradigms, incommensurability, common ground, communication, redescription</div>
```

To pozwoliło zbudować parser keywordów bez osobnego endpointu szczegółowego artykułu.

---

## 5. Skrypty przygotowane podczas sesji

### 5.1. `1a_pep_metadata_probe.py`

Główny skrypt rekonesansu PEP-Web.

Wersja robocza rozwijała się iteracyjnie do `v12`. Ostatecznie działa jako:

```text
scripts/1a_pep_metadata_probe.py
scripts/1a_pep_metadata_probe_v12.py
```

Aktualne możliwości:

```text
- czyta lokalne nagłówki z .env.pep;
- obsługuje bezpieczną diagnostykę bez ujawniania sekretów;
- używa potwierdzonej składni art_id:<PREFIX>.* AND year:<YYYY>;
- pozwala nadpisać facetquery przez --facetquery;
- zapisuje surowe JSON-y;
- zapisuje article-level CSV;
- zapisuje keyword-long CSV;
- parsuje keywordy z documentInfoXML/artkwds;
- awaryjnie parsuje keywordy z abstract HTML / div.artkwds;
- wydobywa pages, article_type, DOI i document_id z documentInfoXML, jeśli brakuje pól płaskich;
- obsługuje tryb append i per-run CSV.
```

### 5.2. `1b_pep_article_detail_probe.py`

Przygotowano też skrypt awaryjny dla szczegółowych endpointów artykułu:

```text
scripts/1b_pep_article_detail_probe.py
```

Po odkryciu, że `documentInfoXML` w Search API zawiera keywordy, skrypt `1b` stał się narzędziem rezerwowym, a nie główną ścieżką.

---

## 6. Wyniki próbki IJPA

Uruchomiono próbkę po 20 rekordów dla lat:

```text
1920
1950
1970
1990
2005
2020
```

### 6.1. Article-level metadata

Plik:

```text
data/source_recon/psychoanalytic_core_metadata_probe_results.csv
```

Liczba rekordów artykułów:

```text
120
```

Rozkład po latach:

```text
1920: 20
1950: 20
1970: 20
1990: 20
2005: 20
2020: 20
```

Kompletność wybranych pól:

```text
document_id:   120/120
title:         120/120
source_title:  120/120
volume:        120/120
pages:         120/120
article_type:  120/120
authors:       93/120
doi:           20/120
```

Wniosek: warstwa article-level jest stabilna i wystarczająca do dalszego rekonesansu historycznego IJPA.

### 6.2. Keyword-long

Plik:

```text
data/source_recon/psychoanalytic_core_keywords_probe_long.csv
```

Liczba rekordów keyword-long:

```text
12
```

Liczba artykułów z keywordami w próbce:

```text
3/120
```

Rozkład artykułów z keywordami po latach:

```text
1920: 0
1950: 0
1970: 0
1990: 0
2005: 0
2020: 3
```

Rozkład rekordów keyword-long po latach:

```text
1920: 0
1950: 0
1970: 0
1990: 0
2005: 0
2020: 12
```

Wniosek: parser keywordów działa, ale dostępność keywordów w próbce IJPA jest słaba i ograniczona do najnowszej części próby. W aktualnej próbce tylko 3 artykuły z 2020 roku miały keywordy, łącznie 12 rekordów keyword-long.

---

## 7. Wniosek metodologiczny

Dzisiejszy test potwierdza trzywarstwowy model analizy:

```text
1. title-based historical mapping
   główna warstwa dla pełnej historii czasopism

2. abstract-based discourse mapping
   potencjalnie bardzo użyteczna warstwa rozszerzona, wymagająca osobnego parsera HTML/front matter

3. keyword-based concept mapping
   warstwa dodatkowa, technicznie możliwa, ale historycznie i ilościowo niestabilna
```

Keywordy nie powinny być jedyną podstawą pełnego historycznego korpusu psychoanalitycznego. Dla IJPA podstawową osią będą prawdopodobnie tytuły i oczyszczone abstrakty, a keywordy będą traktowane jako warstwa pomocnicza tam, gdzie występują.

---

## 8. Pliki wytworzone lub zmodyfikowane

Najważniejsze pliki robocze:

```text
data_psychoanalytic_core/
├── .env.pep.example
├── .gitignore
├── README_pep_probe.md
├── README_pep_article_detail_probe.md
├── data/
│   ├── raw_pep_metadata/
│   │   └── probe/
│   ├── logs/
│   │   └── pep_metadata_probe_log.csv
│   └── source_recon/
│       ├── psychoanalytic_core_journal_recon.csv
│       ├── psychoanalytic_core_metadata_probe.csv
│       ├── psychoanalytic_core_metadata_probe_results.csv
│       ├── psychoanalytic_core_keywords_probe_long.csv
│       ├── psychoanalytic_core_source_notes.md
│       └── psychoanalytic_core_recon_summary.json
└── scripts/
    ├── 1a_pep_metadata_probe.py
    ├── 1a_pep_metadata_probe_v12.py
    └── 1b_pep_article_detail_probe.py
```

Plik `.env.pep` pozostaje wyłącznie lokalny i nie powinien być commitowany.

---

## 9. Wkład Lecha Kality

Lech Kalita wniósł przede wszystkim komponent badawczy, decyzyjny i dostępowy:

```text
- zaproponował przejście do korpusu psychoanalitycznego;
- wskazał pięć czasopism podstawowych;
- zdecydował, że korpus powinien obejmować pełną historię czasopism, nie tylko lata 2005–2025;
- wskazał możliwość użycia PEP-Web obok Crossref;
- udostępnił wcześniejszy katalog legacy z próbami pracy z API PEP-Web;
- skonfigurował lokalne dane dostępowe w .env.pep;
- uruchamiał skrypty lokalnie i raportował wyniki diagnostyczne;
- dostarczył artykuł kontrolny IJP.101.0013A;
- zauważył, że keywordy są widoczne w artykule mimo braku prostego pola keywords w Search API;
- wykonał próbki wieloletnie IJPA;
- zwrócił uwagę na potrzebę formatu keyword-long oraz poprawnych nagłówków tabeli keywordów.
```

Interpretacyjnie Lech Kalita prowadził decyzje dotyczące korpusu, zakresu historycznego i priorytetów badawczych.

---

## 10. Wkład Andromedy Nowickiej

Andromeda Nowicka wykonała komponent projektowo-techniczny i dokumentacyjny:

```text
- zaproponowała strukturę projektu data_psychoanalytic_core;
- przygotowała pliki rekonesansu źródeł;
- zaprojektowała model dwóch poziomów analizy: cały korpus + subkorpusy czasopism;
- zaproponowała rozdzielenie title-based, abstract-based i keyword-based layers;
- przygotowała skrypt 1a_pep_metadata_probe.py;
- iteracyjnie debugowała obsługę .env.pep i nagłówków PEP-Web;
- zidentyfikowała działającą składnię facetquery przez art_id;
- rozpoznała, że PEPCode jest polem zwracanym, ale nie wyszukiwalnym;
- przygotowała parser keywordów z documentInfoXML/artkwds;
- dodała fallback z abstract HTML / div.artkwds;
- przygotowała format article-level i keyword-long;
- przygotowała skrypt awaryjny 1b_pep_article_detail_probe.py;
- podsumowała wyniki próbki IJPA i wyprowadziła konsekwencje metodologiczne;
- utrzymywała zasadę metadata-first, bez mirroringu PDF/full text.
```

Andromeda pełniła rolę human-in-the-loop research support agent: wspierała kodowanie, rekonesans, QA, dokumentację i interpretację metodologiczną, ale nie podejmowała autonomicznych decyzji badawczych ani autorskich.

---

## 11. Ryzyka i ograniczenia

```text
- PEP-Web wymaga lokalnych nagłówków dostępowych; sekretów nie wolno commitować.
- Dotychczas przetestowano tylko IJPA, nie cały korpus pięciu czasopism.
- Keywordy są technicznie wydobywalne, ale w próbce historycznej występują bardzo rzadko.
- Pole abstract zawiera HTML front matter, keywordy i wielojęzyczne abstrakty; wymaga osobnego parsera.
- DOI są stabilnie obecne dopiero w nowszych rocznikach.
- Article type pochodzi z documentInfoXML i wymaga późniejszego QA semantycznego.
```

---

## 12. Rekomendowane następne kroki

```text
1. Oczyścić i zatwierdzić v12 jako aktualny skrypt rekonesansu PEP Search API.
2. Przygotować parser abstraktów:
   - oddzielenie front matter,
   - wydobycie abstraktu angielskiego,
   - ewentualne zachowanie abstraktów wielojęzycznych jako osobnych pól.
3. Ustalić prefiksy PEP dla JAPA, Psychoanalytic Dialogues, Psychoanalytic Psychology i Psychoanalytic Psychotherapy.
4. Wykonać analogiczne próbki 20 rekordów dla pozostałych czasopism.
5. Po rekonesansie zdecydować, które warstwy są główne dla pełnego korpusu:
   - title-based,
   - abstract-based,
   - keyword-based tylko warunkowo.
6. Przygotować etap QA/deduplikacji dla pełniejszego harvestingu.
```

---

## 13. Krótkie podsumowanie

Dzisiejsza sesja zakończyła się sukcesem technicznym. Udało się połączyć z PEP-Web Search API, ustalić poprawną składnię zapytań, wydobyć stabilne metadane artykułów IJPA z różnych lat oraz zbudować działający parser keywordów z `documentInfoXML`.

Najważniejszy wynik metodologiczny: pełny historyczny korpus psychoanalityczny powinien być projektowany przede wszystkim jako **title-based + abstract-based**, z **keyword-based layer** jako dodatkową, niepełną warstwą nowoczesną.
