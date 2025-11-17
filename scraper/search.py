"""
Web Search Module

Performs web searches to find company CNPJ information.
Prioritizes official sources like Receita Federal and company websites.
"""

import requests
import logging
import time
from typing import List, Optional, Dict
from urllib.parse import quote_plus, urlparse
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class SearchResult:
    """Represents a search result with URL and content."""
    
    def __init__(self, url: str, title: str = "", snippet: str = ""):
        self.url = url
        self.title = title
        self.snippet = snippet
        self.content = ""
        
    def __repr__(self):
        return f"SearchResult(url={self.url}, title={self.title[:50]}...)"


def search_company_cnpj(company_name: str, max_results: int = 5) -> List[SearchResult]:
    """
    Search for a company's CNPJ using web search.
    
    Args:
        company_name: Name of the company to search for
        max_results: Maximum number of results to return
        
    Returns:
        List of SearchResult objects
    """
    if not company_name:
        logger.warning("Empty company name provided")
        return []
    
    logger.info(f"Searching for CNPJ of: {company_name}")
    
    results = _google_search(company_name, max_results)
    
    results = _prioritize_sources(results)
    
    return results[:max_results]


def _google_search(company_name: str, max_results: int) -> List[SearchResult]:
    """
    Perform a Google search for company CNPJ.
    
    Args:
        company_name: Company name to search
        max_results: Maximum results to fetch
        
    Returns:
        List of SearchResult objects
    """
    query = f"{company_name} CNPJ"
    encoded_query = quote_plus(query)
    
    search_url = f"https://www.google.com/search?q={encoded_query}&num={max_results}"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        logger.debug(f"Fetching Google search results for: {query}")
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        results = []
        
        search_divs = soup.find_all('div', class_='g')
        
        for div in search_divs[:max_results]:
            try:
                link_tag = div.find('a')
                if not link_tag or not link_tag.get('href'):
                    continue
                
                url = link_tag.get('href')
                
                if not url.startswith('http'):
                    continue
                
                title_tag = div.find('h3')
                title = title_tag.get_text() if title_tag else ""
                
                snippet_tag = div.find('div', class_=['VwiC3b', 'IsZvec'])
                snippet = snippet_tag.get_text() if snippet_tag else ""
                
                result = SearchResult(url=url, title=title, snippet=snippet)
                results.append(result)
                logger.debug(f"Found result: {url}")
                
            except Exception as e:
                logger.debug(f"Error parsing search result: {e}")
                continue
        
        logger.info(f"Found {len(results)} search results")
        return results
        
    except requests.RequestException as e:
        logger.error(f"Error performing Google search: {e}")
        return []


def _prioritize_sources(results: List[SearchResult]) -> List[SearchResult]:
    """
    Prioritize search results based on source reliability.
    
    Official sources (gov.br, Receita Federal) are prioritized.
    
    Args:
        results: List of SearchResult objects
        
    Returns:
        Sorted list of SearchResult objects
    """
    def get_priority(result: SearchResult) -> int:
        """Return priority score (lower is better)."""
        url_lower = result.url.lower()
        
        if 'receita.fazenda.gov.br' in url_lower or 'receitafederal.gov.br' in url_lower:
            return 0
        if '.gov.br' in url_lower:
            return 1
        
        if 'empresas.cnpj.com' in url_lower or 'cnpj.biz' in url_lower:
            return 2
        
        domain = urlparse(result.url).netloc
        if company_name_in_domain(domain):
            return 3
        
        return 4
    
    sorted_results = sorted(results, key=get_priority)
    logger.debug(f"Prioritized {len(sorted_results)} results")
    return sorted_results


def company_name_in_domain(domain: str) -> bool:
    """Check if domain might be a company's official site."""
    return len(domain.split('.')) <= 3 and not any(
        keyword in domain for keyword in ['blog', 'forum', 'wiki', 'social']
    )


def fetch_page_content(url: str, timeout: int = 10) -> Optional[str]:
    """
    Fetch the HTML content of a web page.
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        
    Returns:
        Page content as string or None if failed
    """
    if not url:
        return None
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        logger.debug(f"Fetching content from: {url}")
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        for script in soup(['script', 'style']):
            script.decompose()
        
        text = soup.get_text()
        
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        logger.debug(f"Successfully fetched {len(text)} characters from {url}")
        return text
        
    except requests.RequestException as e:
        logger.warning(f"Error fetching {url}: {e}")
        return None
    except Exception as e:
        logger.warning(f"Error parsing content from {url}: {e}")
        return None


def search_and_extract_cnpj(company_name: str, parser_func) -> Dict[str, any]:
    """
    Search for a company and extract CNPJ from results.
    
    Args:
        company_name: Name of the company
        parser_func: Function to extract CNPJ from text (from parser module)
        
    Returns:
        Dictionary with search results and extracted CNPJs
    """
    results = search_company_cnpj(company_name)
    
    found_cnpjs = []
    sources = []
    
    for result in results:
        time.sleep(1)
        
        content = fetch_page_content(result.url)
        if not content:
            continue
        
        cnpjs = parser_func(content)
        
        if cnpjs:
            for cnpj in cnpjs:
                if cnpj not in found_cnpjs:
                    found_cnpjs.append(cnpj)
                    sources.append(result.url)
                    logger.info(f"Found CNPJ {cnpj} at {result.url}")
    
    return {
        'cnpjs': found_cnpjs,
        'sources': sources,
        'search_results': results
    }
