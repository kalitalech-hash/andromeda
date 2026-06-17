#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
search_ptpp_publication_candidates.py

Metadata-first candidate-publication search for the PTPP membership snapshot.

This script DOES NOT decide final authorship. It only creates auditable candidate
records from public scholarly metadata APIs. Final acceptance/rejection should be
done in a manual audit layer.

Default sources:
  - Crossref REST API
  - OpenAlex API
  - PubMed / NCBI E-utilities
  - ORCID expanded search (optional; requires ORCID_TOKEN env var)

Outputs:
  data_intermediate/publication_candidates_raw.csv
  data_intermediate/authorship_candidates_raw.csv
  data_intermediate/person_source_summary.csv
  logs/publication_candidate_search_log.csv
  docs/publication_candidate_search_summary.json

Usage:
  cd ptpp_publication_contribution_pilot

  python scripts/search_ptpp_publication_candidates.py \
    --members-csv data_raw/ptpp_members_snapshot_reconstructed_2026-06-17.csv \
    --output-dir . \
    --email YOUR_EMAIL@example.org \
    --sources crossref openalex pubmed \
    --max-results-per-source 20 \
    --sleep 0.35

Optional ORCID:
  export ORCID_TOKEN="YOUR_ORCID_PUBLIC_API_BEARER_TOKEN"
  python scripts/search_ptpp_publication_candidates.py ... --sources crossref openalex pubmed orcid

Notes:
  - Use conservative limits first.
  - This script stores metadata only; it does not download PDFs or full texts.
  - PubMed requires a valid email for responsible API use.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import html
import json
import os
import re
import sys
import time
import unicodedata
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import quote_plus

import requests


POLISH_STOPWORDS_AFFILIATION_HINTS = [
    "poland", "polska", "warsaw", "warszawa", "krakow", "kraków",
    "poznan", "poznań", "gdansk", "gdańsk", "wroclaw", "wrocław",
    "lodz", "łódź", "lublin", "katowice", "bialystok", "białystok",
    "psychoanalytic", "psychoanalytical", "psychotherapy", "psychoterapia",
    "psychiatry", "psychiatria", "psychology", "psychologia",
]

DOMAIN_CONCEPT_HINTS = [
    # English
    "psychoanalysis", "psychoanalytic", "psychodynamic", "psychotherapy",
    "transference", "countertransference", "unconscious", "mentalization",
    "attachment", "borderline", "trauma", "therapeutic relationship",
    "supervision", "clinical", "patient", "therapy",
    # Polish
    "psychoanaliza", "psychoanalityczny", "psychodynamiczny", "psychoterapia",
    "przeniesienie", "przeciwprzeniesienie", "nieświadomość", "nieswiadomosc",
    "mentalizacja", "przywiązanie", "przywiazanie", "borderline", "trauma",
    "relacja terapeutyczna", "superwizja", "kliniczny", "pacjent", "terapia",
]

DEFAULT_HEADERS = {
    "User-Agent": "AndromedaNowickaBibliometricBot/0.5 (metadata-only bibliometric research; no PDF mirroring; polite delay)"
}


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


def strip_accents(s: str) -> str:
    s = str(s or "")
    return "".join(
        c for c in unicodedata.normalize("NFKD", s)
        if not unicodedata.combining(c)
    )


