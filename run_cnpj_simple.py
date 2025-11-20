#!/usr/bin/env python3
"""
Simple CNPJ Lookup Script

Uses SerpAPI to get main CNPJ, then extracts filiais from DiretorioBrasil.net.
"""

import sys
import json
import time
import re
from datetime import datetime
from serpapi import GoogleSearch
from sheets import open_sheet
from scraping.filiais_scraper import scrape_all_filiais, write_filiais_to_sheet


def get_serpapi_key():
    """Load SerpAPI key from secrets/serpapi_key.json"""
    with open("secrets/serpapi_key.json", "r") as f:
        data = json.load(f)
        return data["SERPAPI_KEY"]


def get_main_cnpj(company_name):
    """
    Query SerpAPI to get main CNPJ from knowledge graph or organic results.
    Returns: (cnpj_digits, status, notes)
    """
    api_key = get_serpapi_key()
    
    cnpj_pattern = r"\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}"
    
    for attempt in range(1, 4):
        try:
            print(f"  [SerpAPI] Attempt {attempt}/3: Searching for '{company_name} CNPJ'")
            
            params = {
                "q": f"{company_name} CNPJ",
                "engine": "google",
                "hl": "pt-BR",
                "gl": "br",
                "api_key": api_key
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            if "knowledge_graph" in results and "legal_identifier" in results["knowledge_graph"]:
                legal_id = results["knowledge_graph"]["legal_identifier"]
                print(f"  [SerpAPI] Found legal_identifier: {legal_id}")
                
                digits = re.sub(r"\D", "", legal_id)
                if len(digits) == 14:
                    print(f"  [SerpAPI] ✓ Found main CNPJ: {digits}")
                    return digits, "ok", f"Found via SerpAPI knowledge_graph"
                else:
                    print(f"  [SerpAPI] Invalid CNPJ length: {len(digits)} digits")
            else:
                print(f"  [SerpAPI] No knowledge_graph.legal_identifier found, trying organic_results...")
                
                if "organic_results" in results:
                    for i, result in enumerate(results["organic_results"][:5]):
                        snippet = result.get("snippet", "")
                        title = result.get("title", "")
                        
                        text = f"{title} {snippet}"
                        matches = re.findall(cnpj_pattern, text)
                        
                        if matches:
                            raw_cnpj = matches[0]
                            digits = re.sub(r"\D", "", raw_cnpj)
                            
                            if len(digits) == 14:
                                print(f"  [SerpAPI] ✓ Found CNPJ in organic result #{i+1}: {digits}")
                                return digits, "ok", f"Found via SerpAPI organic_results"
                
                print(f"  [SerpAPI] No CNPJ found in organic results either")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"  [SerpAPI] Error on attempt {attempt}: {e}")
            time.sleep(1)
    
    print(f"  [SerpAPI] ✗ Could not find CNPJ for '{company_name}'")
    return None, "not_found", "No CNPJ found in SerpAPI"


def main():
    """Main entry point for simple CNPJ processing."""
    print("=" * 60)
    print("Simple CNPJ Lookup Script")
    print("Using SerpAPI (main CNPJ only, no filiais)")
    print("=" * 60)
    
    try:
        print("Opening Google Sheet...")
        sheet = open_sheet()
        
        all_values = sheet.get_all_values()
        
        if not all_values:
            print("Error: Sheet is empty")
            sys.exit(1)
        
        header = all_values[0]
        expected_header = ['company_name', 'filial_name', 'cnpj', 'status', 'timestamp', 'notes']
        
        if header != expected_header:
            print(f"Updating header row to 6-column schema...")
            sheet.update(range_name='A1:F1', values=[expected_header])
            print(f"Header updated: {expected_header}")
        
        processed_count = 0
        skipped_count = 0
        
        for i in range(1, len(all_values)):
            row_num = i + 1
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
            
            print(f"\nProcessing row {row_num}: {company_name}")
            
            cnpj, status, notes = get_main_cnpj(company_name)
            
            timestamp = datetime.utcnow().isoformat() + 'Z'
            
            if cnpj and status == "ok" and len(cnpj) == 14:
                formatted_cnpj = f"{cnpj[0:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:14]}"
                sheet.update(range_name=f'B{row_num}', values=[['Matriz']])
                sheet.update(range_name=f'C{row_num}:F{row_num}', 
                           values=[[formatted_cnpj, status, timestamp, notes]])
            else:
                sheet.update(range_name=f'B{row_num}', values=[['']])
                sheet.update(range_name=f'C{row_num}:F{row_num}', 
                           values=[[cnpj or '', status, timestamp, notes]])
            
            processed_count += 1
            print(f"  [Sheet] Updated row {row_num}")
            
            if cnpj and status == "ok" and len(cnpj) == 14:
                try:
                    formatted_cnpj = f"{cnpj[0:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:14]}"
                    
                    print(f"\n  [Filiais] Scraping DiretorioBrasil for filiais...")
                    filial_entries = scrape_all_filiais(company_name, formatted_cnpj)
                    
                    if filial_entries:
                        write_filiais_to_sheet(sheet, company_name, filial_entries)
                    else:
                        print(f"  [Filiais] No filiais found on DiretorioBrasil")
                        
                except Exception as e:
                    print(f"  [Filiais] Error scraping filiais: {e}")
                    import traceback
                    traceback.print_exc()
            
            print()
        
        print("=" * 60)
        print("Processing complete!")
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
