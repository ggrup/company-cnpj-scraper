"""
Enhanced CNPJ Lookup Module

Implements a three-layer approach to find company CNPJs:
1. Website crawling with domain variants
2. Portuguese Wikipedia infobox parsing
3. Receita API validation for MATRIZ preference

This module significantly improves accuracy over simple web search.
"""

import re
import time
import logging
import unicodedata
import requests
from typing import List, Dict, Optional, Tuple
from bs4 import BeautifulSoup

from scraper.parser import find_all_valid_cnpjs, validate_cnpj, format_cnpj

logger = logging.getLogger(__name__)


def normalize_company_name(company_name: str) -> str:
    """
    Normalize company name for domain generation.
    
    Removes accents, punctuation, and common suffixes.
    
    Args:
        company_name: Original company name
        
    Returns:
        Normalized slug suitable for domain names
    """
    nfkd = unicodedata.normalize('NFKD', company_name)
    slug = nfkd.encode('ASCII', 'ignore').decode('ASCII')
    
    slug = slug.lower()
    
    suffixes = [
        r'\bs\.?a\.?\b', r'\bsa\b', r'\bltda\.?\b', r'\bme\b', 
        r'\bepp\b', r'\bholding\b', r'\bgrupo\b', r'\bcia\.?\b',
        r'\bcompanhia\b', r'\bempresa\b', r'\bs\.?a\.?s\.?\b'
    ]
    for suffix in suffixes:
        slug = re.sub(suffix, '', slug, flags=re.IGNORECASE)
    
    slug = re.sub(r'[^\w\s]', '', slug)
    slug = re.sub(r'\s+', '', slug)
    
    return slug.strip()


def generate_domain_candidates(company_name: str) -> List[str]:
    """
    Generate candidate domain names from company name.
    
    Args:
        company_name: Company name
        
    Returns:
        List of candidate domain names to try
    """
    slug = normalize_company_name(company_name)
    
    if not slug:
        return []
    
    candidates = [
        f"{slug}.com.br",
        f"{slug}.com",
        f"{slug}.br",
        f"www.{slug}.com.br",
        f"www.{slug}.com"
    ]
    
    return candidates


def crawl_website_for_cnpj(company_name: str) -> Tuple[List[str], Optional[str], str]:
    """
    Crawl company website looking for CNPJ.
    
    Tries multiple domain variants and extracts CNPJ from page content.
    
    Args:
        company_name: Company name
        
    Returns:
        Tuple of (cnpjs_found, website_url, notes)
    """
    logger.info(f"Layer 1: Crawling website for {company_name}")
    
    candidates = generate_domain_candidates(company_name)
    
    if not candidates:
        logger.warning(f"  Could not generate domain candidates for {company_name}")
        return ([], None, "Could not generate domain candidates")
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for domain in candidates:
        try:
            url = f"https://{domain}"
            logger.debug(f"  Trying {url}")
            
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
            
            if response.status_code == 200:
                logger.info(f"  Found website: {url}")
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                for script in soup(['script', 'style']):
                    script.decompose()
                
                text = soup.get_text()
                
                cnpjs = find_all_valid_cnpjs(text)
                
                if cnpjs:
                    logger.info(f"  Found {len(cnpjs)} CNPJ(s) on {url}: {cnpjs}")
                    return (cnpjs, url, f"Found on website {url}")
                else:
                    logger.debug(f"  No CNPJ found on {url}")
            
            time.sleep(0.5)
            
        except requests.RequestException as e:
            logger.debug(f"  Error accessing {domain}: {e}")
            continue
    
    logger.warning(f"  No CNPJ found on any website for {company_name}")
    return ([], None, "No valid website found or no CNPJ on website")


