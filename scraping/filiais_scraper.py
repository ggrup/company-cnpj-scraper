#!/usr/bin/env python3
"""
DiretorioBrasil.net Filial Scraper

Extracts all filial CNPJs from DiretorioBrasil.net based on company name and main CNPJ.
Implements comprehensive anti-blocking measures including proxy rotation, randomized headers,
and retry logic.
"""

import re
import time
import random
import json
import os
import unicodedata
from typing import List, Tuple, Optional, Dict
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Edge/120.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
]

ACCEPT_LANGUAGES = [
    "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    "pt-BR,pt;q=0.9",
    "pt-BR;q=0.9,pt;q=0.8,en;q=0.7",
    "pt-BR,en-US;q=0.9,en;q=0.8",
]

CNPJ_PATTERN = re.compile(r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b')

_PROXY_POOL = []
_PROXY_INDEX = 0


def load_proxies() -> List[str]:
    """
    Load proxies from file. Tries /mnt/data/Webshare Proxy List.txt first,
    then falls back to secrets/webshare_proxies.json.
    
    Returns:
        List of proxy URLs in format http://user:pass@host:port
    """
    global _PROXY_POOL
    
    if _PROXY_POOL:
        return _PROXY_POOL
    
    txt_path = "/mnt/data/Webshare Proxy List.txt"
    if os.path.exists(txt_path):
        print(f"[Proxies] Loading from {txt_path}")
        with open(txt_path, 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
            _PROXY_POOL = proxies
            print(f"[Proxies] Loaded {len(_PROXY_POOL)} proxies from txt file")
            return _PROXY_POOL
    
    json_path = "secrets/webshare_proxies.json"
    if os.path.exists(json_path):
        print(f"[Proxies] Loading from {json_path}")
        with open(json_path, 'r') as f:
            data = json.load(f)
            proxies = data.get("proxies", [])
            _PROXY_POOL = proxies
            print(f"[Proxies] Loaded {len(_PROXY_POOL)} proxies from json file")
            return _PROXY_POOL
    
    print("[Proxies] WARNING: No proxy file found, will use direct connection")
    return []


def get_next_proxy() -> Optional[Dict[str, str]]:
    """
    Get next proxy from the pool using round-robin rotation.
    
    Returns:
        Dict with 'http' and 'https' keys, or None if no proxies available
    """
    global _PROXY_INDEX
    
    proxies = load_proxies()
    if not proxies:
        return None
    
    proxy_url = proxies[_PROXY_INDEX % len(proxies)]
    _PROXY_INDEX += 1
    
    return {
        'http': proxy_url,
        'https': proxy_url
    }


def sanitize_slug(company_name: str) -> str:
    """
    Convert company name to DiretorioBrasil slug format.
    
    Rules:
    - lowercase everything
    - remove accents
    - remove all punctuation (periods, commas, slashes, parentheses, quotes)
    - replace any sequence of spaces with "-"
    - normalize "s.a." or "s a" or "sa." or "sa" → "sa"
    - normalize "ltda" or "ltda." → "ltda"
    - keep alphanumeric + dash only
    
    Examples:
        "Embraer S.A." → "embraer-sa"
        "Raízen S.A." → "raizen-sa"
        "Banco Bradesco S.A." → "banco-bradesco-sa"
        "Mercado Livre Ltda." → "mercado-livre-ltda"
    
    Args:
        company_name: Original company name
        
    Returns:
        Sanitized slug
    """
    text = company_name.lower()
    
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('ascii')
    
    text = re.sub(r'\bs\.?\s*a\.?\b', 'sa', text)
    
    text = re.sub(r'\bltda\.?\b', 'ltda', text)
    
    text = re.sub(r'[^\w\s-]', '', text)
    
    text = re.sub(r'[\s_]+', '-', text)
    
    text = text.strip('-')
    
    text = re.sub(r'-+', '-', text)
    
    return text


def build_filial_url(slug: str, cnpj_digits: str) -> str:
    """
    Build DiretorioBrasil filial URL.
    
    Format: https://www.diretoriobrasil.net/filiais/{slug}-{cnpj_digits}.html
    
    Args:
        slug: Sanitized company name slug
        cnpj_digits: CNPJ with only digits (14 characters)
        
    Returns:
        Full URL
    """
    return f"https://www.diretoriobrasil.net/filiais/{slug}-{cnpj_digits}.html"


def request_with_proxy_rotation(url: str, max_attempts: int = 5) -> Optional[str]:
    """
    Make HTTP request with comprehensive anti-blocking measures.
    
    Features:
    - Rotating proxies from Webshare pool
    - Randomized User-Agent headers
    - Randomized Accept-Language headers
    - Randomized Referer (Google search)
    - Random delays (1.5-4.5 seconds)
    - Retry logic on failures
    - Detection of block pages and captchas
    
    Args:
        url: URL to fetch
        max_attempts: Maximum number of retry attempts
        
    Returns:
        HTML content as string, or None if all attempts failed
    """
    for attempt in range(1, max_attempts + 1):
        try:
            delay = random.uniform(1.5, 4.5)
            time.sleep(delay)
            
            proxies = get_next_proxy()
            
            headers = {
                'User-Agent': random.choice(USER_AGENTS),
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': random.choice(ACCEPT_LANGUAGES),
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Referer': f'https://www.google.com/search?q={urlparse(url).path.split("/")[-1].replace(".html", "")}',
            }
            
            print(f"  [Request] Attempt {attempt}/{max_attempts}: {url[:80]}...")
            if proxies:
                print(f"  [Request] Using proxy (index {_PROXY_INDEX - 1})")
            
            response = requests.get(
                url,
                headers=headers,
                proxies=proxies,
                timeout=15,
                allow_redirects=True
            )
            
            if response.status_code in [403, 422, 423, 429, 500, 502, 503, 504]:
                print(f"  [Request] Got status {response.status_code}, rotating proxy and retrying...")
                continue
            
            if response.status_code != 200:
                print(f"  [Request] Got status {response.status_code}, retrying...")
                continue
            
            if not response.encoding or response.encoding == 'ISO-8859-1':
                response.encoding = 'iso-8859-1'
            
            html = response.text
            
            if len(html) < 500:
                print(f"  [Request] HTML too short ({len(html)} chars), likely blocked, retrying...")
                continue
            
            block_indicators = [
                'você foi bloqueado',
                'access denied',
                'captcha',
                'cloudflare',
                'security check',
                'blocked',
            ]
            
            html_lower = html.lower()
            if any(indicator in html_lower for indicator in block_indicators):
                print(f"  [Request] Block indicator detected in HTML, rotating proxy and retrying...")
                continue
            
            if '<div class="row-list">' not in html and 'empresas' not in html_lower:
                print(f"  [Request] Expected content not found, retrying...")
                continue
            
            print(f"  [Request] ✓ Successfully fetched {len(html)} chars")
            return html
            
        except requests.exceptions.Timeout:
            print(f"  [Request] Timeout on attempt {attempt}, retrying...")
            continue
            
        except requests.exceptions.ConnectionError as e:
            print(f"  [Request] Connection error on attempt {attempt}: {e}, retrying...")
            continue
            
        except Exception as e:
            print(f"  [Request] Error on attempt {attempt}: {e}, retrying...")
            continue
    
    print(f"  [Request] ✗ Failed to fetch after {max_attempts} attempts")
    return None


def parse_filiais(html: str) -> List[Tuple[str, str]]:
    """
    Parse filiais from DiretorioBrasil HTML.
    
    Extracts entries from <div class="row-list"> blocks:
    - filial_name from <h5 class="socio"> (e.g., "Filial", "Matriz")
    - CNPJ from <p class="det"> using regex pattern
    
    Args:
        html: HTML content
        
    Returns:
        List of (filial_name, cnpj) tuples
    """
    soup = BeautifulSoup(html, 'html.parser')
    results = []
    
    row_lists = soup.find_all('div', class_='row-list')
    
    for row in row_lists:
        try:
            socio_tag = row.find('h5', class_='socio')
            if not socio_tag:
                continue
            
            filial_name = socio_tag.get_text(strip=True)
            
            det_tag = row.find('p', class_='det')
            if not det_tag:
                continue
            
            det_text = det_tag.get_text()
            
            cnpj_match = CNPJ_PATTERN.search(det_text)
            if not cnpj_match:
                continue
            
            cnpj = cnpj_match.group(0)
            
            results.append((filial_name, cnpj))
            
        except Exception as e:
            print(f"  [Parser] Error parsing row: {e}")
            continue
    
    return results


def detect_pagination(html: str, base_url: str) -> List[str]:
    """
    Detect pagination links in HTML.
    
    Looks for links with ?p=N pattern in pagination section.
    
    Args:
        html: HTML content
        base_url: Base URL for resolving relative links
        
    Returns:
        List of absolute URLs for additional pages
    """
    soup = BeautifulSoup(html, 'html.parser')
    pagination_urls = set()
    
    pagination = soup.find('nav', attrs={'aria-label': 'Resultado da busca'})
    if not pagination:
        return []
    
    links = pagination.find_all('a', href=True)
    
    for link in links:
        href = link['href']
        
        if link.parent.get('class') and 'disabled' in link.parent.get('class'):
            continue
        
        if '?p=' in href:
            absolute_url = urljoin(base_url, href)
            pagination_urls.add(absolute_url)
    
    return sorted(list(pagination_urls))


def scrape_all_filiais(company_name: str, main_cnpj: str) -> List[Dict[str, str]]:
    """
    Scrape all filiais for a company from DiretorioBrasil.net.
    
    Handles:
    - Slug generation from company name
    - URL building
    - Multi-page pagination
    - Deduplication across pages
    - Filtering out the main CNPJ (already in sheet)
    
    Args:
        company_name: Company name
        main_cnpj: Main CNPJ (formatted or digits only)
        
    Returns:
        List of dicts with keys: filial_name, cnpj
    """
    print(f"\n[DiretorioBrasil] Scraping filiais for: {company_name}")
    
    slug = sanitize_slug(company_name)
    print(f"[DiretorioBrasil] Slug: {slug}")
    
    main_cnpj_digits = re.sub(r'\D', '', main_cnpj)
    if len(main_cnpj_digits) != 14:
        print(f"[DiretorioBrasil] ✗ Invalid main CNPJ: {main_cnpj}")
        return []
    
    initial_url = build_filial_url(slug, main_cnpj_digits)
    print(f"[DiretorioBrasil] URL: {initial_url}")
    
    visited_urls = set()
    all_filiais = {}  # CNPJ -> (filial_name, cnpj)
    urls_to_visit = [initial_url]
    
    while urls_to_visit:
        url = urls_to_visit.pop(0)
        
        if url in visited_urls:
            continue
        
        visited_urls.add(url)
        
        html = request_with_proxy_rotation(url)
        if not html:
            print(f"[DiretorioBrasil] Failed to fetch {url}, skipping...")
            continue
        
        page_filiais = parse_filiais(html)
        print(f"[DiretorioBrasil] Found {len(page_filiais)} entries on this page")
        
        for filial_name, cnpj in page_filiais:
            if cnpj not in all_filiais:
                all_filiais[cnpj] = (filial_name, cnpj)
        
        pagination_urls = detect_pagination(html, url)
        if pagination_urls:
            print(f"[DiretorioBrasil] Found {len(pagination_urls)} pagination links")
            for pag_url in pagination_urls:
                if pag_url not in visited_urls:
                    urls_to_visit.append(pag_url)
    
    results = []
    for cnpj, (filial_name, cnpj_formatted) in all_filiais.items():
        if cnpj == main_cnpj or cnpj == main_cnpj_digits:
            print(f"[DiretorioBrasil] Skipping main CNPJ: {cnpj_formatted}")
            continue
        
        results.append({
            'filial_name': filial_name,
            'cnpj': cnpj_formatted
        })
    
    print(f"[DiretorioBrasil] ✓ Total unique filiais found: {len(results)}")
    return results


def write_filiais_to_sheet(sheet, company_name: str, filial_entries: List[Dict[str, str]], insert_after_row: Optional[int] = None) -> int:
    """
    Write filiais to Google Sheet, avoiding duplicates.
    
    Inserts new rows immediately below the Matriz row (if insert_after_row is provided)
    or appends to the end of the sheet (if insert_after_row is None).
    
    Each filial row contains:
    - company_name: same as original
    - filial_name: extracted text (Filial/Matriz)
    - cnpj: extracted CNPJ
    - status: "ok"
    - timestamp: current time
    - notes: "DiretorioBrasil.net"
    
    Args:
        sheet: Google Sheet worksheet object
        company_name: Company name
        filial_entries: List of dicts with filial_name and cnpj keys
        insert_after_row: (optional) Row number after which to insert filiais.
                         If provided, filiais are inserted at row insert_after_row+1.
                         If None, filiais are appended to the end of the sheet.
    
    Returns:
        Number of rows actually inserted/appended
    """
    from datetime import datetime
    
    if not filial_entries:
        print(f"[Sheet] No filiais to write for {company_name}")
        return 0
    
    print(f"[Sheet] Writing {len(filial_entries)} filiais for {company_name}")
    
    all_values = sheet.get_all_values()
    existing_cnpjs = set()
    
    for row in all_values[1:]:
        if len(row) >= 3 and row[0].strip() == company_name:
            if row[2].strip():
                existing_cnpjs.add(row[2].strip())
    
    timestamp = datetime.utcnow().isoformat() + 'Z'
    rows_to_insert = []
    
    for entry in filial_entries:
        cnpj = entry['cnpj']
        
        if cnpj in existing_cnpjs:
            print(f"  [Sheet] Skipping duplicate CNPJ: {cnpj}")
            continue
        
        new_row = [
            company_name,
            entry['filial_name'],
            cnpj,
            'ok',
            timestamp,
            'DiretorioBrasil.net'
        ]
        
        rows_to_insert.append(new_row)
        existing_cnpjs.add(cnpj)
        print(f"  [Sheet] Prepared: {entry['filial_name']} - {cnpj}")
    
    if not rows_to_insert:
        print(f"[Sheet] No new filiais to write (all duplicates)")
        return 0
    
    if insert_after_row is not None:
        print(f"[Sheet] Inserting {len(rows_to_insert)} rows at position {insert_after_row + 1}")
        sheet.insert_rows(rows_to_insert, row=insert_after_row + 1, value_input_option='RAW')
    else:
        print(f"[Sheet] Appending {len(rows_to_insert)} rows to end of sheet")
        for new_row in rows_to_insert:
            sheet.append_row(new_row)
    
    print(f"[Sheet] ✓ Wrote {len(rows_to_insert)} new filiais to sheet")
    return len(rows_to_insert)
