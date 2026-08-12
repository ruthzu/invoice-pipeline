from uuid import UUID

from rq import Queue

from app.core.redis import get_redis_connection
from app.worker import process_invoice

QUEUE_NAME = "invoices"


def get_queue() -> Queue:
    return Queue(QUEUE_NAME, connection=get_redis_connection())


def enqueue_invoice(invoice_id: UUID) -> None:
    queue = get_queue()
    queue.enqueue(process_invoice, str(invoice_id))
