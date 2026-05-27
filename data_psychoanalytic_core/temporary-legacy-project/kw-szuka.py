import json
import time
from pathlib import Path
from urllib.parse import urlencode

import requests

TIMEOUT = 60
SLEEP = 0.6

def load_secrets():
    return json.loads(Path("pep_secrets.json").read_text(encoding="utf-8"))

def build_headers(secrets):
    h = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
    }
    h.update(secrets)
    return h

def pick_some_ids(csv_path="pep_articles_from_search.csv", n=5):
    import csv
    ids = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            docid = row.get("documentID")
            kwc = row.get("art_kwds_count")
            # wybierz te, które mają keywords w indeksie
            try:
                kwc_i = int(kwc) if kwc not in ("", None) else 0
            except:
                kwc_i = 0
            if docid and kwc_i > 0:
                ids.append(docid)
            if len(ids) >= n:
                break
    return ids

def try_url(session, url):
    r = session.get(url, timeout=TIMEOUT)
    return r.status_code, r.headers.get("content-type",""), r.text[:500]

def main():
    secrets = load_secrets()
    headers = build_headers(secrets)
    s = requests.Session()
    s.headers.update(headers)

    ids = pick_some_ids()
    if not ids:
        raise SystemExit("Nie znalazłam w CSV rekordów z art_kwds_count > 0. Wybierz próbkę ręcznie.")

    docid = ids[0]
    print("[TEST docid]", docid)

    # Kandydaci: typowe wzorce API
    candidates = [
        # (opis, url)
        ("DocumentInfo", f"https://api.pep-web.org/v2/Database/DocumentInfo/?id={docid}&formatrequested=JSON"),
        ("Document",     f"https://api.pep-web.org/v2/Database/Document/?id={docid}&formatrequested=JSON"),
        ("DocMeta",      f"https://api.pep-web.org/v2/Database/DocumentMeta/?id={docid}&formatrequested=JSON"),
        ("Keywords",     f"https://api.pep-web.org/v2/Database/Keywords/?id={docid}&formatrequested=JSON"),
        ("DocKeywords",  f"https://api.pep-web.org/v2/Database/DocKeywords/?id={docid}&formatrequested=JSON"),
        ("Metadata",     f"https://api.pep-web.org/v2/Metadata/Document/?id={docid}&formatrequested=JSON"),
    ]

    for name, url in candidates:
        code, ctype, head = try_url(s, url)
        print(f"{name:12s} -> {code} {ctype}")
        if code == 200:
            # heurystyka: czy odpowiedź zawiera "kw" / "keyword"?
            if "kw" in head.lower() or "keyword" in head.lower():
                print("  looks promising:", url)
        time.sleep(SLEEP)

    print("\nJeśli któryś zwraca 200, wklej mi nazwę + będziemy parsować konkretny format.")
    print("Jeśli wszystkie 404/400: trzeba złapać właściwy endpoint z Network.")

if __name__ == "__main__":
    main()