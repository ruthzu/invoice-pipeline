import tempfile
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.core.config import settings
from app.core.exceptions import ExtractionFailedError, ExtractionRateLimitedError
from app.db.models.invoice import Invoice, InvoiceStatus
from app.db.session import Base
from app.schemas.invoice_extraction import InvoiceExtraction, LineItem
from app.worker import process_invoice
from tests.conftest import TestingSessionLocal, engine


@pytest.fixture(scope="function")
def worker_setup():
    Base.metadata.create_all(bind=engine)

    with tempfile.TemporaryDirectory() as temp_dir:
        original_storage_dir = settings.storage_dir
        settings.storage_dir = temp_dir
        yield temp_dir
        settings.storage_dir = original_storage_dir

    Base.metadata.drop_all(bind=engine)


def _create_invoice(
    db,
    *,
    status: InvoiceStatus = InvoiceStatus.QUEUED,
    storage_path: str | None = None,
    write_file: bool = True,
    temp_dir: str,
) -> Invoice:
    invoice_id = uuid4()
    filename = f"{invoice_id}.pdf"
    path = storage_path or filename

    if write_file:
        file_path = Path(temp_dir) / path
        file_path.write_bytes(b"%PDF-1.4\n")

    invoice = Invoice(
        id=invoice_id,
        original_filename="test.pdf",
        storage_path=path,
        mime_type="application/pdf",
        status=status,
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


@patch("app.worker.extract_invoice")
@patch("app.worker.SessionLocal", TestingSessionLocal)
def test_process_invoice_success(mock_extract, worker_setup):
    temp_dir = worker_setup
    db = TestingSessionLocal()
    invoice = _create_invoice(db, temp_dir=temp_dir)
    invoice_id = str(invoice.id)
    db.close()

    mock_extract.return_value = InvoiceExtraction(
        vendor_name="Acme Corp",
        invoice_number="INV-001",
        line_items=[LineItem(description="Widget", quantity=1.0, unit_price=10.0)],
    )

    process_invoice(invoice_id)

    db = TestingSessionLocal()
    updated = db.query(Invoice).filter(Invoice.id == invoice.id).first()
    assert updated.status == InvoiceStatus.NEEDS_REVIEW
    assert updated.extracted_data["vendor_name"] == "Acme Corp"
    assert updated.extracted_data["confidence_scores"] == {
        "vendor_name": "low",
        "invoice_number": "low",
        "invoice_date": "low",
        "total_amount": "low",
        "line_items": "low",
    }
    assert updated.extraction_error is None
    db.close()
    mock_extract.assert_called_once()


@patch("app.worker.extract_invoice")
@patch("app.worker.SessionLocal", TestingSessionLocal)
def test_process_invoice_extraction_failure(mock_extract, worker_setup):
    temp_dir = worker_setup
    db = TestingSessionLocal()
    invoice = _create_invoice(db, temp_dir=temp_dir)
    invoice_id = str(invoice.id)
    db.close()

    mock_extract.side_effect = ExtractionFailedError(
        '{"error": {"code": 400, "message": "Gemini response failed '
        'schema validation"}}'
    )

    process_invoice(invoice_id)

    db = TestingSessionLocal()
    updated = db.query(Invoice).filter(Invoice.id == invoice.id).first()
    assert updated.status == InvoiceStatus.EXTRACTION_FAILED
    assert updated.extraction_error == "Extraction failed: unable to process document"
    assert "schema validation" not in updated.extraction_error
    assert "Gemini" not in updated.extraction_error
    db.close()


@patch("app.worker.extract_invoice")
@patch("app.worker.SessionLocal", TestingSessionLocal)
def test_process_invoice_skips_already_processed(mock_extract, worker_setup):
    temp_dir = worker_setup
    db = TestingSessionLocal()
    invoice = _create_invoice(
        db, status=InvoiceStatus.EXTRACTED, temp_dir=temp_dir
    )
    invoice.extracted_data = {"vendor_name": "Existing"}
    db.commit()
    invoice_id = str(invoice.id)
    db.close()

    process_invoice(invoice_id)

    mock_extract.assert_not_called()
    db = TestingSessionLocal()
    updated = db.query(Invoice).filter(Invoice.id == invoice.id).first()
    assert updated.status == InvoiceStatus.EXTRACTED
    assert updated.extracted_data == {"vendor_name": "Existing"}
    db.close()


@patch("app.worker.extract_invoice")
@patch("app.worker.SessionLocal", TestingSessionLocal)
def test_process_invoice_file_read_failure(mock_extract, worker_setup):
    temp_dir = worker_setup
    db = TestingSessionLocal()
    invoice = _create_invoice(
        db, storage_path="missing.pdf", write_file=False, temp_dir=temp_dir
    )
    invoice_id = str(invoice.id)
    db.close()

    process_invoice(invoice_id)

    mock_extract.assert_not_called()
    db = TestingSessionLocal()
    updated = db.query(Invoice).filter(Invoice.id == invoice.id).first()
    assert updated.status == InvoiceStatus.EXTRACTION_FAILED
    assert (
        updated.extraction_error
        == "Extraction failed: invoice file not found on disk"
    )
    db.close()


@patch("app.worker.extract_invoice")
@patch("app.worker.SessionLocal", TestingSessionLocal)
def test_process_invoice_rate_limited(mock_extract, worker_setup):
    temp_dir = worker_setup
    db = TestingSessionLocal()
    invoice = _create_invoice(db, temp_dir=temp_dir)
    invoice_id = str(invoice.id)
    db.close()

    mock_extract.side_effect = ExtractionRateLimitedError(
        '429 {"error": {"code": 429, "message": "Resource exhausted"}}'
    )

    process_invoice(invoice_id)

    db = TestingSessionLocal()
    updated = db.query(Invoice).filter(Invoice.id == invoice.id).first()
    assert updated.status == InvoiceStatus.EXTRACTION_FAILED
    assert updated.extraction_error == (
        "Extraction failed: rate limited after retries"
    )
    assert "429" not in updated.extraction_error
    assert "Resource exhausted" not in updated.extraction_error
    db.close()
