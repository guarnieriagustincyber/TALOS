import asyncio
from io import BytesIO
from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException, UploadFile

from study_engine.web.routes import ingestion


def test_upload_rejects_oversized_file_without_reading_it_all(tmp_path, monkeypatch):
    assert ingestion.MAX_COLAB_VECTOR_UPLOAD_BYTES == 50 * 1024 * 1024
    monkeypatch.setattr(ingestion, "MAX_COLAB_VECTOR_UPLOAD_BYTES", 8)
    file = UploadFile(file=BytesIO(b"x" * 32), filename="vectors.jsonl")

    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(
            ingestion.upload_colab_vectors(
                file=file,
                container=SimpleNamespace(working_dir=tmp_path),
            )
        )

    assert exc_info.value.status_code == 413
    assert "demasiado grande" in exc_info.value.detail
    assert file.file.tell() == 9


@pytest.mark.parametrize(
    "filename",
    ["../../../etc/passwd.jsonl", r"..\..\..\etc\passwd.jsonl"],
)
def test_upload_sanitizes_filename_to_colab_directory(tmp_path, monkeypatch, filename):
    upload_dir = tmp_path / "colab"
    upload_dir.mkdir()
    monkeypatch.setattr(ingestion, "DEFAULT_COLAB_DIR", upload_dir)
    saved_paths = []
    monkeypatch.setattr(
        ingestion,
        "sync_vectors",
        lambda **kwargs: saved_paths.append(Path(kwargs["vectors_jsonl"])) or {
            "synced": 0,
            "inserted": 0,
            "updated": 0,
            "pending_after": 0,
        },
    )

    result = asyncio.run(
        ingestion.upload_colab_vectors(
            file=UploadFile(
                file=BytesIO(b'{"vectors": []}'),
                filename=filename,
            ),
            container=SimpleNamespace(working_dir=tmp_path),
        )
    )

    assert len(saved_paths) == 1
    assert saved_paths[0].resolve().parent == upload_dir.resolve()
    assert ".." not in saved_paths[0].name
    assert result.file_used.endswith("_passwd.jsonl")
