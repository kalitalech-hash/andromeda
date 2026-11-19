#!/usr/bin/env python3
"""Andromeda v0.5: deterministic A/B/C screen + non-destructive QC.

Uses titles and available abstracts, NOT full texts. Automatic exclusions are
recorded, never deleted. This is high-precision screening, not a claim of recall.
"""
from __future__ import annotations
import argparse, collections, csv, datetime as dt, hashlib, json, re, unicodedata
from pathlib import Path

FIELDS_EXTRA = ['qa_layer','qa_include','qa_rule','qa_flags','qa_note']
LEX = {
    'avatar': r'\bavatars?\b|\bavatar[- ](?:based|assisted|mediated)\b',
    'voice': r'\bauditory(?: verbal)? hallucinations?\b|\bvoice[- ]hear(?:er|ers|ing)?\b|\bhearing voices\b|\bdistressing voices\b|\bpersecutory voices\b|\bvoice[- ]related distress\b|\bvoices\b',
    'relation': r'\brelat(?:e|ed|es|ing|ional|ionship|ionships)\b|\bdialogu(?:e|es)\b|\bdominanc\w*\b|\bpower\b|\bagency\b|\bassertiv\w*\b|\bpersonif\w*\b|\bvoice[- ]dialogue\b|\bengag(?:e|ement|ing)\b|\bcompassion\b|\bacceptance\b',
    'therapy': r'\btherap\w*\b|\btreat(?:ment|ing)?\b|\bintervention\w*\b|\btrial\b|\bpsychotherap\w*\b|\bcbt\b|\bpsychological\b',
    'vr': r'\bvirtual reality\b|\bimmersive\b|\bVR[- ](?:based|assisted|therapy|intervention|exposure)\b|\bVR\b',
    'psychosis': r'\bpsychos(?:is|es|ocial)\b|\bpsychotic\b|\bschizophren\w*\b|\bauditory(?: verbal)? hallucinations?\b',
}
PATS = {k: re.compile(v, re.I) for k,v in LEX.items()}

def normalize(s):
    return ' '.join(unicodedata.normalize('NFKC', str(s or '')).casefold().split())

def doi(s):
    return re.sub(r'^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)', '', normalize(s)).strip()

def title_key(s):
    return re.sub(r'[^\w]+',' ',normalize(s)).strip()

def file_hash(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(65536),b''):h.update(b)
    return h.hexdigest()

def classify(r, exclude_nonresearch=False):
    title=r.get('title','') or ''
    abstract=r.get('abstract','') or ''
    text=title+' '+abstract
    m={k:bool(p.search(text)) for k,p in PATS.items()}
    flags=[]
    for field in ('title','year','abstract','doi','language'):
        if not (r.get(field,'') or '').strip():flags.append('missing_'+field)
    pub=normalize(r.get('publication_type',''))
    if pub in ('book-review','conference-abstract','conference-paper'):
        flags.append('publication_type_special')
    if exclude_nonresearch and pub in ('book-review','conference-abstract','conference-paper'):
        return ('EXCLUDE', 'publication_type_policy',flags,m)
    if not title.strip() or not (r.get('year','') or '').strip():
        return ('EXCLUDE','required_metadata_missing',flags,m)
    # precedence A -> B -> C. 'Avatar' in abstract alone requires therapy+voice,
    # preventing generic avatar technologies from entering A.
    if m['avatar'] and m['voice'] and m['therapy']:
        return ('A','avatar_voice_therapy',flags,m)
    if m['voice'] and m['relation']:
        return ('B','voices_relational',flags,m)
    if m['vr'] and m['psychosis'] and m['therapy']:
        return ('C','vr_psychosis_intervention',flags,m)
    return ('EXCLUDE','outside_three_strict_layers',flags,m)

def atomic_write(path, content):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(content,encoding='utf-8')
    tmp.replace(path)

def write_csv(path,rows,fields):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_suffix(path.suffix+'.tmp')
    with tmp.open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore')
        writer.writeheader();writer.writerows(rows)
    tmp.replace(path)

