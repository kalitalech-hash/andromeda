# Scraping and Metadata Acquisition Policy

**Project:** Andromeda Nowicka (v0.4)  
**Controller:** Lech Kalita  
**DID:** `did:web:kalitalech-hash.github.io:andromeda`  
**Scope:** bibliometric and discourse-analysis workflows for psychotherapy, psychiatry, and related scientific literature.

---

## 1. Purpose

This policy defines how Andromeda-based projects acquire web-accessible bibliometric data in a transparent, conservative, and auditable way.

The goal is to collect only the information necessary for scholarly bibliometric analysis, while minimizing load on source websites and avoiding unnecessary copying of third-party content.

The preferred acquisition target is **metadata**, not full text.

---

## 2. Default acquisition hierarchy

When several data layers are available, Andromeda projects should prefer the least intrusive layer sufficient for the research question.

Recommended order:

```text
1. Existing structured exports or APIs
2. Crossref / DOI metadata
3. Public HTML metadata from article landing pages
4. Public issue tables of contents
5. Abstracts and keywords where openly displayed
6. Full-text HTML only when methodologically necessary and permitted
7. PDFs only when explicitly licensed, necessary, and narrowly scoped
```

Temporary free access, browser-readable pages, or institutional access should not be treated as automatic permission to create a local mirror of a journal.

---

## 3. Metadata-first rule

The default Andromeda workflow collects:

- article title,
- authors,
- year,
- volume,
- issue,
- pages,
- DOI,
- article URL,
- abstract when publicly available,
- keywords when publicly available,
- article type when available,
- source issue URL,
- acquisition timestamp,
- acquisition status.

The default workflow does **not** collect or store:

- mass-downloaded PDFs,
- complete journal mirrors,
- full-text corpora unless explicitly justified,
- access-controlled material beyond what is permitted by the relevant terms,
- content for redistribution.

---

## 4. Full text and PDF handling

Full text may be considered only when all of the following conditions are met:

1. The research question cannot be answered using metadata, titles, abstracts, or keywords.
2. Access terms, license, or applicable law allow the intended text and data mining use.
3. The acquisition is proportionate to the research question.
4. The project does not redistribute copyrighted full text.
5. The project stores derived analytical features whenever possible instead of raw full text.
6. The decision is documented in the project log.

Mass PDF mirroring is not a default Andromeda practice.

If PDFs are necessary, the project must define:

- exact inclusion scope,
- reason metadata/HTML is insufficient,
- license or permission basis,
- storage location,
- retention rule,
- no-redistribution statement.

---

## 5. Robots.txt, terms, and access controls

Before crawling a new source, the project should check:

- `robots.txt`,
- website terms of use,
- publisher text-and-data-mining policy if available,
- API or export options,
- rate limits,
- login or session requirements,
- whether pages are public, subscription-only, temporarily free, or institutionally accessed.

Robots exclusions and explicit technical barriers should be treated as meaningful signals. Do not bypass access controls, paywalls, CAPTCHAs, bot protections, or session restrictions.

If a site blocks the crawler, the default response is to stop and reassess the acquisition method.

---

## 6. Identification and user agent

Project-specific crawlers should identify themselves clearly.

Recommended user agent:

```text
AndromedaNowickaBibliometricBot/0.4
(metadata-only bibliometric research; contact: CONTACT_EMAIL; no PDF mirroring; polite delay)
```

Recommended HTTP headers:

```python
HEADERS = {
    "User-Agent": (
        "AndromedaNowickaBibliometricBot/0.4 "
        "(metadata-only bibliometric research; contact: CONTACT_EMAIL; "
        "no PDF mirroring; polite delay)"
    ),
    "From": "CONTACT_EMAIL",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,pl;q=0.8",
}
```

The contact address should be a real address monitored by the project controller or research team.

---

## 7. Polite crawling rules

Default crawler behavior:

- use a clear user agent,
- use delays between requests,
- avoid parallel crawling unless explicitly permitted,
- limit initial tests to a small sample,
- stop on repeated errors,
- log HTTP status codes,
- avoid repeatedly requesting the same URL,
- cache already retrieved metadata where appropriate,
- avoid unnecessary PDF requests,
- avoid login automation unless explicitly allowed.

