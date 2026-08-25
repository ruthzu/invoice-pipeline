from unittest.mock import MagicMock, patch

import httpx
import pytest
from google.genai import errors as genai_errors

from app.core.exceptions import ExtractionFailedError, ExtractionRateLimitedError
from app.schemas.invoice_extraction import InvoiceExtraction, LineItem
from app.services.extraction import extract_invoice


def _make_response(
    extraction: InvoiceExtraction | None = None, text: str | None = None
) -> MagicMock:
    response = MagicMock()
    response.parsed = extraction
    response.text = (
        text
        if text is not None
        else (extraction.model_dump_json() if extraction else None)
    )
    return response


def _sample_extraction() -> InvoiceExtraction:
    return InvoiceExtraction(
        vendor_name="Acme Corp",
        invoice_number="INV-001",
        invoice_date="2026-01-15",
        total_amount=150.0,
        line_items=[
            LineItem(description="Widget", quantity=2.0, unit_price=75.0),
        ],
    )


@patch("app.services.extraction.genai.Client")
def test_extract_invoice_success(mock_client_cls):
    mock_client = mock_client_cls.return_value
    expected = _sample_extraction()
    mock_client.models.generate_content.return_value = _make_response(expected)

    result = extract_invoice(b"%PDF-1.4", "application/pdf")

    assert result == expected
    mock_client.models.generate_content.assert_called_once()


@patch("app.services.extraction.time.sleep")
@patch("app.services.extraction.genai.Client")
def test_extract_invoice_retries_transient_server_error(mock_client_cls, mock_sleep):
    mock_client = mock_client_cls.return_value
    expected = _sample_extraction()
    mock_client.models.generate_content.side_effect = [
        genai_errors.ServerError(500, {"error": {"message": "server error"}}, None),
        _make_response(expected),
    ]

    result = extract_invoice(b"%PDF-1.4", "application/pdf")

    assert result == expected
    assert mock_client.models.generate_content.call_count == 2
    mock_sleep.assert_called_once_with(1)


@patch("app.services.extraction.time.sleep")
@patch("app.services.extraction.genai.Client")
def test_extract_invoice_retries_rate_limit(mock_client_cls, mock_sleep):
    mock_client = mock_client_cls.return_value
    expected = _sample_extraction()
    mock_client.models.generate_content.side_effect = [
        genai_errors.ClientError(429, {"error": {"message": "rate limited"}}, None),
        _make_response(expected),
    ]

    result = extract_invoice(b"%PDF-1.4", "application/pdf")

    assert result == expected
    assert mock_client.models.generate_content.call_count == 2
    mock_sleep.assert_called_once_with(1)


@patch("app.services.extraction.time.sleep")
@patch("app.services.extraction.genai.Client")
def test_extract_invoice_exhausts_retries_on_rate_limit(mock_client_cls, mock_sleep):
    mock_client = mock_client_cls.return_value
    rate_limit_error = genai_errors.ClientError(
        429, {"error": {"message": "rate limited"}}, None
    )
    mock_client.models.generate_content.side_effect = [rate_limit_error] * 3

    with pytest.raises(ExtractionRateLimitedError):
        extract_invoice(b"%PDF-1.4", "application/pdf")

    assert mock_client.models.generate_content.call_count == 3
    assert mock_sleep.call_args_list == [((1,),), ((2,),)]


@patch("app.services.extraction.genai.Client")
def test_extract_invoice_does_not_retry_schema_validation_failure(mock_client_cls):
    mock_client = mock_client_cls.return_value
    mock_client.models.generate_content.return_value = _make_response(
        text='{"vendor_name": "Acme", "line_items": [{"description": "x"}]}'
    )

    with pytest.raises(ExtractionFailedError, match="schema validation"):
        extract_invoice(b"%PDF-1.4", "application/pdf")

    mock_client.models.generate_content.assert_called_once()


@patch("app.services.extraction.genai.Client")
def test_extract_invoice_does_not_retry_non_transient_client_error(mock_client_cls):
    mock_client = mock_client_cls.return_value
    mock_client.models.generate_content.side_effect = genai_errors.ClientError(
        400, {"error": {"message": "bad request"}}, None
    )

    with pytest.raises(ExtractionFailedError):
        extract_invoice(b"%PDF-1.4", "application/pdf")

    mock_client.models.generate_content.assert_called_once()


@patch("app.services.extraction.time.sleep")
@patch("app.services.extraction.genai.Client")
def test_extract_invoice_retries_network_error(mock_client_cls, mock_sleep):
    mock_client = mock_client_cls.return_value
    expected = _sample_extraction()
    mock_client.models.generate_content.side_effect = [
        httpx.ConnectError("connection refused"),
        _make_response(expected),
    ]

    result = extract_invoice(b"%PDF-1.4", "application/pdf")

    assert result == expected
    assert mock_client.models.generate_content.call_count == 2
    mock_sleep.assert_called_once_with(1)


@patch("app.services.extraction.genai.Client")
def test_extract_invoice_raises_on_empty_response(mock_client_cls):
    mock_client = mock_client_cls.return_value
    mock_client.models.generate_content.return_value = _make_response(text="")

    with pytest.raises(ExtractionFailedError, match="empty response"):
        extract_invoice(b"%PDF-1.4", "application/pdf")
