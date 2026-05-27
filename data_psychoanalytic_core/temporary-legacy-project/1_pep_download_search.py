import json
import time
from pathlib import Path
from urllib.parse import urlparse, parse_qs

import requests

SLEEP = 0.8
TIMEOUT = 60
PAGE_LIMIT = 200

RAW_DIR = Path("raw_pep")
RAW_DIR.mkdir(exist_ok=True)

def load_secrets():
    return json.loads(Path("pep_secrets.json").read_text(encoding="utf-8"))

def build_headers(secrets: dict):
    h = {
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json, text/plain, */*",
    }
    # minimalne, ale wystarczające
    for k, v in secrets.items():
        h[k] = v
    return h

def parse_base_and_params(full_url: str):
    u = urlparse(full_url)
    base = f"{u.scheme}://{u.netloc}{u.path}"
    qs = {k: v[0] for k, v in parse_qs(u.query).items()}
    return base, qs

def main():
    secrets = load_secrets()
    headers = build_headers(secrets)

    # !!! TU WKLEJASZ URL z Network (Request URL) jako STRING w cudzysłowie !!!
    SEARCH_URL = "https://api.pep-web.org/v2/Database/Search/?abstract=true&facetquery=art_id%3A(RFP.023.0367A+OR+IJP.006.0247A+OR+RBP.069.0109A+OR+PY.007.0021A+OR+RFP.053.1405A+OR+RPP-CS.018B.0055A+OR+PD.001.0029A+OR+TVPA.025.0276A+OR+IJP.089.0795A+OR+RRP.013B.0017A+OR+IJP.049.0484A+OR+JBP.081.0041A+OR+IJP.033.0235A+OR+CJP.013.0057A+OR+IJP.039.0144A+OR+PSU.039.0151A+OR+LU-AM.020B.0007A+OR+IJP.040.0308A+OR+APM.001.0025A+OR+IJP.007.0324A+OR+RFP.032.0595A+OR+CPS.019.0389A+OR+RBP.070.0031A+OR+IJP.031.0081A+OR+PY.011.0077A+OR+PAQ.034.0155A+OR+RPP-CS.007B.0004A+OR+IJP.043.0306A+OR+TVPA.022.0256A+OR+RRP.013B.0043A+OR+IJP.039.0350A+OR+JBP.080.0159A+OR+IJP.018.0256A+OR+CJP.008.0099A+OR+IJP.076.0019A+OR+LU-AM.020B.0122A+OR+APM.005.0009A+OR+RFP.035.0859A+OR+PAQ.034.0155A+OR+RBP.072.0011A+OR+PAQ.073.0047A+OR+PY.041.0179A+OR+RPP-CS.020B.0027A+OR+IJP.057.0275A+OR+TVPA.010.0148A+OR+PAQ.011.0301A+OR+RRP.006A.0053A+OR+CPS.022.0087A+OR+JBP.080.0103A+OR+CJP.019.0329A+OR+PSU.040.0153A+OR+IJP.078.1071A+OR+LU-AM.023A.0021A+OR+IJP.075.0785A+OR+APM.007.0007A+OR+RFP.050.1339A+OR+RBP.073.0053A+OR+PY.040.0055A+OR+APA.001.0104A+OR+RPP-CS.017B.0087A+OR+IJP.012.0397A+OR+RPP-CS.017B.0087A+OR+TVPA.023.0172A+OR+APA.002.0005A+OR+RRP.006A.0069A+OR+JBP.082.0177A+OR+CJP.018.0181A+OR+IJP.027.0030A+OR+IJP.039.0374A+OR+PSU.040.0379A+OR+LU-AM.027A.0141A+OR+IJP.078.0227A+OR+APM.008.0045A+OR+IJP.030.0225A+OR+RFP.050.1299A+OR+IJP.018.0373A+OR+RBP.075.0029A+OR+IFP.013.0031A+OR+RPP-CS.007A.0063A+OR+PSC.018.0245A+OR+IJP.077.0217A+OR+RRP.007B.0032A+OR+RPSA.004.0215A+OR+JBP.082.0017A+OR+PI.010.0601A+OR+PSU.014C.0001A+OR+IJP.010.0125A+OR+LU-AM.030A.0031A+OR+APM.013.0017A+OR+PAQ.031.0001A+OR+SPR.039.0013A+OR+IJP.066.0405A+OR+PAQ.019.0482A+OR+PAQ.015.0419A+OR+SPR.037.0099A+OR+ijp.041.0016a+OR+PI.004.0221A+OR+IRP.001.0125A+OR+SPR.037.0015A+OR+APA.027S.0263A+OR+PSC.005.0074A+OR+TVPA.022.0195A+OR+SPR.040.0029A+OR+IJP.079.0649A+OR+PY.034.0115A+OR+IJP.010.0303A+OR+SPR.040.0001A+OR+IJP.077.0667A+OR+PSU.039.0347A+OR+PSC.018.0286A+OR+SPR.040.0094A+OR+PAQ.015.0419A+OR+IJP.053.0333A+OR+SPR.038.0086A)&formatrequested=XML&synonyms=false"

    base, params = parse_base_and_params(SEARCH_URL)

    # wymuś JSON
    params["formatrequested"] = "JSON"

    # paging
    params["limit"] = str(PAGE_LIMIT)
    offset = 0
    page = 0

    while True:
        params["offset"] = str(offset)

        r = requests.get(base, params=params, headers=headers, timeout=TIMEOUT)
        if r.status_code != 200:
            print("ERROR", r.status_code)
            print(r.text[:2000])
            break

        data = r.json()
        out = RAW_DIR / f"search_page_{page:04d}.json"
        out.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

        info = data.get("documentList", {}).get("responseInfo", {})
        count = info.get("count", 0)
        full = info.get("fullCount", None)

        print(f"[OK] page={page} offset={offset} count={count} fullCount={full}")

        if not count:
            break

        offset += int(count)
        page += 1

        if full is not None and offset >= int(full):
            break

        time.sleep(SLEEP)

    print("DONE. Raw pages in:", RAW_DIR.resolve())

if __name__ == "__main__":
    main()