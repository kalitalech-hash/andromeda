#!/usr/bin/env python3
from __future__ import annotations
import json, re, datetime as dt
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd

FAMILIES = [
"drive_conflict_defense","dream_fantasy_unconscious","ego_self_narcissism","object_relations",
"kleinian_bionian","winnicottian_environment_holding","attachment_development_infant",
"transference_countertransference","technique_interpretation_process","relational_intersubjective_field",
"trauma_dissociation_affect_regulation","psychosis_borderline_primitive_states","body_sexuality_gender",
"language_narrative_symbolization","culture_race_social_ethics","empirical_research_measurement",
"history_theory_schools"]
PERIOD_ORDER={"1920-1945":1,"1946-1969":2,"1970-1989":3,"1990-2009":4,"2010-2025":5}
JOURNAL_ORDER={"ijpa":1,"japa":2,"psychoanalytic_dialogues":3,"psychoanalytic_psychology":4,"psychoanalytic_psychotherapy":5}
INDICES={
"classical_drive_conflict_index":(["drive_conflict_defense"],[]),
"classical_metapsychology_index":(["drive_conflict_defense","dream_fantasy_unconscious","transference_countertransference","technique_interpretation_process"],[]),
"relational_shift_index":(["relational_intersubjective_field"],["drive_conflict_defense"]),
"contemporary_contextualization_index":(["relational_intersubjective_field","culture_race_social_ethics","trauma_dissociation_affect_regulation"],[]),
"narrative_reframing_index":(["relational_intersubjective_field","language_narrative_symbolization","culture_race_social_ethics"],["drive_conflict_defense"]),
"research_psychology_index":(["empirical_research_measurement"],[])
}
def now(): return dt.datetime.now(dt.timezone.utc).isoformat()
def paths():
    sd=Path(__file__).resolve().parent; pr=sd.parent; tr=pr/"data"/"title_abstract"
    return {"scripts":sd,"project":pr,"title":tr,"global":tr/"global","refined":tr/"semantic_refined","out":tr/"resubmit_pp"}
def read_csv(p:Path):
    if not p.exists() or p.stat().st_size==0: return pd.DataFrame()
    try: return pd.read_csv(p,dtype=str,keep_default_na=False,encoding="utf-8-sig")
    except UnicodeDecodeError: return pd.read_csv(p,dtype=str,keep_default_na=False,encoding="utf-8")
def write_csv(df,p): p.parent.mkdir(parents=True,exist_ok=True); df.to_csv(p,index=False,encoding="utf-8-sig")
def write_json(obj,p): p.parent.mkdir(parents=True,exist_ok=True); p.write_text(json.dumps(obj,ensure_ascii=False,indent=2),encoding="utf-8")
def nser(df,col):
    return pd.to_numeric(df[col],errors="coerce").fillna(0.0) if col in df.columns else pd.Series([0.0]*len(df),index=df.index)
def norm_period(s): return str(s or "").strip().replace("–","-").replace("—","-").replace(" ","")
def make_period(y):
    try: y=int(float(str(y).strip()))
    except Exception: return ""
    if 1920<=y<=1945: return "1920-1945"
    if 1946<=y<=1969: return "1946-1969"
    if 1970<=y<=1989: return "1970-1989"
    if 1990<=y<=2009: return "1990-2009"
    if 2010<=y<=2025: return "2010-2025"
    return ""
def sort_df(df):
    out=df.copy()
    if "period" in out.columns:
        out["period"]=out["period"].map(norm_period); out["_po"]=out["period"].map(PERIOD_ORDER).fillna(999).astype(int)
    if "journal_key" in out.columns:
        out["_jo"]=out["journal_key"].map(JOURNAL_ORDER).fillna(999).astype(int)
    cols=[c for c in ["scenario","_jo","_po","journal_key","period"] if c in out.columns]
    if cols: out=out.sort_values(cols)
    return out.drop(columns=[c for c in ["_po","_jo"] if c in out.columns])
