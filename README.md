# Company CNPJ Scraper

AI agent that searches for Brazilian company CNPJ numbers using SerpAPI and extracts all branch offices (filiais) from DiretorioBrasil.net, saving results to Google Sheets.

## Overview

This tool reads a list of Brazilian company names from a Google Sheet, uses SerpAPI to find their official CNPJ numbers, then automatically extracts all filiais (branch offices) from DiretorioBrasil.net. All results are written back to the same Google Sheet with proper organization and formatting.

## Features

- 🔍 **Main CNPJ lookup** using SerpAPI (Google search results)
- 🏢 **Automatic filiais extraction** from DiretorioBrasil.net with anti-blocking measures
- 📊 **Google Sheets integration** for input/output with real-time updates
- 🎯 **Smart organization** - filiais grouped immediately below their Matriz (headquarters)
- ✅ **CNPJ validation** using official Brazilian algorithm
- 🔄 **CNPJ formatting** - displays CNPJs in standard Brazilian format (XX.XXX.XXX/XXXX-XX)
- 🛡️ **Anti-blocking protection** - rotating proxies, randomized headers, retry logic
- 📄 **Pagination support** - extracts filiais across multiple pages
- ⏸️ **Idempotent processing** - skips rows with existing CNPJs
- 🔒 **Secure credential management** - secrets folder for API keys and proxies

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Credentials

Create the following files in the `secrets/` folder:

**secrets/google_credentials.json**
- Google Service Account credentials for Sheets API access
- Download from Google Cloud Console

**secrets/serpapi_key.json**
- Your SerpAPI key for Google search results
```json
{
  "SERPAPI_KEY": "your_serpapi_key_here"
}
```

**secrets/webshare_proxies.json** (required for filiais extraction)
- Webshare proxy list for DiretorioBrasil.net scraping
- Format: one proxy per line in the format `username:password@host:port`
```json
{
  "proxies": [
    "username1:password1@proxy1.webshare.io:9999",
    "username2:password2@proxy2.webshare.io:9999"
  ]
}
```

### 3. Run the Scraper

**Recommended: Simple Mode (Main CNPJ + Filiais):**
```bash
python run_cnpj_simple.py
```

This will:
- Find the main CNPJ for each company using SerpAPI
- Automatically extract all filiais from DiretorioBrasil.net
- Write results to your Google Sheet with proper formatting and organization

That's it! The results will be written to your Google Sheet.

## Usage

### Main Script (Recommended)

```bash
python run_cnpj_simple.py
```

This script performs a complete CNPJ lookup with filiais extraction:

**What it does:**
1. Reads company names from column A of your Google Sheet
2. Uses SerpAPI to find the main CNPJ for each company
3. Writes the Matriz (headquarters) row with:
   - Column B: "Matriz" label
   - Column C: Formatted CNPJ (XX.XXX.XXX/XXXX-XX)
   - Columns D-F: Status, timestamp, notes
4. Automatically scrapes DiretorioBrasil.net for all filiais
5. Inserts filial rows immediately below the Matriz row
6. Skips rows that already have a CNPJ filled (idempotent)

