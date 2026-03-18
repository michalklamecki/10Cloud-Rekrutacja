# FinServe PoC — Credit Application Data Extraction

![Automation diagram](./Automation%20diagram.png)

This repository contains a small Proof of Concept (PoC) that automates extraction of data from credit application PDFs. The system extracts key fields from application PDFs, normalizes and validates them, and stores structured results in a local SQLite database.

Overview
--------

- Extract raw text from PDF pages using `pdfplumber`.
- Re-structure raw text into JSON using a local LLM (Ollama).
- Save validated and normalized records to a local SQLite database (`finserve.db`).

How it works
------------

1. The script opens the provided PDF and processes it page by page.
2. For each page it extracts raw text using `pdfplumber`.
3. The extracted text is sent to a local LLM (via Ollama). The model is instructed (via a prompt) to return a compact JSON object containing fields such as `first_name`, `last_name`, `company_name`, `tax_id`, `requested_loan_amount`, `email`, and `phone_number`.
4. The script performs light validation and normalization (trim whitespace, parse amounts to numbers, simple email/phone regex checks, sanitize tax IDs).
5. The normalized record is inserted into the `applications` table together with source PDF name, page number and UTC timestamp.

## Database schema

Table `applications`:

- `id` INTEGER PRIMARY KEY
- `source_pdf` TEXT — source PDF filename
- `page_number` INTEGER — page number within PDF
- `first_name` TEXT
- `last_name` TEXT
- `company_name` TEXT
- `tax_id` TEXT
- `requested_loan_amount` REAL
- `email` TEXT
- `phone_number` TEXT
- `created_at` TEXT — UTC timestamp

Prerequisites
-------------

- Python 3.8+
- Ollama (local server/model)
- Dependencies installed from `requirements.txt` (for example `pdfplumber`, an HTTP client for Ollama, etc.)

Installation
------------

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Ensure Ollama is running and the desired model is available:

```bash
ollama serve
ollama pull llama3.1:8b
```

Running the script
------------------

Basic usage (from project directory):

```bash
python main.py --pdf "path/to/application.pdf"
```

Typical options (implementation-dependent):

- `--pdf` — path to the PDF file (required)
- `--model` — Ollama model name (default: `llama3.1:8b` or value from `OLLAMA_MODEL` env)
- `--db` — path to SQLite DB file (default: `finserve.db`)

Example with options:

```bash
python main.py --pdf "applications.pdf" --model "llama3.1:8b" --db "data/finserve.db"
```

Environment variables
---------------------

- `OLLAMA_MODEL` — optional, sets default Ollama model.

Example (PowerShell):

```powershell
$env:OLLAMA_MODEL = "llama3.1:8b"
```

Data validation and normalization
---------------------------------

The script typically performs these steps:

- Trim extra whitespace
- Remove formatting characters from `tax_id`
- Parse requested amounts into numeric (`float`) values
- Basic regex checks for `email` and `phone_number`

Troubleshooting
---------------

- Ollama connection error: check that `ollama serve` is running and the model is available (`ollama list`).

Potential improvements
----------------------

- Ingest PDFs directly from email via webhook (automatic pickup of attachments and processing).
- Add a human-in-the-loop system to review and confirm extracted data before final persistence.
- Add comprehensive logging (structured logs, rotation, and error tracking).

ERP integration and business value
---------------------------------

This pipeline can be integrated with an ERP system to automatically feed customer and application data into back-office workflows. By eliminating manual data entry, such integration can save significant amounts of time for staff who currently enter these records by hand and reduce human errors in downstream processes.

Repository files
----------------

- `main.py` — script entrypoint
- `requirements.txt` — Python dependencies
- `README.md` — this file (project description and instructions)
