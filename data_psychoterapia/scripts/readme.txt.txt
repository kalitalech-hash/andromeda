# Psychoterapia — skrypty analityczne

Paczka zawiera dwa repo-ready skrypty odpowiadające pipeline’owi użytemu do pracy nad korpusem słów kluczowych czasopisma **„Psychoterapia”**.

## Zawartość

- `01_prepare_long_semantic_psychoterapia.py`  
  Ramowy skrypt czyszczenia, polonizacji i semantycznego scalania słów kluczowych.
- `02_analysis_pipeline_psychoterapia.py`  
  Główny pipeline analityczny: statystyki opisowe, okresy analityczne, trendy, sieć współwystępowania, klastry, tabele i ryciny.
- `requirements.txt`

## Pliki wejściowe

### 1. Warstwa metadanych artykułów
`raw_articles.csv`

Kolumny:
- `year`
- `issue_label`
- `item_type`
- `title`
- `url`

Ta warstwa **nie zawiera słów kluczowych**. Sama nie wystarcza do odtworzenia warstwy keyword-long bez osobnego etapu scrapingu / ekstrakcji słów kluczowych.

### 2. Warstwa finalna po przygotowaniu semantycznym
`keywords_long_polish_semantic.csv`

Kolumny:
- `year`
- `issue_label`
- `item_type`
- `title`
- `url`
- `keyword`
- `keyword_raw`
- `keyword_norm`
- `keyword_final`
- `keyword_pl`
- `keyword_norm_auto`
- `keyword_concept_auto`
- `keyword_semantic_auto`

## Jak rozumieć pakiet

Scrapery i ekstrakcja słów kluczowych z witryny czasopisma są już w repozytorium projektu i nie są częścią tej paczki.

Dlatego paczka obejmuje:
1. **ramowy skrypt od warstwy keyword-long po scrapingu do warstwy `long_semantic`**,  
2. **pełny pipeline analityczny** pracujący na warstwie `keywords_long_polish_semantic.csv`.

## Uruchamianie

### Przygotowanie warstwy semantycznej
```bash
python 01_prepare_long_semantic_psychoterapia.py \
  --input keywords_long_raw.csv \
  --output keywords_long_polish_semantic_generated.csv \
  --log psychoterapia_keyword_transform_log.csv