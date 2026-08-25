import pytest

from app.core.exceptions import IllegalStatusTransitionError
from app.db.models.invoice import Invoice, InvoiceStatus
from app.services.state_machine import LEGAL_TRANSITIONS, transition_status


def _invoice(status: InvoiceStatus) -> Invoice:
    return Invoice(status=status)


def test_every_legal_transition_succeeds():
    for current_status, new_statuses in LEGAL_TRANSITIONS.items():
        for new_status in new_statuses:
            invoice = _invoice(current_status)
            transition_status(invoice, new_status)
            assert invoice.status == new_status


@pytest.mark.parametrize(
    ("current_status", "new_status"),
    [
        (InvoiceStatus.PENDING, InvoiceStatus.APPROVED),
        (InvoiceStatus.NEEDS_REVIEW, InvoiceStatus.PENDING),
        (InvoiceStatus.EXTRACTION_FAILED, InvoiceStatus.QUEUED),
        (InvoiceStatus.AUTO_APPROVED, InvoiceStatus.APPROVED),
        (InvoiceStatus.APPROVED, InvoiceStatus.REJECTED),
        (InvoiceStatus.REJECTED, InvoiceStatus.NEEDS_REVIEW),
    ],
)
def test_illegal_transition_raises_with_both_statuses(
    current_status: InvoiceStatus, new_status: InvoiceStatus
):
    with pytest.raises(IllegalStatusTransitionError) as exc_info:
        transition_status(_invoice(current_status), new_status)

    message = str(exc_info.value)
    assert current_status.value in message
    assert new_status.value in message
