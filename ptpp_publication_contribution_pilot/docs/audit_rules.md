# Audit rules

## Person-publication matching

High confidence:
- ORCID or PBN person profile confirms identity, or
- full name + affiliation/history + publication domain strongly match.

Medium confidence:
- full name and publication domain match, but no unique identifier.
- Requires manual accept before final inclusion.

Low confidence:
- name match only, common surname, no affiliation or topic confirmation.
- Keep in candidates; do not analyze as accepted.

Reject:
- clearly different field/person/country, or implausible identity match.

## Final inclusion

A publication enters data_final only if:
- bibliographic record is deduplicated;
- person-publication link is high confidence or manually accepted medium;
- source database and retrieval date are logged.
