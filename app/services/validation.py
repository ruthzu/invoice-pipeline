from datetime import date

from app.schemas.invoice_extraction import InvoiceExtraction


def validate_invoice(extraction: InvoiceExtraction) -> list[str]:
    errors: list[str] = []

    try:
        if extraction.total_amount is not None and extraction.total_amount <= 0:
            errors.append("total_amount must be positive")
    except Exception:
        errors.append("total_amount must be positive")

    try:
        if extraction.invoice_date is not None:
            parsed_date = date.fromisoformat(extraction.invoice_date)
            if parsed_date.isoformat() != extraction.invoice_date:
                errors.append("invoice_date is not a valid date")
    except Exception:
        errors.append("invoice_date is not a valid date")

    return errors
