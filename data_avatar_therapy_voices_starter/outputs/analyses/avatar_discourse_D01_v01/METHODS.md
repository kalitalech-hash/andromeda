# D01 — Wstępna analiza dyskursu głosów w tytułach i abstraktach

## Korpus i status

Źródło: `analysis_corpus_ABC.csv` w `outputs/qa/avatar01_full_strict_v05/`; kontrolowany warunkiem `publication_type == article`. N=209; A=12, B=184, C=13. Brak abstraktu: 12; analiza tych rekordów opiera się wyłącznie na tytule. Poprzednia warstwa QA i źródłowe rekordy pozostają bez zmian.

## Metoda D01

W 13 jawnych rodzinach sygnałów leksykalnych szukamy obecności wyrażeń regularnych w każdym tytule i dostępnym abstrakcie (normalizacja Unicode NFKC; dopasowanie bez rozróżnienia wielkości liter). Każdy sygnał liczymy najwyżej raz na publikację. Kategorie **mogą współwystępować**. Zależności analizujemy jako współobecność dwóch sygnałów **w publikacji**, nie jako bezpośrednią relację semantyczną ani przyczynową.

Okresy: 2009–2015 (n=42), 2016–2020 (n=60), 2021–2026 (n=107; rok 2026 niepełny). Analizy względne mają mianownik równy liczbie zakwalifikowanych publikacji w danej grupie/okresie.

## Wyniki empiryczne (sygnały leksykalne)

- Język doświadczenia (`experience_language`): 144/209 publikacji. To **szeroki leksykon**, obejmujący także zwykłe słowo `experience`; nie jest to jednoznaczny wskaźnik fenomenologii.
- Język relacji (`relational_language`): 164/209.
- Język dystresu (`distress`): 93/209.
- Władza/kontrola/sprawczość (`power_control`): 70/209.
- Dialog (`dialogue`): 31/209.
- Wzmianki o VR: 22/209; awatarach: 14/209.

Te sygnały nie są rozłączne i **nie należy utożsamiać ich liczebności** z odsetkiem terapii określonego rodzaju. Sam dobór korpusu według A/B/C wzmacnia częstość części słownictwa.

## Hipotezy do przeglądu eksperckiego

1. Możliwe przesunięcie języka w kierunku indywidualnego doświadczenia i relacji z głosami. **Niepotwierdzone**: słowniki są szerokie, a źródła/query ranking są nierównomierne.
2. AVATAR i VR mogą tworzyć technologiczną podwarstwę w dyskursie zdominowanym przez relacje i dystres. Wymaga analizy tytułów niezależnie od abstraktów i kontroli artykułów z prób klinicznych.
3. Porównania między czasopismami wymagają oddzielnych mianowników źródło × okres, oceny indeksowania oraz limitów pobierania.

## Ograniczenia i następny etap

**Nie jest to finalne semantyczne mapowanie dyskursu.** Są to wyniki reprodukowalnego, wstępnego przesiewu leksykalnego na publicznej warstwie metadanych. Konieczne: kandydackie n-gramy tytułów i abstraktów, konserwatywny słownik ID pojęć, osobna kolejka HITL oraz sprawdzenie stabilności wyników dla samych tytułów i przypadków bez abstraktu. Nie wyprowadzamy wniosków o skuteczności terapii ani o pełnym polu badań.

W analizie użyto korpusu ograniczonego limitami wyszukiwania OpenAlex; `--full` oznaczało zakończenie zaplanowanych stron, nie wyszukiwanie wyczerpujące. Nie kopiujemy tekstów abstraktów do tej warstwy wyników.
