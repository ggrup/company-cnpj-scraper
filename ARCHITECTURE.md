# Architecture - Company CNPJ Scraper

## Overview

This project implements a Python-based scraper that finds Brazilian company CNPJ numbers using SerpAPI and automatically extracts all filiais (branch offices) from DiretorioBrasil.net. Results are written to Google Sheets with proper organization and formatting.

## System Design

### High-Level Flow

```
Google Sheet Input → SerpAPI Lookup → DiretorioBrasil Scraping → Google Sheet Output
       ↓                    ↓                      ↓                        ↓
  Company Names      Main CNPJ (Matriz)    All Filiais (Branches)    Organized Results
```

### Component Architecture

#### 1. Main Entry Point (`run_cnpj_simple.py`)

**Purpose**: Orchestrates the complete CNPJ lookup and filiais extraction workflow

**Key Functions**:
- `get_serpapi_key()` → str: Loads SerpAPI key from secrets
- `get_main_cnpj(company_name)` → Tuple[str, str, str]: Queries SerpAPI for main CNPJ
- `main()`: Main orchestration loop with row offset tracking

**Workflow**:
1. Opens Google Sheet and validates header
2. Iterates through companies (skips existing CNPJs)
3. For each company:
   - Calls SerpAPI to find main CNPJ
   - Formats CNPJ to Brazilian standard (XX.XXX.XXX/XXXX-XX)
   - Writes Matriz row with "Matriz" label
   - Calls filiais scraper
   - Inserts filial rows immediately below Matriz
   - Updates row offset for subsequent companies

**Row Offset Tracking**:
```python
row_offset = 0  # Tracks cumulative insertions
for i in range(1, len(all_values)):
    row_num = i + 1 + row_offset  # Adjust for inserted rows
    # ... process company ...
    if filiais_found:
        rows_inserted = write_filiais_to_sheet(..., insert_after_row=row_num)
        row_offset += rows_inserted  # Update for next iteration
```

#### 2. Google Sheets Integration (`sheets.py`)

**Purpose**: Handles authentication and I/O with Google Sheets API

**Key Functions**:
- `open_sheet()` → Worksheet: Authenticates and opens the configured sheet
- Uses gspread library with OAuth2 service account credentials

**Authentication**:
- Service account credentials from `secrets/google_credentials.json`
- Requires sheet sharing with service account email

#### 3. Filiais Scraper Module (`scraping/filiais_scraper.py`)

**Purpose**: Comprehensive DiretorioBrasil.net scraper with anti-blocking measures

**Key Functions**:

**`sanitize_slug(company_name: str) → str`**
- Converts company name to URL-safe slug
- Rules:
  - Lowercase everything
  - Remove accents (e.g., "ã" → "a")
  - Remove punctuation
  - Replace spaces with hyphens
  - Normalize "S.A." → "sa", "Ltda." → "ltda"
- Example: "Embraer S.A." → "embraer-sa"

**`build_filial_url(slug: str, cnpj_digits: str) → str`**
- Constructs DiretorioBrasil.net URL
- Format: `https://www.diretoriobrasil.net/filiais/{slug}-{cnpj_digits}.html`
- Example: `https://www.diretoriobrasil.net/filiais/embraer-sa-07689002000189.html`

**`load_proxies() → List[str]`**
- Loads Webshare proxies from `secrets/webshare_proxies.json`
- Fallback to `secrets/webshare_proxy.txt` if JSON not found
- Returns list of proxy strings in format: `http://username:password@host:port`

**`get_next_proxy() → str`**
- Rotates through proxy list
- Returns next proxy in round-robin fashion

**`request_with_proxy_rotation(url: str) → str`**
- Core HTTP request function with anti-blocking measures
- Features:
  - Rotating proxies (automatic on failures)
  - Randomized User-Agent headers (Chrome, Firefox, Safari, Edge, mobile)
  - Randomized Accept-Language headers
  - Randomized Referer headers (Google search)
  - Random delays (1.5-4.5 seconds)
  - Retry logic (5 attempts)
  - Error handling for 403, 422, 423, 429, 5xx errors
- Returns HTML content or raises exception

**`parse_filiais(html: str) → List[Dict[str, str]]`**
- Parses HTML to extract filial entries
- Looks for pattern: "Filial\n{Company Name}\n...\nCNPJ: XX.XXX.XXX/XXXX-XX"
- Returns list of dicts: `[{"filial_name": "Filial", "cnpj": "XX.XXX.XXX/XXXX-XX"}, ...]`
- Uses regex: `\b\d{2}\.\d{3}\.\d{3}\/\d{4}\-\d{2}\b`

**`detect_pagination(html: str) → List[str]`**
- Detects pagination links in HTML
- Looks for: `?pagina=2`, `?pagina=3`, etc.
- Returns list of full URLs for additional pages

