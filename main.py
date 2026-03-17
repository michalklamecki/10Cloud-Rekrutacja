"""
FinServe PoC - Problem 1: Manual Data Entry for Credit Applications

This script reads a credit application PDF, extracts text page-by-page, and
uses a local Ollama model to produce structured JSON payloads per page/client.

How to run:
1) Install dependencies:
   pip install -r requirements.txt

2) Ensure Ollama is installed and running locally.

3) Pull/start a model (example):
   ollama run llama3

4) Run the script with a PDF path:
   python main.py --pdf "/path/to/credit_application.pdf"

Optional:
- Set a model via environment variable:
  export OLLAMA_MODEL="mistral"
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

import pdfplumber
from ollama import chat


# Configurable Ollama model (default can be overridden with OLLAMA_MODEL env var).
MODEL_NAME = os.getenv("OLLAMA_MODEL", "llama3.1:8b")

# Expected output schema for the core banking simulation payload.
TARGET_SCHEMA: dict[str, str] = {
    "first_name": "string",
    "last_name": "string",
    "company_name": "string|null",
    "tax_id": "string",
    "requested_loan_amount": "number",
    "email": "string",
    "phone_number": "string",
}


def extract_pages_from_pdf(pdf_path: str) -> list[dict[str, Any]]:
    """Extract text from each PDF page using pdfplumber.

    Args:
        pdf_path: Absolute or relative path to a PDF file.

    Returns:
        A list of dictionaries, each with:
        - page_number: int
        - text: str

    Raises:
        FileNotFoundError: If file does not exist.
        ValueError: If extracted text is empty.
        RuntimeError: If PDF cannot be read.
    """
    path = Path(pdf_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    try:
        page_entries: list[dict[str, Any]] = []
        with pdfplumber.open(path) as pdf:
            for idx, page in enumerate(pdf.pages, start=1):
                text = (page.extract_text() or "").strip()
                if text:
                    page_entries.append({"page_number": idx, "text": text})
    except Exception as exc:
        raise RuntimeError(f"Failed to read PDF '{pdf_path}': {exc}") from exc

    if not page_entries:
        raise ValueError("No readable text found in the PDF.")

    return page_entries


def extract_data_with_llm(text: str, model: str = MODEL_NAME) -> dict[str, Any]:
    """Extract structured credit application fields from free text via Ollama.

    Uses Ollama JSON mode and strict instructions to return only a valid JSON
    object matching the required schema.

    Args:
        text: Raw text extracted from a credit application PDF.
        model: Ollama model name (e.g., 'llama3', 'mistral').

    Returns:
        Parsed dictionary with extracted fields.

    Raises:
        ValueError: If model returns invalid JSON or required keys are missing.
        RuntimeError: If Ollama call fails.
    """
    system_prompt = (
        "You are an information extraction engine for financial documents. "
        "Return ONLY one valid JSON object, with no markdown, no code fences, "
        "no comments, and no extra keys. "
        "If a field is unknown, use null. "
        "Use this exact schema: "
        '{"first_name": string|null, "last_name": string|null, "company_name": string|null, '
        '"tax_id": string|null, "requested_loan_amount": number|null, "email": string|null, '
        '"phone_number": string|null}'
    )

    user_prompt = (
        "Extract the required fields from the following credit application text.\n\n"
        f"Schema keys required: {list(TARGET_SCHEMA.keys())}\n\n"
        "Document text:\n"
        f"{text}"
    )

    try:
        response = chat(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            format="json",  # Enforces JSON mode in Ollama where supported.
            options={"temperature": 0},
        )
    except Exception as exc:
        raise RuntimeError(f"Ollama request failed: {exc}") from exc

    raw_content = response.get("message", {}).get("content", "").strip()
    if not raw_content:
        raise ValueError("Ollama returned an empty response.")

    try:
        data = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            "Ollama response is not valid JSON. "
            f"Raw response: {raw_content[:300]}"
        ) from exc

    required_keys = set(TARGET_SCHEMA.keys())
    response_keys = set(data.keys()) if isinstance(data, dict) else set()

    if not isinstance(data, dict):
        raise ValueError("Parsed response is not a JSON object.")

    missing = required_keys - response_keys
    if missing:
        raise ValueError(f"Missing required keys in LLM output: {sorted(missing)}")

    # Keep only expected keys (defensive cleanup if model adds extras).
    cleaned = {key: data.get(key) for key in TARGET_SCHEMA.keys()}
    return cleaned


def main() -> None:
    """Orchestrate per-page PDF reading, LLM extraction, and JSON output."""
    parser = argparse.ArgumentParser(
        description="FinServe PoC: Extract credit application data from PDF using Ollama."
    )
    parser.add_argument(
        "--pdf",
        required=True,
        help="Path to the credit application PDF file.",
    )
    parser.add_argument(
        "--model",
        default=MODEL_NAME,
        help="Ollama model name (default: env OLLAMA_MODEL or 'llama3').",
    )

    args = parser.parse_args()

    try:
        pages = extract_pages_from_pdf(args.pdf)
        applications: list[dict[str, Any]] = []

        for page in pages:
            page_number = page["page_number"]
            page_text = page["text"]
            extracted_data = extract_data_with_llm(page_text, model=args.model)
            applications.append({"page_number": page_number, **extracted_data})

        result = {
            "source_pdf": str(Path(args.pdf).name),
            "total_pages_processed": len(applications),
            "applications": applications,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (FileNotFoundError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
