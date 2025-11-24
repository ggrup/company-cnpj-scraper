#!/usr/bin/env python3
"""
Batch CNPJ Lookup Script

Processes companies from Google Sheets and fills in CNPJ information.
Uses SerpAPI for main CNPJ lookup and DiretorioBrasil.net (with Webshare proxies) for filiais.

This script now delegates to run_cnpj_simple.py which implements the modern pipeline
with proper anti-blocking measures and proxy rotation.
"""

from run_cnpj_simple import main as simple_main

if __name__ == '__main__':
    print("=" * 60)
    print("Batch CNPJ Lookup Script")
    print("Using SerpAPI + DiretorioBrasil.net with Webshare proxies")
    print("=" * 60)
    simple_main()
