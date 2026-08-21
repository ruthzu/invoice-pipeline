from app.schemas.invoice_extraction import InvoiceExtraction
from app.services.validation import validate_invoice


def test_valid_invoice_has_no_validation_errors():
    extraction = InvoiceExtraction(total_amount=100.0, invoice_date="2019-02-28")

    assert validate_invoice(extraction) == []


def test_negative_total_is_flagged():
    extraction = InvoiceExtraction(total_amount=-1.0)

    assert validate_invoice(extraction) == ["total_amount must be positive"]


def test_zero_total_is_flagged():
    extraction = InvoiceExtraction(total_amount=0.0)

    assert validate_invoice(extraction) == ["total_amount must be positive"]


def test_valid_iso_date_is_not_flagged():
    extraction = InvoiceExtraction(invoice_date="2019-02-28")

    assert validate_invoice(extraction) == []


def test_malformed_date_is_flagged():
    extraction = InvoiceExtraction(invoice_date="2019/02/28")

    assert validate_invoice(extraction) == ["invoice_date is not a valid date"]


def test_invalid_calendar_date_is_flagged():
    for invoice_date in ("2019-99-99", "2019-02-30"):
        extraction = InvoiceExtraction(invoice_date=invoice_date)

        assert validate_invoice(extraction) == ["invoice_date is not a valid date"]


def test_null_values_are_not_validation_errors():
    extraction = InvoiceExtraction(total_amount=None, invoice_date=None)

    assert validate_invoice(extraction) == []
