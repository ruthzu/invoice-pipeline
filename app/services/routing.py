from app.db.models.invoice import InvoiceStatus
from app.schemas.invoice_extraction import ConfidenceScores


def decide_routing(
    confidence_scores: ConfidenceScores,
    validation_errors: list[str],
) -> InvoiceStatus:
    if validation_errors or "low" in confidence_scores.model_dump().values():
        return InvoiceStatus.NEEDS_REVIEW
    return InvoiceStatus.AUTO_APPROVED
