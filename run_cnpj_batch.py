#!/usr/bin/env python3
"""
Batch CNPJ Lookup Script

Processes companies from Google Sheets and fills in CNPJ information.
Uses existing CNPJ lookup logic from the scraper modules.
"""

import sys
from datetime import datetime
from sheets import open_sheet
from scraper.search import search_and_extract_cnpj
from scraper.parser import find_all_valid_cnpjs


def process_row(row_num, company_name):
    """
    Process a single company and return the results.
    
    Args:
        row_num: Row number in the sheet
        company_name: Name of the company to look up
        
    Returns:
        dict with keys: website, cnpj, status, timestamp, notes
    """
    print(f"Processing row {row_num}: {company_name}")
    
    try:
        search_results = search_and_extract_cnpj(company_name, find_all_valid_cnpjs)
        
        cnpjs = search_results['cnpjs']
        sources = search_results['sources']
        
        result = {
            'website': '',
            'cnpj': '',
            'status': 'not_found',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'notes': ''
        }
        
        if len(cnpjs) == 0:
            result['status'] = 'not_found'
            result['notes'] = 'No CNPJ found in search results'
            print(f"  Could not find CNPJ for {company_name}, marking as not_found")
            
        elif len(cnpjs) == 1:
            result['cnpj'] = cnpjs[0]
            result['website'] = sources[0] if sources else ''
            result['status'] = 'success'
            result['notes'] = 'CNPJ found successfully'
            print(f"  Found CNPJ: {cnpjs[0]}")
            
        else:
            result['cnpj'] = cnpjs[0]  # Use first one
            result['website'] = sources[0] if sources else ''
            result['status'] = 'ambiguous'
            result['notes'] = f'Multiple CNPJs found: {", ".join(cnpjs)}. Using first one.'
            print(f"  Found multiple CNPJs for {company_name}: {cnpjs}. Using first: {cnpjs[0]}")
        
        return result
        
    except Exception as e:
        print(f"  Error processing {company_name}: {e}")
        return {
            'website': '',
            'cnpj': '',
            'status': 'error',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'notes': f'Error: {str(e)}'
        }


def main():
    """Main entry point for batch CNPJ processing."""
    print("=" * 60)
    print("Batch CNPJ Lookup Script")
    print("=" * 60)
    
    try:
        print("Opening Google Sheet...")
        sheet = open_sheet()
        
        all_values = sheet.get_all_values()
        
        if not all_values:
            print("Error: Sheet is empty")
            sys.exit(1)
        
        header = all_values[0]
        expected_header = ['company_name', 'website', 'cnpj', 'status', 'timestamp', 'notes']
        
        if header != expected_header:
            print(f"Warning: Header row doesn't match expected format")
            print(f"Expected: {expected_header}")
            print(f"Found: {header}")
            print("Proceeding anyway...")
        
        processed_count = 0
        skipped_count = 0
        
        for i in range(1, len(all_values)):
            row_num = i + 1  # Sheet row number (1-indexed)
            row = all_values[i]
            
            while len(row) < 6:
                row.append('')
            
            company_name = row[0].strip() if row[0] else ''
            existing_cnpj = row[2].strip() if len(row) > 2 and row[2] else ''
            
            if not company_name:
                print(f"Skipping row {row_num}: Empty company name")
                skipped_count += 1
                continue
            
            if existing_cnpj:
                print(f"Skipping row {row_num}: {company_name} (CNPJ already filled)")
                skipped_count += 1
                continue
            
            result = process_row(row_num, company_name)
            
            updates = [
                result['website'],
                result['cnpj'],
                result['status'],
                result['timestamp'],
                result['notes']
            ]
            
            cell_range = f'B{row_num}:F{row_num}'
            sheet.update(cell_range, [updates])
            
            processed_count += 1
            print(f"  Updated row {row_num} in sheet")
            print()
        
        print("=" * 60)
        print("Processing complete!")
        print(f"Total rows processed: {processed_count}")
        print(f"Total rows skipped: {skipped_count}")
        print("=" * 60)
        
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
