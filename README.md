# Company CNPJ Scraper

AI agent that searches for Brazilian company CNPJ numbers and saves them to a CSV file.

## Overview

This tool reads a list of Brazilian company names from a CSV file, searches the web for their official CNPJ numbers, and saves the results to an output CSV file. It prioritizes official sources like Receita Federal (gov.br) and company official websites.

## Features

- 🔍 Web search for company CNPJ numbers
- ✅ CNPJ validation using official Brazilian algorithm
- 📊 CSV input/output for easy data management
- 🎯 Prioritizes official and reliable sources
- 📝 Detailed logging for transparency
- ⏸️ Resume capability to continue interrupted processing
- 🧪 Unit tests for CNPJ validation

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Prepare Input File

Create a CSV file with a `company_name` column. An example is provided in `input/companies.csv`:

```csv
company_name
Petrobras
Vale
Itaú Unibanco
```

### 3. Run the Scraper

```bash
python main.py --input input/companies.csv --output data/cnpj_results.csv
```

That's it! The results will be saved to `data/cnpj_results.csv`.

## Usage

### Basic Usage

```bash
python main.py --input input/companies.csv --output data/cnpj_results.csv
```

### With Verbose Logging

```bash
python main.py --input input/companies.csv --output data/results.csv --verbose
```

### Resume Interrupted Processing

If the script was interrupted, you can resume from where it left off:

```bash
python main.py --input input/companies.csv --output data/results.csv --resume
```

### Command Line Options

- `--input`: Path to input CSV file (default: `input/companies.csv`)
- `--output`: Path to output CSV file (default: `data/cnpj_results.csv`)
- `--verbose`: Enable detailed debug logging
- `--resume`: Skip already processed companies

## Input Format

The input CSV must have a `company_name` column:

```csv
company_name
Company Name 1
Company Name 2
Company Name 3
```

## Output Format

The output CSV contains the following columns:

- `company_input`: Original company name from input
- `company_found_name`: Company name found on source (if available)
- `cnpj`: CNPJ number in format 00.000.000/0000-00
- `source_url`: URL where the CNPJ was found
- `status`: Search status
  - `found`: Single CNPJ found successfully
  - `not_found`: No CNPJ found
  - `ambiguous`: Multiple different CNPJs found
- `created_at`: Timestamp of when the search was performed

Example output:

```csv
company_input,company_found_name,cnpj,source_url,status,created_at
Petrobras,Petrobras,33.000.167/0001-01,https://example.com,found,2025-11-17T20:30:00
Vale,Vale,33.592.510/0001-54,https://example.com,found,2025-11-17T20:30:15
Unknown Company,,,not_found,2025-11-17T20:30:30
```

## Project Structure

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
│   └── test_parser.py     # Unit tests
├── input/
│   └── companies.csv      # Example input file
├── data/
│   └── cnpj_results.csv   # Output file (created when you run)
├── requirements.txt       # Python dependencies
├── README.md             # This file
└── ARCHITECTURE.md       # System design documentation
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

1. **Read Input**: Reads company names from the input CSV file
2. **Search**: For each company, performs a web search with the query "{company_name} CNPJ"
3. **Prioritize**: Filters and prioritizes results from official sources (gov.br, Receita Federal)
4. **Extract**: Fetches page content and extracts CNPJ numbers using regex patterns
5. **Validate**: Validates extracted CNPJs using the official Brazilian algorithm
6. **Save**: Writes results to the output CSV file with status and source information

## CNPJ Validation

The tool validates CNPJ numbers using the official Brazilian algorithm with check digits. It:

- Accepts both formatted (00.000.000/0000-00) and raw (00000000000000) formats
- Validates the two check digits using the official calculation
- Rejects invalid patterns (all same digits, wrong length, etc.)
- Formats all CNPJs to the standard format: 00.000.000/0000-00

## Limitations

- Depends on web search quality and availability
- May encounter rate limits from search engines (includes 1-second delays between requests)
- Requires internet connection
- CNPJ data may be outdated on some websites
- Cannot solve CAPTCHAs (headless scraping only)

## Troubleshooting

### No results found

- Check your internet connection
- Try running with `--verbose` to see detailed logs
- Some companies may not have their CNPJ publicly available online

### Rate limiting

The script includes 1-second delays between requests to be respectful to servers. If you encounter rate limiting:

- Wait a few minutes before running again
- Use `--resume` to continue from where you left off

### Import errors

Make sure all dependencies are installed:

```bash
pip install -r requirements.txt
```

## Contributing

This project was built by an AI agent (Devin). For questions or issues, please contact the repository owner.

## License

This project is provided as-is for educational and research purposes.
