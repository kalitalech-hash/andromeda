# Umysł gracza — rozszerzenie psychoanalytic_core o 8 czasopism

**Andromeda Nowicka v0.5 | pakiet roboczy 2026-11-13**  
**Status: przygotowany i testowany offline; żaden nowy harvest PEP nie został wykonany.**

## Co to robi?

Do istniejących 5 czasopism z `data_psychoanalytic_core/` dodaje **osobną warstwę** 8 czasopism w okresie 1970–2025. Korzysta z istniejącego lokalnie skryptu Lecha `1a_pep_metadata_probe_v12.py`, bez modyfikowania go, bez pobierania PDF-ów ani pełnych tekstów. Wydzielony katalog wyjściowy:

```
andromeda/
  data_psychoanalytic_core/           # istniejące dane Lecha — BEZ ZMIAN
  data_gaming_mind_extension/          # nowa warstwa robocza — DANE NIE DO GIT
     data/probe/
     data/harvest/
     data/qa/
  gaming_mind_extension_bundle/       # niniejszy kod i konfiguracja
```

Pliki **z kodem** można umieścić w repozytorium; pozyskanych danych źródłowych PEP i pliku `.env.pep` nie należy publikować.

## Dla Melisy — tylko jedno zadanie

**Prześlij Lechowi tę paczkę ZIP** z prośbą o wykonanie najpierw testu `probe` i sprawdzenie logów. Nie musisz podawać loginu, hasła ani klucza API i nie musisz ręcznie pobierać danych.

## Dla Lecha — instrukcja uruchomienia

**Wymagania:** lokalne repo `kalitalech-hash/andromeda`, Python z `requests` i `pandas`, poprzedni skrypt `data_psychoanalytic_core/scripts/1a_pep_metadata_probe_v12.py`, skrypt odzyskiwania abstraktów `1e_extract_abstract_texts_from_raw_json.py`, lokalne legalne uprawnienia API.

1. Rozpakować `gaming_mind_extension_bundle/` **w katalogu głównym** repozytorium `andromeda` (obok `data_psychoanalytic_core/`).
2. Zapoznać się z aktualnymi warunkami PEP API i lokalnym zakresem autoryzacji. **Nie uruchamiać próby, jeśli zakres lub zgoda są niejasne.** Nie przesyłać nikomu `.env.pep`.
3. Z katalogu `andromeda/` wyświetlić plan bez sieci:

   ```bash
   python gaming_mind_extension_bundle/gaming_extension.py plan
   ```
4. Jeśli dostęp na takie zapytania jest dozwolony, wykonać mały test ośmiu czasopism (po jednym roku, maks. 25 wyników na źródło):

   ```bash
   python gaming_mind_extension_bundle/gaming_extension.py probe --permission-checked
   ```

5. Sprawdzić `data_gaming_mind_extension/data/probe/manifest.csv`: status HTTP, `n_rows`, `wrong_prefix_ids`. `ok_sample_limited` to poprawny test, w którym celowo ograniczono liczbę rekordów. **W przypadku `wrong_prefix`, `empty`, `http_error`: STOP.**
6. Dopiero po kontroli i **jawnej decyzji badawczej Lecha**, jeśli pozwalają warunki korzystania z API, pełne pobranie metadanych dla lat 1970–2025:

   ```bash
   python gaming_mind_extension_bundle/gaming_extension.py harvest --permission-checked --approved
   ```

### Wznowienie harvestu po zatrzymaniu (bez dublowania pobrań)

Nowy checkpoint sprawdza **manifest, CSV, log HTTP, obecność surowego artefaktu lokalnego oraz prefix ID**. Tylko roczniki ze zweryfikowanym statusem `ok` i spójnymi plikami są pomijane. Pojedynczy niekompletny checkpoint kończy działanie komunikatem STOP; nie jest nadpisywany i nie jest pobierany ponownie automatycznie.

Dla `modern_psychoanalysis`, 2018, zapisano `HTTP 200` i `n_rows=0`. To **nie jest dowód, że czasopismo nie wydało artykułów w 2018**. Najpierw lokalnie zbadaj `data_gaming_mind_extension/data/harvest/logs/modern_psychoanalysis/modern_psychoanalysis_2018_api_log.csv` oraz odpowiadający mu JSON w `.../raw_pep_metadata/modern_psychoanalysis/2018` (nie publikuj payloadu). Sprawdź kwerendę, kształt odpowiedzi i limity dostępu. Jeśli problem nie jest wyjaśniony, zachowaj rok jako **unverified_metadata_gap**, a nie rzeczywiste zero w korpusie.

Po sprawdzeniu lokalnego JSON i uznaniu, że można kontynuować bez rozstrzygania brakującego rocznika, wykonaj **jednorazowo** (z głównego katalogu repo):

```bash
python gaming_mind_extension_bundle/gaming_extension.py harvest --permission-checked --approved --continue-with-gap modern_psychoanalysis:2018 --gap-note "HTTP 200 zero records; local response inspected; gap remains unresolved"
```

