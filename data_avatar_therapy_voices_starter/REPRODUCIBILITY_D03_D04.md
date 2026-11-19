# Reprodukcja analiz D03–D04 i ryciny publikacyjnej

**Workspace:** `data_avatar_therapy_voices_starter/`. Uruchamiaj poniższe polecenia z tego katalogu. Wszystkie etapy wykorzystują lokalne dane w repozytorium, **bez nowych zapytań OpenAlex, PDF-ów ani full-text mining**.

## Wersjonowane wejścia

- `outputs/qa/avatar01_full_strict_v05/analysis_corpus_ABC.csv` — 266 po selekcji tematycznej, filtrowane w D03 do `publication_type=article`, n=209 (A=12, B=184, C=13).
- `outputs/analyses/avatar_discourse_D02_v01/candidate_article_concepts.csv` — 414 kandydackich przypisań.
- `outputs/analyses/avatar_discourse_D02_v01/semantic_map_provisional.csv` — 89 fraz i 23 pojęcia.
- Badacz potwierdził trafność wszystkich pojęć kandydackich; w D03 akceptacja dotyczy słownika, **nie** kontekstowej walidacji każdego artykułu.
- `outputs/analyses/avatar_discourse_D03_v01/terms_semantic_final.csv` — zatwierdzona pochodna warstwa semantyczna.
- `outputs/analyses/avatar_discourse_D04_anchor_maps_v01/strict_ego_edges.csv` — źródło publikacyjnej ryciny.

## Odtwarzanie

```powershell
python scripts/06_approved_semantic_analysis_D03.py --corpus outputs/qa/avatar01_full_strict_v05/analysis_corpus_ABC.csv --assignments outputs/analyses/avatar_discourse_D02_v01/candidate_article_concepts.csv --mapping outputs/analyses/avatar_discourse_D02_v01/semantic_map_provisional.csv --output-dir outputs/analyses/avatar_discourse_D03_REPRO_v01 --researcher-approved

python scripts/07_focused_avatar_vr_D04.py --corpus outputs/qa/avatar01_full_strict_v05/analysis_corpus_ABC.csv --terms outputs/analyses/avatar_discourse_D03_REPRO_v01/terms_semantic_final.csv --out-dir outputs/analyses/avatar_discourse_D04_REPRO_v01

python scripts/08_render_D04_publication_figure.py --edges outputs/analyses/avatar_discourse_D04_REPRO_v01/strict_ego_edges.csv --output outputs/analyses/avatar_discourse_D04_FIGURE_REPRO_v01/FIGURE_1_AVATAR.svg
```

Każdy skrypt używa nowego katalogu docelowego; **nie nadpisuj** historycznych warstw. Skrypt ryciny wymaga siedmiu znanych krawędzi AVATAR i zatrzyma się, jeśli zmieni się struktura sieci.

## Kontrola spójności (oczekiwane liczby)

| Miara | Oczekiwane |
|---|---:|
| Artykuły po filtrze A/B/C + `article` | 209 |
| Pojęcia zatwierdzone | 23 |
| Warianty terminów | 89 |
| Pary artykuł–pojęcie | 414 |
| Artykuły z co najmniej jednym pojęciem | 192 |
| Artykuły bez dopasowań | 17 |
| Wszystkie różne pary pojęć | 102 |
| Strict AVATAR therapy | 7 |
| Strict VR intervention | 3 |
| Krawędzie AVATAR, bez progu n | 7 |
| Krawędzie VR, bez progu n | 1 |
| Wzmianki o metodologii jakościowej / badaniach kontrolowanych | 35 / 18 |
| Wzmianki o dystresie / niepokoju / strachu | 77 / 30 / 24 |

**Zastrzeżenie:** zapisane wyniki D03 i D04 są dostępne na GitHubie, ale nie ma jeszcze automatycznego testu regresyjnego potwierdzającego identyczność każdego bajtu po świeżym uruchomieniu skryptów. Wiersze mogą być posortowane inaczej; porównuj zestawy identyfikatorów oraz wartości i sumy, nie wyłącznie hash pliku. Renderer SVG dodano teraz; wymaga lokalnego uruchomienia i porównania wizualnego z opublikowaną wersją.

## Finalne pliki

- `outputs/analyses/avatar_discourse_D03_v01/` — zatwierdzony słownik, tabela `terms_semantic_final.csv`, częstości, sieć, log.
- `outputs/analyses/avatar_discourse_D04_anchor_maps_v01/` — ego edges, analiza czułości, audyt artykułów, wizualizacja robocza i opis.
- `outputs/analyses/avatar_discourse_D04_publication_v01/MANUSCRIPT_PL.md` — trzy akapity do części teoretycznej.
- `outputs/analyses/avatar_discourse_D04_publication_v01/FIGURE_1_AVATAR.svg` — opublikowana rycina; `scripts/08_render_D04_publication_figure.py` odtwarza jej konstrukcję na podstawie `strict_ego_edges.csv`.

## Zasady interpretacji

Nie porównuj liczby wszystkich badań jakościowych z ilościowymi na podstawie samych fraz 35 vs 18 (RCT nie wyczerpują metod ilościowych). Nie przypisuj automatycznie lęku lub dystresu do głosów, jeśli wzmianka dotyczy innego zjawiska. Dane są ograniczone do publicznej warstwy metadanych i do zaplanowanego, niewyczerpującego wyszukiwania OpenAlex. Roczna zmienność **nie była przedmiotem finalnego manuskryptu D04**, choć D03 przechowuje tabele okresowe do audytu.

Bibliometric preparation and metadata discourse mapping supported by Andromeda Nowicka (v0.5), research support agent, under the supervision of Lech Kalita.
