"""
CNPJ Parser Module

Extracts and validates Brazilian CNPJ numbers from text.
CNPJ format: 00.000.000/0000-00
"""

import re
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


def extract_cnpj_from_text(text: str) -> List[str]:
    """
    Extract all potential CNPJ numbers from text.
    
    Args:
        text: Text content to search for CNPJs
        
    Returns:
        List of CNPJ strings found (may include invalid ones)
    """
    if not text:
        return []
    
    pattern_formatted = r'\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}'
    
    pattern_raw = r'\b\d{14}\b'
    
    cnpjs = []
    
    formatted_matches = re.findall(pattern_formatted, text)
    cnpjs.extend(formatted_matches)
    
    raw_matches = re.findall(pattern_raw, text)
    for raw_cnpj in raw_matches:
        formatted = format_cnpj(raw_cnpj)
        if formatted and formatted not in cnpjs:
            cnpjs.append(formatted)
    
    logger.debug(f"Found {len(cnpjs)} potential CNPJ(s) in text")
    return cnpjs


def validate_cnpj(cnpj: str) -> bool:
    """
    Validate a CNPJ number using the official algorithm.
    
    The CNPJ validation uses two check digits calculated from the first 12 digits.
    
    Args:
        cnpj: CNPJ string (formatted or raw)
        
    Returns:
        True if CNPJ is valid, False otherwise
    """
    if not cnpj:
        return False
    
    cnpj_digits = re.sub(r'[^\d]', '', cnpj)
    
    if len(cnpj_digits) != 14:
        return False
    
    if len(set(cnpj_digits)) == 1:
        return False
    
    weights_first = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_first = sum(int(cnpj_digits[i]) * weights_first[i] for i in range(12))
    remainder_first = sum_first % 11
    check_digit_first = 0 if remainder_first < 2 else 11 - remainder_first
    
    if int(cnpj_digits[12]) != check_digit_first:
        return False
    
    weights_second = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    sum_second = sum(int(cnpj_digits[i]) * weights_second[i] for i in range(13))
    remainder_second = sum_second % 11
    check_digit_second = 0 if remainder_second < 2 else 11 - remainder_second
    
    if int(cnpj_digits[13]) != check_digit_second:
        return False
    
    return True


def format_cnpj(cnpj: str) -> Optional[str]:
    """
    Format a CNPJ string to the standard format: 00.000.000/0000-00
    
    Args:
        cnpj: CNPJ string (formatted or raw)
        
    Returns:
        Formatted CNPJ string or None if invalid format
    """
    if not cnpj:
        return None
    
    cnpj_digits = re.sub(r'[^\d]', '', cnpj)
    
    if len(cnpj_digits) != 14:
        return None
    
    formatted = f"{cnpj_digits[0:2]}.{cnpj_digits[2:5]}.{cnpj_digits[5:8]}/{cnpj_digits[8:12]}-{cnpj_digits[12:14]}"
    
    return formatted


def find_valid_cnpj(text: str) -> Optional[str]:
    """
    Find and return the first valid CNPJ from text.
    
    Args:
        text: Text content to search
        
    Returns:
        First valid CNPJ found (formatted) or None
    """
    cnpjs = extract_cnpj_from_text(text)
    
    for cnpj in cnpjs:
        if validate_cnpj(cnpj):
            logger.debug(f"Valid CNPJ found: {cnpj}")
            return format_cnpj(cnpj)
    
    logger.debug("No valid CNPJ found in text")
    return None


def find_all_valid_cnpjs(text: str) -> List[str]:
    """
    Find and return all valid CNPJs from text.
    
    Args:
        text: Text content to search
        
    Returns:
        List of all valid CNPJs found (formatted, deduplicated)
    """
    cnpjs = extract_cnpj_from_text(text)
    valid_cnpjs = []
    
    for cnpj in cnpjs:
        if validate_cnpj(cnpj):
            formatted = format_cnpj(cnpj)
            if formatted and formatted not in valid_cnpjs:
                valid_cnpjs.append(formatted)
    
    logger.debug(f"Found {len(valid_cnpjs)} valid CNPJ(s)")
    return valid_cnpjs
