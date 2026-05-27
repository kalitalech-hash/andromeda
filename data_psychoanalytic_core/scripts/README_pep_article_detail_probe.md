# PEP article-detail metadata probe

This is a narrow, metadata-first probe for one PEP article ID.

Confirmed control case:

```text
IJP.101.0013A
expected article keywords:
Paradigms; incommensurability; common ground; communication; redescription
```

Run from `data_psychoanalytic_core`:

```powershell
python scripts/1b_pep_article_detail_probe.py --art-id IJP.101.0013A --diagnose --search-default-terms --delay 3
```

The script:

- reads local credentials from `.env.pep`,
- tests a small set of article-detail endpoint candidates,
- saves raw JSON/text responses under `data/raw_pep_metadata/article_detail_probe/`,
- writes `data/logs/pep_article_detail_probe_log.csv`,
- writes `data/source_recon/pep_article_detail_probe_summary.csv`,
- searches responses for expected terms and keyword-like field names,
- does not download PDFs.

If a candidate endpoint contains the expected keyword line, the next step is to
turn that endpoint into a proper keyword extractor.

## Abstract layer note

The Search API already returns full abstracts for recent IJPA records. This
creates a third analytical layer:

```text
title-based historical mapping
abstract-based discourse mapping
keyword-based concept mapping, if article keywords can be extracted
```

Abstracts should be treated as a richer metadata layer than titles but still
not as full-text analysis. Use them for derived analytical features and avoid
redistribution of long verbatim abstract corpora when not needed.
