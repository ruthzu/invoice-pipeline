#!/usr/bin/env python3
"""Manual extraction smoke-test script for real invoice documents."""

import argparse
import json
import mimetypes
import sys
from pathlib import Path

from app.core.exceptions import ExtractionError
from app.services.extraction import extract_invoice

MIME_OVERRIDES = {
    ".pdf": "application/pdf",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
}


def resolve_mime_type(path: Path) -> str:
    override = MIME_OVERRIDES.get(path.suffix.lower())
    if override:
        return override
    guessed, _ = mimetypes.guess_type(path.name)
    return guessed or "application/octet-stream"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Extract structured invoice data from a document using Gemini."
    )
    parser.add_argument("file_path", help="Path to a PDF, JPEG, or PNG invoice")
    args = parser.parse_args()

    path = Path(args.file_path)
    if not path.is_file():
        print(f"File not found: {path}", file=sys.stderr)
        return 1

    mime_type = resolve_mime_type(path)
    file_bytes = path.read_bytes()

    try:
        result = extract_invoice(file_bytes, mime_type)
    except ExtractionError as exc:
        print(f"Extraction failed: {exc}", file=sys.stderr)
        return 1

    print(json.dumps(result.model_dump(), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
