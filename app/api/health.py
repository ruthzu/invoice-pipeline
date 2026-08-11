import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from app.db.session import get_db

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        # Test database connectivity with a simple query
        db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        # Log the real exception server-side
        logger.error("Database health check failed: %s", e)
        # Return a flat error response without exposing internal details
        return JSONResponse(
            status_code=503,
            content={"status": "error", "detail": "database unavailable"},
        )
