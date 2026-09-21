import asyncio
import pytest
from pathlib import Path
from fastapi import HTTPException, UploadFile
import io

from study_engine.utils.pdf_utils import (
    validate_and_hash_pdf,
    save_and_hash_uploaded_pdf,
)


def test_validate_and_hash_pdf(tmp_path: Path):
    pdf_file = tmp_path / "valid.pdf"
    content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    pdf_file.write_bytes(content)

    doc_hash = validate_and_hash_pdf(pdf_file)
    assert len(doc_hash) == 64
    assert isinstance(doc_hash, str)

    # Invalid header
    invalid_file = tmp_path / "invalid.pdf"
    invalid_file.write_bytes(b"NOT_A_PDF")
    with pytest.raises(ValueError, match="Invalid PDF header"):
        validate_and_hash_pdf(invalid_file)

    # Non-existent file
    with pytest.raises(FileNotFoundError):
        validate_and_hash_pdf(tmp_path / "missing.pdf")


def test_save_and_hash_uploaded_pdf(tmp_path: Path):
    async def _run():
        target_dir = tmp_path / "sources"
        content = b"%PDF-1.4 valid stream content"
        upload = UploadFile(filename="doc.pdf", file=io.BytesIO(content))

        doc_hash, final_path = await save_and_hash_uploaded_pdf(upload, target_dir)
        assert len(doc_hash) == 64
        assert final_path.exists()
        assert final_path.name == f"{doc_hash}.pdf"

        # Invalid stream header
        bad_upload = UploadFile(filename="bad.pdf", file=io.BytesIO(b"MALFORMED"))
        with pytest.raises(HTTPException) as exc_info:
            await save_and_hash_uploaded_pdf(bad_upload, target_dir)
        assert exc_info.value.status_code == 400

    asyncio.run(_run())
