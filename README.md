# Company CNPJ Scraper

AI agent that searches for Brazilian company CNPJ numbers using SerpAPI and saves them to Google Sheets.

## Overview

This tool reads a list of Brazilian company names from a Google Sheet, uses SerpAPI to find their official CNPJ numbers, and writes the results back to the same Google Sheet. It supports two modes: simple lookup (main CNPJ only) and batch processing (with filiais extraction).

## Features

- 🔍 CNPJ lookup using SerpAPI (Google search results)
- ✅ CNPJ validation using official Brazilian algorithm
- 📊 Google Sheets integration for input/output
- 🏢 Optional filiais (branch) extraction from CNPJ.biz
- 📝 Detailed logging for transparency
- ⏸️ Idempotent processing (skips rows with existing CNPJs)
- 🔒 Secure credential management (secrets folder)

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

**secrets/webshare_proxies.json** (optional, only for filiais extraction)
- Webshare proxy list for CNPJ.biz scraping
```json
{
  "proxies": [
    "http://username:password@host:port"
  ]
}
```

### 3. Run the Scraper

**Simple Mode (Main CNPJ only):**
```bash
python run_cnpj_simple.py
```

**Batch Mode (With filiais extraction):**
```bash
python run_cnpj_batch.py
```

That's it! The results will be written to your Google Sheet.

## Usage

### Simple Mode (Recommended)

Use this mode to get only the main CNPJ for each company:

```bash
python run_cnpj_simple.py
```

This script:
- Reads company names from column A of your Google Sheet
- Uses SerpAPI to find the main CNPJ
- Writes results to columns C-F (cnpj, status, timestamp, notes)
- Skips rows that already have a CNPJ filled
- Does NOT extract filiais (branches)

### Batch Mode (Advanced)

Use this mode to extract filiais and related companies:

```bash
python run_cnpj_batch.py
```

This script:
- Does everything the simple mode does
- Additionally scrapes CNPJ.biz to find all filiais
- Inserts new rows for each filial under the parent company
- Requires Webshare proxies (configured in secrets/webshare_proxies.json)

**Note:** Batch mode may encounter blocking from CNPJ.biz. Use simple mode if you only need main CNPJs.

## Google Sheet Format

Your Google Sheet should have the following columns:

| Column | Name | Description |
|--------|------|-------------|
| A | company_name | Company name to search for |
| B | filial_name | Filial/branch name (filled by batch mode) |
| C | cnpj | CNPJ number in format 00.000.000/0000-00 |
| D | status | Search status (ok, not_found, error) |
| E | timestamp | ISO timestamp of when the search was performed |
| F | notes | Additional notes about the search |

### Input Format

Before running the script, your sheet should look like:

| company_name | filial_name | cnpj | status | timestamp | notes |
|--------------|-------------|------|--------|-----------|-------|
| Agibank | | | | | |
| Nubank | | | | | |
| Banco do Brasil | | | | | |

### Output Format (Simple Mode)

After running `run_cnpj_simple.py`:

| company_name | filial_name | cnpj | status | timestamp | notes |
|--------------|-------------|------|--------|-----------|-------|
| Agibank | | 10.664.513/0001-50 | ok | 2025-11-20T22:30:00Z | Found via SerpAPI knowledge_graph |
| Nubank | | 18.236.120/0001-58 | ok | 2025-11-20T22:30:15Z | Found via SerpAPI organic_results |
| Unknown Company | | | not_found | 2025-11-20T22:30:30Z | No CNPJ found in SerpAPI |

### Output Format (Batch Mode)

After running `run_cnpj_batch.py`, filiais are inserted as new rows:

| company_name | filial_name | cnpj | status | timestamp | notes |
|--------------|-------------|------|--------|-----------|-------|
| Agibank | | 10.664.513/0001-50 | ok | 2025-11-20T22:30:00Z | Found via SerpAPI |
| Agibank | Agibank Filial Porto Alegre | 10.664.513/0002-31 | ok | 2025-11-20T22:30:05Z | Filial from CNPJ.biz |
| Agibank | Agibank Filial São Paulo | 10.664.513/0003-12 | ok | 2025-11-20T22:30:05Z | Filial from CNPJ.biz |

## Project Structure

```
company-cnpj-scraper/
├── run_cnpj_simple.py      # Simple mode: main CNPJ lookup only
├── run_cnpj_batch.py       # Batch mode: with filiais extraction
├── sheets.py               # Google Sheets API wrapper
├── cnpj_lookup.py          # SerpAPI CNPJ lookup logic
├── cnpjbiz_scraper.py      # CNPJ.biz scraper for filiais
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

### Simple Mode (run_cnpj_simple.py)

1. **Read Input**: Opens Google Sheet and reads company names from column A
2. **SerpAPI Search**: For each company, queries SerpAPI with "{company_name} CNPJ"
3. **Extract CNPJ**: Tries to extract CNPJ from:
   - Knowledge graph (legal_identifier field)
   - Organic search results (snippets and titles)
4. **Validate**: Validates extracted CNPJs using regex pattern
5. **Write Results**: Updates columns C-F with CNPJ, status, timestamp, and notes
6. **Skip Existing**: Automatically skips rows that already have a CNPJ

### Batch Mode (run_cnpj_batch.py)

1. **Main CNPJ Lookup**: Same as simple mode (steps 1-6)
2. **Filiais Extraction**: For each found CNPJ:
   - Visits CNPJ.biz using Webshare proxies
   - Scrapes "Ver Todas as Filiais" table
   - Extracts razão social and CNPJ for each filial
3. **Insert Rows**: Inserts new rows below parent company for each filial
4. **Update Sheet**: Writes all filiais to Google Sheet with proper column mapping

## CNPJ Validation

The tool validates CNPJ numbers using the official Brazilian algorithm with check digits. It:

- Accepts both formatted (00.000.000/0000-00) and raw (00000000000000) formats
- Validates the two check digits using the official calculation
- Rejects invalid patterns (all same digits, wrong length, etc.)
- Formats all CNPJs to the standard format: 00.000.000/0000-00

## Limitations

- **SerpAPI Dependency**: Requires a valid SerpAPI key (paid service after free tier)
- **Rate Limits**: SerpAPI has rate limits based on your plan
- **CNPJ.biz Blocking**: Batch mode may be blocked by CNPJ.biz (requires residential proxies)
- **Internet Connection**: Requires stable internet connection
- **Google Sheets API**: Requires proper service account setup and permissions
- **Data Accuracy**: CNPJ data depends on what's indexed by Google search

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

### Batch mode not finding filiais

- CNPJ.biz actively blocks datacenter proxies
- Verify your Webshare proxies are working in `secrets/webshare_proxies.json`
- Consider using residential proxies instead of datacenter proxies
- Use simple mode if you only need main CNPJs

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
