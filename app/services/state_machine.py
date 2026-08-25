from app.core.exceptions import IllegalStatusTransitionError
from app.db.models.invoice import Invoice, InvoiceStatus

LEGAL_TRANSITIONS: dict[InvoiceStatus, set[InvoiceStatus]] = {
    InvoiceStatus.PENDING: {InvoiceStatus.QUEUED},
    InvoiceStatus.QUEUED: {
        InvoiceStatus.NEEDS_REVIEW,
        InvoiceStatus.AUTO_APPROVED,
        InvoiceStatus.EXTRACTION_FAILED,
    },
    InvoiceStatus.NEEDS_REVIEW: {InvoiceStatus.APPROVED, InvoiceStatus.REJECTED},
    InvoiceStatus.EXTRACTION_FAILED: set(),
    InvoiceStatus.AUTO_APPROVED: set(),
    InvoiceStatus.APPROVED: set(),
    InvoiceStatus.REJECTED: set(),
}


def transition_status(invoice: Invoice, new_status: InvoiceStatus) -> None:
    current_status = invoice.status
    if new_status not in LEGAL_TRANSITIONS.get(current_status, set()):
        raise IllegalStatusTransitionError(current_status, new_status)
    invoice.status = new_status
