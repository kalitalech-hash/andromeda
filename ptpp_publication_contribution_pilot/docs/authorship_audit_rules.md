# Audit rules for PTPP authorship candidates

## Statusy audytu

W pliku `authorship_candidates_raw.csv` każde dopasowanie startuje jako:

```text
candidate_needs_review
```

Zalecane wartości po audycie:

```text
accept_high_confidence
accept_manual
reject_homonym
reject_wrong_field
reject_insufficient_evidence
merge_duplicate
needs_second_review
```

## Minimalne kryteria akceptacji

### High confidence

- pełne imię i nazwisko lub ORCID zgodny z osobą;
- publikacja z obszaru psychoterapii, psychoanalizy, psychiatrii, psychologii klinicznej lub powiązanej humanistyki;
- brak silnej przesłanki, że to homonim.

### Medium confidence

- nazwisko i imię/inicjał zgodne;
- tytuł/czasopismo/afiliacja sugeruje właściwe pole;
- brak ORCID lub jednoznacznego profilu;
- wymaga akceptacji ręcznej.

### Reject

- ta sama forma nazwiska, ale inna dziedzina lub kraj bez związku z osobą;
- publikacja techniczna/medyczna/humanistyczna niezgodna z profilem i bez innej przesłanki;
- dopasowanie tylko po nazwisku;
- brak wystarczających metadanych.

## Finalne pliki po audycie

Po audycie zalecam utworzyć:

```text
data_final/publications.csv
data_final/authorships.csv
data_final/person_publication_summary.csv
logs/manual_authorship_audit_log.csv
```
