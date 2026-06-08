# Methodology: title + abstract discourse mapping

This pipeline is designed for bibliometric and discourse analysis when titles and abstracts are the available or methodologically preferred textual layer.

## Analytical claim

The pipeline supports claims about:

- lexical signals in article titles,
- thematic signals in abstracts,
- semantic concepts constructed through auditable mapping,
- temporal shifts in the title/abstract metadata layer,
- article-level co-occurrence of semantic concepts.

It does not support unqualified claims about full article content.

## Data layers

```text
raw metadata
→ QA and deduplication
→ normalized title/abstract text
→ candidate lexical terms
→ semantic concept map
→ audit decisions
→ periodized article–concept data
→ trend and network analyses
```

## Human-in-the-loop steps

Human review is required for:

- corpus inclusion and exclusion rules,
- ambiguous publication types,
- ambiguous or polysemous terms,
- semantic merging decisions,
- translated Polish concept labels,
- interpretation of trends and clusters.

## PEP-Web-style caution

For subscription, licensed, or database-mediated psychoanalytic corpora, this pipeline should usually process a local working export and publish only derived analytical outputs. Do not store access-controlled abstracts, full texts, PDFs, cookies, tokens, or credentials in the repository.
