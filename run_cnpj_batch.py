#!/usr/bin/env python3
"""
Batch CNPJ Lookup Script

Processes companies from Google Sheets and fills in CNPJ information.
Uses existing CNPJ lookup logic from the scraper modules.
"""

import sys
from datetime import datetime
from sheets import open_sheet
from cnpj_lookup import lookup_cnpj
from cnpjbiz_scraper import scrape_all_entities


def process_row(row_num, company_name):
    """
    Process a single company and return the results.
    
    Uses Google SERP-based CNPJ lookup.
    
    Args:
        row_num: Row number in the sheet
        company_name: Name of the company to look up
        
    Returns:
        dict with keys: website, cnpj, status, timestamp, notes
    """
    print(f"Processing row {row_num}: {company_name}")
    
    try:
        cnpj, source, debug = lookup_cnpj(company_name)
        
        result = {
            'website': source if source != 'none' else '',
            'cnpj': cnpj if cnpj else '',
            'status': 'success' if cnpj else 'not_found',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'notes': debug
        }
        
        if cnpj:
            print(f"  Found CNPJ: {cnpj}")
        else:
            print(f"  Could not find CNPJ for {company_name}, marking as not_found")
        
        return result
        
    except Exception as e:
        print(f"  Error processing {company_name}: {e}")
        import traceback
        traceback.print_exc()
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
            
            if result['cnpj']:
                print(f"  Scraping CNPJ.biz for related companies...")
                try:
                    all_entities = scrape_all_entities(result['cnpj'])
                    print(f"  Found {len(all_entities)} related entities on CNPJ.biz")
                    
                    timestamp = datetime.utcnow().isoformat() + 'Z'
                    for ent in all_entities:
                        new_row = [
                            company_name,
                            ent["razao_social"],
                            ent["razao_social"],
                            ent["cnpj"],
                            ent["tipo"],
                            timestamp,
                            "cnpj.biz"
                        ]
                        sheet.append_row(new_row)
                        print(f"    Added: {ent['razao_social']} ({ent['cnpj']}) - {ent['tipo']}")
                    
                    print(f"  Inserted {len(all_entities)} related entities")
                except Exception as e:
                    print(f"  Error scraping CNPJ.biz: {e}")
            
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
