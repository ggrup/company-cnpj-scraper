import re
import time
import random
import requests
from bs4 import BeautifulSoup
from cnpj_lookup import normalize_cnpj

BASE = "https://www.cnpj.biz"

HEADERS_LIST = [
    {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"},
    {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0"},
    {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0 Safari/537.36"},
]

def get(url, retries=3):
    for _ in range(retries):
        try:
            headers = random.choice(HEADERS_LIST)
            headers["Accept-Language"] = "pt-BR,pt;q=0.9"
            headers["Accept"] = "text/html"
            time.sleep(random.uniform(1.2, 2.8))
            r = requests.get(url, headers=headers, timeout=15)
            if r.status_code == 200:
                return r.text
            if r.status_code in [403, 429]:
                time.sleep(3)
        except:
            time.sleep(2)
    return None

def extract_table_rows(html):
    soup = BeautifulSoup(html, "html.parser")
    rows = []
    for tr in soup.select("table tr"):
        cols = [c.get_text(strip=True) for c in tr.find_all("td")]
        if len(cols) >= 2:
            razao = cols[0]
            raw_cnpj = cols[1]
            tipo = cols[-1] if len(cols) >= 3 else ""
            cnpj = normalize_cnpj(raw_cnpj)
            if cnpj:
                rows.append({"razao_social": razao, "cnpj": cnpj, "tipo": tipo})
    return rows

def scrape_cnpj_biz_all(main_cnpj):
    digits = re.sub(r"\D", "", main_cnpj)
    base_url = f"{BASE}/{digits}"
    filiais_url = f"{BASE}/cnpj/{digits}/filiais"
    relacionadas_url = f"{BASE}/cnpj/{digits}/empresas-relacionadas"

    output = []

    html = get(base_url)
    if html:
        output.extend(extract_table_rows(html))

    html_f = get(filiais_url)
    if html_f:
        output.extend(extract_table_rows(html_f))

    html_r = get(relacionadas_url)
    if html_r:
        output.extend(extract_table_rows(html_r))

    unique = {}
    for row in output:
        unique[row["cnpj"]] = row

    return list(unique.values())