def search_wikipedia_for_cnpj(company_name: str) -> Tuple[List[str], Optional[str], str]:
    """
    Search Portuguese Wikipedia for company CNPJ.
    
    Uses Wikipedia API to find company page and parse infobox.
    
    Args:
        company_name: Company name
        
    Returns:
        Tuple of (cnpjs_found, wikipedia_url, notes)
    """
    logger.info(f"Layer 2: Searching Wikipedia for {company_name}")
    
    try:
        search_url = "https://pt.wikipedia.org/w/api.php"
        search_params = {
            'action': 'query',
            'list': 'search',
            'srsearch': company_name,
            'format': 'json',
            'srlimit': 1
        }
        
        response = requests.get(search_url, params=search_params, timeout=10)
        response.raise_for_status()
        
        search_data = response.json()
        
        if not search_data.get('query', {}).get('search'):
            logger.warning(f"  No Wikipedia page found for {company_name}")
            return ([], None, "No Wikipedia page found")
        
        page_title = search_data['query']['search'][0]['title']
        logger.info(f"  Found Wikipedia page: {page_title}")
        
        parse_params = {
            'action': 'parse',
            'page': page_title,
            'prop': 'text',
            'format': 'json'
        }
        
        time.sleep(0.5)  # Be respectful
        
        response = requests.get(search_url, params=parse_params, timeout=10)
        response.raise_for_status()
        
        parse_data = response.json()
        
        if 'parse' not in parse_data or 'text' not in parse_data['parse']:
            logger.warning(f"  Could not parse Wikipedia page for {page_title}")
            return ([], None, "Could not parse Wikipedia page")
        
        html_content = parse_data['parse']['text']['*']
        soup = BeautifulSoup(html_content, 'html.parser')
        
        infobox = soup.find('table', class_='infobox')
        
        if not infobox:
            logger.warning(f"  No infobox found on Wikipedia page")
            return ([], None, "No infobox found on Wikipedia page")
        
        cnpjs = []
        for row in infobox.find_all('tr'):
            header = row.find('th')
            if header and 'cnpj' in header.get_text().lower():
                value = row.find('td')
                if value:
                    text = value.get_text()
                    found_cnpjs = find_all_valid_cnpjs(text)
                    cnpjs.extend(found_cnpjs)
        
        if not cnpjs:
            infobox_text = infobox.get_text()
            cnpjs = find_all_valid_cnpjs(infobox_text)
        
        wiki_url = f"https://pt.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
        
        if cnpjs:
            logger.info(f"  Found {len(cnpjs)} CNPJ(s) on Wikipedia: {cnpjs}")
            return (cnpjs, wiki_url, f"Found on Wikipedia page {page_title}")
        else:
            logger.warning(f"  No CNPJ found in Wikipedia infobox")
            return ([], wiki_url, "Wikipedia page found but no CNPJ in infobox")
        
    except Exception as e:
        logger.error(f"  Error searching Wikipedia: {e}")
        return ([], None, f"Error searching Wikipedia: {str(e)}")


def validate_with_receita_api(cnpj: str) -> Optional[Dict]:
    """
    Validate CNPJ with Receita Federal API and get metadata.
    
    Prefers MATRIZ establishments.
    
    Args:
        cnpj: CNPJ to validate (formatted or raw)
        
    Returns:
        Dict with API data or None if validation fails
    """
    cnpj_raw = re.sub(r'[^\d]', '', cnpj)
    
    if len(cnpj_raw) != 14:
        return None
    
    try:
        url = f"https://publica.cnpj.ws/cnpj/{cnpj_raw}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data
        
        time.sleep(0.5)
        url = f"https://minhareceita.org/{cnpj_raw}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            return data
        
    except Exception as e:
        logger.debug(f"  Error validating CNPJ with API: {e}")
    
    return None


def find_cnpj_layered(company_name: str) -> Dict[str, str]:
    """
    Find company CNPJ using three-layer approach.
    
    Layers:
    1. Website crawling with domain variants
    2. Portuguese Wikipedia infobox parsing
    3. Receita API validation for MATRIZ preference
    
    Args:
        company_name: Company name to search
        
    Returns:
        Dict with keys: cnpj, website, status, notes
    """
    logger.info(f"Starting layered CNPJ lookup for: {company_name}")
    
    all_cnpjs = []
    source_url = None
    layer_notes = []
    
    cnpjs, url, notes = crawl_website_for_cnpj(company_name)
    if cnpjs:
        all_cnpjs.extend(cnpjs)
        if not source_url:
            source_url = url
        layer_notes.append(f"Layer1(website): {notes}")
    else:
        layer_notes.append(f"Layer1(website): {notes}")
    
    if not all_cnpjs:
        time.sleep(1)  # Be respectful between layers
        cnpjs, url, notes = search_wikipedia_for_cnpj(company_name)
        if cnpjs:
            all_cnpjs.extend(cnpjs)
            if not source_url:
                source_url = url
            layer_notes.append(f"Layer2(wikipedia): {notes}")
        else:
            layer_notes.append(f"Layer2(wikipedia): {notes}")
    
    unique_cnpjs = list(dict.fromkeys(all_cnpjs))
    
    if not unique_cnpjs:
        logger.warning(f"No CNPJ found for {company_name} after all layers")
        return {
            'cnpj': '',
            'website': '',
            'status': 'not_found',
            'notes': '; '.join(layer_notes)
        }
    
    selected_cnpj = unique_cnpjs[0]
    is_matriz = False
    
    for cnpj in unique_cnpjs:
        time.sleep(0.5)
        api_data = validate_with_receita_api(cnpj)
        
        if api_data:
            if api_data.get('identificador_matriz_filial') == 1 or \
               api_data.get('descricao_identificador_matriz_filial') == 'MATRIZ':
                selected_cnpj = cnpj
                is_matriz = True
                layer_notes.append(f"Layer3(API): Validated as MATRIZ")
                break
    
    if len(unique_cnpjs) == 1:
        status = 'success'
        notes = '; '.join(layer_notes)
    else:
        status = 'multiple'
        notes = f"Multiple CNPJs found: {', '.join(unique_cnpjs)}. Selected: {selected_cnpj}"
        if is_matriz:
            notes += " (MATRIZ)"
        notes += "; " + '; '.join(layer_notes)
    
    logger.info(f"Found CNPJ for {company_name}: {selected_cnpj} (status: {status})")
    
    return {
        'cnpj': format_cnpj(selected_cnpj),
        'website': source_url or '',
        'status': status,
        'notes': notes
    }
