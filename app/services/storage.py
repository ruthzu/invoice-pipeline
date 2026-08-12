import logging
import os
from pathlib import Path
from typing import BinaryIO
from uuid import UUID

from app.core.config import settings

logger = logging.getLogger(__name__)


async def save_uploaded_file(file_id: UUID, file_content: BinaryIO, mime_type: str) -> str:
    """
    Save an uploaded file to storage directory using UUID-based filename.
    
    Args:
        file_id: UUID for the file (used as filename)
        file_content: Binary file content to save
        mime_type: MIME type to determine file extension
        
    Returns:
        str: Storage path relative to storage directory
        
    Raises:
        OSError: If file cannot be written to disk
    """
    # Create storage directory if it doesn't exist
    storage_path = Path(settings.storage_dir)
    storage_path.mkdir(parents=True, exist_ok=True)
    
    # Determine file extension from MIME type
    extension_map = {
        "application/pdf": ".pdf",
        "image/jpeg": ".jpg", 
        "image/png": ".png"
    }
    extension = extension_map.get(mime_type, "")
    
    # Create filename using UUID
    filename = f"{file_id}{extension}"
    file_path = storage_path / filename
    
    # Write file to disk
    try:
        with open(file_path, "wb") as f:
            # Read and write in chunks to handle large files efficiently
            while chunk := file_content.read(8192):
                f.write(chunk)
        
        logger.info(f"Successfully saved file {filename} to storage")
        return filename
    except Exception as e:
        logger.error(f"Failed to save file {filename}: {e}")
        # Clean up partial file if it exists
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass
        raise