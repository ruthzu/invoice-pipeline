#!/usr/bin/env python3
"""Test extraction against CORD-v2 receipt dataset."""

import argparse
import io
import json
import os
import sys

# Load .env early, but only set HF_TOKEN in environment (not passed to Settings)
from pathlib import Path

env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                if key == "HF_TOKEN":
                    os.environ.setdefault(key, value)

from datasets import load_dataset

from app.core.exceptions import ExtractionError
from app.services.extraction import extract_invoice


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Test invoice extraction against CORD-v2 dataset receipts."
    )
    parser.add_argument(
        "--index",
        type=int,
        default=0,
        help="Index of the receipt to test (default: 0)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=1,
        help="Number of receipts to process (default: 1)",
    )
    parser.add_argument(
        "--show-image-info",
        action="store_true",
        help="Show image metadata",
    )
    args = parser.parse_args()

    # Check for HF_TOKEN in environment
    hf_token = os.getenv("HF_TOKEN")
    if hf_token:
        print("Using HF_TOKEN from environment", file=sys.stderr)
    else:
        print(
            "Warning: HF_TOKEN not set (slower downloads, rate limits)", file=sys.stderr
        )

    print("Loading CORD-v2 dataset...", file=sys.stderr)
    dataset = load_dataset(
        "naver-clova-ix/cord-v2",
        split="train",
        token=hf_token,
    )
    print(f"Dataset loaded: {len(dataset)} receipts total\n", file=sys.stderr)

    if args.index >= len(dataset):
        print(
            f"Error: index {args.index} out of range "
            f"(dataset has {len(dataset)} items)",
            file=sys.stderr,
        )
        return 1

    end_index = min(args.index + args.limit, len(dataset))
    success_count = 0
    error_count = 0

    for idx in range(args.index, end_index):
        item = dataset[idx]
        print(f"\n{'=' * 60}", file=sys.stderr)
        print(f"Processing receipt {idx}...", file=sys.stderr)

        if args.show_image_info:
            image = item["image"]
            print(f"  Image format: {image.format}", file=sys.stderr)
            print(f"  Image size: {image.size}", file=sys.stderr)
            print(f"  Image mode: {image.mode}", file=sys.stderr)

        # Convert PIL image to bytes
        image = item["image"]
        img_buffer = io.BytesIO()
        image.save(img_buffer, format="PNG")
        file_bytes = img_buffer.getvalue()

        try:
            result = extract_invoice(file_bytes, "image/png")
            print(f"✓ Receipt {idx} extracted successfully", file=sys.stderr)
            print(f"\n--- Receipt {idx} Extraction ---")
            print(json.dumps(result.model_dump(), indent=2))
            success_count += 1
        except ExtractionError as exc:
            print(f"✗ Receipt {idx} extraction failed: {exc}", file=sys.stderr)
            error_count += 1

    print(f"\n{'=' * 60}", file=sys.stderr)
    print(
        f"Summary: {success_count} succeeded, {error_count} failed",
        file=sys.stderr,
    )

    return 0 if error_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
