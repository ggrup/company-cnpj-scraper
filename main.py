#!/usr/bin/env python3
"""
Company CNPJ Scraper

Main entry point for the CNPJ scraper application.
Searches for Brazilian company CNPJ numbers and saves results to CSV.
"""

import argparse
import logging
import sys
from pathlib import Path

from scraper.parser import find_all_valid_cnpjs
from scraper.search import search_and_extract_cnpj
from storage.csv_writer import (
    read_companies,
    initialize_output_file,
    append_result,
    create_result,
    read_existing_results
)


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging for the application.
    
    Args:
        verbose: If True, set DEBUG level, otherwise INFO
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def process_company(company_name: str, output_file: str) -> None:
    """
    Process a single company: search for CNPJ and save result.
    
    Args:
        company_name: Name of the company to search
        output_file: Path to output CSV file
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Processing: {company_name}")
    
    try:
        search_results = search_and_extract_cnpj(company_name, find_all_valid_cnpjs)
        
        cnpjs = search_results['cnpjs']
        sources = search_results['sources']
        
        if len(cnpjs) == 0:
            result = create_result(
                company_input=company_name,
                status='not_found'
            )
            logger.warning(f"No CNPJ found for: {company_name}")
            
        elif len(cnpjs) == 1:
            result = create_result(
                company_input=company_name,
                cnpj=cnpjs[0],
                source_url=sources[0] if sources else '',
                status='found',
                company_found_name=company_name  # Could be improved with extraction
            )
            logger.info(f"Found CNPJ for {company_name}: {cnpjs[0]}")
            
        else:
            result = create_result(
                company_input=company_name,
                cnpj=cnpjs[0],
                source_url=sources[0] if sources else '',
                status='ambiguous',
                company_found_name=company_name
            )
            logger.warning(
                f"Multiple CNPJs found for {company_name}: {cnpjs}. "
                f"Using first one: {cnpjs[0]}"
            )
        
        append_result(output_file, result)
        
    except Exception as e:
        logger.error(f"Error processing {company_name}: {e}", exc_info=True)
        result = create_result(
            company_input=company_name,
            status='not_found'
        )
        append_result(output_file, result)


def main():
    """Main entry point for the CLI application."""
    parser = argparse.ArgumentParser(
        description='Search for Brazilian company CNPJ numbers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --input input/companies.csv --output data/cnpj_results.csv
  python main.py --input input/companies.csv --output data/results.csv --verbose
  python main.py --input input/companies.csv --output data/results.csv --resume
        """
    )
    
    parser.add_argument(
        '--input',
        type=str,
        default='input/companies.csv',
        help='Path to input CSV file with company names (default: input/companies.csv)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='data/cnpj_results.csv',
        help='Path to output CSV file for results (default: data/cnpj_results.csv)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose (DEBUG) logging'
    )
    
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume processing, skip already processed companies'
    )
    
    args = parser.parse_args()
    
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("Company CNPJ Scraper")
    logger.info("=" * 60)
    
    if not Path(args.input).exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    
    try:
        logger.info(f"Reading companies from: {args.input}")
        companies = read_companies(args.input)
        
        if not companies:
            logger.error("No companies found in input file")
            sys.exit(1)
        
        logger.info(f"Found {len(companies)} companies to process")
        
        initialize_output_file(args.output)
        logger.info(f"Output will be saved to: {args.output}")
        
        processed_companies = set()
        if args.resume:
            processed_companies = set(read_existing_results(args.output))
            logger.info(f"Resuming: {len(processed_companies)} companies already processed")
        
        total = len(companies)
        skipped = 0
        
        for i, company_name in enumerate(companies, 1):
            if company_name in processed_companies:
                logger.info(f"[{i}/{total}] Skipping (already processed): {company_name}")
                skipped += 1
                continue
            
            logger.info(f"[{i}/{total}] Processing: {company_name}")
            process_company(company_name, args.output)
        
        logger.info("=" * 60)
        logger.info("Processing complete!")
        logger.info(f"Total companies: {total}")
        if skipped > 0:
            logger.info(f"Skipped (already processed): {skipped}")
        logger.info(f"Newly processed: {total - skipped}")
        logger.info(f"Results saved to: {args.output}")
        logger.info("=" * 60)
        
    except KeyboardInterrupt:
        logger.warning("\nProcessing interrupted by user")
        logger.info(f"Partial results saved to: {args.output}")
        sys.exit(130)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
