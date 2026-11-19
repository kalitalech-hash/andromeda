# Selected-topic metadata acquisition protocol (OpenAlex-first)

## Stage 0 — define the inference target

State whether the project is (i) exploratory discourse mapping, (ii) bibliometric description of a bounded source set, or (iii) evidence retrieval aspiring to systematic coverage. Do not present (i)/(ii) as (iii). Decide what counts as a publication, whether trials/protocols/reviews count separately, which dates and languages matter, and which journals/databases delimit the source universe.

Freeze a signed, versioned topic protocol **before running searches**. Operational concepts must be translated into documented search families, not discovered post hoc and treated as prior criteria.

## Stage 0a — source reconnaissance

1. Prefer lawful metadata APIs / existing exports. For journal-scoped OpenAlex, obtain stable source IDs and cross-check names and ISSNs.
2. Document alternative or historical source titles, merger/rename uncertainty, missing years, indexing and abstract coverage.
3. Maintain `source_candidates.csv` with source identifier, requested name, match confidence, decision, reason, decision maker and date. Preserve the raw discovery response.
4. Manually approve the source manifest. Never infer a yes/no from malformed or shifted CSV cells.

## Stage 1 — small pilot, stratified where sensible

Construct a query matrix (approved sources × concept/search family × optional time period). Make limits explicit, e.g. `per_page=5` and one page per cell, and record API response counts and result ordering. `OpenAlex search` may cover indexed fields beyond title/abstract; candidate retrieval is **not** topical eligibility.

Required pilot QA: duplicates across queries, % absent abstracts and DOI, article-type and language distribution, counts by source/year/query, false-positive exemplars, potential topic-specific false negatives, sentinel study recall where a researcher supplies a known-relevant set. If possible compare title-only, title+abstract and metadata search choices **as separate documented variants**, not as equivalent calls.

Decision gate: **expand / revise terms or source scope / stop**. Record approver, decision date, rationale and revised protocol version; changed searches start a distinct run directory.

## Stage 2 — expanded acquisition

Use the source's documented API access rules, account quotas and authentication. Record API version/endpoint where available, UTC acquisition times and code version. Credentials come from environment variables and must be redacted from saved URLs/errors/headers.

Build a run fingerprint from approved sources, dates, query strings, paging limits, sorting, language and record-type filters. Checkpoint each successful page atomically; resume only if fingerprint matches. Cache successful pages and suppress duplicate requests. Treat any previously failed `last_error` as historical if the final summary says completed; retain it for audit with incident status.

On HTTP 429, record redacted status, safe provider reason and Retry-After if present, and stop. Resume only when permitted by the provider budget / retry guidance. Never rotate identities/IPs to defeat quotas. Handle 401/403 and repeated 5xx likewise. Keep a real contact address and polite default delays.

## Coverage and stopping labels

- `pilot_sample`: deliberately small sample for method validation; not a general corpus.
- `bounded_harvest`: completed **configured** search, subject to source/query/page/time caps; may be larger than the pilot but not exhaustive.
- `exhaustive_search_claimed`: **not assigned automatically**. Requires independent search-validation protocol, assessment of database coverage, retrieval completeness and human sign-off. Exhaustive within one API is not equivalent to all literature.

Record `configured_scope_complete` separately from `coverage_exhaustive`. Also preserve cap-hit flags by query cell, available API `meta.count`, max pages, actual pages, item counts and overlap. A query stopped at `page_cap` despite more available results is a known truncation.

## Dataset handoff

Persist raw API observations (subject to provider terms), a deduplicated candidate table with provenance and query matches, `acquisition_log.csv`, `run_manifest.json`, `acquisition_summary.json` and `source_audit_snapshot.csv`. Include a stable record ID and origin source for each item. Do not overwrite sample, raw or prior run layers.

The downstream selected-topic QA decides *eligibility*; acquisition itself must not secretly implement semantic exclusion.

## Rights and infrastructure

Read `../SCRAPING_POLICY.md` and `../robots.md` before each new source. Prefer API metadata; abstracts only when their processing and retention are permitted. No PDF mirroring by default, no full-text scraping to compensate for insufficient metadata. Avoid public raw dumps of third-party abstracts when redistribution rights have not been checked.
