import logging
from io import BytesIO
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models.invoice import Invoice, InvoiceStatus
from app.db.session import get_db
from app.services.storage import save_uploaded_file

logger = logging.getLogger(__name__)
router = APIRouter()

# MIME type to magic bytes mapping for validation
ALLOWED_MIME_TYPES = {
    "application/pdf": [b"%PDF-"],
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"]
}


def validate_file_type(content_type: str, file_content: bytes) -> bool:
    """
    Validate file type by checking both Content-Type and magic bytes.
    
    Args:
        content_type: Declared MIME type from request
        file_content: First few bytes of the file
        
    Returns:
        bool: True if file type is valid, False otherwise
    """
    if content_type not in ALLOWED_MIME_TYPES:
        return False
    
    magic_bytes = ALLOWED_MIME_TYPES[content_type]
    return any(file_content.startswith(magic) for magic in magic_bytes)


@router.post("/invoices", status_code=201)
async def upload_invoice(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload an invoice file (PDF, JPEG, or PNG).
    
    Returns:
        dict: {"id": UUID, "status": "PENDING"}
    """
    # Check Content-Length if provided by client
    content_length = request.headers.get("content-length")
    if content_length:
        content_length_mb = int(content_length) / (1024 * 1024)
        if content_length_mb > settings.max_upload_size_mb:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {settings.max_upload_size_mb}MB"
            )
    
    # Validate declared content type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only PDF, JPEG, and PNG files are allowed"
        )
    
    # Read file in chunks and enforce size limit while reading
    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    chunk_size = 8192
    chunks = []
    total_size = 0

    try:
        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > max_bytes:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size is {settings.max_upload_size_mb}MB"
                )
            chunks.append(chunk)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to read uploaded file: {e}")
        raise HTTPException(status_code=400, detail="Unable to read uploaded file")

    file_content = b"".join(chunks)
    
    # Validate magic bytes (file signature)
    if not validate_file_type(file.content_type, file_content):
        raise HTTPException(
            status_code=400,
            detail="File content does not match declared type. File may be corrupted or have wrong extension"
        )
    
    # Generate UUID for the file (collision-proof)
    file_id = uuid4()
    
    # Save file to storage first
    try:
        file_stream = BytesIO(file_content)
        storage_path = await save_uploaded_file(file_id, file_stream, file.content_type)
    except Exception as e:
        logger.error(f"Failed to save file to storage: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file")
    
    # Create database record after successful file write
    try:
        invoice = Invoice(
            id=file_id,
            original_filename=file.filename or "unknown",
            storage_path=storage_path,
            mime_type=file.content_type,
            status=InvoiceStatus.PENDING
        )
        
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        
        logger.info(f"Successfully created invoice record {file_id}")
        
        return {
            "id": str(invoice.id),
            "status": invoice.status.value
        }
        
    except Exception as e:
        # File is already written, log orphaned file situation
        logger.error(
            f"Failed to create database record for file {storage_path}. "
            f"Orphaned file exists at storage path. Error: {e}"
        )
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create invoice record")