**Features:**
- ✅ Anti-blocking measures (rotating proxies, randomized headers, delays)
- ✅ Pagination support (extracts filiais across multiple pages)
- ✅ Duplicate detection (won't insert the same CNPJ twice)
- ✅ Smart organization (all CNPJs for each company grouped together)

### Legacy Batch Mode

```bash
python run_cnpj_batch.py
```

This is the older batch processing script. Use `run_cnpj_simple.py` instead for better results.

## Google Sheet Format

Your Google Sheet should have the following columns:

| Column | Name | Description |
|--------|------|-------------|
| A | company_name | Company name to search for (INPUT) |
| B | filial_name | "Matriz" for headquarters, "Filial" for branches (OUTPUT) |
| C | cnpj | CNPJ number in format XX.XXX.XXX/XXXX-XX (OUTPUT) |
| D | status | Search status: "ok", "not_found", "error" (OUTPUT) |
| E | timestamp | ISO timestamp of when the search was performed (OUTPUT) |
| F | notes | Source and additional details (OUTPUT) |

### Input Format

Before running the script, your sheet should look like:

| company_name | filial_name | cnpj | status | timestamp | notes |
|--------------|-------------|------|--------|-----------|-------|
| Agibank | | | | | |
| Nubank | | | | | |
| Banco do Brasil | | | | | |

### Output Format

After running `run_cnpj_simple.py`, your sheet will be organized with Matriz and filiais grouped together:

| company_name | filial_name | cnpj | status | timestamp | notes |
|--------------|-------------|------|--------|-----------|-------|
| Embraer S.A. | Matriz | 07.689.002/0001-89 | ok | 2025-11-20T22:30:00Z | Found via SerpAPI knowledge_graph |
| Embraer S.A. | Filial | 07.689.002/0002-70 | ok | 2025-11-20T22:30:05Z | DiretorioBrasil.net |
| Embraer S.A. | Filial | 07.689.002/0003-51 | ok | 2025-11-20T22:30:05Z | DiretorioBrasil.net |
| Embraer S.A. | Filial | 07.689.002/0004-32 | ok | 2025-11-20T22:30:05Z | DiretorioBrasil.net |
| Petrobras | Matriz | 33.000.167/0001-01 | ok | 2025-11-20T22:31:00Z | Found via SerpAPI knowledge_graph |
| Petrobras | Filial | 33.000.167/0002-92 | ok | 2025-11-20T22:31:05Z | DiretorioBrasil.net |
| Unknown Company | | | not_found | 2025-11-20T22:32:00Z | No CNPJ found in SerpAPI |

**Key features:**
- **Matriz rows** have "Matriz" in column B and formatted CNPJ in column C
- **Filial rows** are inserted immediately below their Matriz
- **All CNPJs** for each company are grouped together
- **Failed lookups** have empty CNPJ and filial_name columns

## Project Structure

```
company-cnpj-scraper/
├── run_cnpj_simple.py      # Main script: CNPJ lookup + filiais extraction
├── run_cnpj_batch.py       # Legacy batch mode script
├── sheets.py               # Google Sheets API wrapper
├── scraping/               # Scraping modules
│   ├── __init__.py
│   └── filiais_scraper.py  # DiretorioBrasil.net filiais scraper
├── secrets/                # Credentials (gitignored)
│   ├── google_credentials.json
│   ├── serpapi_key.json
│   └── webshare_proxies.json
├── scraper/                # Legacy scraper modules
│   ├── search.py
│   └── parser.py
├── storage/                # Legacy CSV writer
│   └── csv_writer.py
├── tests/
│   └── test_parser.py      # Unit tests
├── requirements.txt        # Python dependencies
├── README.md              # This file
└── ARCHITECTURE.md        # System design documentation
```

## Running Tests

Run the unit tests to verify the CNPJ parser:

```bash
pytest tests/
```

Run tests with coverage:

```bash
pytest tests/ --cov=scraper --cov-report=html
```

## How It Works

### Main Workflow (run_cnpj_simple.py)

**Phase 1: Main CNPJ Lookup**
1. Opens Google Sheet and reads company names from column A
2. For each company without a CNPJ:
   - Queries SerpAPI with "{company_name} CNPJ"
   - Extracts CNPJ from knowledge graph or organic results
   - Validates CNPJ format (14 digits)
   - Formats CNPJ to Brazilian standard (XX.XXX.XXX/XXXX-XX)
3. Writes Matriz row with:
   - Column B: "Matriz"
   - Column C: Formatted CNPJ
   - Columns D-F: Status, timestamp, notes

**Phase 2: Filiais Extraction**
1. For each successfully found CNPJ:
   - Builds DiretorioBrasil.net URL using company name slug and CNPJ
   - Scrapes filiais page with anti-blocking measures:
     * Rotating Webshare proxies
     * Randomized User-Agent headers
     * Random delays (1.5-4.5 seconds)
     * Retry logic (5 attempts per request)
   - Parses HTML to extract filial names and CNPJs
   - Detects and follows pagination links
2. Inserts filial rows immediately below Matriz row
3. Updates row offset tracking to maintain correct positioning

**Phase 3: Organization**
- All CNPJs for each company are grouped together
- Matriz row appears first, followed by all filiais
- Subsequent companies are positioned correctly after insertions

### Anti-Blocking Measures

The scraper implements comprehensive anti-blocking protection:
- **Proxy Rotation**: Automatically rotates through Webshare proxies on failures
- **Randomized Headers**: User-Agent, Accept-Language, Referer headers
- **Request Delays**: Random delays between 1.5-4.5 seconds
- **Retry Logic**: Up to 5 attempts per request with proxy rotation
- **Error Handling**: Graceful handling of 403, 422, 423, 429, 5xx errors

## CNPJ Validation

The tool validates CNPJ numbers using the official Brazilian algorithm with check digits. It:

- Accepts both formatted (00.000.000/0000-00) and raw (00000000000000) formats
- Validates the two check digits using the official calculation
- Rejects invalid patterns (all same digits, wrong length, etc.)
- Formats all CNPJs to the standard format: 00.000.000/0000-00

## Limitations

- **SerpAPI Dependency**: Requires a valid SerpAPI key (paid service after free tier)
- **Rate Limits**: SerpAPI has rate limits based on your plan
- **Proxy Requirement**: DiretorioBrasil.net scraping requires Webshare proxies
- **Internet Connection**: Requires stable internet connection
- **Google Sheets API**: Requires proper service account setup and permissions
- **Data Accuracy**: CNPJ data depends on what's indexed by Google and DiretorioBrasil.net
- **Processing Time**: Filiais extraction adds ~2-5 seconds per company (due to anti-blocking delays)

## Troubleshooting

### "No CNPJ found in SerpAPI"

- Check that your SerpAPI key is valid in `secrets/serpapi_key.json`
- Verify the company name is spelled correctly in the Google Sheet
- Some companies may not have their CNPJ indexed by Google
- Try searching manually on Google to verify the CNPJ exists online

### "Permission denied" or Google Sheets errors

- Verify `secrets/google_credentials.json` is valid
- Check that the service account has edit access to your Google Sheet
- Ensure the sheet ID in `sheets.py` matches your sheet

### Filiais not being extracted

- DiretorioBrasil.net may block requests without proper proxies
- Verify your Webshare proxies are configured in `secrets/webshare_proxies.json`
- Check proxy format: `username:password@host:port` (one per line in JSON array)
- Ensure proxies are active and not rate-limited
- Check the console output for specific error messages

### Import errors

Make sure all dependencies are installed:

```bash
pip install -r requirements.txt
```

### SerpAPI rate limit exceeded

- Check your SerpAPI plan limits at https://serpapi.com/dashboard
- Wait for your rate limit to reset
- The script will automatically skip rows with existing CNPJs on re-run

## Contributing

This project was built by an AI agent (Devin). For questions or issues, please contact the repository owner.

## License

This project is provided as-is for educational and research purposes.
