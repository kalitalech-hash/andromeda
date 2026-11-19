#!/usr/bin/env python3
"""D03: researcher-approved D02 concepts -> auditable document frequencies and co-presence.
From data_avatar_therapy_voices_starter:
python scripts/06_approved_semantic_analysis_D03.py \
 --corpus outputs/qa/avatar01_full_strict_v05/analysis_corpus_ABC.csv \
 --assignments outputs/analyses/avatar_discourse_D02_v01/candidate_article_concepts.csv \
 --mapping outputs/analyses/avatar_discourse_D02_v01/semantic_map_provisional.csv \
 --output-dir outputs/analyses/avatar_discourse_D03_reproduced_v01 \
 --researcher-approved
"""
from __future__ import annotations
import argparse,csv,hashlib,json,math
from collections import Counter
from itertools import combinations
from pathlib import Path

PERIODS=[("2009-2015",2009,2015),("2016-2020",2016,2020),("2021-2026",2021,2026)]
def read(path):
    with Path(path).open(encoding="utf-8-sig",newline="") as fh:return list(csv.DictReader(fh))
def write(path,header,rows):
    with path.open("w",encoding="utf-8",newline="") as fh:
        w=csv.writer(fh);w.writerow(header);w.writerows(rows)
def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    ap=argparse.ArgumentParser()
    for k in ("corpus","assignments","mapping","output_dir"):ap.add_argument("--"+k.replace("_","-"),required=True)
    ap.add_argument("--researcher-approved",action="store_true",help="Explicit HITL sign-off; fail closed otherwise")
    a=ap.parse_args()
    if not a.researcher_approved:ap.error("Explicit researcher approval is required.")
    out=Path(a.output_dir)
    if out.exists() and any(out.iterdir()):ap.error("Output directory nonempty; choose a new version.")
    records=[r for r in read(a.corpus) if r.get("publication_type")=="article" and r.get("qa_layer") in ("A","B","C")]
    mapping=read(a.mapping); assignments=read(a.assignments)
    cdict={r["concept_id"]:(r["concept_label_en"],r["concept_label_pl"]) for r in mapping}
    known={r.get("openalex_id") or r["article_id"]:r for r in records}
    if len(known)!=len(records) or not known:raise ValueError("Missing/duplicate corpus IDs")
    pairs=set()
    for r in assignments:
        key=(r["article_id"],r["concept_id"])
        if key in pairs or key[0] not in known or key[1] not in cdict:raise ValueError("Duplicate or invalid article-concept pair")
        pairs.add(key)
    belongs={id:set() for id in known}
    for aid,cid in pairs:belongs[aid].add(cid)
    def distribution(sub):
        d=Counter()
        for r in sub:
            for cid in belongs[r.get("openalex_id") or r["article_id"]]:d[cid]+=1
        return d
    overall=distribution(records)
    concepts=sorted(cdict)
    out.mkdir(parents=True)
    write(out/"semantic_map_approved.csv",["candidate_term","concept_id","concept_label_en","concept_label_pl","D02_n_documents","semantic_action","audit_decision","decision_actor","decision_note"],[(r["candidate_term"],r["concept_id"],r["concept_label_en"],r["concept_label_pl"],r.get("n_documents",""),"merge_approved_by_researcher","approved","researcher","User approved D02 concepts; this does not validate each article in context") for r in mapping])
    write(out/"terms_semantic_final.csv",["article_id","concept_id","concept_label_en","concept_label_pl","qa_layer","year","approval_status"],[(aid,cid,*cdict[cid],known[aid]["qa_layer"],known[aid]["year"],"approved_concept_mapping") for aid,cid in sorted(pairs)])
    write(out/"concept_counts_overall.csv",["concept_id","concept_label_en","concept_label_pl","n_articles","pct_articles"],[(c,*cdict[c],overall[c],round(100*overall[c]/len(records),2)) for c in concepts])
    def stratify(groups):
        rows=[]
        for label,sub in groups:
            n=len(sub); d=distribution(sub)
            for c in concepts:rows.append((label,n,c,d[c],round(100*d[c]/n,2) if n else 0))
        return rows
    byperiod=[(name,[r for r in records if r["year"].isdigit() and lo<=int(r["year"])<=hi]) for name,lo,hi in PERIODS]
    write(out/"concept_period_trends.csv",["period","n_articles","concept_id","n_articles_with_concept","pct_articles_in_period"],stratify(byperiod))
    write(out/"concept_layer_comparison.csv",["layer","n_articles","concept_id","n_articles_with_concept","pct_articles_in_layer"],stratify([(k,[r for r in records if r["qa_layer"]==k]) for k in "ABC"]))
    write(out/"concept_journal_comparison.csv",["journal","n_articles","concept_id","n_articles_with_concept","pct_articles_in_journal"],stratify([(k,[r for r in records if r["journal"]==k]) for k in sorted({r["journal"] for r in records})]))
    write(out/"period_denominators.csv",["period","n_articles","A","B","C","articles_with_any_concept"],[(p,len(sub),*(sum(r["qa_layer"]==l for r in sub) for l in "ABC"),sum(bool(belongs[r.get("openalex_id") or r["article_id"]]) for r in sub)) for p,sub in byperiod])
    edges=Counter()
    for set_ in belongs.values():edges.update(combinations(sorted(set_),2))
    n=len(records)
    write(out/"concept_copresence_edges.csv",["source_concept_id","target_concept_id","weight_n_articles","source_df","target_df","cosine","lift"],[(a,b,w,overall[a],overall[b],round(w/math.sqrt(overall[a]*overall[b]),4),round(w*n/(overall[a]*overall[b]),4)) for (a,b),w in sorted(edges.items(),key=lambda kv:(-kv[1],kv[0]))])
    summary={"schema_version":"avatar_discourse_D03_v01","mapping_status":"RESEARCHER_APPROVED_CONCEPTS","n_articles":n,"n_concepts":len(concepts),"n_approved_variants":len(mapping),"n_article_concept_pairs":len(pairs),"articles_with_matches":sum(bool(v) for v in belongs.values()),"articles_without_matches":sum(not v for v in belongs.values()),"n_distinct_edges":len(edges),"input_sha256":{"corpus":sha(a.corpus),"assignments":sha(a.assignments),"mapping":sha(a.mapping)},"scope":"metadata-bounded selected-topic corpus; not contextual full-text validation"}
    (out/"analysis_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (out/"transformation_log.json").write_text(json.dumps({"approval":"human researcher in conversation","steps":["validate D02 mapping","validate unique article-concept pairs","aggregate counts by period, layer, journal","calculate co-presence"],"previous_layers_overwritten":False},indent=2)+"\n",encoding="utf-8")
    (out/"METHODS.md").write_text("# D03 approved concept aggregation\n\nResearcher-approved D02 phrase-to-concept mapping; not independent validation of each match. Title + accessible abstract, article-labelled A/B/C cohort. Binary document presence; overlapping concepts; co-presence within an article. Rates per stratum use all article-labelled eligible records as denominators, including unmatched articles. Source retrieval was bounded, 2026 incomplete. No inference about treatment efficacy, field-wide prevalence, or causal relation.\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
