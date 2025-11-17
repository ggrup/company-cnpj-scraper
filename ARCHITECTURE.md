# Architecture - Company CNPJ Scraper

## Overview

This project implements a Python-based scraper that finds Brazilian company CNPJ numbers by searching the web and parsing results from reliable sources.

## System Design

### High-Level Flow

```
Input CSV → Read Companies → Search Web → Parse CNPJ → Validate → Save to CSV
```

### Component Architecture

#### 1. Main Entry Point (`main.py`)
- Command-line interface using `argparse`
- Orchestrates the entire workflow
- Handles logging configuration
- Arguments:
  - `--input`: Path to input CSV file (default: `input/companies.csv`)
  - `--output`: Path to output CSV file (default: `data/cnpj_results.csv`)

#### 2. Scraper Module (`scraper/`)

**`scraper/search.py`**
- Responsible for web search and HTML fetching
- Uses requests library for HTTP calls
- Implements search strategies:
  - Google search (via requests + HTML parsing)
  - Fallback to direct site searches if needed
- Functions:
  - `search_company_cnpj(company_name: str) -> List[SearchResult]`
  - `fetch_page_content(url: str) -> str`
- Prioritizes official sources:
  - Receita Federal (gov.br domains)
  - Company official websites
  - Reliable business directories

**`scraper/parser.py`**
- Extracts and validates CNPJ from HTML content
- Functions:
  - `extract_cnpj_from_text(text: str) -> List[str]`
  - `validate_cnpj(cnpj: str) -> bool`
  - `format_cnpj(cnpj: str) -> str` (ensures 00.000.000/0000-00 format)
- Uses regex patterns to find CNPJ numbers
- Validates CNPJ checksum digits (Brazilian algorithm)

#### 3. Storage Module (`storage/`)

**`storage/csv_writer.py`**
- Handles reading input CSV and writing output CSV
- Functions:
  - `read_companies(filepath: str) -> List[str]`
  - `write_result(filepath: str, result: CompanyResult)`
  - `append_result(filepath: str, result: CompanyResult)`
- Data structure for results:
  ```python
  CompanyResult:
    - company_input: str
    - company_found_name: str
    - cnpj: str
    - source_url: str
    - status: str (found/not_found/ambiguous)
    - created_at: datetime
  ```

### Data Flow

1. **Input Phase**
   - Read `input/companies.csv`
   - Extract company names from `company_name` column

2. **Search Phase**
   - For each company:
     - Construct search query: "{company_name} CNPJ"
     - Fetch search results
     - Filter for reliable sources
     - Extract top 3-5 URLs

3. **Extraction Phase**
   - For each URL:
     - Fetch page content
     - Parse HTML/text for CNPJ patterns
     - Validate CNPJ format and checksum
     - Extract company name if available

4. **Decision Phase**
   - If single valid CNPJ found: status = "found"
   - If no CNPJ found: status = "not_found"
   - If multiple different CNPJs: status = "ambiguous"

5. **Output Phase**
   - Write result to `data/cnpj_results.csv`
   - Include timestamp and source URL

### Technology Stack

- **Python 3.8+**: Core language
- **requests**: HTTP requests
- **beautifulsoup4**: HTML parsing
- **pandas**: CSV handling (optional, can use csv module)
- **pytest**: Unit testing
- **logging**: Built-in Python logging

### Error Handling

- Network errors: Log and mark as "not_found"
- Parsing errors: Log and continue to next source
- Invalid CNPJ: Skip and try next result
- Rate limiting: Add delays between requests (1-2 seconds)

### Logging Strategy

- INFO level: Progress updates (company X of Y)
- DEBUG level: Search URLs, CNPJ candidates found
- WARNING level: No results found, ambiguous results
- ERROR level: Network failures, file I/O errors

### Directory Structure

```
company-cnpj-scraper/
├── main.py                 # CLI entry point
├── scraper/
│   ├── __init__.py
│   ├── search.py          # Web search logic
│   └── parser.py          # CNPJ extraction & validation
├── storage/
│   ├── __init__.py
│   └── csv_writer.py      # CSV I/O operations
├── tests/
│   ├── __init__.py
│   └── test_parser.py     # Unit tests for CNPJ parser
├── input/
│   └── companies.csv      # Example input file
├── data/
│   └── .gitkeep           # Output directory
├── requirements.txt       # Python dependencies
├── README.md             # Usage instructions
└── ARCHITECTURE.md       # This file
```

### Future Enhancements (Post-V1)

- Add support for search APIs (SerpAPI, Google Custom Search)
- Implement caching to avoid re-searching
- Add database support (SQLite, PostgreSQL)
- Parallel processing for faster execution
- Web UI for easier use
- Confidence scoring for results
- Support for other Brazilian company identifiers

### Limitations

- Dependent on web search quality
- May hit rate limits on search engines
- Requires internet connection
- CNPJ data may be outdated on some sites
- Cannot solve CAPTCHAs (headless only)
