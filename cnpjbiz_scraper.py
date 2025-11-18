import re
import time
import random
import requests
from bs4 import BeautifulSoup
from cnpj_lookup import normalize_cnpj

BASE = "https://www.cnpj.biz"

USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13.5; rv:117.0) Gecko/20100101 Firefox/117.0",
]

def fetch(url):
    for _ in range(5):
        headers = {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
            "Connection": "keep-alive",
            "DNT": "1",
            "Upgrade-Insecure-Requests": "1",
        }

        time.sleep(random.uniform(1.8, 4.2))

        try:
            r = requests.get(url, headers=headers, timeout=15)
            text = r.text

            if "Você foi bloqueado" in text or "Access Denied" in text:
                print("[BLOCKED] CNPJ.biz blocked this request. Retrying...")
                continue

            if "<table" not in text:
                print("[EMPTY] No table detected. Retrying...")
                continue

            return text

        except Exception as e:
            print("Error", e)
            time.sleep(2)

    print(f"FAILED to fetch {url} after multiple retries.")
    return None


def parse_table(html):
    soup = BeautifulSoup(html, "html.parser")
    rows = []

    table = soup.find("table")
    if not table:
        return rows

    for tr in table.select("tr"):
        tds = [td.get_text(strip=True) for td in tr.select("td")]

        if len(tds) < 2:
            continue

        razao = tds[0]
        raw_cnpj = tds[1]
        tipo = tds[-1] if len(tds) >= 3 else ""

        cnpj = normalize_cnpj(raw_cnpj)
        if cnpj:
            rows.append({"razao_social": razao, "cnpj": cnpj, "tipo": tipo})

    return rows


def scrape_all_entities(main_cnpj):
    digits = re.sub(r"\D", "", main_cnpj)

    urls = [
        f"{BASE}/{digits}",
        f"{BASE}/cnpj/{digits}/filiais",
        f"{BASE}/cnpj/{digits}/empresas-relacionadas",
    ]

    results = []

    for url in urls:
        html = fetch(url)
        if html:
            rows = parse_table(html)
            results.extend(rows)
        else:
            print(f"[NO HTML] Could not fetch {url}")

    unique = {}
    for r in results:
        unique[r["cnpj"]] = r

    return list(unique.values())
