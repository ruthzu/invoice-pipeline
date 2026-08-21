import logging
import time

import httpx
from google import genai
from google.genai import errors as genai_errors
from google.genai import types
from pydantic import ValidationError

from app.core.config import settings
from app.core.exceptions import (
    ExtractionError,
    ExtractionFailedError,
    ExtractionRateLimitedError,
)
from app.schemas.invoice_extraction import InvoiceExtraction

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = (
    "Extract structured invoice data from this document. "
    "Return vendor name, invoice number, invoice date, total amount, "
    "and line items. Use null for any field that is not present in the document. "
    "Alongside the extracted values, self-report a confidence level of high, "
    "medium, or low for each top-level field (vendor_name, invoice_number, "
    "invoice_date, total_amount, line_items), based on how certain you are "
    "that the extracted value is correct and present in the document."
)

MAX_ATTEMPTS = 3
BACKOFF_SECONDS = (1, 2)


def _is_transient_error(exc: Exception) -> bool:
    if isinstance(exc, genai_errors.ServerError):
        return True
    if isinstance(exc, genai_errors.ClientError) and exc.code == 429:
        return True
    return isinstance(
        exc,
        (
            httpx.TimeoutException,
            httpx.NetworkError,
            httpx.ConnectError,
            TimeoutError,
            ConnectionError,
            OSError,
        ),
    )


def _raise_typed_error(exc: Exception) -> None:
    logger.error("Extraction failed: %s", exc, exc_info=True)
    if isinstance(exc, genai_errors.ClientError) and exc.code == 429:
        raise ExtractionRateLimitedError(str(exc)) from exc
    raise ExtractionFailedError(str(exc)) from exc


def _parse_response(response: genai.types.GenerateContentResponse) -> InvoiceExtraction:
    if response.parsed is not None:
        if isinstance(response.parsed, InvoiceExtraction):
            return response.parsed
        return InvoiceExtraction.model_validate(response.parsed)

    if not response.text:
        raise ExtractionFailedError("Gemini returned an empty response")

    return InvoiceExtraction.model_validate_json(response.text)


def _call_gemini(
    client: genai.Client, file_bytes: bytes, mime_type: str
) -> InvoiceExtraction:
    response = client.models.generate_content(
        model=settings.llm_model,
        contents=[
            EXTRACTION_PROMPT,
            types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=InvoiceExtraction,
        ),
    )
    return _parse_response(response)


def extract_invoice(file_bytes: bytes, mime_type: str) -> InvoiceExtraction:
    client = genai.Client(api_key=settings.gemini_api_key)
    last_error: Exception | None = None

    for attempt in range(MAX_ATTEMPTS):
        try:
            return _call_gemini(client, file_bytes, mime_type)
        except ValidationError as exc:
            logger.error(
                "Gemini response failed schema validation: %s", exc, exc_info=True
            )
            raise ExtractionFailedError(
                "Gemini response failed schema validation"
            ) from exc
        except ExtractionError:
            raise
        except Exception as exc:
            last_error = exc
            if not _is_transient_error(exc):
                _raise_typed_error(exc)

            logger.warning(
                "Transient extraction error on attempt %s/%s: %s",
                attempt + 1,
                MAX_ATTEMPTS,
                exc,
                exc_info=True,
            )
            if attempt < MAX_ATTEMPTS - 1:
                time.sleep(BACKOFF_SECONDS[attempt])

    assert last_error is not None
    _raise_typed_error(last_error)
    raise AssertionError("unreachable")
