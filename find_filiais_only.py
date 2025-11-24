#!/usr/bin/env python3
"""
Script to find and add filiais (branches) for existing CNPJs in the sheet.
This only processes rows that have a CNPJ but haven't had their filiais processed yet.
Uses DiretorioBrasil.net with Webshare proxies for reliable filiais extraction.
"""

import sys
from datetime import datetime
from sheets import open_sheet
from scraping.filiais_scraper import scrape_all_filiais, write_filiais_to_sheet

def main():
    print("=" * 60)
    print("CNPJ Filiais Finder")
    print("=" * 60)
    print("Debug: Starting script...")
    
    try:
        print("Opening Google Sheet...")
        sheet = open_sheet()
        all_values = sheet.get_all_values()
        
        if not all_values:
            print("Error: Sheet is empty")
            sys.exit(1)
            
        print(f"Debug: Found {len(all_values)} rows in the sheet (including header)")
        
        header = all_values[0]
        expected_header = ['company_name', 'filial_name', 'cnpj', 'status', 'timestamp', 'notes']
        
        if header != expected_header:
            print(f"Warning: Header row doesn't match expected format")
            print(f"Expected: {expected_header}")
            print(f"Found: {header}")
            print("Proceeding anyway...")
        
        processed_count = 0
        skipped_count = 0
        
        # Get all existing CNPJs to avoid duplicates
        existing_cnpjs = set()
        for row in all_values[1:]:  # Skip header
            if len(row) > 2 and row[2].strip():  # If CNPJ exists
                existing_cnpjs.add(row[2].strip().replace('.', '').replace('/', '').replace('-', ''))
        
        print(f"Found {len(existing_cnpjs)} unique CNPJs in the sheet")
        
        # Process each row
        for i in range(1, len(all_values)):
            row_num = i + 1  # Sheet row number (1-indexed)
            row = all_values[i]
            
            while len(row) < 6:
                row.append('')
            
            company_name = row[0].strip() if row[0] else ''
            cnpj = row[2].strip() if len(row) > 2 and row[2] else ''
            
            print(f"\nChecking row {row_num}:")
            print(f"  Company: '{company_name}'")
            print(f"  CNPJ: '{cnpj}'")
            
            if not cnpj:
                print("  -> Skipping: No CNPJ found")
                skipped_count += 1
                continue
                
            # Check if this is a parent company (not a filial)
            is_parent = True
            for other_row in all_values[1:]:
                if len(other_row) > 2 and other_row[2] == cnpj and other_row[1] not in ['', 'Matriz']:
                    is_parent = False
                    break
            
            if not is_parent:
                print("  -> Skipping: This appears to be a filial, not a parent company")
                skipped_count += 1
                continue
                
            # Check if filiais have already been processed by looking at the filial_name column
            has_filiais = any(
                other_row[0] == company_name and  # Same company
                other_row[1] not in ['', 'Matriz'] and  # Has a filial name
                other_row[2] != cnpj  # Different CNPJ
                for other_row in all_values[1:]  # Check all other rows
                if len(other_row) > 2  # Ensure row has enough columns
            )
            
            if has_filiais:
                print("  -> Skipping: Filiais already processed for this CNPJ")
                skipped_count += 1
                continue
                
            print(f"\nProcessing filiais for {company_name} (CNPJ: {cnpj})")
            
            try:
                # Scrape filiais using DiretorioBrasil.net with Webshare proxies
                print(f"  Scraping DiretorioBrasil.net for filiais...")
                filial_entries = scrape_all_filiais(company_name, cnpj)
                
                if filial_entries:
                    print(f"  Found {len(filial_entries)} filiais on DiretorioBrasil.net")
                    
                    # Add filiais to sheet using the dedicated writer
                    rows_inserted = write_filiais_to_sheet(sheet, company_name, filial_entries, insert_after_row=row_num)
                    
                    if rows_inserted > 0:
                        processed_count += 1
                        print(f"  Added {rows_inserted} filiais for {company_name}")
                        
                        # Update existing_cnpjs set with new CNPJs
                        for entry in filial_entries:
                            clean = entry['cnpj'].replace('.', '').replace('/', '').replace('-', '')
                            existing_cnpjs.add(clean)
                    else:
                        print("  No new filiais to add (all duplicates)")
                        skipped_count += 1
                else:
                    print(f"  No filiais found for {company_name}")
                    skipped_count += 1
                    
            except Exception as e:
                print(f"  Error processing {company_name}: {e}")
                import traceback
                traceback.print_exc()
                continue
        
        print("\n" + "=" * 60)
        print("Processing complete!")
        print(f"Total rows in sheet: {len(all_values)-1}")
        print(f"Total companies processed: {processed_count}")
        print(f"Total companies skipped: {skipped_count}")
        print("=" * 60)
        
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
