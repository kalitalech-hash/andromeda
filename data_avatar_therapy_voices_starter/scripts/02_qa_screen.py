#!/usr/bin/env python3
"""Non-destructive deduplication and triage; never auto-include on lexical matches."""
import argparse,csv,datetime as dt,json,re,unicodedata
from collections import Counter,defaultdict
from pathlib import Path

PATTERNS={
 "A_avatar":r"\b(?:avatar(?:-based)?|virtual reality|VR|dialogue with (?:a |the )?voice)\b",
 "B_voices":r"\b(?:auditory (?:verbal )?hallucinations?|hearing voices|voice[- ]hearing|distressing voices|relating to voices|voice[- ]related distress)\b",
 "C_psychosis":r"\b(?:psychosis|psychotic|schizophreni\w*)\b",
 "D_relational":r"\b(?:power|agency|dominance|assertiveness|dialogue|relational|recovery|personification)\b"
}

def norm(s):return " ".join(unicodedata.normalize("NFKC",s or "").casefold().split())
def doi_key(s):
    s=norm(s);return re.sub(r"^(https?://(?:dx\.)?doi\.org/|doi:\s*)","",s).strip()
def slug(s):return re.sub(r"\W+"," ",norm(s)).strip()
def read_csv(p):
    with Path(p).open(encoding="utf-8-sig",newline="") as f:return list(csv.DictReader(f))
def write_csv(path,rows,fields):
    with path.open("w",encoding="utf-8",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader();w.writerows(rows)
def main():
    p=argparse.ArgumentParser();p.add_argument("--input",required=True);p.add_argument("--output-dir",default="outputs/qa");a=p.parse_args()
    out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=True)
    rows=read_csv(a.input); accepted=[]; duplicates=[]; missing=[];seen={}
    for idx,row in enumerate(rows,1):
        key=doi_key(row.get("doi",""))
        if key:key="doi:"+key
        elif row.get("openalex_id") or row.get("article_id"):key="id:"+norm(row.get("openalex_id") or row.get("article_id"))
        else:key=f"title_year:{slug(row.get('title',''))}:{row.get('year','')}"
        if key in seen:
            duplicates.append({"row_number":idx,"duplicate_key":key,"retained_row_number":seen[key],"matched_search_query":row.get("matched_search_query", "")});continue
        seen[key]=idx
        text=norm(" ".join([row.get("title", ""),row.get("abstract", "")]))
        flags={k:bool(re.search(pat,text,re.I)) for k,pat in PATTERNS.items()}
        row=dict(row)
        row.update({f"flag_{k}":int(v) for k,v in flags.items()})
        row["review_priority"]="high" if flags["A_avatar"] and flags["B_voices"] else "medium" if flags["B_voices"] or (flags["A_avatar"] and flags["C_psychosis"]) else "low"
        row["human_include"]="";row["human_layer"]="";row["human_exclusion_reason"]="";row["human_notes"]=""
        row["abstract_missing"]=int(not bool(row.get("abstract","").strip()))
        row["title_missing"]=int(not bool(row.get("title","").strip()))
        row["year_missing"]=int(not bool(str(row.get("year", "")).strip()))
        if row["title_missing"] or row["year_missing"]:missing.append({"row_number":idx,"article_id":row.get("article_id",""),"missing_title":row["title_missing"],"missing_year":row["year_missing"]})
        accepted.append(row)
    fields=list(accepted[0]) if accepted else list(rows[0])+[f"flag_{k}" for k in PATTERNS]+["review_priority","human_include","human_layer","human_exclusion_reason","human_notes","abstract_missing","title_missing","year_missing"] if rows else ["article_id","title","year","review_priority","human_include","human_layer"]
    write_csv(out/"records_deduplicated_for_review.csv",accepted,fields)
    write_csv(out/"duplicate_search_hits.csv",duplicates,["row_number","duplicate_key","retained_row_number","matched_search_query"])
    write_csv(out/"missing_metadata.csv",missing,["row_number","article_id","missing_title","missing_year"])
    counts=Counter(r["review_priority"] for r in accepted)
    per_journal=Counter(r.get("journal","") for r in accepted)
    summary={"input_rows":len(rows),"unique_candidates":len(accepted),"duplicate_search_hits":len(duplicates),"missing_abstract":sum(r["abstract_missing"] for r in accepted),"missing_title":sum(r["title_missing"] for r in accepted),"missing_year":sum(r["year_missing"] for r in accepted),"priority_counts":dict(counts),"journal_counts":dict(per_journal),"manual_review_complete":False,"method":"Lexical flags are review priorities, not inclusion decisions. Records are only candidate publications; all manual decisions pending."}
    (out/"qa_summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
    (out/"transformation_log.json").write_text(json.dumps({"timestamp_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"input":a.input,"transformations":["DOI normalization (for deduplication keys only)","Fallback OpenAlex ID, then title-year keys","retain first duplicate candidate","non-exclusionary lexical triage","blank expert review fields"],"raw_input_unchanged":True},indent=2),encoding="utf-8")
    (out/"methodological_note.md").write_text("# Stage 02 — QA and screening\n\nInput is OpenAlex journal-scoped search candidates, not a systematic literature corpus. Duplicates across search queries are resolved by normalized DOI then OpenAlex ID then normalized title/year. Lexical flags assign **review priority only**; they cannot establish thematic relevance or study design. Abstract missingness and source heterogeneity are recorded. Human screening must decide A (avatar/voice dialogue), B (psychological approaches to voices), C (other VR-psychosis context), exclude, or unresolved. Check primary study vs protocol/review and multiple reports of the same trial before quantitative analyses. No PDFs or full text were acquired.\n",encoding="utf-8")
    print(json.dumps(summary,ensure_ascii=False,indent=2))
if __name__=="__main__":main()
