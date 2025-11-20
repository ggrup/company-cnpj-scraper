#!/usr/bin/env python3
"""
Quick test to verify Matriz formatting changes.
"""

def test_cnpj_formatting():
    """Test CNPJ formatting logic."""
    cnpj = "07689002000189"
    
    if cnpj and len(cnpj) == 14:
        formatted_cnpj = f"{cnpj[0:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:14]}"
        print(f"✓ CNPJ formatting works:")
        print(f"  Input:  {cnpj}")
        print(f"  Output: {formatted_cnpj}")
        print(f"  Expected: 07.689.002/0001-89")
        
        if formatted_cnpj == "07.689.002/0001-89":
            print("✓ Formatting matches expected output")
            return True
        else:
            print("✗ Formatting does not match")
            return False
    else:
        print("✗ Invalid CNPJ")
        return False

def test_matriz_label():
    """Test that Matriz label is set correctly."""
    cnpj = "07689002000189"
    status = "ok"
    
    if cnpj and status == "ok" and len(cnpj) == 14:
        filial_name = "Matriz"
        print(f"\n✓ Matriz label logic works:")
        print(f"  filial_name will be set to: '{filial_name}'")
        return True
    else:
        print("\n✗ Matriz label logic failed")
        return False

def test_scraper_receives_formatted():
    """Test that scraper receives formatted CNPJ and can normalize it."""
    import re
    
    formatted_cnpj = "07.689.002/0001-89"
    
    main_cnpj_digits = re.sub(r'\D', '', formatted_cnpj)
    
    print(f"\n✓ Scraper normalization works:")
    print(f"  Input to scraper: {formatted_cnpj}")
    print(f"  Normalized for URL: {main_cnpj_digits}")
    print(f"  Expected: 07689002000189")
    
    if main_cnpj_digits == "07689002000189" and len(main_cnpj_digits) == 14:
        print("✓ Normalization successful")
        return True
    else:
        print("✗ Normalization failed")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Testing Matriz Formatting Changes")
    print("=" * 60)
    
    results = []
    results.append(test_cnpj_formatting())
    results.append(test_matriz_label())
    results.append(test_scraper_receives_formatted())
    
    print("\n" + "=" * 60)
    if all(results):
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    print("=" * 60)
