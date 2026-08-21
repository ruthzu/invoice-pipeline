import logging
from pathlib import Path
from uuid import UUID

from rq import Queue, Worker
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.core.exceptions import (
    ExtractionError,
    ExtractionFailedError,
    ExtractionRateLimitedError,
)
from app.core.redis import get_redis_connection
from app.db.models.invoice import Invoice, InvoiceStatus
from app.db.session import SessionLocal
from app.services.confidence import apply_heuristics
from app.services.extraction import extract_invoice
from app.services.validation import validate_invoice

logger = logging.getLogger(__name__)

SKIP_STATUSES = {
    InvoiceStatus.EXTRACTED,
    InvoiceStatus.EXTRACTION_FAILED,
    InvoiceStatus.PROCESSED,
}


def _extraction_error_reason(exc: ExtractionError) -> str:
    if isinstance(exc, ExtractionRateLimitedError):
        return "Extraction failed: rate limited after retries"
    return "Extraction failed: unable to process document"


def _read_invoice_file(invoice: Invoice) -> bytes:
    file_path = Path(settings.storage_dir) / invoice.storage_path
    return file_path.read_bytes()


def _mark_extraction_failed(
    db, invoice: Invoice, reason: str, invoice_id: str
) -> None:
    invoice.status = InvoiceStatus.EXTRACTION_FAILED
    invoice.extraction_error = reason[:199]
    invoice.extracted_data = None
    try:
        db.commit()
    except SQLAlchemyError as exc:
        logger.error(
            "Failed to save extraction failure for invoice %s: %s",
            invoice_id,
            exc,
            exc_info=True,
        )
        db.rollback()
        raise


def process_invoice(invoice_id: str) -> None:
    logger.info("Received invoice job for invoice id=%s", invoice_id)
    db = SessionLocal()
    try:
        invoice = db.query(Invoice).filter(Invoice.id == UUID(invoice_id)).first()
        if invoice is None:
            logger.error("Invoice %s not found", invoice_id)
            return

        if invoice.status in SKIP_STATUSES:
            logger.info("Invoice %s already processed, skipping", invoice_id)
            return

        try:
            file_bytes = _read_invoice_file(invoice)
        except OSError as exc:
            logger.error(
                "Failed to read invoice file for %s: %s",
                invoice_id,
                exc,
                exc_info=True,
            )
            _mark_extraction_failed(
                db,
                invoice,
                "Extraction failed: invoice file not found on disk",
                invoice_id,
            )
            return

        try:
            extraction = extract_invoice(file_bytes, invoice.mime_type)
        except ExtractionRateLimitedError as exc:
            logger.error(
                "Extraction rate limited for invoice %s: %s",
                invoice_id,
                exc,
                exc_info=True,
            )
            _mark_extraction_failed(
                db, invoice, _extraction_error_reason(exc), invoice_id
            )
            return
        except ExtractionFailedError as exc:
            logger.error(
                "Extraction failed for invoice %s: %s",
                invoice_id,
                exc,
                exc_info=True,
            )
            _mark_extraction_failed(
                db, invoice, _extraction_error_reason(exc), invoice_id
            )
            return

        extraction.confidence_scores = apply_heuristics(extraction)
        invoice.validation_errors = validate_invoice(extraction)
        invoice.extracted_data = extraction.model_dump()
        invoice.extraction_error = None
        invoice.status = InvoiceStatus.EXTRACTED

        try:
            db.commit()
        except SQLAlchemyError as exc:
            logger.error(
                "Extraction succeeded for invoice %s but DB commit failed; "
                "extracted data was lost on save: %s",
                invoice_id,
                exc,
                exc_info=True,
            )
            db.rollback()
            raise
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    conn = get_redis_connection()
    worker = Worker([Queue("invoices", connection=conn)], connection=conn)
    worker.work()