def aggregate_family_period(jp, scenario, exclude=None, post1990=False):
    d=jp.copy()
    for c in ["journal_key","period","semantic_family","n_articles_refined","n_articles_group"]:
        if c not in d.columns: raise SystemExit(f"Missing column {c} in by-journal-period refined table")
    d["period"]=d["period"].map(norm_period)
    if exclude: d=d[~d["journal_key"].isin(exclude)].copy()
    if post1990: d=d[d["period"].isin(["1990-2009","2010-2025"])].copy()
    d["n_hits"]=nser(d,"n_articles_refined"); d["n_group"]=nser(d,"n_articles_group")
    g=d.groupby(["period","semantic_family"],as_index=False).agg(n_hits=("n_hits","sum"),n_articles=("n_group","sum"))
    g["pct"]=(100*g["n_hits"]/g["n_articles"].replace(0,pd.NA)).round(4)
    g["scenario"]=scenario
    return sort_df(g[["scenario","period","semantic_family","n_hits","n_articles","pct"]])
def pivot_indices(fam_period):
    if fam_period.empty: return pd.DataFrame()
    p=fam_period.pivot_table(index=["scenario","period"],columns="semantic_family",values="pct",aggfunc="first",fill_value=0).reset_index()
    p.columns.name=None
    for fam in FAMILIES:
        if fam not in p.columns: p[fam]=0.0
    den=fam_period.groupby(["scenario","period"],as_index=False).agg(n_articles=("n_articles","max"))
    p=p.merge(den,on=["scenario","period"],how="left")
    for idx,(pos,neg) in INDICES.items():
        val=pd.Series([0.0]*len(p),index=p.index)
        for f in pos: val=val+nser(p,f)
        for f in neg: val=val-nser(p,f)
        p[idx]=val.round(4)
    p["relational_to_drive_conflict_ratio"]=(nser(p,"relational_intersubjective_field")/nser(p,"drive_conflict_defense").replace(0,pd.NA)).round(4)
    p["contemporary_to_classical_ratio"]=(nser(p,"contemporary_contextualization_index")/nser(p,"classical_metapsychology_index").replace(0,pd.NA)).round(4)
    return sort_df(p)
def first_last(df):
    rows=[]
    for sc,g in df.groupby("scenario",dropna=False):
        g=sort_df(g)
        if g.empty: continue
        a,b=g.iloc[0],g.iloc[-1]
        row={"scenario":sc,"first_period":a.get("period",""),"last_period":b.get("period",""),"n_periods":int(g["period"].nunique())}
        for c in ["drive_conflict_defense","relational_intersubjective_field","culture_race_social_ethics","trauma_dissociation_affect_regulation","relational_shift_index","contemporary_contextualization_index","narrative_reframing_index"]:
            if c in g.columns:
                row[c+"_first"]=round(float(a.get(c,0) or 0),4); row[c+"_last"]=round(float(b.get(c,0) or 0),4); row[c+"_change"]=round(row[c+"_last"]-row[c+"_first"],4)
        rows.append(row)
    return pd.DataFrame(rows)
def lineplot(df,p,title,cols):
    import matplotlib.pyplot as plt
    if df.empty: return
    fig,ax=plt.subplots(figsize=(8,5))
    for sc,g in df.groupby("scenario"):
        g=sort_df(g); x=list(g["period"])
        for c in cols:
            if c in g.columns: ax.plot(x,pd.to_numeric(g[c],errors="coerce"),marker="o",label=f"{sc}: {c}")
    ax.set_title(title); ax.set_xlabel("Period"); ax.set_ylabel("Coverage / index")
    ax.tick_params(axis="x",rotation=35); ax.legend(fontsize=7); fig.tight_layout()
    p.parent.mkdir(parents=True,exist_ok=True); fig.savefig(p,dpi=300); plt.close(fig)
