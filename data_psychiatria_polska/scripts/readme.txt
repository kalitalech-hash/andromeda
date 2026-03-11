# Psychiatria Polska — skrypty analityczne

Paczka zawiera dwa repo-ready skrypty odpowiadające pipeline’owi użytemu do pracy nad korpusem słów kluczowych czasopisma „Psychiatria Polska”.

## Zawartość

- `01_clean_keywords_pp.py` — ramowy skrypt czyszczenia i semantycznego scalania słów kluczowych
- `02_analysis_pipeline_pp.py` — główny pipeline analityczny: statystyki opisowe, okresy analityczne, trendy, sieć współwystępowania, klastry, tabele i ryciny
- `requirements.txt`

## Oczekiwane pliki wejściowe

### Warstwa wstępnie oczyszczona
`pp_keywords_cleaned.csv`

Kolumny:
- `url`
- `year`
- `volume`
- `issue`
- `doi`
- `keyword_raw`
- `keyword_norm`

### Warstwa finalna po scalaniu
`pp_keywords_final_clean_v7.csv`

Kolumny:
- `url`
- `year`
- `volume`
- `issue`
- `doi`
- `keyword_final_polish`

## Uruchamianie

### Czyszczenie / scalanie
```bash
python 01_clean_keywords_pp.py --input pp_keywords_cleaned.csv --output pp_keywords_final_clean_generated.csv --log pp_keyword_transform_log.csv