from pathlib import Path
from uuid import UUID

from app.core.config import settings
from app.db.models.invoice import Invoice
from tests.conftest import TestingSessionLocal, client, create_test_file


def test_upload_valid_pdf(setup_database):
    """Test uploading a valid PDF file."""
    # PDF magic bytes
    pdf_content = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"

    response = client.post(
        "/invoices",
        files={"file": ("test.pdf", create_test_file(pdf_content), "application/pdf")},
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] == "PENDING"

    invoice_id = UUID(data["id"])

    # Verify database record
    db = TestingSessionLocal()
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    assert invoice is not None
    assert invoice.original_filename == "test.pdf"
    assert invoice.mime_type == "application/pdf"
    assert invoice.status.value == "PENDING"
    db.close()

    # Verify file exists on disk
    storage_path = Path(settings.storage_dir) / invoice.storage_path
    assert storage_path.exists()


def test_upload_valid_jpeg(setup_database):
    """Test uploading a valid JPEG file."""
    # JPEG magic bytes
    jpeg_content = b"\xff\xd8\xff\xe0\x00\x10JFIF"

    response = client.post(
        "/invoices",
        files={"file": ("test.jpg", create_test_file(jpeg_content), "image/jpeg")},
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] == "PENDING"


def test_upload_valid_png(setup_database):
    """Test uploading a valid PNG file."""
    # PNG magic bytes
    png_content = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"

    response = client.post(
        "/invoices",
        files={"file": ("test.png", create_test_file(png_content), "image/png")},
    )

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] == "PENDING"


def test_upload_invalid_content_type(setup_database):
    """Test uploading file with invalid content type."""
    content = b"some text content"

    response = client.post(
        "/invoices",
        files={"file": ("test.txt", create_test_file(content), "text/plain")},
    )

    assert response.status_code == 400
    assert "Invalid file type" in response.json()["detail"]


def test_upload_mismatched_magic_bytes(setup_database):
    """Test uploading file with PDF extension but text content."""
    # Text content but claiming to be PDF
    text_content = b"This is just plain text, not a PDF"

    response = client.post(
        "/invoices",
        files={"file": ("fake.pdf", create_test_file(text_content), "application/pdf")},
    )

    assert response.status_code == 400
    assert "File content does not match declared type" in response.json()["detail"]


def test_upload_oversized_file(setup_database):
    """Test uploading file that exceeds size limit."""
    # Create content larger than max size (default 10MB)
    large_content = b"x" * (11 * 1024 * 1024)  # 11MB
    pdf_header = b"%PDF-1.4\n"
    oversized_content = pdf_header + large_content

    response = client.post(
        "/invoices",
        files={
            "file": (
                "large.pdf",
                create_test_file(oversized_content),
                "application/pdf",
            )
        },
    )

    assert response.status_code == 413
    assert "File too large" in response.json()["detail"]


def test_upload_empty_file(setup_database):
    """Test uploading empty file."""
    empty_content = b""

    response = client.post(
        "/invoices",
        files={
            "file": ("empty.pdf", create_test_file(empty_content), "application/pdf")
        },
    )

    assert response.status_code == 400
    assert "File content does not match declared type" in response.json()["detail"]


def test_multiple_uploads_different_uuids(setup_database):
    """Test that multiple uploads get different UUIDs."""
    pdf_content = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"

    response1 = client.post(
        "/invoices",
        files={"file": ("test1.pdf", create_test_file(pdf_content), "application/pdf")},
    )

    response2 = client.post(
        "/invoices",
        files={"file": ("test2.pdf", create_test_file(pdf_content), "application/pdf")},
    )

    assert response1.status_code == 201
    assert response2.status_code == 201

    id1 = response1.json()["id"]
    id2 = response2.json()["id"]

    assert id1 != id2  # UUIDs should be different


def test_storage_path_not_exposed(setup_database):
    """Test that storage path is not exposed in API response."""
    pdf_content = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"

    response = client.post(
        "/invoices",
        files={"file": ("test.pdf", create_test_file(pdf_content), "application/pdf")},
    )

    assert response.status_code == 201
    data = response.json()

    # Response should only contain id and status, not storage_path
    assert set(data.keys()) == {"id", "status"}
    assert "storage_path" not in data
