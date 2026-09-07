from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models.invoice import Invoice
from app.db.session import get_db

router = APIRouter()


@router.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    status_counts = {
        status.value: count
        for status, count in db.query(Invoice.status, func.count(Invoice.id))
        .group_by(Invoice.status)
        .all()
    }
    average_duration = (
        db.query(func.avg(Invoice.extraction_duration_ms))
        .filter(Invoice.extraction_duration_ms.is_not(None))
        .scalar()
    )
    recent_count = (
        db.query(func.count(Invoice.id))
        .filter(Invoice.created_at >= datetime.now(UTC) - timedelta(hours=24))
        .scalar()
    )
    return {
        "invoice_counts_by_status": status_counts,
        "average_extraction_duration_ms": average_duration or 0,
        "invoices_created_last_24_hours": recent_count or 0,
    }
