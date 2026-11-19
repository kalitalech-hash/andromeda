#!/usr/bin/env python3
"""D02: candidate phrases and explicitly *provisional* conservative semantic map.
No abstract redistribution; human review needed before downstream "final" analysis.
Run from data_avatar_therapy_voices_starter:
python scripts/05_semantic_candidates_D02.py --input outputs/qa/avatar01_full_strict_v05/analysis_corpus_ABC.csv --output-dir outputs/analyses/avatar_discourse_D02_v01
"""
import argparse,csv,json,hashlib,re,unicodedata
from pathlib import Path
from collections import Counter
from itertools import combinations

# Narrow phrases only; each variant separately audited. This is NOT a final thematic ontology.
CONCEPTS=[
("VOICE_AUDITORY_HALLUCINATIONS","auditory hallucinations","omamy słuchowe",["auditory verbal hallucinations","auditory hallucinations","verbal hallucinations"]),
("VOICE_HEARING","voice hearing","słyszenie głosów",["voice hearing","voice-hearing","hearing voices","voice hearers","voice-hearers"]),
("VOICE_DISTRESS","voice-related distress","dystres związany z głosami",["voice related distress","voice-related distress","distressing voices","distressing auditory hallucinations"]),
("VOICE_RELATING","relating to voices","relacja z głosami",["relating to voices","relating with voices","relationship with voices","relationship to voices","relating therapy"]),
("VOICE_DIALOGUE","dialogue with voices","dialog z głosami",["dialogue with voices","dialogues with voices","dialoguing with voices","voice dialogue","voice-dialogue"]),
("AVATAR_THERAPY","avatar therapy","terapia AVATAR",["avatar therapy","avatar-based therapy","avatar-assisted therapy","avatar assisted therapy","avatar-therapist"]),
("VR_INTERVENTION","virtual reality intervention","interwencja VR",["virtual reality therapy","virtual reality intervention","virtual reality-based therapy","virtual reality-assisted therapy","virtual reality exposure"]),
("VOICE_POWER","voice power/control","władza i kontrola głosów",["voice power","voice dominance","power of voices","dominance of voices","voice control","control over voices"]),
("VOICE_APPRAISALS","appraisals of voices","oceny poznawcze głosów",["appraisals of voices","voice appraisals","appraisal of voices"]),
("INNER_SPEECH","inner speech","mowa wewnętrzna",["inner speech","internal speech"]),
("LIVED_EXPERIENCE","lived experience","doświadczenie przeżywane",["lived experience","lived experiences"]),
("PHENOMENOLOGICAL_METHOD","phenomenological method","metoda fenomenologiczna",["phenomenological analysis","phenomenological approach","interpretative phenomenological"]),
("QUALITATIVE_METHOD","qualitative methodology","metodologia jakościowa",["qualitative study","qualitative research","qualitative analysis","thematic analysis","grounded theory"]),
("CONTROLLED_TRIAL","controlled trial","badanie kontrolowane",["randomized controlled trial","randomised controlled trial","controlled trial","randomised trial","randomized trial"]),
("TRAUMA_EXPOSURE","trauma exposure","doświadczenia traumatyczne",["traumatic experiences","traumatic events","childhood trauma","psychological trauma","trauma history","trauma exposure"]),
("PEER_SUPPORT","peer support","wsparcie rówieśnicze",["peer support","peer-led support"]),
("CBT","cognitive behavioral therapy","terapia poznawczo-behawioralna",["cognitive behavioural therapy","cognitive behavioral therapy","cbt for psychosis","cbtp"]),
("ANTIPSYCHOTICS","antipsychotic medication","leki przeciwpsychotyczne",["antipsychotic medication","antipsychotic treatment","antipsychotics"]),
("SOCIAL_RELATIONSHIPS","social relationships","relacje społeczne",["social relationships","social functioning","social support","social isolation"]),
("VOICE_IDENTITY","voice identity","tożsamość głosów",["voice identity","identity of voices","personification of voices"]),
("VOICE_AGENCY","sense of agency","poczucie sprawczości",["sense of agency","personal agency"]),
("RECOVERY","personal recovery","zdrowienie",["personal recovery","recovery oriented","recovery-oriented","recovery journey"]),
("COMMAND_VOICES","command hallucinations","głosy nakazujące",["command hallucinations","command voices","command auditory hallucinations"]),
]
STOP=set("""the and for with from this that those these where which under over between during after before without into about their they them when while were was are our has have had being been using based results findings participants patient patients study studies analysis methods aim aims objective objectives clinical research article paper therapy voices voice hearing auditory hallucinations hallucination schizophrenia psychosis psychotic an of in to a or by on is it as be we do did can may not but than other more most such at both all including related associated""".split())
PERIODS=[("2009-2015",2009,2015),("2016-2020",2016,2020),("2021-2026",2021,2026)]
def norm(s):return re.sub(r"\s+"," ",unicodedata.normalize("NFKC",s or "").lower().translate(str.maketrans({"‐":"-","‑":"-","‒":"-","–":"-","—":"-"})))
def hit(text,phrase):
    return bool(re.search(r"(?<![a-z])"+re.escape(norm(phrase)).replace(r"\ ","\\s+")+r"(?![a-z])",text))