Recommended initial crawl mode:

```text
sample-first
1-2 issues
then QA report
then decision whether full acquisition is justified
```

Default delay:

```text
3-8 seconds between requests
```

For fragile or small publisher sites, increase the delay.

---

## 8. Logging requirements

Every acquisition run should produce a log file, preferably CSV or JSONL, containing:

- timestamp,
- requested URL,
- source domain,
- HTTP status,
- content type,
- response size if available,
- parser used,
- extraction status,
- error message if any,
- retry count,
- user-agent string,
- script version,
- run ID.

Suggested output:

```text
<journal>_scrape_log.csv
```

A project README or methodological note should state:

- acquisition date,
- data source,
- scope of acquisition,
- whether full text or PDFs were accessed,
- whether any records were excluded,
- known limitations.

---

## 9. Data minimization

Collect only fields required for the declared bibliometric analysis.

Do not collect:

- personal data unrelated to publication authorship,
- website analytics identifiers,
- cookies,
- session tokens,
- account-specific access information,
- irrelevant page content,
- recommended-article widgets unless methodologically relevant and explicitly logged,
- advertisements or tracking snippets.

Do not store credentials in scripts or repositories.

---

## 10. Reproducibility and auditability

Each corpus should preserve the transformation chain:

```text
raw acquisition output
→ QA and deduplication
→ normalized metadata
→ semantic mappings
→ audit decisions
→ periodized analytical files
→ final analytical outputs
```

Do not overwrite earlier layers. Keep:

- raw metadata,
- cleaned metadata,
- excluded-record logs,
- normalization maps,
- semantic merge logs,
- manual audit decisions,
- analysis summaries.

Each exclusion should be documented rather than silently removed.

---

## 11. Handling missing or inconsistent data

When data are missing or inconsistent:

- preserve the raw value,
- add a normalized value only when justified,
- flag uncertainty,
- do not infer article type, year, or keywords without a traceable rule,
- place ambiguous cases in an audit queue.

Typical flags:

```text
missing_keywords
missing_abstract
missing_year
duplicate_url
duplicate_doi
out_of_scope_year
article_type_uncertain
parser_uncertain
manual_review_needed
```

---

## 12. Publisher contact and takedown response

If contacted by a publisher or website operator:

1. pause the crawler,
2. document the contact,
3. clarify the research purpose,
4. provide the user-agent and contact details,
5. remove or reduce collected content if requested and legally appropriate,
6. prefer metadata-only alternatives,
7. update the project log and policy note.

Andromeda projects should be prepared to explain:

- what was collected,
- why it was collected,
- how many requests were made,
- whether full text or PDFs were downloaded,
- where data are stored,
- what is publicly redistributed.

---

## 13. Publication and redistribution

Repository outputs may include:

- code,
- documentation,
- derived tables,
- aggregate counts,
- normalized keyword/concept mappings,
- figures,
- statistical summaries,
- logs without sensitive access details.

Repository outputs should not include:

- full copyrighted articles,
- mass-downloaded PDFs,
- raw full-text corpora from restricted sources,
- access tokens,
- cookies,
- credentials,
- publisher content beyond fair quotation or permitted metadata use.

When in doubt, publish derived analytical data rather than source content.

---

## 14. Standard methodological note

Suggested wording for papers or project READMEs:

```text
Bibliometric metadata were acquired using a metadata-first, human-in-the-loop workflow. The crawler identified itself as AndromedaNowickaBibliometricBot/0.4, used polite request delays, and prioritized article landing-page metadata, tables of contents, abstracts, and keywords over full-text acquisition. PDFs were not mirrored unless explicitly stated. All transformations from raw metadata to normalized analytical concepts were logged and preserved as separate auditable data layers.
```

---

## 15. Version note

Version **v0.4** introduces explicit governance for ethical metadata acquisition, clearer separation between reusable pipelines and applied corpora, and a stronger metadata-first norm for future Andromeda projects.
