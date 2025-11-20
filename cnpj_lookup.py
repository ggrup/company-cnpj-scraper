import os
import re
import requests

CNPJ_REGEX = r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}"

def normalize_cnpj(raw: str | None) -> str | None:
    if not raw:
        return None
    digits = re.sub(r"\D", "", raw)
    if len(digits) != 14:
        return None
    return f"{digits[0:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:14]}"

def get_serpapi_key():
    path = "secrets/serpapi_key.txt"
    if not os.path.exists(path):
        raise Exception("Missing SerpAPI key: please paste it into secrets/serpapi_key.txt")
    with open(path, "r") as f:
        return f.read().strip()

def lookup_cnpj(company_name: str):
    api_key = get_serpapi_key()

    params = {
        "engine": "google",
        "q": f"CNPJ {company_name}",
        "hl": "pt",
        "gl": "br",
        "api_key": api_key,
    }

    try:
        resp = requests.get("https://serpapi.com/search", params=params, timeout=10)
        data = resp.json()

        if "answer_box" in data and isinstance(data["answer_box"], dict):
            snippet = data["answer_box"].get("snippet", "") or data["answer_box"].get("answer", "")
            match = re.search(CNPJ_REGEX, snippet)
            if match:
                return normalize_cnpj(match.group(0)), "serpapi_answer_box", snippet

        for item in data.get("organic_results", []):
            snippet = item.get("snippet", "")
            match = re.search(CNPJ_REGEX, snippet)
            if match:
                return normalize_cnpj(match.group(0)), "serpapi_organic", snippet

        for item in data.get("inline_results", []):
            snippet = item.get("snippet", "")
            match = re.search(CNPJ_REGEX, snippet)
            if match:
                return normalize_cnpj(match.group(0)), "serpapi_inline", snippet

        return None, "none", "No CNPJ found in SerpAPI results."

    except Exception as e:
        return None, "error", f"SerpAPI error: {e}"
