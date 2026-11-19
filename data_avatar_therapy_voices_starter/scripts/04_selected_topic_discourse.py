#!/usr/bin/env python3
"""Andromeda D01: exploratory lexical signals in selected-topic article metadata.
Standard-library only; writes aggregate outputs, never republishes raw abstracts.
Run from data_avatar_therapy_voices_starter:
 python scripts/04_selected_topic_discourse.py --input outputs/qa/avatar01_full_strict_v05/analysis_corpus_ABC.csv --output-dir outputs/analyses/avatar_discourse_D01_v01
"""
from __future__ import annotations
import argparse, csv, datetime as dt, hashlib, json, re, unicodedata
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

PATTERNS = {
 "avatar_mention": r"\bavatars?\b",
 "virtual_reality": r"\bvirtual reality\b|\bimmersive\b|\bVR[- ](?:based|assisted|therapy|intervention|exposure)\b|\bVR\b",
 "relational_language": r"\brelat(?:e|ed|es|ing|ional|ionship|ionships)\b|\binterpersonal\b|\btherapeutic alliance\b",
 "dialogue": r"\bdialogu(?:e|es|ing)\b|\bconversation\b",
 "power_control": r"\bpower\b|\bcontrol\b|\bdominanc\w*\b|\bassertiv\w*\b|\bagency\b",
 "distress": r"\bdistress\w*\b|\bsuffer\w*\b|\bfear\b|\bthreat\w*\b",
 "cbt": r"\bcognitive behaviou?r\w*\b|\bcbt\b|\bcbtp\b",
 "trauma": r"\btrauma\w*\b|\badvers\w*\b|\babuse\b",
 "recovery": r"\brecover\w*\b|\bempower\w*\b|\bwellbeing\b",
 "experience_language": r"\bphenomenolog\w*\b|\bexperience\w*\b|\blived experience\b",
 "neuro_language": r"\bbrain\b|\bneural\b|\bneuro\w*\b|\bcortex\b|\bimaging\b|\bconnectiv\w*\b",
 "social_context": r"\bsocial\b|\bstigma\b|\bdiscriminat\w*\b|\bmarginali[sz]\w*\b",
 "medication": r"\bantipsychotic\w*\b|\bmedication\w*\b|\bpharmacolog\w*\b",
}
PERIODS = (("2009-2015",2009,2015),("2016-2020",2016,2020),("2021-2026",2021,2026))
TEXT_FIELDS = ("title", "abstract")
def write_csv(path, fields, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        w=csv.writer(f);w.writerow(fields);w.writerows(rows)
def main():
    p=argparse.ArgumentParser();p.add_argument("--input",required=True);p.add_argument("--output-dir",required=True)
    a=p.parse_args();inp=Path(a.input);out=Path(a.output_dir)
    if out.exists() and any(out.iterdir()):raise SystemExit("Output exists and is nonempty; use a fresh versioned directory.")
    out.mkdir(parents=True,exist_ok=True)
    with inp.open(encoding="utf-8-sig",newline="") as f: all_rows=list(csv.DictReader(f))
    rows=[r for r in all_rows if r.get("publication_type")=="article" and r.get("qa_layer") in ("A","B","C")]
    ids=[r.get("openalex_id") or r.get("article_id") for r in rows]
    if len(ids)!=len(set(ids)):raise ValueError("Duplicate article IDs in selected cohort.")
    pat={k:re.compile(v,re.I) for k,v in PATTERNS.items()}
    hits={}
    for r in rows:
        uid=r.get("openalex_id") or r["article_id"]
        text=unicodedata.normalize("NFKC",(r.get("title") or "")+" "+(r.get("abstract") or ""))
        hits[uid]={k for k,rx in pat.items() if rx.search(text)}
    docfreq=Counter(k for found in hits.values() for k in found)
    write_csv(out/"lexical_signals_overall.csv",("signal","n_articles","pct_articles"),
      [(k,docfreq[k],round(100*docfreq[k]/len(rows),2) if rows else 0) for k in PATTERNS])
    layer_rows=[]
    for layer in "ABC":
        subset=[r for r in rows if r["qa_layer"]==layer];n=len(subset)
        for k in PATTERNS:
            found=sum(k in hits[r.get("openalex_id") or r["article_id"]] for r in subset)
            layer_rows.append((layer,n,k,found,round(100*found/n,2) if n else 0))
    write_csv(out/"lexical_signals_by_layer.csv",("layer","n_layer","signal","n_articles","pct_within_layer"),layer_rows)
    period_rows=[];period_summary=[]
    for label,lo,hi in PERIODS:
        subset=[r for r in rows if r.get("year","").isdigit() and lo<=int(r["year"])<=hi];n=len(subset)
        period_summary.append((label,n,*[sum(r["qa_layer"]==l for r in subset) for l in "ABC"]))
        for k in PATTERNS:
            found=sum(k in hits[r.get("openalex_id") or r["article_id"]] for r in subset)
            period_rows.append((label,n,k,found,round(100*found/n,2) if n else 0))
    write_csv(out/"lexical_signals_by_period.csv",("period","n_period","signal","n_articles","pct_within_period"),period_rows)
    write_csv(out/"period_layer_denominators.csv",("period","n_articles","A","B","C"),period_summary)
    edges=Counter()
    for found in hits.values():
        for pair in combinations(sorted(found),2):edges[pair]+=1
    write_csv(out/"lexical_copresence_edges.csv",("signal_a","signal_b","n_articles"),
      [(a,b,n) for (a,b),n in sorted(edges.items(),key=lambda v:(-v[1],v[0])) if n>=3])
    with inp.open("rb") as f:source_hash=hashlib.sha256(f.read()).hexdigest()
    summary={"schema":"avatar_discourse_D01_v01","source_file":str(inp),"source_sha256":source_hash,
      "input_rows":len(all_rows),"article_only_ABC":len(rows),"no_abstract":sum(not (r.get("abstract") or "").strip() for r in rows),
      "counts_by_layer":dict(Counter(r["qa_layer"] for r in rows)),
      "periods":[{"period":p,"n":n,"A":a,"B":b,"C":c} for p,n,a,b,c in period_summary],
      "signals":dict(docfreq),"method":"Regex presence within title + available abstract; document frequency; overlap allowed.",
      "limitations":"Exploratory lexical flags, not validated semantic concepts. Query-capped and user-selected corpus; unequal abstract availability and layer sizes; no causal or full-field inference.",
      "created_utc":dt.datetime.now(dt.timezone.utc).isoformat()}
    (out/"analysis_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (out/"signal_dictionary.json").write_text(json.dumps(PATTERNS,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (out/"transformation_log.json").write_text(json.dumps({"source_sha256":source_hash,"steps":["type-filter article and existing A/B/C","NFKC normalization in memory","regex lexical signal presence","period counts","article co-presence"],"excluded_records_preserved_upstream":True,"raw_unchanged":True},indent=2)+"\n",encoding="utf-8")
    (out/"METHODS.md").write_text("# D01 exploratory lexical signals\n\nTitle-and-abstract document frequency in article-labelled A/B/C cohort. Signals are overlapping and based on regex, not expert-validated semantic merges; missing abstracts contribute title-only. Period percentages use all selected articles in each period. Co-presence is within one publication, not semantic/causal linkage. No complete literature coverage is claimed. Subsequent stages must perform technical term extraction, conservative semantic normalization and expert review before final discourse interpretation.\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
