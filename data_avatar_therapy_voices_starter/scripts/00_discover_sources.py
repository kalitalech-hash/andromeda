#!/usr/bin/env python3
"""Propose OpenAlex source IDs. Never silently approve fuzzy source matches."""
import argparse, csv, json, os, time
from pathlib import Path
from urllib.parse import urlparse
import requests

API = "https://api.openalex.org"

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--config", default="config/corpus.json")
    p.add_argument("--output", default="outputs/source_candidates.csv")
    p.add_argument("--contact-email", default=os.getenv("ANDROMEDA_CONTACT_EMAIL"))
    args=p.parse_args()
    if not args.contact_email or "@" not in args.contact_email:
        p.error("Provide a genuine contact via --contact-email or ANDROMEDA_CONTACT_EMAIL")
    cfg=json.loads(Path(args.config).read_text(encoding="utf-8"))
    out=Path(args.output);out.parent.mkdir(parents=True,exist_ok=True)
    rows=[]
    session=requests.Session()
    session.headers.update({"User-Agent": f"AndromedaNowickaBibliometricBot/0.5 (metadata-only bibliometric research; contact: {args.contact_email}; no PDF mirroring; polite delay)","From":args.contact_email})
    for j in cfg["journals"]:
        url=API+"/sources"
        res=session.get(url,params={"search":j["name"],"per-page":5,"mailto":args.contact_email},timeout=40)
        res.raise_for_status()
        for item in res.json().get("results",[]):
            rows.append({"requested_journal":j["name"],"candidate_name":item.get("display_name",""),"openalex_source_id":item.get("id",""),"issn_l":item.get("issn_l",""),"issn":";".join(item.get("issn") or []),"works_count":item.get("works_count",0),"exact_name_match":str(j["name"].casefold()==item.get("display_name","").casefold()),"approved_by_researcher":""})
        time.sleep(3)
    with out.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]) if rows else ["requested_journal","candidate_name","openalex_source_id","approved_by_researcher"]);w.writeheader();w.writerows(rows)
    print(f"Saved {len(rows)} candidate rows to {out}. Review ISSNs and fill source IDs in config manually; then set source_ids_confirmed=true.")

if __name__=="__main__": main()