def write(path,header,rows):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f);w.writerow(header);w.writerows(rows)
def main():
    ap=argparse.ArgumentParser();ap.add_argument("--input",required=True);ap.add_argument("--output-dir",required=True);a=ap.parse_args()
    dest=Path(a.output_dir)
    if dest.exists() and any(dest.iterdir()):raise SystemExit("Nonempty output dir: use new version.")
    dest.mkdir(parents=True,exist_ok=True)
    raw=Path(a.input).read_bytes()
    with Path(a.input).open(encoding="utf-8-sig",newline="") as f:records=list(csv.DictReader(f))
    rows=[r for r in records if r.get("publication_type")=="article" and r.get("qa_layer") in {"A","B","C"}]
    assert len(rows)==209, "Expected frozen article-only A/B/C cohort (209); audit if changed."
    keys=[r.get("openalex_id") or r.get("article_id") for r in rows]
    assert len(set(keys))==len(rows)
    freq=Counter()
    matches=[]
    for row in rows:
        text=norm((row.get("title") or "")+" "+(row.get("abstract") or ""))
        for cid,en,pl,variants in CONCEPTS:
            vv=[v for v in variants if hit(text,v)]
            if vv:
                matches.append([row.get("openalex_id") or row.get("article_id"),row["qa_layer"],row["year"],cid,"|".join(vv)])
                freq[cid]+=1
    write(dest/"candidate_article_concepts.csv",["article_id","qa_layer","year","concept_id","matched_variants"],matches)
    overview=[];dictionary=[];audit=[]
    for cid,en,pl,variants in CONCEPTS:
        overview.append([cid,en,pl,freq[cid],round(100*freq[cid]/len(rows),2)])
        for v in variants:
            n=sum(hit(norm((r.get("title") or "")+" "+(r.get("abstract") or "")),v) for r in rows)
            dictionary.append([v,cid,en,pl,"merge_candidate","pending_human_review",n])
            audit.append([v,cid,n,"review","", "A phrase match is not contextual validation; approve or reject merge"])
    write(dest/"semantic_map_provisional.csv",["candidate_term","concept_id","concept_label_en","concept_label_pl","semantic_action","audit_decision","n_documents"],dictionary)
    write(dest/"semantic_audit_queue.csv",["candidate_term","suggested_concept_id","n_documents","audit_decision","reviewer","notes"],audit)
    write(dest/"candidate_concept_counts.csv",["concept_id","concept_label_en","concept_label_pl","n_documents","pct_documents"],overview)
    # Candidate n-grams: document presence in title+abstract; small, auditable vocabulary.
    grams=Counter()
    for r in rows:
        t=re.findall(r"[a-z][a-z'-]{2,}",norm((r.get("title") or "")+" "+(r.get("abstract") or "")))
        unique=set()
        for n in (1,2,3):
            for i in range(len(t)-n+1):
                ws=t[i:i+n]
                if any(w in STOP for w in ws):continue
                unique.add(" ".join(ws))
        grams.update(unique)
    candidates=sorted(((k,v) for k,v in grams.items() if v>=3),key=lambda kv:(-kv[1],kv[0]))[:200]
    write(dest/"candidate_ngrams_top200.csv",["candidate_ngram","n_documents","review_status"],[(t,n,"unmapped_review") for t,n in candidates])
    by_period=[];by_layer=[]
    for label,lo,hi in PERIODS:
        subset=[r for r in rows if r.get("year","").isdigit() and lo<=int(r["year"])<=hi]
        idx={r.get("openalex_id") or r.get("article_id") for r in subset}
        for cid,en,pl,variants in CONCEPTS:
            n=sum(m[0] in idx and m[3]==cid for m in matches)
            by_period.append([label,len(subset),cid,n,round(100*n/len(subset),2) if subset else 0])
    for layer in "ABC":
        sub=[r for r in rows if r["qa_layer"]==layer];idx={r.get("openalex_id") or r.get("article_id") for r in sub}
        for cid,en,pl,variants in CONCEPTS:
            n=sum(m[0] in idx and m[3]==cid for m in matches)
            by_layer.append([layer,len(sub),cid,n,round(100*n/len(sub),2)])
    write(dest/"candidate_concept_by_period.csv",["period","n_period","concept_id","n_documents","pct_within_period"],by_period)
    write(dest/"candidate_concept_by_layer.csv",["layer","n_layer","concept_id","n_documents","pct_within_layer"],by_layer)
    sha=hashlib.sha256(raw).hexdigest()
    summary={"schema":"D02_v01_provisional","source_sha256":sha,"n_articles":len(rows),"missing_abstract":sum(not r.get("abstract","").strip() for r in rows),"n_candidate_concepts":len(CONCEPTS),"n_variant_rules":sum(len(x[3]) for x in CONCEPTS),"concept_assignments":len(matches),"approval_status":"NOT_APPROVED","method":"exact multiword phrase matches + candidate 1-3 grams, title and available abstract; no unreviewed normalization promoted to final"}
    (dest/"qa_summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    (dest/"transformation_log.json").write_text(json.dumps({"input_sha256":sha,"stages":["type filter and ID check","NFKC lowercase punctuation normalization for matching","strict phrase detection","document frequency","unmapped n-grams","pending HITL audit"],"raw_unmodified":True},indent=2)+"\n",encoding="utf-8")
    (dest/"METHODS.md").write_text("# D02 — provisional semantic candidate mapping\n\nN=209 article-labelled A/B/C records. The dictionary contains only narrow, interpretable multiword phrases, merged **provisionally**. No concept or merge is expert-approved; all have `pending_human_review` and the separate audit queue. N-grams are statistical candidate expressions only and must not be interpreted as validated topics. Titles and accessible abstracts are analyzed; records without abstracts contribute titles only. Terms are binary per document, variants are de-duplicated within concepts, and concepts overlap. Terms and counts are not a systematic-search prevalence estimate. No raw abstracts copied to outputs. D03 must resolve audit decisions before `terms_semantic_final.csv` can be used in final semantic analysis.\n",encoding="utf-8")
    print(json.dumps(summary,indent=2))
if __name__=="__main__":main()
