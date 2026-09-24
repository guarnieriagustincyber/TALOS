"""Contract and behavioral tests for Colab and Google Drive vector synchronization endpoints."""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from study_engine.cli import load_contract
from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.retrieval.vector_store import SQLiteVectorStore, VectorRecord
from study_engine.storage.knowledge_store import KnowledgeStore
from study_engine.web.app import create_app
from study_engine.web.dependencies import AppContainer, set_container


def _unit_vector(dim: int = 4096) -> list:
    return [1.0 / (dim ** 0.5)] * dim


@pytest.fixture(scope="module")
def colab_test_env(tmp_path_factory):
    tmp_dir = tmp_path_factory.mktemp("colab_web_test_dir")
    kdb = tmp_dir / "knowledge_store.db"
    vdb = tmp_dir / "vector_store.db"

    store = KnowledgeStore(kdb)
    store.initialize()
    store.create_notebook(Notebook(id="nb1", name="NB1"))
    rec = SourceRecord(
        source_id="src1",
        manifest=SourceManifest(source_id="src1", filename="a.pdf", byte_size=1, sha256="0" * 64),
    )
    doc = Document(id="doc1", source_id="src1", title="Doc", content="")
    chunks = [
        Chunk(id="c_done", document_id="doc1", source_id="src1", content="texto indexado", index=0),
        Chunk(id="c_pend", document_id="doc1", source_id="src1", content="texto pendiente", index=1),
    ]
    store.store_ingestion_bundle(rec, [doc], chunks, notebook_id="nb1")

    contract = load_contract()

    vstore = SQLiteVectorStore(vdb)
    vstore.save_records([
        VectorRecord(
            chunk_id="c_done",
            notebook_id="nb1",
            source_id="src1",
            provider_id=contract["provider_id"],
            model_id=contract["model_id"],
            dimensions=contract["dimensions"],
            vector=_unit_vector(contract["dimensions"]),
        )
    ])
    vstore.close()

    container = AppContainer(working_dir=tmp_dir, use_mock=True)
    container.knowledge_store = store
    set_container(container)
    app = create_app()
    client = TestClient(app)
    return client, tmp_dir, kdb, vdb


def test_colab_status_endpoint(colab_test_env):
    """GET /api/ingestion/colab/status returns chunk and vector metrics."""
    client, _, _, _ = colab_test_env
    res = client.get("/api/ingestion/colab/status")
    assert res.status_code == 200
    data = res.json()
    assert "total_chunks" in data
    assert "total_vectors" in data
    assert "pending_chunks" in data
    assert "rclone_installed" in data
    assert "remote_path" in data
    assert data["total_chunks"] >= 2
    assert data["total_vectors"] >= 1
    assert data["pending_chunks"] == 1


def test_colab_export_endpoint(colab_test_env):
    """POST /api/ingestion/colab/export generates pending file without crashing."""
    client, _, _, _ = colab_test_env
    res = client.post("/api/ingestion/colab/export?upload_to_gdrive=false")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["count"] == 1
    assert data["filename"] is not None
    assert data["download_url"] is not None

    dl_res = client.get(data["download_url"])
    assert dl_res.status_code == 200
    assert "c_pend" in dl_res.text


def test_colab_download_not_found(colab_test_env):
    """GET /api/ingestion/colab/download/nonexistent.jsonl returns 404."""
    client, _, _, _ = colab_test_env
    res = client.get("/api/ingestion/colab/download/nonexistent.jsonl")
    assert res.status_code == 404


def test_colab_upload_vectors_flow(colab_test_env):
    """POST /api/ingestion/colab/upload-vectors accepts .jsonl and updates vector store."""
    client, _, _, _ = colab_test_env
    contract = load_contract()

    # Vector payload matching talos-vectors-v1 schema with authoritative contract
    meta_line = json.dumps({
        "_meta": {
            "schema": "talos-vectors-v1",
            "contract": contract,
            "count": 1
        }
    })
    data_line = json.dumps({
        "chunk_id": "c_pend",
        "notebook_id": "nb1",
        "vector": _unit_vector(contract["dimensions"]),
    })
    payload = f"{meta_line}\n{data_line}\n"

    # Reject non-jsonl
    bad_upload = client.post(
        "/api/ingestion/colab/upload-vectors",
        files={"file": ("bad.txt", b"some text", "text/plain")},
    )
    assert bad_upload.status_code == 400

    # Accept jsonl
    good_upload = client.post(
        "/api/ingestion/colab/upload-vectors",
        files={"file": ("vectors_test.jsonl", payload.encode("utf-8"), "application/x-jsonlines")},
    )
    assert good_upload.status_code == 200
    res_data = good_upload.json()
    assert res_data["status"] == "ok"
    assert res_data["synced"] == 1
    assert res_data["pending_remaining"] == 0

    # Verify pending count dropped to 0
    status_res = client.get("/api/ingestion/colab/status")
    assert status_res.status_code == 200
    assert status_res.json()["pending_chunks"] == 0
