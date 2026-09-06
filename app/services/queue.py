from uuid import UUID

from rq import Queue, Retry

from app.core.redis import get_redis_connection
from app.worker import process_invoice

QUEUE_NAME = "invoices"


def get_queue() -> Queue:
    return Queue(QUEUE_NAME, connection=get_redis_connection())


def enqueue_invoice(invoice_id: UUID) -> None:
    queue = get_queue()
    # Protects against worker crashes or OOM kills that prevent process_invoice
    # from running its own exception handlers and recording a terminal status.
    queue.enqueue(
        process_invoice, str(invoice_id), retry=Retry(max=2, interval=[10, 30])
    )
