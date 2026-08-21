import enum
from uuid import uuid4

from sqlalchemy import JSON, Column, DateTime, Enum, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func

from app.db.session import Base


class InvoiceStatus(enum.Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    PROCESSED = "PROCESSED"
    EXTRACTED = "EXTRACTED"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    original_filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    status = Column(Enum(InvoiceStatus), nullable=False, default=InvoiceStatus.PENDING)
    extracted_data = Column(JSON, nullable=True)
    validation_errors = Column(JSON, nullable=True)
    extraction_error = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