def norm_text(s: str) -> str:
    s = html.unescape(str(s or ""))
    s = unicodedata.normalize("NFKC", s)
    s = s.replace("\u00a0", " ")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def norm_key(s: str) -> str:
    s = strip_accents(norm_text(s)).lower()
    s = re.sub(r"[^a-z0-9ąćęłńóśźżĄĆĘŁŃÓŚŹŻ\- ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def split_name_from_ptpp(row: Dict[str, str]) -> Tuple[str, str, str]:
    """Return full_name, surname, given_names using existing snapshot columns when available."""
    full = norm_text(row.get("name_ptpp_order") or row.get("name_raw") or row.get("full_name") or "")
    surname = norm_text(row.get("surname_guess") or row.get("last_name") or "")
    given = norm_text(row.get("given_names_guess") or row.get("first_name") or "")

    if not (surname and given) and full:
        # PTPP snapshot is usually "Surname Given Names".
        parts = full.split()
        if len(parts) >= 2:
            surname = surname or parts[0]
            given = given or " ".join(parts[1:])
    return full, surname, given


def western_name(given: str, surname: str) -> str:
    return norm_text(f"{given} {surname}")


def name_fingerprint(given: str, surname: str) -> str:
    return norm_key(f"{surname} {given}")


def initials(given_names: str) -> str:
    return "".join(p[0] for p in re.split(r"[\s\-]+", strip_accents(given_names).strip()) if p).lower()


def author_name_score(given: str, surname: str, candidate_author: str) -> Tuple[float, str]:
    """Conservative string-level match score for candidate author name."""
    ca = norm_key(candidate_author)
    s = norm_key(surname)
    g = norm_key(given)
    gi = initials(given)

    if not ca or not s:
        return 0.0, "no_author_name"

    # surname must be present for most useful matches
    if s not in ca:
        # allow hyphenated / compound surname partial, but mark lower
        surname_parts = [p for p in re.split(r"[\s\-]+", s) if len(p) > 2]
        if not any(p in ca for p in surname_parts):
            return 0.0, "surname_absent"
        surname_score = 0.45
    else:
        surname_score = 0.65

    given_score = 0.0
    if g and g in ca:
        given_score = 0.30
    else:
        cand_tokens = re.split(r"[\s\-]+", ca)
        # Initials in "A. Kowalska" style.
        if gi and any(tok[:1] == gi[:1] for tok in cand_tokens):
            given_score = 0.15
        # If full given has multiple names, first given is often enough.
        first_given = g.split()[0] if g else ""
        if first_given and first_given in ca:
            given_score = max(given_score, 0.22)

    score = min(1.0, surname_score + given_score)
    basis = "surname+given" if given_score >= 0.22 else "surname+initial_or_partial" if given_score else "surname_only"
    return round(score, 3), basis


def text_domain_score(title: str, abstract: str = "", keywords: Optional[List[str]] = None, container: str = "") -> Tuple[float, List[str]]:
    text = norm_key(" ".join([title or "", abstract or "", container or "", " ".join(keywords or [])]))
    hits = []
    for hint in DOMAIN_CONCEPT_HINTS:
        hk = norm_key(hint)
        if hk and hk in text:
            hits.append(hint)
    if not hits:
        return 0.0, []
    score = min(0.35, 0.05 * len(set(hits)))
    return round(score, 3), sorted(set(hits))


def affiliation_hint_score(affiliations: Iterable[str]) -> Tuple[float, List[str]]:
    text = norm_key(" ".join(affiliations or []))
    hits = [h for h in POLISH_STOPWORDS_AFFILIATION_HINTS if norm_key(h) in text]
    if not hits:
        return 0.0, []
    return min(0.20, 0.04 * len(set(hits))), sorted(set(hits))


def make_publication_id(source: str, external_id: str, title: str = "", year: str = "") -> str:
    raw = f"{source}|{external_id or ''}|{title or ''}|{year or ''}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:20]


@dataclass
class CandidatePublication:
    candidate_publication_id: str
    source_database: str
    source_record_id: str
    doi: str
    title: str
    year: str
    publication_type: str
    journal_or_source: str
    publisher: str
    url: str
    language: str
    abstract_present: bool
    abstract_text: str
    keywords: str
    raw_json_path: str


@dataclass
class AuthorshipCandidate:
    candidate_publication_id: str
    person_id: str
    name_ptpp_order: str
    surname_guess: str
    given_names_guess: str
    membership_category: str
    source_database: str
    name_as_published: str
    author_position: str
    author_orcid: str
    affiliations: str
    name_match_score: float
    name_match_basis: str
    domain_score: float
    domain_hits: str
    affiliation_score: float
    affiliation_hits: str
    total_candidate_score: float
    confidence_hint: str
    audit_status: str
    audit_notes: str


class SearchLog:
    def __init__(self):
        self.rows: List[Dict[str, Any]] = []

    def add(self, **kwargs):
        row = {"timestamp_utc": now_utc(), **kwargs}
        self.rows.append(row)

    def write(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        keys = sorted({k for r in self.rows for k in r.keys()})
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=keys)
            w.writeheader()
            w.writerows(self.rows)


def request_json(url: str, headers: Dict[str, str], timeout: int, log: SearchLog, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        r = requests.get(url, headers=headers, timeout=timeout)
        log.add(url=url, http_status=r.status_code, bytes=len(r.content), **context)
        if r.status_code == 200:
            return r.json()
        return None
    except Exception as e:
        log.add(url=url, http_status="EXCEPTION", error=str(e), **context)
        return None


def extract_crossref_item(item: Dict[str, Any], raw_json_dir: Path) -> Tuple[CandidatePublication, List[Dict[str, Any]]]:
    doi = norm_text(item.get("DOI", ""))
    title = norm_text(" ".join(item.get("title", []) or []))
    year = ""
    for date_key in ("published-print", "published-online", "published", "created", "deposited"):
        parts = item.get(date_key, {}).get("date-parts")
        if parts and parts[0]:
            year = str(parts[0][0])
            break
    ctitle = norm_text(" ".join(item.get("container-title", []) or []))
    pub_type = norm_text(item.get("type", ""))
    publisher = norm_text(item.get("publisher", ""))
    url = norm_text(item.get("URL", ""))
    abstract = norm_text(re.sub(r"<[^>]+>", " ", item.get("abstract", "") or ""))
    lang = norm_text(item.get("language", ""))
    keywords = item.get("subject", []) or []
    extid = doi or url or title
    cid = make_publication_id("crossref", extid, title, year)
    raw_path = raw_json_dir / f"{cid}.json"
    raw_path.write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
    pub = CandidatePublication(
        candidate_publication_id=cid,
        source_database="crossref",
        source_record_id=extid,
        doi=doi,
        title=title,
        year=year,
        publication_type=pub_type,
        journal_or_source=ctitle,
        publisher=publisher,
        url=url,
        language=lang,
        abstract_present=bool(abstract),
        abstract_text=abstract,
        keywords="; ".join(map(norm_text, keywords)),
        raw_json_path=str(raw_path),
    )
    return pub, item.get("author", []) or []


def search_crossref(person: Dict[str, str], args, log: SearchLog, raw_json_dir: Path) -> Tuple[List[CandidatePublication], List[AuthorshipCandidate]]:
    full, surname, given = split_name_from_ptpp(person)
    q_author = quote_plus(western_name(given, surname))
    # Crossref query.author is broad; keep rows low and score afterward.
    url = (
        "https://api.crossref.org/works"
        f"?query.author={q_author}"
        f"&rows={args.max_results_per_source}"
        "&select=DOI,title,container-title,type,publisher,published-print,published-online,published,created,deposited,URL,author,abstract,subject,language"
    )
    if args.email:
        url += f"&mailto={quote_plus(args.email)}"
    headers = {**DEFAULT_HEADERS}
    if args.email:
        headers["From"] = args.email

    data = request_json(url, headers, args.timeout, log, {"source_database": "crossref", "person_id": person.get("person_id", ""), "query_name": western_name(given, surname)})
    pubs, auths = [], []
    for item in (data or {}).get("message", {}).get("items", []) or []:
        pub, authors = extract_crossref_item(item, raw_json_dir)
        pubs.append(pub)
        dscore, dhits = text_domain_score(pub.title, pub.abstract_text, pub.keywords.split("; "), pub.journal_or_source)
        for idx, au in enumerate(authors, start=1):
            name_as = norm_text(" ".join([au.get("given", "") or "", au.get("family", "") or ""]))
            nscore, nbasis = author_name_score(given, surname, name_as)
            if nscore <= 0:
                continue
            affs = [norm_text(a.get("name", "")) for a in au.get("affiliation", []) or [] if a.get("name")]
            ascore, ahits = affiliation_hint_score(affs)
            total = round(nscore + dscore + ascore, 3)
            auths.append(make_authorship(person, pub, name_as, idx, au.get("ORCID", "") or "", affs, nscore, nbasis, dscore, dhits, ascore, ahits, total))
    return pubs, auths


def extract_openalex_work(work: Dict[str, Any], raw_json_dir: Path) -> Tuple[CandidatePublication, List[Dict[str, Any]]]:
    doi = norm_text((work.get("doi") or "").replace("https://doi.org/", ""))
    title = norm_text(work.get("title", ""))
    year = str(work.get("publication_year") or "")
    pub_type = norm_text(work.get("type", ""))
    src = work.get("primary_location", {}).get("source") or {}
    journal = norm_text(src.get("display_name", ""))
    publisher = norm_text(src.get("host_organization_name", "") or "")
    url = norm_text(work.get("id", ""))
    language = norm_text(work.get("language", ""))
    # OpenAlex inverted abstract index is reconstructed only if asked; keep metadata bounded.
    abstract = ""
    keywords = [kw.get("display_name", "") for kw in work.get("keywords", []) or []]
    extid = doi or work.get("id", "") or title
    cid = make_publication_id("openalex", extid, title, year)
    raw_path = raw_json_dir / f"{cid}.json"
    raw_path.write_text(json.dumps(work, ensure_ascii=False, indent=2), encoding="utf-8")
    pub = CandidatePublication(
        candidate_publication_id=cid,
        source_database="openalex",
        source_record_id=norm_text(work.get("id", "")),
        doi=doi,
        title=title,
        year=year,
        publication_type=pub_type,
        journal_or_source=journal,
        publisher=publisher,
        url=url,
        language=language,
        abstract_present=False,
        abstract_text=abstract,
        keywords="; ".join(map(norm_text, keywords)),
        raw_json_path=str(raw_path),
    )
    return pub, work.get("authorships", []) or []


def search_openalex(person: Dict[str, str], args, log: SearchLog, raw_json_dir: Path) -> Tuple[List[CandidatePublication], List[AuthorshipCandidate]]:
    full, surname, given = split_name_from_ptpp(person)
    name = western_name(given, surname)
    headers = {**DEFAULT_HEADERS}
    if args.email:
        headers["mailto"] = args.email

    # Step 1: find author entities.
    authors_url = f"https://api.openalex.org/authors?search={quote_plus(name)}&per-page={min(args.max_author_entities, 25)}"
    if args.email:
        authors_url += f"&mailto={quote_plus(args.email)}"
    adata = request_json(authors_url, headers, args.timeout, log, {"source_database": "openalex_authors", "person_id": person.get("person_id", ""), "query_name": name})

    pubs, auths = [], []
    author_entities = []
    for a in (adata or {}).get("results", []) or []:
        nscore, nbasis = author_name_score(given, surname, a.get("display_name", ""))
        if nscore >= args.min_name_score:
            author_entities.append((a, nscore, nbasis))

    # Step 2: fetch works for plausible author entities.
    for a, entity_score, entity_basis in author_entities[: args.max_author_entities]:
        aid = a.get("id", "")
        if not aid:
            continue
        filter_id = aid.replace("https://openalex.org/", "")
        works_url = (
            "https://api.openalex.org/works"
            f"?filter=authorships.author.id:{quote_plus(filter_id)}"
            f"&per-page={args.max_results_per_source}"
            "&sort=publication_date:desc"
        )
        if args.email:
            works_url += f"&mailto={quote_plus(args.email)}"
        wdata = request_json(works_url, headers, args.timeout, log, {"source_database": "openalex_works", "person_id": person.get("person_id", ""), "query_name": name, "openalex_author_id": aid})
        for work in (wdata or {}).get("results", []) or []:
            pub, authorships = extract_openalex_work(work, raw_json_dir)
            pubs.append(pub)
            dscore, dhits = text_domain_score(pub.title, pub.abstract_text, pub.keywords.split("; "), pub.journal_or_source)
            for idx, au in enumerate(authorships, start=1):
                au_name = norm_text(au.get("author", {}).get("display_name", ""))
                au_id = norm_text(au.get("author", {}).get("id", ""))
                nscore, nbasis = author_name_score(given, surname, au_name)
                if au_id == aid:
                    nscore = max(nscore, entity_score)
                    nbasis = f"openalex_author_entity:{entity_basis}"
                if nscore <= 0:
                    continue
                affs = []
                for inst in au.get("institutions", []) or []:
                    if inst.get("display_name"):
                        affs.append(norm_text(inst.get("display_name")))
                    if inst.get("country_code"):
                        affs.append(norm_text(inst.get("country_code")))
                ascore, ahits = affiliation_hint_score(affs)
                orcid = norm_text(au.get("author", {}).get("orcid", ""))
                total = round(nscore + dscore + ascore, 3)
                auths.append(make_authorship(person, pub, au_name, idx, orcid, affs, nscore, nbasis, dscore, dhits, ascore, ahits, total))
        polite_sleep(args.sleep)
    return pubs, auths


def search_pubmed(person: Dict[str, str], args, log: SearchLog, raw_json_dir: Path) -> Tuple[List[CandidatePublication], List[AuthorshipCandidate]]:
    full, surname, given = split_name_from_ptpp(person)
    name = western_name(given, surname)
    headers = {**DEFAULT_HEADERS}
    term = quote_plus(f'"{surname} {initials(given)[:1]}"[Author] OR "{name}"[Author]')
    base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
    esearch = f"{base}/esearch.fcgi?db=pubmed&term={term}&retmode=json&retmax={args.max_results_per_source}"
    if args.email:
        esearch += f"&email={quote_plus(args.email)}"
    if args.ncbi_api_key:
        esearch += f"&api_key={quote_plus(args.ncbi_api_key)}"
    data = request_json(esearch, headers, args.timeout, log, {"source_database": "pubmed_esearch", "person_id": person.get("person_id", ""), "query_name": name})
    ids = (data or {}).get("esearchresult", {}).get("idlist", []) or []
    if not ids:
        return [], []

    polite_sleep(args.sleep)
    esummary = f"{base}/esummary.fcgi?db=pubmed&id={','.join(ids)}&retmode=json"
    if args.email:
        esummary += f"&email={quote_plus(args.email)}"
    if args.ncbi_api_key:
        esummary += f"&api_key={quote_plus(args.ncbi_api_key)}"
    sdata = request_json(esummary, headers, args.timeout, log, {"source_database": "pubmed_esummary", "person_id": person.get("person_id", ""), "query_name": name})

    pubs, auths = [], []
    result = (sdata or {}).get("result", {})
    for pmid in ids:
        item = result.get(pmid) or {}
        if not item:
            continue
        title = norm_text(item.get("title", ""))
        year = norm_text((item.get("pubdate", "") or "")[:4])
        journal = norm_text(item.get("fulljournalname", "") or item.get("source", ""))
        doi = ""
        for aid in item.get("articleids", []) or []:
            if aid.get("idtype") == "doi":
                doi = norm_text(aid.get("value", ""))
        pub_type = "; ".join(item.get("pubtype", []) or [])
        url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
        cid = make_publication_id("pubmed", pmid, title, year)
        raw_path = raw_json_dir / f"{cid}.json"
        raw_path.write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
        pub = CandidatePublication(
            candidate_publication_id=cid,
            source_database="pubmed",
            source_record_id=pmid,
            doi=doi,
            title=title,
            year=year,
            publication_type=pub_type,
            journal_or_source=journal,
            publisher="",
            url=url,
            language="",
            abstract_present=False,
            abstract_text="",
            keywords="",
            raw_json_path=str(raw_path),
        )
        pubs.append(pub)
        dscore, dhits = text_domain_score(pub.title, "", [], pub.journal_or_source)
        for idx, au in enumerate(item.get("authors", []) or [], start=1):
            name_as = norm_text(au.get("name", ""))
            nscore, nbasis = author_name_score(given, surname, name_as)
            if nscore <= 0:
                continue
            total = round(nscore + dscore, 3)
            auths.append(make_authorship(person, pub, name_as, idx, "", [], nscore, nbasis, dscore, dhits, 0.0, [], total))
    return pubs, auths


def search_orcid(person: Dict[str, str], args, log: SearchLog, raw_json_dir: Path) -> Tuple[List[CandidatePublication], List[AuthorshipCandidate]]:
    """ORCID adapter: finds public ORCID IDs and stores them as person-level evidence.
    It does not yet harvest ORCID works, because public/membership-token behavior varies.
    """
    token = os.environ.get("ORCID_TOKEN", "").strip()
    if not token:
        log.add(source_database="orcid", person_id=person.get("person_id", ""), http_status="SKIPPED", error="ORCID_TOKEN not set")
        return [], []
    full, surname, given = split_name_from_ptpp(person)
    query = quote_plus(f'family-name:"{surname}" AND given-names:"{given}"')
    url = f"https://pub.orcid.org/v3.0/expanded-search/?q={query}&rows={args.max_results_per_source}"
    headers = {
        **DEFAULT_HEADERS,
        "Accept": "application/json",
        "Authorization": f"Bearer {token}",
    }
    data = request_json(url, headers, args.timeout, log, {"source_database": "orcid_expanded_search", "person_id": person.get("person_id", ""), "query_name": western_name(given, surname)})
    raw_id = make_publication_id("orcid_search", person.get("person_id", ""), western_name(given, surname), "")
    raw_path = raw_json_dir / f"{raw_id}.json"
    raw_path.write_text(json.dumps(data or {}, ensure_ascii=False, indent=2), encoding="utf-8")
    # No publication candidates emitted here. Use it to enrich persons_disambiguation later.
    return [], []


def make_authorship(person, pub, name_as, idx, orcid, affs, nscore, nbasis, dscore, dhits, ascore, ahits, total) -> AuthorshipCandidate:
    if total >= 1.05:
        hint = "high_candidate"
    elif total >= 0.80:
        hint = "medium_candidate"
    elif total >= 0.65:
        hint = "low_candidate"
    else:
        hint = "very_low_candidate"
    return AuthorshipCandidate(
        candidate_publication_id=pub.candidate_publication_id,
        person_id=person.get("person_id", ""),
        name_ptpp_order=person.get("name_ptpp_order", person.get("name_raw", "")),
        surname_guess=person.get("surname_guess", person.get("last_name", "")),
        given_names_guess=person.get("given_names_guess", person.get("first_name", "")),
        membership_category=person.get("membership_category", ""),
        source_database=pub.source_database,
        name_as_published=name_as,
        author_position=str(idx),
        author_orcid=orcid,
        affiliations=" | ".join(affs),
        name_match_score=nscore,
        name_match_basis=nbasis,
        domain_score=dscore,
        domain_hits="; ".join(dhits),
        affiliation_score=round(ascore, 3),
        affiliation_hits="; ".join(ahits),
        total_candidate_score=total,
        confidence_hint=hint,
        audit_status="candidate_needs_review",
        audit_notes="",
    )


def polite_sleep(seconds: float):
    if seconds and seconds > 0:
        time.sleep(seconds)


def read_members(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def dedupe_pubs(pubs: List[CandidatePublication]) -> List[CandidatePublication]:
    seen = set()
    out = []
    for p in pubs:
        key = (norm_key(p.doi) if p.doi else "", norm_key(p.title), p.year, p.source_database)
        if key in seen:
            continue
        seen.add(key)
        out.append(p)
    return out


def write_dataclass_csv(path: Path, rows: List[Any], fieldnames: Optional[List[str]] = None):
    path.parent.mkdir(parents=True, exist_ok=True)
    dicts = [asdict(r) if hasattr(r, "__dataclass_fields__") else dict(r) for r in rows]
    if fieldnames is None:
        fieldnames = list(dicts[0].keys()) if dicts else []
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in dicts:
            w.writerow({k: r.get(k, "") for k in fieldnames})


def write_summary(path: Path, args, members: List[Dict[str, str]], pubs: List[CandidatePublication], auths: List[AuthorshipCandidate], log: SearchLog):
    source_counts = {}
    for a in auths:
        source_counts[a.source_database] = source_counts.get(a.source_database, 0) + 1
    conf_counts = {}
    for a in auths:
        conf_counts[a.confidence_hint] = conf_counts.get(a.confidence_hint, 0) + 1
    summary = {
        "created_at_utc": now_utc(),
        "members_input_rows": len(members),
        "candidate_publications_rows": len(pubs),
        "authorship_candidate_rows": len(auths),
        "authorship_candidates_by_source": source_counts,
        "authorship_candidates_by_confidence_hint": conf_counts,
        "sources_requested": args.sources,
        "max_results_per_source": args.max_results_per_source,
        "note": "Candidates only. Do not interpret as verified PTPP member publications without manual audit.",
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--members-csv", required=True, help="Path to PTPP members snapshot CSV")
    ap.add_argument("--output-dir", default=".", help="Project root / output directory")
    ap.add_argument("--email", default=os.environ.get("ANDROMEDA_CONTACT_EMAIL", ""), help="Contact email for polite API use")
    ap.add_argument("--sources", nargs="+", default=["crossref", "openalex", "pubmed"], choices=["crossref", "openalex", "pubmed", "orcid"])
    ap.add_argument("--max-results-per-source", type=int, default=20)
    ap.add_argument("--max-author-entities", type=int, default=4)
    ap.add_argument("--min-name-score", type=float, default=0.65)
    ap.add_argument("--sleep", type=float, default=0.35)
    ap.add_argument("--timeout", type=int, default=30)
    ap.add_argument("--limit-persons", type=int, default=0, help="For testing only; 0 means all rows")
    ap.add_argument("--ncbi-api-key", default=os.environ.get("NCBI_API_KEY", ""))
    args = ap.parse_args()

    out = Path(args.output_dir)
    members_path = Path(args.members_csv)
    members = read_members(members_path)
    if args.limit_persons:
        members = members[: args.limit_persons]

    raw_json_dir = out / "data_intermediate" / "raw_api_json"
    raw_json_dir.mkdir(parents=True, exist_ok=True)

    log = SearchLog()
    all_pubs: List[CandidatePublication] = []
    all_auths: List[AuthorshipCandidate] = []

    searchers = {
        "crossref": search_crossref,
        "openalex": search_openalex,
        "pubmed": search_pubmed,
        "orcid": search_orcid,
    }

    for i, person in enumerate(members, start=1):
        full, surname, given = split_name_from_ptpp(person)
        if not surname or not given:
            log.add(source_database="all", person_id=person.get("person_id", ""), http_status="SKIPPED", error="missing parsed surname/given", name_ptpp_order=full)
            continue
        print(f"[{i}/{len(members)}] {surname}, {given}", flush=True)
        for src in args.sources:
            try:
                pubs, auths = searchers[src](person, args, log, raw_json_dir)
                all_pubs.extend(pubs)
                all_auths.extend(auths)
            except KeyboardInterrupt:
                raise
            except Exception as e:
                log.add(source_database=src, person_id=person.get("person_id", ""), http_status="EXCEPTION", error=repr(e), query_name=western_name(given, surname))
            polite_sleep(args.sleep)

    all_pubs = dedupe_pubs(all_pubs)

    write_dataclass_csv(out / "data_intermediate" / "publication_candidates_raw.csv", all_pubs)
    write_dataclass_csv(out / "data_intermediate" / "authorship_candidates_raw.csv", all_auths)

    # Person/source summary
    summary_rows = {}
    for a in all_auths:
        key = (a.person_id, a.source_database)
        if key not in summary_rows:
            summary_rows[key] = {
                "person_id": a.person_id,
                "name_ptpp_order": a.name_ptpp_order,
                "membership_category": a.membership_category,
                "source_database": a.source_database,
                "candidate_authorships": 0,
                "high_candidate": 0,
                "medium_candidate": 0,
                "low_candidate": 0,
                "very_low_candidate": 0,
                "max_total_candidate_score": 0.0,
            }
        r = summary_rows[key]
        r["candidate_authorships"] += 1
        r[a.confidence_hint] = r.get(a.confidence_hint, 0) + 1
        r["max_total_candidate_score"] = max(float(r["max_total_candidate_score"]), float(a.total_candidate_score))
    write_dataclass_csv(out / "data_intermediate" / "person_source_summary.csv", list(summary_rows.values()))

    log.write(out / "logs" / "publication_candidate_search_log.csv")
    write_summary(out / "docs" / "publication_candidate_search_summary.json", args, members, all_pubs, all_auths, log)

    print("\nDone.")
    print(f"Candidate publications: {len(all_pubs)}")
    print(f"Authorship candidates:  {len(all_auths)}")
    print("Next: manually audit data_intermediate/authorship_candidates_raw.csv")


if __name__ == "__main__":
    main()
