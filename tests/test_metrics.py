from datetime import UTC, datetime
from uuid import uuid4

from app.db.models.invoice import Invoice, InvoiceStatus
from tests.conftest import TestingSessionLocal, client


def _create_invoice(
    status: InvoiceStatus,
    duration: int | None = None,
    created_at: datetime | None = None,
) -> None:
    db = TestingSessionLocal()
    db.add(
        Invoice(
            id=uuid4(),
            original_filename="metrics.pdf",
            storage_path="metrics.pdf",
            mime_type="application/pdf",
            status=status,
            extraction_duration_ms=duration,
            created_at=created_at,
        )
    )
    db.commit()
    db.close()


def test_metrics_returns_aggregate_values(setup_database):
    _create_invoice(InvoiceStatus.PENDING, duration=100)
    _create_invoice(InvoiceStatus.PENDING, duration=300)
    _create_invoice(InvoiceStatus.APPROVED, created_at=datetime.now(UTC))

    response = client.get("/metrics")

    assert response.status_code == 200
    data = response.json()
    assert data["invoice_counts_by_status"] == {"PENDING": 2, "APPROVED": 1}
    assert data["average_extraction_duration_ms"] == 200
    assert data["invoices_created_last_24_hours"] == 3


def test_metrics_empty_database_returns_zero_values(setup_database):
    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.json() == {
        "invoice_counts_by_status": {},
        "average_extraction_duration_ms": 0,
        "invoices_created_last_24_hours": 0,
    }