**`scrape_all_filiais(company_name: str, main_cnpj: str) → List[Dict[str, str]]`**
- Main orchestration function for filiais extraction
- Workflow:
  1. Sanitize company name to slug
  2. Normalize CNPJ (remove punctuation)
  3. Build initial URL
  4. Scrape first page
  5. Detect pagination
  6. Scrape additional pages
  7. Deduplicate CNPJs
  8. Exclude main CNPJ from results
- Returns list of unique filial entries

**`write_filiais_to_sheet(sheet, company_name: str, filial_entries: List[Dict], insert_after_row: Optional[int]) → int`**
- Writes filiais to Google Sheet
- Features:
  - Duplicate detection (checks existing CNPJs for company)
  - Positioned insertion (uses `sheet.insert_rows()` at specific row)
  - Batch insertion (all rows inserted at once)
  - Returns count of inserted rows for offset tracking
- If `insert_after_row` is None, appends to end (legacy mode)
- If `insert_after_row` is provided, inserts at `row + 1`

#### 4. Legacy Modules

**`scraper/parser.py`**
- CNPJ validation and formatting utilities
- Functions:
  - `validate_cnpj(cnpj: str) → bool`: Official Brazilian checksum algorithm
  - `format_cnpj(cnpj: str) → str`: Formats to XX.XXX.XXX/XXXX-XX
  - `extract_cnpj_from_text(text: str) → List[str]`: Regex extraction
  - `find_all_valid_cnpjs(text: str) → List[str]`: Extract + validate

**`scraper/search.py`** (Legacy)
- Old Google search-based scraper
- Not used in current implementation

**`storage/csv_writer.py`** (Legacy)
- Old CSV-based I/O
- Not used in current implementation

**`run_cnpj_batch.py`** (Alternative Entry Point)
- Delegates to `run_cnpj_simple.py` for unified pipeline
- Uses same SerpAPI + DiretorioBrasil.net architecture
- Use `run_cnpj_simple.py` instead

### Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. INPUT PHASE                                                  │
│    - Read Google Sheet                                          │
│    - Extract company names from column A                        │
│    - Skip rows with existing CNPJs                              │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. SERPAPI LOOKUP PHASE                                         │
│    - Query: "{company_name} CNPJ"                               │
│    - Extract from knowledge_graph.legal_identifier              │
│    - Fallback to organic_results snippets                       │
│    - Validate format (14 digits)                                │
│    - Format to XX.XXX.XXX/XXXX-XX                               │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. MATRIZ WRITE PHASE                                           │
│    - Write to row N:                                            │
│      * Column B: "Matriz"                                       │
│      * Column C: Formatted CNPJ                                 │
│      * Columns D-F: Status, timestamp, notes                    │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. FILIAIS SCRAPING PHASE                                       │
│    - Build DiretorioBrasil.net URL                              │
│    - Scrape with anti-blocking:                                 │
│      * Rotating proxies                                         │
│      * Randomized headers                                       │
│      * Random delays (1.5-4.5s)                                 │
│      * Retry logic (5 attempts)                                 │
│    - Parse HTML for filial entries                              │
│    - Follow pagination links                                    │
│    - Deduplicate CNPJs                                          │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. FILIAIS WRITE PHASE                                          │
│    - Insert rows at position N+1:                               │
│      * Column A: Company name (same as Matriz)                  │
│      * Column B: "Filial"                                       │
│      * Column C: Filial CNPJ                                    │
│      * Columns D-F: "ok", timestamp, "DiretorioBrasil.net"     │
│    - Update row_offset += rows_inserted                         │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. ORGANIZATION PHASE                                           │
│    - All CNPJs for each company grouped together                │
│    - Matriz row first, followed by filiais                      │
│    - Subsequent companies positioned correctly                  │
└─────────────────────────────────────────────────────────────────┘
```

### Technology Stack

- **Python 3.8+**: Core language
- **requests**: HTTP requests for web scraping
- **beautifulsoup4**: HTML parsing
- **lxml**: Fast XML/HTML parser backend
- **gspread**: Google Sheets API client
- **google-auth**: OAuth2 authentication
- **serpapi**: SerpAPI Python client
- **pytest**: Unit testing framework

### Anti-Blocking Strategy

The scraper implements a comprehensive anti-blocking strategy for DiretorioBrasil.net:

1. **Proxy Rotation**
   - Webshare proxy pool
   - Automatic rotation on failures (403, 422, 423, 429, 5xx)
   - Round-robin selection

2. **Header Randomization**
   - User-Agent: Rotates through Chrome, Firefox, Safari, Edge, mobile variants
   - Accept-Language: Randomizes between pt-BR, en-US, es-ES
   - Referer: Simulates Google search traffic

3. **Request Timing**
   - Random delays: 1.5-4.5 seconds between requests
   - Prevents pattern detection

4. **Retry Logic**
   - 5 attempts per request
   - Rotates proxy on each retry
   - Exponential backoff (via delays)

5. **Error Handling**
   - Graceful handling of HTTP errors
   - Logging for debugging
   - Continues processing on failures

### Error Handling

- **Network errors**: Log and mark as "not_found"
- **Parsing errors**: Log and continue to next source
- **Invalid CNPJ**: Skip and try next result
- **Rate limiting**: Automatic retry with proxy rotation
- **Sheet errors**: Log and exit gracefully

### Logging Strategy

- **INFO level**: Progress updates (company X of Y, filiais found)
- **DEBUG level**: URLs, CNPJ candidates, proxy rotation
- **WARNING level**: No results found, blocking detected
- **ERROR level**: Network failures, authentication errors

### Directory Structure

```
company-cnpj-scraper/
├── run_cnpj_simple.py      # Main script: CNPJ lookup + filiais
├── run_cnpj_batch.py       # Alternative entry point (delegates to run_cnpj_simple.py)
├── sheets.py               # Google Sheets API wrapper
├── scraping/               # Scraping modules
│   ├── __init__.py
│   └── filiais_scraper.py  # DiretorioBrasil.net scraper with Webshare proxies
├── secrets/                # Credentials (gitignored)
│   ├── google_credentials.json
│   ├── serpapi_key.json
│   └── webshare_proxies.json
├── scraper/                # CNPJ validation utilities
│   ├── __init__.py
│   ├── search.py          # Search utilities
│   └── parser.py          # CNPJ validation algorithms
├── storage/                # CSV writer utilities
│   ├── __init__.py
│   └── csv_writer.py
├── tests/
│   ├── __init__.py
│   └── test_parser.py     # Unit tests for CNPJ validation
├── requirements.txt       # Python dependencies
├── README.md             # Usage instructions
└── ARCHITECTURE.md       # This file
```

### Performance Considerations

**Processing Time**:
- SerpAPI lookup: ~1-2 seconds per company
- Filiais scraping: ~2-5 seconds per company (due to anti-blocking delays)
- Sheet writes: ~0.5-1 second per operation
- **Total**: ~3-8 seconds per company (depending on number of filiais)

**Optimization Strategies**:
- Batch sheet writes (insert_rows instead of multiple append_row calls)
- Skip companies with existing CNPJs (idempotent)
- Efficient row offset tracking (avoids re-reading sheet)

**Scalability**:
- Current implementation: Sequential processing
- Potential improvement: Parallel processing with thread pool
- Limitation: SerpAPI rate limits, proxy pool size

### Security Considerations

1. **Credentials Management**
   - All secrets in `secrets/` folder (gitignored)
   - Service account for Google Sheets (no user credentials)
   - Proxy credentials in JSON format

2. **Data Privacy**
   - No sensitive data stored locally
   - All data written to Google Sheets (user-controlled)
   - No logging of CNPJ data

3. **Rate Limiting**
   - Respects SerpAPI rate limits
   - Anti-blocking delays prevent IP bans
   - Proxy rotation distributes load

### Future Enhancements

1. **Performance**
   - Parallel processing for multiple companies
   - Caching of SerpAPI results
   - Database backend for historical data

2. **Features**
   - Support for other Brazilian business directories
   - Confidence scoring for CNPJ matches
   - Email notifications on completion
   - Web UI for easier use

3. **Robustness**
   - Automatic proxy health checking
   - Fallback to alternative sources
   - Better error recovery

### Limitations

- **SerpAPI Dependency**: Requires paid API key after free tier
- **Proxy Requirement**: DiretorioBrasil.net scraping requires Webshare proxies
- **Sequential Processing**: No parallel execution (yet)
- **Internet Dependency**: Requires stable connection
- **Data Accuracy**: Depends on source data quality
- **Processing Time**: ~3-8 seconds per company (anti-blocking delays)

### Testing

**Unit Tests** (`tests/test_parser.py`):
- CNPJ validation algorithm
- CNPJ formatting
- CNPJ extraction from text
- Edge cases (invalid formats, duplicates)

**Manual Testing**:
- Test with known companies (e.g., Embraer S.A.)
- Verify sheet organization
- Check filiais extraction
- Validate anti-blocking measures

**Run Tests**:
```bash
pytest tests/
pytest tests/ --cov=scraper --cov-report=html
```

## Conclusion

This architecture provides a robust, production-ready solution for Brazilian CNPJ lookup and filiais extraction. The system balances performance, reliability, and anti-blocking measures to deliver accurate results organized in Google Sheets.
