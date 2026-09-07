import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from rq import Queue
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from app.core.redis import get_redis_connection
from app.db.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    database_status = "ok"
    redis_status = "ok"
    queue_depth = 0
    queue_available = True
    database_available = True

    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error("Database health check failed: %s", e)
        database_status = "error"
        database_available = False

    try:
        get_redis_connection().ping()
    except Exception as e:
        logger.error("Redis health check failed: %s", e)
        redis_status = "error"

    try:
        queue_depth = Queue("invoices", connection=get_redis_connection()).count
    except Exception as e:
        logger.error("Queue health check failed: %s", e)
        queue_available = False

    content = {
        "status": "ok"
        if database_status == "ok" and redis_status == "ok" and queue_available
        else "degraded",
        "checks": {
            "database": database_status,
            "redis": redis_status,
            "queue_depth": queue_depth,
        },
    }
    if not database_available:
        return JSONResponse(
            status_code=503,
            content=content,
        )
    return content
