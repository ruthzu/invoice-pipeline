from app.db.models.invoice import InvoiceStatus
from app.schemas.invoice_extraction import ConfidenceScores
from app.services.routing import decide_routing


def _high_confidence() -> ConfidenceScores:
    return ConfidenceScores(
        vendor_name="high",
        invoice_number="high",
        invoice_date="high",
        total_amount="high",
        line_items="high",
    )


def test_no_issues_are_auto_approved():
    assert decide_routing(_high_confidence(), []) == InvoiceStatus.AUTO_APPROVED


def test_any_low_confidence_needs_review():
    scores = _high_confidence()
    scores.total_amount = "low"

    assert decide_routing(scores, []) == InvoiceStatus.NEEDS_REVIEW


def test_any_validation_error_needs_review():
    assert decide_routing(_high_confidence(), ["total_amount must be positive"]) == (
        InvoiceStatus.NEEDS_REVIEW
    )


def test_both_issues_still_need_review():
    scores = _high_confidence()
    scores.total_amount = "low"

    assert decide_routing(scores, ["invoice_date is not a valid date"]) == (
        InvoiceStatus.NEEDS_REVIEW
    )