def run(input_path, output_dir, exclude_nonresearch=False):
    input_path=Path(input_path); out=Path(output_dir)
    if not input_path.is_file():raise FileNotFoundError(input_path)
    if input_path.resolve().is_relative_to(out.resolve()):
        raise ValueError('Source file cannot reside inside the QA output directory')
    with input_path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        required={'title','year','doi','openalex_id','journal'}
        if not required.issubset(set(reader.fieldnames or [])):
            raise ValueError(f'Missing required columns: {sorted(required-set(reader.fieldnames or []))}')
        records=list(reader)
        fields=list(reader.fieldnames)
    for field in FIELDS_EXTRA:
        if field not in fields:fields.append(field)
    seen_ids={};seen_doi={};seen_title_year={}
    retained=[];dups=[];excluded=[];audit=[]
    counts=collections.Counter(); rules=collections.Counter(); by_journal=collections.Counter(); types=collections.Counter()
    for idx,r in enumerate(records,2):
        r=dict(r);oid=normalize(r.get('openalex_id'));dk=doi(r.get('doi'))
        tk=title_key(r.get('title'))+'|'+str(r.get('year','')).strip() if r.get('title') and r.get('year') else ''
        dup_with=None;dup_rule=None
        for label,key,lookup in [('openalex_id',oid,seen_ids),('doi',dk,seen_doi),('title_year',tk,seen_title_year)]:
            if key and key in lookup:dup_with=lookup[key];dup_rule=label;break
        if dup_with is not None:
            dups.append({'row_number':idx,'article_id':r.get('openalex_id',''),'duplicate_of_row':dup_with,'match_type':dup_rule})
            continue
        if oid:seen_ids[oid]=idx
        if dk:seen_doi[dk]=idx
        if tk:seen_title_year[tk]=idx
        layer,rule,flags,_=classify(r,exclude_nonresearch)
        r.update({'qa_layer':layer,'qa_include':'true' if layer!='EXCLUDE' else 'false','qa_rule':rule,'qa_flags':';'.join(flags),'qa_note':'automated_strict_v0.5_not_fulltext_review'})
        audit.append(r);counts[layer]+=1;rules[rule]+=1;types[r.get('publication_type','')]+=1
        if layer=='EXCLUDE':excluded.append(r)
        else:retained.append(r);by_journal[(r.get('journal',''),layer)]+=1
    write_csv(out/'screening_all_audited.csv',audit,fields)
    write_csv(out/'analysis_corpus_ABC.csv',retained,fields)
    write_csv(out/'excluded_records.csv',excluded,fields)
    write_csv(out/'duplicates.csv',dups,['row_number','article_id','duplicate_of_row','match_type'])
    summary={'schema_version':'strict_qa_0.5','input_path':str(input_path),'input_sha256':file_hash(input_path),
             'created_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'raw_count':len(records),
             'unique_count':len(audit),'duplicates':len(dups),'included':len(retained),'excluded':len(excluded),
             'layers':dict(counts),'rules':dict(rules), 'publication_types':dict(types),
             'missing_abstract_all':sum(not r.get('abstract','').strip() for r in audit),
             'missing_abstract_included':sum(not r.get('abstract','').strip() for r in retained),
             'missing_doi_all':sum(not r.get('doi','').strip() for r in audit),
             'journal_layer_counts':[{'journal':j,'layer':l,'n':n} for (j,l),n in sorted(by_journal.items())],
             'exclude_nonresearch':exclude_nonresearch,
             'methods_warning':'High-precision heuristic; not a validated exhaustive topic screen. Search sample/full remains page-capped. Excluded rows remain accessible. Nonexclusive meanings resolved with A>B>C precedence.'}
    atomic_write(out/'qa_summary.json',json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
    atomic_write(out/'transformation_log.json',json.dumps({'timestamp_utc':summary['created_utc'],'input_sha256':summary['input_sha256'],'steps':['deduplicate id/doi/title+year','mark missing fields','apply deterministic A>B>C rules','record all excluded rows','export non-destructive derived corpus'],'rule_patterns':LEX,'output_version':'0.5'},indent=2,ensure_ascii=False)+'\n')
    atomic_write(out/'methodological_note.md',f'''# Stage 02 — strict automatic screening\n\nSource: `{input_path}`; SHA-256: `{summary['input_sha256']}`.\n\nRetained: **{len(retained)}** (A {counts['A']}, B {counts['B']}, C {counts['C']}); excluded: **{len(excluded)}**; duplicates: **{len(dups)}**.\n\nUser-approved strict inclusion: A = avatar-based therapy of voices; B = voices and their relational/dialogic framing; C = virtual reality + psychosis + treatment. First matching class wins (A > B > C). All other records are excluded from analytical outputs, but preserved in `excluded_records.csv` and `screening_all_audited.csv`.\n\nOnly titles and available abstracts are used; *absence of abstract is flagged, not alone a reason for exclusion*. This conservative lexical screen may miss synonymic formulations and **does not establish exhaustive coverage or human-validated relevance**. Report this limitation in manuscript methods. Source acquisition remains page-capped.\n\nNo raw record or earlier corpus layer was overwritten.\n''')
    print(json.dumps(summary,ensure_ascii=False,indent=2))
    return summary

if __name__=='__main__':
    ap=argparse.ArgumentParser(description='QA-02 strictly retain A (avatar voices), B (relating to voices), C (VR psychosis treatment)')
    ap.add_argument('--input',default='outputs/raw/avatar01_full_v04/raw_candidates.csv')
    ap.add_argument('--output-dir',default='outputs/qa/avatar01_full_strict_v05')
    ap.add_argument('--exclude-nonresearch-types',action='store_true',help='Additionally exclude book reviews and conference-only records')
    a=ap.parse_args();run(a.input,a.output_dir,a.exclude_nonresearch_types)
