#!/usr/bin/env python3
"""Isolated, human-in-the-loop PEP metadata extension for Gaming Mind.

No network on `plan`/`audit`; `probe` needs a checked permission basis;
`harvest` additionally needs an explicit approval flag.
Keeps all new data under data_gaming_mind_extension/ and never modifies
Lech's psychoanalytic_core tables or scripts.
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import random
import re
import sys
import time

import pandas as pd

HERE = Path(__file__).resolve().parent
CONFIG = json.loads((HERE / 'journals.json').read_text(encoding='utf-8'))
TERM_CONFIG = json.loads((HERE / 'gaming_search_terms.json').read_text(encoding='utf-8'))
JOURNALS = CONFIG['new_journals']


def root_repo() -> Path:
    for path in [HERE.parent, Path.cwd(), *Path.cwd().parents]:
        if (path / 'data_psychoanalytic_core/scripts/1a_pep_metadata_probe_v12.py').is_file():
            return path.resolve()
    raise SystemExit('Repository not found. Put this folder next to data_psychoanalytic_core/.')


def load_module(script: Path, module_name: str):
    spec = importlib.util.spec_from_file_location(module_name, script)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Cannot load module {script}')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_json(path: Path, obj: object):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding='utf-8')


def append_csv(path: Path, row: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    with path.open('a', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(row))
        if not exists:
            writer.writeheader()
        writer.writerow(row)


def file_paths(out: Path, stage: str, key: str, year: int) -> dict:
    stem = f'{key}_{year}'
    return {
        'raw': out / stage / 'raw_pep_metadata' / key / str(year),
        'articles': out / stage / 'harvest' / 'articles_by_year' / key / f'{stem}_articles.csv',
        'keywords': out / stage / 'harvest' / 'keywords_by_year' / key / f'{stem}_keywords.csv',
        'log': out / stage / 'logs' / key / f'{stem}_api_log.csv',
    }


def parse_keys(spec: str) -> list[str]:
    if spec == 'all':
        return list(JOURNALS)
    keys = [x.strip() for x in spec.split(',') if x.strip()]
    if not keys or any(x not in JOURNALS for x in keys):
        raise SystemExit('Invalid --journals: ' + spec + '; choose ' + ', '.join(JOURNALS))
    return list(dict.fromkeys(keys))


def read_csv(path: Path) -> pd.DataFrame:
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path, dtype=str, keep_default_na=False, encoding='utf-8-sig')


def run_network(args, out: Path, repo: Path) -> int:
    if not args.permission_checked:
        raise SystemExit('STOP: Lech must check API/usage permissions; then pass --permission-checked.')
    if args.action == 'harvest' and not args.approved:
        raise SystemExit('STOP: full harvesting needs explicit human approval; pass --approved after a successful probe.')
    stage = args.action
    probe_path = repo / 'data_psychoanalytic_core/scripts/1a_pep_metadata_probe_v12.py'
    base = load_module(probe_path, 'andromeda_pep_probe_v12')
    base.PROJECT_ROOT = repo   # raw output is under repo: relative path logging works
    for key, meta in JOURNALS.items():
        base.JOURNALS[key] = {'journal_label': meta['title'], 'pep_code': meta['pep_prefix']}
    env_path = repo / 'data_psychoanalytic_core/.env.pep'
    if args.env:
        env_path = Path(args.env).expanduser().resolve()
    if not env_path.exists() and not any(k.startswith('PEP_') for k in __import__('os').environ):
        raise SystemExit('No local .env.pep or PEP_* env settings. Do not paste credentials into chat.')
    keys = parse_keys(args.journals)
    jobs = [(key, year) for key in keys for year in (
        [args.probe_year] if stage == 'probe' else
        range(max(1970, JOURNALS[key]['first_year']), 2026)
    )]
    manifest = out / stage / 'manifest.csv'
    print('Stage:', stage, 'Jobs:', len(jobs), 'Output:', out)
    processed = 0
    for key, year in jobs:
        meta = JOURNALS[key]
        p = file_paths(out, stage, key, year)
        if p['articles'].exists() and p['log'].exists():
            print('SKIP existing:', key, year)
            continue
        if stage == 'harvest':
            probe_articles = file_paths(out, 'probe', key, args.probe_year)['articles']
            probe_manifest = read_csv(out / 'probe' / 'manifest.csv')
            probe_ok = (not probe_manifest.empty and
                        (probe_manifest['journal'] == key).any() and
                        probe_manifest.loc[probe_manifest['journal'] == key, 'status'].isin(['ok', 'ok_sample_limited']).any())
            if not probe_articles.exists() or not probe_ok:
                raise SystemExit(f'STOP: missing successful probe for {key}; run `probe` and inspect logs first.')
        for path in p.values():
            path.mkdir(parents=True, exist_ok=True) if path == p['raw'] else path.parent.mkdir(parents=True, exist_ok=True)
        argv = ['--journal', key, '--year', str(year),
                '--facetquery', f"art_id:{meta['pep_prefix']}.* AND year:{year}",
                '--limit', str(args.probe_limit if stage == 'probe' else args.limit),
                '--delay', '0', '--timeout', '60', '--env', str(env_path),
                '--flat-csv', str(p['articles']), '--keywords-long-csv', str(p['keywords']),
                '--log', str(p['log']), '--out-dir', str(p['raw'])]
        status = 'ok'; note = ''
        try:
            code = base.main(argv)
            if code != 0:
                status = 'failed'; note = f'probe return code {code}'
        except Exception as exc:
            status = 'failed'; note = f'{type(exc).__name__}: {exc}'
        df = read_csv(p['articles'])
        log = read_csv(p['log'])
        http = ','.join(log['status_code'].tolist()) if 'status_code' in log else ''
        n = len(df)
        prefix_ids = df.get('document_id', pd.Series(dtype=str)).astype(str)
        wrong_prefix = int((~prefix_ids.str.upper().str.startswith(meta['pep_prefix'] + '.')).sum()) if n else 0
        if not log.empty and any(x not in {'200', ''} for x in log.get('status_code', [])):
            status = 'http_error'; note = 'Non-200 HTTP result; stop for manual investigation.'
        if n == 0:
            status = 'empty'; note = 'No records: verify code/year/permissions.'
        if wrong_prefix:
            status = 'wrong_prefix'; note = f'{wrong_prefix} document IDs mismatch journal code.'
        if stage == 'probe' and n >= args.probe_limit and status == 'ok':
            status = 'ok_sample_limited'; note = 'Sample reached probe limit (expected; not complete coverage).'
        if stage == 'harvest' and n >= args.limit:
            status = 'possible_truncation'; note = 'Hit harvest limit; pagination needed before continuing.'
        manifest_row = {'timestamp_utc': utc_now(), 'stage': stage, 'journal': key,
                        'pep_prefix': meta['pep_prefix'], 'year': year, 'status': status,
                        'http_statuses': http, 'n_rows': n, 'wrong_prefix_ids': wrong_prefix,
                        'csv': str(p['articles']), 'note': note}
        append_csv(manifest, manifest_row)
        print(key, year, status, f'n={n}', note)
        processed += 1
        if status not in {'ok', 'ok_sample_limited'}:
            print('STOP: inspect manifest; no automatic retries or bypass.')
            return 2
        if processed < len(jobs):
            time.sleep(random.uniform(4, 8))
    print('Finished. Inspect', manifest)
    return 0


def audit(out: Path, repo: Path, args) -> int:
    keys = parse_keys(args.journals)
    harvested = []
    source_files = []
    for key in keys:
        base = out / 'harvest' / 'harvest' / 'articles_by_year' / key
        if not base.exists():
            continue
        for file in sorted(base.glob('*_articles.csv')):
            df = read_csv(file)
            if df.empty:
                continue
            df['journal_key'] = key
            df['source_local_csv'] = str(file.relative_to(repo))
            source_files.append(str(file.relative_to(repo)))
            harvested.append(df)
    target = out / 'qa'
    target.mkdir(parents=True, exist_ok=True)
    if not harvested:
        print('No full-harvest records yet. Run probe and then approved harvest.')
        return 1
    all_df = pd.concat(harvested, ignore_index=True).fillna('')
    all_df['year_for_analysis'] = pd.to_numeric(all_df.get('year_record', ''), errors='coerce')
    all_df['qa_out_of_period'] = ~all_df['year_for_analysis'].between(1970, 2025)
    all_df['qa_missing_title'] = all_df.get('title', '').astype(str).str.strip().eq('')
    all_df['qa_missing_id'] = all_df.get('document_id', '').astype(str).str.strip().eq('')
    ids = all_df['document_id'].astype(str).str.strip()
    all_df['qa_duplicate_id'] = ids.ne('') & ids.duplicated(keep='first')
    all_df['qa_wrong_journal_prefix'] = [not str(pid).upper().startswith(JOURNALS[key]['pep_prefix'] + '.')
                                        for pid, key in zip(ids, all_df['journal_key'])]
    all_df['qa_ART'] = all_df.get('article_type', '').astype(str).str.upper().eq('ART')
    all_df.to_csv(target / 'all_records_with_flags.csv', index=False, encoding='utf-8-sig')
    reject_mask = (~all_df['qa_ART'] | all_df['qa_out_of_period'] | all_df['qa_missing_title'] |
                   all_df['qa_missing_id'] | all_df['qa_duplicate_id'] | all_df['qa_wrong_journal_prefix'])
    excluded = all_df[reject_mask].copy()
    excluded.to_csv(target / 'exclusions_audit.csv', index=False, encoding='utf-8-sig')
    art = all_df[~reject_mask].copy()
    # Re-use Lech's reviewed abstract recovery script: local raw JSON only.
    script = repo / 'data_psychoanalytic_core/scripts/1e_extract_abstract_texts_from_raw_json.py'
    recovery = load_module(script, 'andromeda_abstract_recovery')
    raw_root = out / 'harvest' / 'raw_pep_metadata'
    raw_files = recovery.list_raw_json_files(raw_root, keys)
    abstracts, candidates, abstract_stats = recovery.extract_all(raw_files, repo)
    (target / 'audit').mkdir(exist_ok=True)
    abstracts[['article_id', 'abstract_text_length', 'abstract_extraction_field_name', 'raw_json_file']].to_csv(
        target / 'audit' / 'abstract_extraction_log.csv', index=False, encoding='utf-8-sig') if not abstracts.empty else None
    if not abstracts.empty:
        art = art.merge(abstracts[['article_id', 'abstract_text', 'abstract_text_length']],
                        left_on='document_id', right_on='article_id', how='left', validate='many_to_one')
    if 'abstract_text' not in art:
        art['abstract_text'] = ''
    art['abstract_text'] = art['abstract_text'].fillna('')
    art['title_clean'] = art['title'].astype(str).apply(recovery.clean_html_text)
    art['abstract_clean'] = art['abstract_text'].astype(str).apply(recovery.clean_html_text)
    art['text_for_analysis'] = art['title_clean'] + '. ' + art['abstract_clean']
    art['qa_missing_abstract'] = art['abstract_clean'].str.strip().eq('')
    art['qa_suspiciously_long_abstract'] = art['abstract_clean'].str.len() > 12000
    art.to_csv(target / 'ART_title_abstract_extension.csv', index=False, encoding='utf-8-sig')
    (art.groupby(['journal_key', 'year_for_analysis'], dropna=False).size()
        .rename('n_ART').reset_index().to_csv(target / 'counts_by_journal_year.csv',
                                              index=False, encoding='utf-8-sig'))
    screen(art, target)
    summary = {'created_at_utc': utc_now(), 'analysis_years': [1970, 2025],
               'source_files': source_files, 'n_raw_rows': len(all_df),
               'n_excluded_records': len(excluded), 'n_ART_eligible': len(art),
               'ART_by_journal': {str(k): int(v) for k, v in art['journal_key'].value_counts().items()},
               'n_ART_missing_abstract': int(art['qa_missing_abstract'].sum()),
               'n_ART_suspiciously_long_abstract': int(art['qa_suspiciously_long_abstract'].sum()),
               'n_wrong_prefix': int(all_df['qa_wrong_journal_prefix'].sum()),
               'n_duplicate_document_id': int(all_df['qa_duplicate_id'].sum()),
               'n_abstract_json_files': abstract_stats['raw_json_files_seen'],
               'n_abstract_json_errors': abstract_stats['raw_json_errors'],
               'n_abstracts_extracted_unique': abstract_stats['extracted_abstract_rows'],
               'limitations': ['Metadata title-and-abstract layer, not full texts.',
                               'Missing abstracts and metadata fields require QA.',
                               'New journals have uneven starting years.',
                               'Topical coding remains human-in-the-loop.']}
    save_json(target / 'summary.json', summary)
    save_json(target / 'transformation_log.json', {
        'created_at_utc': utc_now(),
        'source': 'Existing PEP v12 flattened yearly CSV and locally preserved API JSON',
        'steps': ['concatenate yearly raw metadata without rewriting files',
                  'mark year/title/id/prefix/duplicate/ART status for QA',
                  'create exclusions audit (non-ART and QA failures)',
                  'extract abstracts from locally preserved JSON using Lech 1e routine',
                  'create title_clean + abstract_clean as a metadata-bounded analysis layer',
                  'mark missing/very long abstracts; screen exploratory gaming terms',
                  'leave all substantive inclusion judgments pending human review'],
        'source_file_count': len(source_files),
        'screening_vocabulary_version': TERM_CONFIG['version'],
        'corpus_rule': 'article_type == ART, 1970-2025, with documented exclusions',
    })
    (target / 'method_note.md').write_text(
        '# Extension QA methodological note\n\n'
        'Input: PEP-Web metadata (eight additional journals, 1970–2025).\n\n'
        'The ART-only title-and-abstract layer is used for exploratory gaming discourse screening. '
        'Excluded/ambiguous records are preserved with QA flags. '
        'Term hits are not yet interpreted as scientifically relevant discourse instances. '
        'No full texts or PDFs were downloaded by this extension.\n', encoding='utf-8')
    print('Audit saved:', target / 'summary.json')
    print('ART-eligible:', len(art), 'screening candidates saved.')
    return 0


def screen(df: pd.DataFrame, target: Path):
    patterns = {tier: {name: re.compile(expr) for name, expr in terms.items()}
                for tier, terms in TERM_CONFIG.items() if isinstance(terms, dict)}
    hits = []
    for row in df.to_dict('records'):
        text = str(row.get('text_for_analysis', ''))
        matches = {tier: [name for name, regex in pat.items() if regex.search(text)]
                   for tier, pat in patterns.items()}
        if not any(matches.values()):
            continue
        tier = 'strong' if matches.get('high_precision') else 'needs_context'
        hits.append({'document_id': row.get('document_id', ''), 'year': row.get('year_for_analysis', ''),
                     'journal_key': row.get('journal_key', ''), 'title': row.get('title_clean', ''),
                     'match_tier': tier, 'high_precision': '; '.join(matches.get('high_precision', [])),
                     'contextual_review': '; '.join(matches.get('contextual_review', [])),
                     'manual_decision': '', 'review_notes': '',
                     'abstract_length': len(str(row.get('abstract_clean','')))})
    cols = ['document_id', 'year', 'journal_key', 'title', 'match_tier', 'high_precision',
            'contextual_review', 'manual_decision', 'review_notes', 'abstract_length']
    pd.DataFrame(hits, columns=cols).to_csv(target / 'gaming_candidate_review_queue.csv', index=False,
                                            encoding='utf-8-sig')


def main():
    p = argparse.ArgumentParser(description='PEP metadata extension — separate working layer')
    p.add_argument('action', choices=['plan', 'probe', 'harvest', 'audit'])
    p.add_argument('--journals', default='all')
    p.add_argument('--probe-year', type=int, default=2020)
    p.add_argument('--probe-limit', type=int, default=25)
    p.add_argument('--limit', type=int, default=500)
    p.add_argument('--permission-checked', action='store_true', help='Explicit local TOS/API check completed')
    p.add_argument('--approved', action='store_true', help='Explicit approval of full metadata harvest')
    p.add_argument('--env', default=None, help='Local path to existing PEP env; do not share')
    args = p.parse_args()
    repo = root_repo()
    out = repo / 'data_gaming_mind_extension' / 'data'
    if args.action != 'plan':
        private_root = out.parent
        private_root.mkdir(parents=True, exist_ok=True)
        ignore_file = private_root / '.gitignore'
        if not ignore_file.exists():
            ignore_file.write_text('data/\n', encoding='utf-8')
    if args.action == 'plan':
        plan = [{'journal_key': key, 'title': m['title'], 'pep_prefix_to_probe': m['pep_prefix'],
                 'begin': max(1970, m['first_year']), 'end': 2025,
                 'pep_url': m['pep_url']} for key, m in JOURNALS.items()]
        print('Planned isolated extension at', out)
        for row in plan: print(row)
        return 0
    if args.action in {'probe', 'harvest'}:
        return run_network(args, out, repo)
    return audit(out, repo, args)


if __name__ == '__main__':
    sys.exit(main())
