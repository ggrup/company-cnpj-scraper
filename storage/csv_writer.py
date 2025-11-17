"""
CSV Storage Module

Handles reading input CSV files and writing output results.
"""

import csv
import logging
import os
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class CompanyResult:
    """Data structure for company CNPJ search results."""
    company_input: str
    company_found_name: str
    cnpj: str
    source_url: str
    status: str  # found, not_found, ambiguous
    created_at: str
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for CSV writing."""
        return asdict(self)


def read_companies(filepath: str) -> List[str]:
    """
    Read company names from a CSV file.
    
    Expects a CSV with a 'company_name' column.
    
    Args:
        filepath: Path to the input CSV file
        
    Returns:
        List of company names
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If CSV format is invalid
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input file not found: {filepath}")
    
    companies = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            if 'company_name' not in reader.fieldnames:
                raise ValueError(
                    f"CSV must have a 'company_name' column. Found: {reader.fieldnames}"
                )
            
            for row in reader:
                company_name = row['company_name'].strip()
                if company_name:
                    companies.append(company_name)
        
        logger.info(f"Read {len(companies)} companies from {filepath}")
        return companies
        
    except csv.Error as e:
        raise ValueError(f"Error reading CSV file: {e}")


def initialize_output_file(filepath: str) -> None:
    """
    Initialize the output CSV file with headers.
    
    Creates the file and writes the header row if it doesn't exist.
    If the file exists, does nothing.
    
    Args:
        filepath: Path to the output CSV file
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    if os.path.exists(filepath):
        logger.debug(f"Output file already exists: {filepath}")
        return
    
    headers = [
        'company_input',
        'company_found_name',
        'cnpj',
        'source_url',
        'status',
        'created_at'
    ]
    
    try:
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
        
        logger.info(f"Initialized output file: {filepath}")
        
    except IOError as e:
        logger.error(f"Error creating output file: {e}")
        raise


def append_result(filepath: str, result: CompanyResult) -> None:
    """
    Append a single result to the output CSV file.
    
    Args:
        filepath: Path to the output CSV file
        result: CompanyResult object to write
    """
    try:
        if not os.path.exists(filepath):
            initialize_output_file(filepath)
        
        with open(filepath, 'a', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=result.to_dict().keys())
            writer.writerow(result.to_dict())
        
        logger.debug(f"Appended result for {result.company_input}")
        
    except IOError as e:
        logger.error(f"Error writing to output file: {e}")
        raise


def write_results(filepath: str, results: List[CompanyResult]) -> None:
    """
    Write multiple results to the output CSV file.
    
    This will overwrite the file if it exists.
    
    Args:
        filepath: Path to the output CSV file
        results: List of CompanyResult objects to write
    """
    if not results:
        logger.warning("No results to write")
        return
    
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    try:
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].to_dict().keys())
            writer.writeheader()
            
            for result in results:
                writer.writerow(result.to_dict())
        
        logger.info(f"Wrote {len(results)} results to {filepath}")
        
    except IOError as e:
        logger.error(f"Error writing results file: {e}")
        raise


def create_result(
    company_input: str,
    cnpj: str = "",
    source_url: str = "",
    status: str = "not_found",
    company_found_name: str = ""
) -> CompanyResult:
    """
    Create a CompanyResult object with current timestamp.
    
    Args:
        company_input: Original company name from input
        cnpj: CNPJ number found (empty if not found)
        source_url: URL where CNPJ was found
        status: Status of the search (found/not_found/ambiguous)
        company_found_name: Company name found on the source
        
    Returns:
        CompanyResult object
    """
    return CompanyResult(
        company_input=company_input,
        company_found_name=company_found_name,
        cnpj=cnpj,
        source_url=source_url,
        status=status,
        created_at=datetime.now().isoformat()
    )


def read_existing_results(filepath: str) -> List[str]:
    """
    Read already processed companies from output file.
    
    This allows resuming interrupted processing.
    
    Args:
        filepath: Path to the output CSV file
        
    Returns:
        List of company names already processed
    """
    if not os.path.exists(filepath):
        return []
    
    processed = []
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                processed.append(row['company_input'])
        
        logger.info(f"Found {len(processed)} already processed companies")
        return processed
        
    except (csv.Error, IOError) as e:
        logger.warning(f"Error reading existing results: {e}")
        return []
