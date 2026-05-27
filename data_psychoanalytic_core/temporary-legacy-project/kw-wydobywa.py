import csv
import json
import time
import re
from pathlib import Path
from xml.etree import ElementTree as ET

import requests

# --- ustawienia ---
IN_CSV = "pep_articles_from_search.csv"
OUT_WIDE = "pep_keywords_wide.csv"
OUT_LONG = "pep_keywords_long.csv"

BASE_URL = "https://api.pep-web.org/v2/Database/Search/"
BATCH_SIZE = 50         # ile art_id na jeden request (bezpiecznie)
SLEEP = 0.8             # przerwa między requestami
TIMEOUT = 60

# --- helpers ---
def load_secrets():
    return json.loads(Path("pep_secrets.json").read_text(encoding="utf-8"))

def build_headers(secrets: dict):
    h = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
    }
    h.update(secrets)
    return h

def safe_int(x):
    try:
        return int(x)
    except:
        return 0

def chunked(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

def extract_keywords_from_xml(xml_text: str):
    """
    Próbuje wydobyć keywords z XML-a w polach typu documentInfoXML / documentMetaXML.
    Szuka tagów zawierających 'kw' / 'key' w nazwie, a potem zbiera ich tekst.
    """
    if not xml_text or "<" not in xml_text:
        return []

    # Czasem XML ma HTML-owe encje; ElementTree sobie zwykle radzi, ale bywają śmieci
    # Spróbujmy najpierw jak jest:
    try:
        root = ET.fromstring(xml_text)
        kws = []
        for el in root.iter():
            tag = (el.tag or "").lower()
            if "kw" in tag or "keyword" in tag or "key" in tag:
                text = (el.text or "").strip()
                if text:
                    kws.append(text)
        return dedupe(kws)
    except Exception:
        pass

    # Fallback: regex po treści
    kws = re.findall(r">(.*?)<", xml_text)
    kws = [x.strip() for x in kws if x.strip()]
    # heurystyka: odfiltruj bardzo długie rzeczy (żeby nie łapać całych akapitów)
    kws = [x for x in kws if 1 <= len(x) <= 80]
    return dedupe(kws)

def dedupe(items):
    seen = set()
    out = []
    for x in items:
        key = x.strip().lower()
        if not key:
            continue
        if key not in seen:
            seen.add(key)
            out.append(x.strip())
    return out

def extract_keywords_from_doc(doc: dict):
    """
    Najpierw sprawdza pola JSON, potem parsuje XML z documentInfoXML/documentMetaXML.
    """
    kws = []

    # 1) Jeśli API jednak czasem daje listę keywords
    for k in ["keywords", "kwds", "art_kwds", "keywordList"]:
        v = doc.get(k)
        if isinstance(v, list):
            kws.extend([str(x).strip() for x in v if str(x).strip()])
        elif isinstance(v, str) and v.strip():
            # czasem bywa "a; b; c"
            if ";" in v:
                kws.extend([x.strip() for x in v.split(";") if x.strip()])
            else:
                kws.append(v.strip())

    kws = dedupe(kws)
    if kws:
        return kws

    # 2) XML ukryty w polach
    for xml_field in ["documentInfoXML", "documentMetaXML", "documentRefXML"]:
        xml_text = doc.get(xml_field, "")
        kws2 = extract_keywords_from_xml(xml_text)
        if kws2:
            return kws2

    return []

def main():
    secrets = load_secrets()
    headers = build_headers(secrets)

    # 1) wczytaj listę docID z CSV (tylko te z kwds_count > 0)
    ids = []
    meta = {}  # docid -> (year, pepcode, title)
    with open(IN_CSV, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            docid = (row.get("documentID") or "").strip()
            kwc = safe_int(row.get("art_kwds_count"))
            if docid and kwc > 0:
                ids.append(docid)
                meta[docid] = {
                    "year": row.get("year", ""),
                    "PEPCode": row.get("PEPCode", ""),
                    "title": row.get("title", ""),
                    "sourceTitle": row.get("sourceTitle", ""),
                }

    if not ids:
        raise SystemExit("Nie znalazłam żadnych rekordów z art_kwds_count > 0 w pep_articles_from_search.csv")

    print(f"[INFO] docIDs z kwds_count>0: {len(ids)}")

    wide_rows = []
    long_rows = []

    session = requests.Session()
    session.headers.update(headers)

    # 2) dociągaj paczkami przez facetquery=art_id:(A OR B OR C)
    for bi, batch in enumerate(chunked(ids, BATCH_SIZE), start=1):
        facet = "art_id:(" + " OR ".join(batch) + ")"
        params = {
            "facetquery": facet,
            "formatrequested": "JSON",
            "synonyms": "false",
            "abstract": "false",
            "limit": str(len(batch)),
            "offset": "0",
        }

        r = session.get(BASE_URL, params=params, timeout=TIMEOUT)
        if r.status_code != 200:
            print("[ERROR]", r.status_code, r.text[:500])
            break

        data = r.json()
        docs = data.get("documentList", {}).get("responseSet", [])
        print(f"[OK] batch {bi} -> docs: {len(docs)}")

        for d in docs:
            docid = (d.get("documentID") or "").strip()
            kws = extract_keywords_from_doc(d)

            m = meta.get(docid, {})
            wide_rows.append({
                "documentID": docid,
                "PEPCode": d.get("PEPCode", m.get("PEPCode","")),
                "year": d.get("year", m.get("year","")),
                "title": d.get("title", m.get("title","")),
                "sourceTitle": d.get("sourceTitle", m.get("sourceTitle","")),
                "keywords": "; ".join(kws),
                "kw_count_extracted": len(kws),
            })

            for kw in kws:
                long_rows.append({
                    "documentID": docid,
                    "PEPCode": d.get("PEPCode", m.get("PEPCode","")),
                    "year": d.get("year", m.get("year","")),
                    "keyword_raw": kw,
                })

        time.sleep(SLEEP)

    # 3) zapisz wyniki
    with open(OUT_WIDE, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(wide_rows[0].keys()) if wide_rows else [])
        if wide_rows:
            w.writeheader()
            w.writerows(wide_rows)

    with open(OUT_LONG, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(long_rows[0].keys()) if long_rows else [])
        if long_rows:
            w.writeheader()
            w.writerows(long_rows)

    print("[DONE] Wrote:")
    print(" -", OUT_WIDE, f"(rows={len(wide_rows)})")
    print(" -", OUT_LONG, f"(rows={len(long_rows)})")

if __name__ == "__main__":
    main()