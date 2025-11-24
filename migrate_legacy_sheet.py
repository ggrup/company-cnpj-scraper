#!/usr/bin/env python3
"""
One-time migration script to fix legacy sheet data.

This script updates rows that were written by the old run_cnpj_batch.py code
which used column B for "website/source" instead of "filial_name".

It replaces legacy source markers (like "serpapi_organic") with "Matriz" 
for rows that have valid CNPJs and successful status.
"""

from sheets import open_sheet
from datetime import datetime


def migrate_legacy_rows():
    """
    Migrates legacy rows from old schema to new schema.
    
    Old schema: [company_name, website, cnpj, status, timestamp, notes]
    New schema: [company_name, filial_name, cnpj, status, timestamp, notes]
    
    Changes:
    - Column B: "serpapi_organic" → "Matriz" (for successful CNPJ lookups)
    - Column B: other legacy values → "Matriz" (for successful CNPJ lookups)
    - Leaves "Filial" and "Matriz" rows untouched
    """
    print("=" * 60)
    print("Legacy Sheet Migration Script")
    print("=" * 60)
    
    sheet = open_sheet()
    all_values = sheet.get_all_values()
    
    if not all_values:
        print("Error: Sheet is empty")
        return
    
    print(f"Total rows in sheet: {len(all_values)}")
    
    # Find rows with legacy source markers in column B
    legacy_markers = [
        'serpapi_organic',
        'serpapi_knowledge_graph',
        'knowledge_graph',
        'organic_results',
        'none'
    ]
    
    rows_to_update = []
    
    for i, row in enumerate(all_values[1:], start=2):  # Skip header, start at row 2
        if len(row) < 4:
            continue
            
        col_b = row[1].strip() if len(row) > 1 and row[1] else ''
        cnpj = row[2].strip() if len(row) > 2 and row[2] else ''
        status = row[3].strip() if len(row) > 3 and row[3] else ''
        
        # Check if this is a legacy row that needs migration
        if col_b in legacy_markers and cnpj and status in ['success', 'ok']:
            company_name = row[0].strip() if row[0] else ''
            rows_to_update.append((i, company_name, col_b))
    
    if not rows_to_update:
        print("\n✓ No legacy rows found - sheet is already using the new schema!")
        return
    
    print(f"\nFound {len(rows_to_update)} legacy rows to migrate:")
    for row_num, company, old_value in rows_to_update:
        print(f"  Row {row_num}: {company[:50]:<50} | '{old_value}' → 'Matriz'")
    
    # Ask for confirmation
    print(f"\nThis will update column B from legacy source markers to 'Matriz'")
    print("for rows with valid CNPJs and successful status.")
    
    response = input("\nProceed with migration? (yes/no): ").strip().lower()
    
    if response != 'yes':
        print("Migration cancelled.")
        return
    
    # Perform migration
    print("\nMigrating rows...")
    updated_count = 0
    
    for row_num, company, old_value in rows_to_update:
        try:
            # Update column B to "Matriz"
            sheet.update(range_name=f'B{row_num}', values=[['Matriz']])
            updated_count += 1
            print(f"  ✓ Updated row {row_num}: {company[:40]}")
        except Exception as e:
            print(f"  ✗ Error updating row {row_num}: {e}")
    
    print("\n" + "=" * 60)
    print(f"Migration complete!")
    print(f"Successfully updated {updated_count} of {len(rows_to_update)} rows")
    print("=" * 60)


if __name__ == '__main__':
    migrate_legacy_rows()