Komenda nie powtarza pomyślnych lat; 2018 zostaje ominięty **wyłącznie jako dokumentowana, niezweryfikowana luka** w lokalnym `data_gaming_mind_extension/data/harvest/coverage_gaps.csv`. Jeśli wznowienie zatrzyma się na innym `empty`, skontroluj osobno ten rok i jawnie potwierdź go przez osobny `--continue-with-gap JOURNAL:YEAR`; nie ignoruj innych błędów.

**Uwaga:** `audit` może tworzyć częściowe wyniki robocze także przy lukach; dopóki `summary.json` nie podaje `coverage_complete: true`, nie interpretuj ich jako kompletnego przekroju czasopism 1970–2025. Nie zmieniaj ręcznie manifestu, nie usuwaj dotychczasowych plików i nie ponawiaj automatycznie `empty` ani HTTP 403/429.

7. Po ukończeniu harvestu, lokalna kontrola i selekcja kandydatów (bez sieci):

   ```bash
   python gaming_mind_extension_bundle/gaming_extension.py audit
   ```

8. Do rozmowy przesłać **jedynie po sprawdzeniu zasad przekazywania danych** `data_gaming_mind_extension/data/qa/gaming_candidate_review_queue.csv` oraz `summary.json` (lub tylko ich agregaty). Nie wysyłać surowych odpowiedzi API, tokenów, logów z sekretami ani nie udostępniać surowych abstraktów publicznie.

## Sprawdzone kody z publicznego katalogu PEP — do potwierdzenia próbą API

| Tytuł | PEP identyfikator katalogowy | Pierwszy rok dla badania |
|---|---|---:|
| Contemporary Psychoanalysis | CPS | 1970 |
| British Journal of Psychotherapy | BJP | 1984 |
| Modern Psychoanalysis | MPSA | 1976 |
| Journal of Child Psychotherapy | JCPTX | 1970 |
| Neuropsychoanalysis | NP | 1999 |
| Psychoanalysis, Culture & Society | PCAS | 1996 |
| Psychoanalytic Inquiry | PI | 1981 |
| The Psychoanalytic Quarterly | PAQ | 1970 |

Źródła: oficjalne karty czasopism `https://pep-web.org/journals/<code>`; listy tytułów PEP `https://support.pep-web.org/about-the-pep-archive/pep-journals/`.

**Ważne:** publiczny kod adresu/katalogu nie jest automatycznym potwierdzeniem działania kwerendy `art_id:<CODE>.*`. Stąd obowiązkowy test API, ręczny przegląd kilku rekordów i kontrola identyfikatorów przed pełnym pobieraniem.

## Wyniki po audycie

- `all_records_with_flags.csv` — wiersze z flagami QA, w tym typ artykułu;
- `exclusions_audit.csv` — dokumentowane wykluczenia (non-ART, duplikaty, nieprawidłowy rok/ID);
- `ART_title_abstract_extension.csv` — odrębna warstwa ART + tytuły i odzyskane abstrakty;
- `audit/abstract_extraction_log.csv` — skąd odzyskano abstrakty, **bez kopiowania ich treści do logu**;
- `gaming_candidate_review_queue.csv` — słownikowe trafienia (mocne i kontekstowe), **nie finalna lista artykułów o grach**;
- `summary.json` — maszynowe podsumowanie i diagnostyka;
- `probe/manifest.csv` i `harvest/manifest.csv` — log pozyskania metadanych.

## Metoda i ograniczenia

- Analiza obejmuje **tytuły i abstrakty**, nie pełne artykuły. Wykrycie obecności wyrazu jest kandydaturą, nie kodem konceptualizacji; wszystkie trafienia należy ocenić ręcznie.
- Słownik eksploracyjny obejmuje gry wideo, gaming, platformy, MMO, RPG, CRPG, roguelike, soulslike, walkę turową i nazwy konkretnych gier. `role-playing`, `game`, `avatar`, `gaming` mają niską swoistość i podlegają ręcznej walidacji.
- Różne lata powstania czasopism i nierówna jakość abstraktów wymagają normalizacji do liczby publikacji w danym roku lub okresie oraz analiz wrażliwości. Dla PCAS indeks sięga 1996, mimo że karta wydawcy podaje obecny tytuł od 2004 r.
- Wprowadzono domyślny `ART-only`, ale odrzucone inne typy zachowujemy do ewentualnego przeglądu.
- Jeśli próba zwróci `HTTP 403/429/5xx`, inny prefix lub niepełne wyniki, proces **zatrzymuje się**. Nie próbujemy obchodzić ochrony dostępu.
- Nie nadpisujemy danych Lecha, nie tworzymy PDF mirrorów, nie publikujemy surowych danych PEP.
- **Nie sprawdzałam działania API na żywo**, ponieważ nie posiadam poświadczeń Lecha i nie powinnam ich otrzymać.

## Źródło procedur

Repo: `https://github.com/kalitalech-hash/andromeda` — wykorzystanie istniejących modułów:

- `data_psychoanalytic_core/scripts/1a_pep_metadata_probe_v12.py`
- `data_psychoanalytic_core/scripts/1e_extract_abstract_texts_from_raw_json.py`
- `SCRAPING_POLICY.md` i `robots.md`

Wykorzystanie tych skryptów przez lokalny import nie wymaga ich edycji. Kod pakietu jest przygotowany do przeglądu przez Lecha przed uruchomieniem na żywym API.
