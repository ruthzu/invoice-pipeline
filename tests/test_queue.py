from unittest.mock import patch
from uuid import UUID

from tests.conftest import TestingSessionLocal, client, create_test_file

from app.db.models.invoice import Invoice


def test_upload_succeeds_when_redis_unreachable(setup_database):
    """Upload returns 201 and stays PENDING when enqueue fails."""
    pdf_content = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"

    with patch(
        "app.api.invoices.enqueue_invoice",
        side_effect=ConnectionError("Redis unreachable"),
    ):
        response = client.post(
            "/invoices",
            files={
                "file": ("test.pdf", create_test_file(pdf_content), "application/pdf")
            },
        )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "PENDING"

    invoice_id = UUID(data["id"])
    db = TestingSessionLocal()
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    assert invoice is not None
    assert invoice.status.value == "PENDING"
    db.close()
