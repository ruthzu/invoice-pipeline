import logging
from uuid import UUID

from rq import Queue, Worker

from app.core.redis import get_redis_connection
from app.db.models.invoice import Invoice, InvoiceStatus
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


def process_invoice(invoice_id: str) -> None:
    logger.info("Received invoice job for invoice id=%s", invoice_id)
    db = SessionLocal()
    try:
        invoice = db.query(Invoice).filter(Invoice.id == UUID(invoice_id)).first()
        if invoice is None:
            logger.error("Invoice %s not found", invoice_id)
            return
        invoice.status = InvoiceStatus.PROCESSED
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    conn = get_redis_connection()
    worker = Worker([Queue("invoices", connection=conn)], connection=conn)
    worker.work()
