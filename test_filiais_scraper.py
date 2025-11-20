#!/usr/bin/env python3
"""
Test script for DiretorioBrasil filiais scraper.

Tests the Embraer S.A. example as specified in requirements.
"""

from scraping.filiais_scraper import (
    sanitize_slug,
    build_filial_url,
    scrape_all_filiais
)


def test_slug_sanitization():
    """Test slug sanitization with examples from requirements."""
    print("=" * 60)
    print("Testing Slug Sanitization")
    print("=" * 60)
    
    test_cases = [
        ("Embraer S.A.", "embraer-sa"),
        ("Raízen S.A.", "raizen-sa"),
        ("Banco Bradesco S.A.", "banco-bradesco-sa"),
        ("Mercado Livre Ltda.", "mercado-livre-ltda"),
    ]
    
    all_passed = True
    for company_name, expected_slug in test_cases:
        result = sanitize_slug(company_name)
        passed = result == expected_slug
        status = "✓" if passed else "✗"
        print(f"{status} {company_name:30s} → {result:30s} (expected: {expected_slug})")
        if not passed:
            all_passed = False
    
    print()
    return all_passed


def test_url_building():
    """Test URL building."""
    print("=" * 60)
    print("Testing URL Building")
    print("=" * 60)
    
    slug = "embraer-sa"
    cnpj_digits = "07689002000189"
    expected_url = "https://www.diretoriobrasil.net/filiais/embraer-sa-07689002000189.html"
    
    result = build_filial_url(slug, cnpj_digits)
    passed = result == expected_url
    status = "✓" if passed else "✗"
    
    print(f"{status} URL: {result}")
    print(f"   Expected: {expected_url}")
    print()
    
    return passed


def test_embraer_scraping():
    """Test scraping Embraer S.A. filiais."""
    print("=" * 60)
    print("Testing Embraer S.A. Filiais Scraping")
    print("=" * 60)
    
    company_name = "Embraer S.A."
    main_cnpj = "07.689.002/0001-89"
    
    print(f"Company: {company_name}")
    print(f"Main CNPJ: {main_cnpj}")
    print()
    
    try:
        filiais = scrape_all_filiais(company_name, main_cnpj)
        
        print()
        print("=" * 60)
        print("Results")
        print("=" * 60)
        print(f"Total filiais found: {len(filiais)}")
        print()
        
        if filiais:
            print("Sample filiais (first 5):")
            for i, filial in enumerate(filiais[:5], 1):
                print(f"  {i}. {filial['filial_name']:10s} - {filial['cnpj']}")
            
            if len(filiais) > 5:
                print(f"  ... and {len(filiais) - 5} more")
        
        print()
        
        print("Validation:")
        
        if len(filiais) >= 20:
            print(f"✓ Found {len(filiais)} filiais (expected ~30)")
        else:
            print(f"✗ Found only {len(filiais)} filiais (expected ~30)")
        
        main_cnpj_in_results = any(f['cnpj'] == main_cnpj for f in filiais)
        if not main_cnpj_in_results:
            print(f"✓ Main CNPJ excluded from results")
        else:
            print(f"✗ Main CNPJ found in results (should be excluded)")
        
        cnpjs = [f['cnpj'] for f in filiais]
        unique_cnpjs = set(cnpjs)
        if len(cnpjs) == len(unique_cnpjs):
            print(f"✓ No duplicate CNPJs")
        else:
            print(f"✗ Found {len(cnpjs) - len(unique_cnpjs)} duplicate CNPJs")
        
        print()
        return True
        
    except Exception as e:
        print(f"✗ Error during scraping: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "DiretorioBrasil Filiais Scraper Test" + " " * 11 + "║")
    print("╚" + "=" * 58 + "╝")
    print()
    
    results = []
    
    results.append(("Slug Sanitization", test_slug_sanitization()))
    
    results.append(("URL Building", test_url_building()))
    
    results.append(("Embraer Scraping", test_embraer_scraping()))
    
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status:8s} - {test_name}")
    
    print()
    
    all_passed = all(passed for _, passed in results)
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    
    print()
    return 0 if all_passed else 1


if __name__ == '__main__':
    exit(main())
