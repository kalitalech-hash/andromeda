# Selected-topic corpus: methods reporting template

Replace all `[FIELDS]` with observed values; do not infer coverage from a run label.

## Research question and pre-specified scope
[QUESTION], [SUBTOPICS], [DATE RANGE], [LANGUAGES], [SOURCE UNIVERSE], [PUBLICATION TYPES], [ANALYTICAL METADATA LAYER]. Approved by [RESEARCHER/DATE/PROTOCOL VERSION].

## Retrieval and pilot
Metadata retrieved using [OPENALEX/API VERSION/OTHER SOURCES] on [DATE], with [SEARCH QUERIES], [FILTERS], [SORTING], [SOURCE IDs] and [API/ACCOUNT POLICY]. A pilot of [SIZE/STRATA] informed [TERMS/SOURCE ADJUSTMENTS] after [QA DECISION].

## Acquisition limits and coverage
The expanded run retrieved [RAW HITS] records and [UNIQUE] unique candidates from [CELLS/PAGES] with [PAGE CAP]. The resulting acquisition is classified as [PILOT / BOUNDED HARVEST / VALIDATED COVERAGE CLAIM]. [TRUNCATION AND OVERLAP METRICS]. Neither OpenAlex general search nor per-query caps prove a comprehensive search.

## QA and article-type selection
Record keys [DEDUP KEYS] yielded [N DUPLICATES / MANUAL PAIRS]. Missing title/year/abstract/DOI rates: [COUNTS]. Publication-type restrictions [RULE + REASON]. OpenAlex type labels were treated as metadata categories rather than independently verified study designs.

## Topic selection and sensitivity
Topic rules [VERSION / EXACT MATCH FEATURES / PRECEDENCE / HUMAN REVIEW]. From [DENOMINATOR] unique candidates: [INCLUDED], [EXCLUDED WITH REASONS], [UNCERTAIN]. [RESEARCHER-APPROVED STRICT EXCLUSION?] [SENSITIVITY CHECK METHOD/RESULT OR 'NOT PERFORMED'].

## Analytical layer
The frozen [CORPUS VERSION/HASH] was passed to [KEYWORD / TITLE / TITLE+ABSTRACT] pipeline. Semantic normalization [MAP VERSION/APPROVER], periodization [WINDOWS] and any network thresholds [VALUES] are reported separately.

## Limitations
Analyses map metadata-bounded expressions in the **selected and retrieved corpus**. Index coverage, source/date selection, API ranking, missing abstracts and imperfect topical screening constrain generalizability. Neither full-text scholarly interpretation nor treatment efficacy was inferred from these metadata alone.

## Governance
Raw records, audit trails, excluded rows, transformation logs and aggregated outputs were maintained in separate layers. Content access and redistribution respected `SCRAPING_POLICY.md` and `robots.md`. Andromeda Nowicka (v0.5) supported data preparation and methods documentation as a research support agent; expert decisions remained human-led.
