# Andromeda Nowicka v0.5 — etap 01 v0.4 (Fast & Safe)

## Co zmieniono

- Zatwierdzone identyfikatory 5 czasopism są **jawnie zapisane** w `config/corpus.json` (`approved_sources`).
- `source_candidates.csv` zostaje zachowany jako dowód rozpoznania źródeł. Oryginalne wiersze miały błędnie rozdzielone pola ISSN, więc nie wolno odczytywać zgody badacza z jednej pozycji we wszystkich wierszach. Lista pięciu źródeł odpowiada uzgodnieniu w rozmowie i jest walidowana wobec nazw/ID z CSV, **nie wyliczana automatycznie z niewiarygodnej kolumny**.
- Widoczny postęp, komunikaty o opóźnieniach, brak przerwy po ostatnim żądaniu.
- `--sample` (domyślnie): 1 strona × 5 rekordów × 6 zapytań × 5 czasopism (maksymalnie ~150 surowych trafień, przed deduplikacją).
- `--full`: maksymalnie 2 strony × 50 rekordów × 6 zapytań × 5 czasopism (według konfiguracji). Nadal **nie jest to wyszukiwanie wyczerpujące**.
- Atomowy checkpoint po każdej pobranej stronie; Ctrl+C nie usuwa checkpointów.
- Kolejny start z tym samym poleceniem wznawia pracę, pomijając zapisane strony.
- Wszystkie wyniki v0.4 są w **osobnych** katalogach; wcześniejsze wyniki pozostają nienaruszone.
- Blokady 401/403/429/5xx zatrzymują pobieranie, bez obchodzenia ograniczeń.

## Instalacja i umiejscowienie

Rozpakuj paczkę, a następnie z katalogu `data_avatar_therapy_voices_starter`:

1. Podmień `scripts/01_acquire_candidates.py` na nowy plik.
2. Podmień `config/corpus.json` na nowy plik (zachowaj starą wersję, jeśli masz lokalne zmiany).
3. **Zachowaj własny** `outputs/source_candidates.csv`. Plik `source_candidates.csv` w paczce to referencyjna kopia audytu — nie zastępuj własnej.

W terminalu PowerShell:

```powershell
python scripts/01_acquire_candidates.py --audit-only --require-all-five
python scripts/01_acquire_candidates.py --sample --require-all-five --contact-email 'TWOJ_ADRES@UCZELNIA.PL'
```

Po próbie, jeżeli pokrycie tematu jest dobre:

```powershell
python scripts/01_acquire_candidates.py --full --require-all-five --contact-email 'TWOJ_ADRES@UCZELNIA.PL'
```

Nie uruchamiaj jednocześnie kilku kopii tego samego trybu, ponieważ współdzielą checkpointy.

## Wyniki

Dla próbki:

```text
outputs/raw/avatar01_sample_v04/
  run_manifest.json
  source_audit_snapshot.csv
  checkpoints/S..._q01_p001.json
  raw_candidates.csv
  acquisition_log.csv
  acquisition_summary.json
```

Pełny tryb zapisuje do `outputs/raw/avatar01_full_v04/`.

Pole `complete_configured_scope=true` oznacza tylko, że zakończono wszystkie **zaplanowane** ograniczone zapytania. `full_search_exhaustive=false` pozostaje prawdziwe; przegląd całej literatury wymaga odrębnego protokołu.

Wznowienie: uruchom identyczne polecenie. Gdy zmienisz konfigurację (źródła, frazy, daty, rozmiar strony), wybierz nowy `--output-dir` (np. `outputs/raw/run2`) — nie mieszaj przebiegów. Również `--full` i `--sample` mają oddzielne katalogi.

## Uwagi metodologiczne

- Metadane są pobierane z OpenAlex; nie są pobierane PDF ani pełne teksty.
- OpenAlex `search` nie gwarantuje filtrowania tylko po tytule i abstrakcie; kandydatów należy przesiewać ręcznie.
- Abstrakty są rekonstruowane wyłącznie gdy API je udostępnia. Sprawdź prawa do ich dalszego udostępniania.
- Ścieżka analityczna pozostaje: `raw -> QA -> normalization -> HITL semantic audit -> analysis`.

## Testy offline

Testy składni, pięciu uzgodnionych ID, syntetycznej odpowiedzi OpenAlex, checkpointingu i odtworzenia CSV wykonano lokalnie. Nie wykonano rzeczywistych zapytań sieciowych.
