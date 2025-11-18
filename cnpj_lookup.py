import re
import time
import requests

GOOGLE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0 Safari/537.36"
    ),
    "Accept-Language": "pt-BR,pt;q=0.9,en;q=0.8",
}

CNPJ_REGEX = r"\d{2}\D?\d{3}\D?\d{3}\D?\d{4}\D?\d{2}"


def normalize_cnpj(raw: str) -> str | None:
    """Normalize any CNPJ-like string into XX.XXX.XXX/XXXX-XX."""
    digits = re.sub(r"\D", "", raw)
    if len(digits) != 14:
        return None
    return f"{digits[0:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:14]}"


def lookup_cnpj_google(company_name: str):
    """
    Layer 1 (Primary): Extract CNPJ from Google SERP HTML.
    """
    try:
        query = f"CNPJ {company_name} site:br"
        url = "https://www.google.com/search"
        params = {"q": query}

        resp = requests.get(url, headers=GOOGLE_HEADERS, params=params, timeout=10)

        if resp.status_code != 200:
            return None, f"Google HTTP {resp.status_code} for query '{query}'"

        html = resp.text
        matches = re.findall(CNPJ_REGEX, html)

        if not matches:
            return None, f"No CNPJ found in Google HTML for '{company_name}'"

        first = matches[0]
        normalized = normalize_cnpj(first)
        if not normalized:
            return None, f"Found candidate '{first}', but normalization failed"

        return normalized, f"Found via Google SERP (raw={first})"

    except Exception as e:
        return None, f"Google lookup error: {e!r}"


def lookup_cnpj(company_name: str):
    """
    Entry point for batch runner. Only Google layer used.
    """
    time.sleep(1.0)  # reduce risk of Google rate limits
    cnpj, debug = lookup_cnpj_google(company_name)

    if cnpj:
        return cnpj, "google", debug

    return None, "none", debug
