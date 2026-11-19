#!/usr/bin/env python3
"""D04 focused AVATAR/VR ego maps, exact approved D03 concepts + broad mention sensitivity.
Uses metadata only. Run from data_avatar_therapy_voices_starter:
python scripts/07_focused_avatar_vr_D04.py --corpus outputs/qa/avatar01_full_strict_v05/analysis_corpus_ABC.csv --terms outputs/analyses/avatar_discourse_D03_v01/terms_semantic_final.csv --out-dir outputs/analyses/avatar_discourse_D04_reproduced_v01
"""
import argparse,csv,hashlib,json,re,unicodedata
from pathlib import Path
from collections import Counter
from itertools import combinations

RX={
 "AVATAR_MENTION":r"\bavatars?\b",
 "VR_MENTION":r"\bvirtual reality\b|\bimmersive\b|\bVR[- ](?:based|assisted|therapy|intervention|exposure)\b|\bVR\b",
 "ANXIETY":r"\banxiet\w*\b|\banxious\b|\bworr\w*\b",
 "FEAR":r"\bfear\w*\b|\bafraid\b|\bfrighten\w*\b",
 "DISCOMFORT":r"\bdiscomfort\b|\buncomfortab\w*\b",
 "DISTRESS":r"\bdistress\w*\b",
}
ANCHORS=("AVATAR_THERAPY","VR_INTERVENTION")
def csvread(p):
    with Path(p).open(encoding="utf-8-sig",newline="") as fh:return list(csv.DictReader(fh))
def csvwrite(p,heads,rows):
    with p.open("w",encoding="utf-8",newline="") as fh:
        w=csv.writer(fh);w.writerow(heads);w.writerows(rows)
def main():
    pa=argparse.ArgumentParser()
    pa.add_argument("--corpus",required=True);pa.add_argument("--terms",required=True);pa.add_argument("--out-dir",required=True)
    a=pa.parse_args();out=Path(a.out_dir)
    if out.exists() and any(out.iterdir()):pa.error("Choose a fresh empty versioned folder")
    records=[r for r in csvread(a.corpus) if r.get("publication_type")=="article" and r.get("qa_layer") in {"A","B","C"}]
    terms=csvread(a.terms);byid={r.get("openalex_id") or r["article_id"]:set() for r in records}
    if len(byid)!=len(records):raise ValueError("Duplicate corpus identifiers")
    for x in terms:
        if x["article_id"] not in byid:raise ValueError("Unrecognized article ID")
        byid[x["article_id"]].add(x["concept_id"])
    if len(records)!=209:raise ValueError("Input differs from frozen D03 corpus")
    out.mkdir(parents=True)
    strict_counts=Counter();strict_edges=Counter()
    for ids in byid.values():
        for anchor in ANCHORS:
            if anchor in ids:
                strict_counts[anchor]+=1
                for cid in ids-{anchor}:strict_edges[(anchor,cid)]+=1
    broad_cohorts={k:[] for k in RX}
    for r in records:
        text=unicodedata.normalize("NFKC",r["title"]+" "+r.get("abstract",""))
        for k,regex in RX.items():
            if re.search(regex,text,re.I):broad_cohorts[k].append(r)
    broad_edges=Counter()
    for k in ("AVATAR_MENTION","VR_MENTION"):
        for r in broad_cohorts[k]:
            aid=r.get("openalex_id") or r["article_id"]
            skip="AVATAR_THERAPY" if k=="AVATAR_MENTION" else "VR_INTERVENTION"
            for cid in byid[aid]-{skip}:broad_edges[(k,cid)]+=1
    csvwrite(out/"strict_ego_edges.csv",["anchor","co_present_concept","n_articles"],[(a,c,n) for (a,c),n in sorted(strict_edges.items(),key=lambda x:(x[0][0],-x[1],x[0][1]))])
    csvwrite(out/"broader_mention_edges.csv",["anchor","co_present_approved_concept","n_articles"],[(a,c,n) for (a,c),n in sorted(broad_edges.items(),key=lambda x:(x[0][0],-x[1],x[0][1]))])
    audit=[]
    for r in records:
        aid=r.get("openalex_id") or r["article_id"]
        anchors=sorted(set(ANCHORS)&byid[aid])
        if not anchors:continue
        audit.append([aid,r["year"],r["journal"],r["qa_layer"],r["title"],"|".join(anchors),"|".join(sorted(byid[aid]-set(ANCHORS)))])
    csvwrite(out/"anchor_strict_records.csv",["article_id","year","journal","qa_layer","title","strict_anchor","other_approved_concepts"],audit)
    both=sum(re.search(RX["VR_MENTION"],(r["title"]+" "+r.get("abstract","")),re.I)!=None for r in broad_cohorts["AVATAR_MENTION"])
    anxiety_or_fear=sum(any(re.search(RX[k],r["title"]+" "+r.get("abstract",""),re.I) for k in ("ANXIETY","FEAR")) for r in records)
    d_a_f=sum(any(re.search(RX[k],r["title"]+" "+r.get("abstract",""),re.I) for k in ("DISTRESS","ANXIETY","FEAR")) for r in records)
    summary={"schema_version":"D04_anchor_maps_v01","input_sha256":{"corpus":hashlib.sha256(Path(a.corpus).read_bytes()).hexdigest(),"terms":hashlib.sha256(Path(a.terms).read_bytes()).hexdigest()},"n_articles":len(records),"strict_anchors":dict(strict_counts),"broad_mentions":{k:len(v) for k,v in broad_cohorts.items()},"broad_avatar_and_vr_overlap":both,"anxiety_or_fear":anxiety_or_fear,"distress_or_anxiety_or_fear":d_a_f,"method":"binary per-article co-presence: strict approved concepts and broader standalone mentions","limitation":"Page-capped acquisition; phrase matches do not independently validate intervention target or study design"}
    (out/"anchor_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (out/"METHODS.md").write_text("# D04 focused AVATAR/VR map\n\nTwo noninterchangeable analyses: strict researcher-approved D03 concepts versus broad regex mentions in titles and available abstracts. All edges including n=1 kept. Denominators are anchor-specific. VR mention is not necessarily VR treatment for voices. `CONTROLLED_TRIAL` and `QUALITATIVE_METHOD` are textual method mentions, not study-type adjudication.\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
