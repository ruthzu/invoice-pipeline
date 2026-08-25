import asyncio
from datetime import datetime
from uuid import uuid4

import httpx
import pytest

from app.core.config import settings
from app.db.models.invoice import Invoice, InvoiceStatus
from app.db.session import Base
from app.main import app
from tests.conftest import TestingSessionLocal, engine


async def _post(path: str, json: dict | None = None) -> httpx.Response:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        return await client.post(path, json=json)


def post(path: str, json: dict | None = None) -> httpx.Response:
    return asyncio.run(_post(path, json))


@pytest.fixture
def setup_database():
    Base.metadata.create_all(bind=engine)
    original_storage_dir = settings.storage_dir
    try:
        yield
    finally:
        settings.storage_dir = original_storage_dir
        Base.metadata.drop_all(bind=engine)


def _create_invoice(status: InvoiceStatus) -> Invoice:
    db = TestingSessionLocal()
    invoice = Invoice(
        id=uuid4(),
        original_filename="review.pdf",
        storage_path="review.pdf",
        mime_type="application/pdf",
        status=status,
        extracted_data={"confidence_scores": {}},
        validation_errors=[],
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    db.close()
    return invoice


def test_approve_needs_review_invoice(setup_database):
    invoice = _create_invoice(InvoiceStatus.NEEDS_REVIEW)

    response = post(f"/invoices/{invoice.id}/approve")

    assert response.status_code == 200
    assert response.json()["status"] == "APPROVED"
    db = TestingSessionLocal()
    updated = db.get(Invoice, invoice.id)
    assert updated.status == InvoiceStatus.APPROVED
    assert updated.reviewed_by == "mvp-reviewer"
    assert isinstance(updated.reviewed_at, datetime)
    db.close()


def test_reject_needs_review_invoice(setup_database):
    invoice = _create_invoice(InvoiceStatus.NEEDS_REVIEW)

    response = post(
        f"/invoices/{invoice.id}/reject",
        json={"reason": "The extracted total is unclear"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "REJECTED"
    db = TestingSessionLocal()
    updated = db.get(Invoice, invoice.id)
    assert updated.status == InvoiceStatus.REJECTED
    assert updated.rejection_reason == "The extracted total is unclear"
    assert updated.reviewed_by == "mvp-reviewer"
    assert isinstance(updated.reviewed_at, datetime)
    db.close()


def test_approve_wrong_status_returns_conflict(setup_database):
    invoice = _create_invoice(InvoiceStatus.AUTO_APPROVED)

    response = post(f"/invoices/{invoice.id}/approve")

    assert response.status_code == 409


def test_reject_wrong_status_returns_conflict(setup_database):
    invoice = _create_invoice(InvoiceStatus.APPROVED)

    response = post(
        f"/invoices/{invoice.id}/reject",
        json={"reason": "Not acceptable"},
    )

    assert response.status_code == 409


def test_reject_empty_reason_returns_bad_request(setup_database):
    invoice = _create_invoice(InvoiceStatus.NEEDS_REVIEW)

    response = post(
        f"/invoices/{invoice.id}/reject",
        json={"reason": "   "},
    )

    assert response.status_code == 400


def test_reject_missing_reason_returns_bad_request(setup_database):
    invoice = _create_invoice(InvoiceStatus.NEEDS_REVIEW)

    response = post(f"/invoices/{invoice.id}/reject", json={})

    assert response.status_code == 400


def test_approve_nonexistent_invoice_returns_not_found(setup_database):
    response = post(f"/invoices/{uuid4()}/approve")

    assert response.status_code == 404


def test_reject_nonexistent_invoice_returns_not_found(setup_database):
    response = post(
        f"/invoices/{uuid4()}/reject",
        json={"reason": "Not acceptable"},
    )

    assert response.status_code == 404
