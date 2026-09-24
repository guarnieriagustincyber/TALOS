"""Ciclo Colab incremental: export-pending → sync-vectors → verify-index.

Cubre los contratos del slice:
- export-pending solo exporta chunks SIN vector e5 (dim=384) — Left Join real.
- Caso base: índice completo → 0 pendientes.
- sync-vectors es idempotente (mismo archivo 2 veces → mismo estado).
- sync-vectors es atómico: archivo con un registro inválido → rollback, nada insertado.
- sync-vectors valida contract: dim incorrecta o schema desconocido → aborta.
- sync-vectors rechaza chunk_id inexistente en knowledge_store.
- verify-index reporta pending==0 e integrity ok.
"""

import json
import sqlite3

import pytest

from study_engine.cli import (
    CONTROL_QUERIES,
    export_pending,
    sync_vectors,
    verify_index,
)
from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.retrieval.vector_store import SQLiteVectorStore, VectorRecord
from study_engine.storage.knowledge_store import KnowledgeStore


def _unit_vector(dim: int = 4096) -> list:
    return [1.0 / dim ** 0.5] * dim


@pytest.fixture()
def colab_env(tmp_path):
    """knowledge_store con 2 chunks (1 con vector, 1 sin) en 1 notebook."""
    kdb = tmp_path / "knowledge.db"
    vdb = tmp_path / "vectors.db"

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

    vstore = SQLiteVectorStore(vdb)
    vstore.save_records([
        VectorRecord(
            chunk_id="c_done", notebook_id="nb1", source_id="src1",
            provider_id="sentence_transformers", model_id="Qwen3-Embedding-8B",
            dimensions=4096, vector=_unit_vector(),
        )
    ])
    vstore.close()

    # Puntero al contract versionado real (el test suele correr desde repo root)
    contract = None
    from study_engine.cli import DEFAULT_CONTRACT_PATH
    if DEFAULT_CONTRACT_PATH.exists():
        contract = DEFAULT_CONTRACT_PATH
    return {"kdb": kdb, "vdb": vdb, "out_dir": tmp_path / "colab", "contract": contract}


def _write_vectors(path, rows, with_meta=True):
    lines = []
    if with_meta:
        from study_engine.cli import VECTORS_SCHEMA, load_contract
        contract = load_contract()
        lines.append(json.dumps({"_meta": {"schema": VECTORS_SCHEMA, "contract": contract}}))
    for r in rows:
        lines.append(json.dumps(r))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_export_pending_solo_chunks_sin_vector(colab_env):
    out, count = export_pending(colab_env["kdb"], colab_env["vdb"], colab_env["out_dir"])
    assert count == 1
    rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["_meta"]["schema"] == "talos-pending-v1"
    assert rows[0]["_meta"]["contract"]["dimensions"] == 4096
    assert rows[1:] == [{"chunk_id": "c_pend", "notebook_id": "nb1", "text": "texto pendiente"}]


def test_export_pending_caso_base_indice_completo(colab_env):
    # primero cerrar la brecha
    vfile = colab_env["out_dir"] / "vectors.jsonl"
    colab_env["out_dir"].mkdir(exist_ok=True)
    _write_vectors(vfile, [{"chunk_id": "c_pend", "notebook_id": "nb1", "vector": _unit_vector()}])
    sync_vectors(vfile, colab_env["vdb"], colab_env["kdb"])

    _, count = export_pending(colab_env["kdb"], colab_env["vdb"], colab_env["out_dir"])
    assert count == 0


def test_sync_vectors_idempotente(colab_env):
    vfile = colab_env["out_dir"] / "vectors.jsonl"
    colab_env["out_dir"].mkdir(exist_ok=True)
    _write_vectors(vfile, [{"chunk_id": "c_pend", "notebook_id": "nb1", "vector": _unit_vector()}])

    r1 = sync_vectors(vfile, colab_env["vdb"], colab_env["kdb"])
    assert r1 == {"synced": 1, "inserted": 1, "updated": 0, "pending_after": 0}

    # Re-sync del MISMO archivo: no inserta nada nuevo, solo reemplaza
    r2 = sync_vectors(vfile, colab_env["vdb"], colab_env["kdb"])
    assert r2 == {"synced": 1, "inserted": 0, "updated": 1, "pending_after": 0}

    con = sqlite3.connect(f"file:{colab_env['vdb']}?mode=ro", uri=True)
    assert con.execute("SELECT COUNT(*) FROM chunk_embeddings").fetchone()[0] == 2  # c_done + c_pend
    con.close()


def test_sync_vectors_atomico_ante_registro_invalido(colab_env):
    vfile = colab_env["out_dir"] / "vectors_bad.jsonl"
    colab_env["out_dir"].mkdir(exist_ok=True)
    _write_vectors(vfile, [
        {"chunk_id": "c_pend", "notebook_id": "nb1", "vector": _unit_vector()},
        {"chunk_id": "c_done", "notebook_id": "nb1", "vector": [0.1] * 128},  # dim incorrecta
    ])

    with pytest.raises(ValueError, match="dim"):
        sync_vectors(vfile, colab_env["vdb"], colab_env["kdb"])

    con = sqlite3.connect(f"file:{colab_env['vdb']}?mode=ro", uri=True)
    assert con.execute("SELECT COUNT(*) FROM chunk_embeddings").fetchone()[0] == 1  # intacto
    con.close()
    _, count = export_pending(colab_env["kdb"], colab_env["vdb"], colab_env["out_dir"])
    assert count == 1  # c_pend sigue pendiente


def test_sync_vectors_rechaza_chunk_desconocido(colab_env):
    vfile = colab_env["out_dir"] / "vectors_unknown.jsonl"
    colab_env["out_dir"].mkdir(exist_ok=True)
    _write_vectors(vfile, [{"chunk_id": "c_fantasma", "notebook_id": "nb1", "vector": _unit_vector()}])
    with pytest.raises(ValueError, match="no existen"):
        sync_vectors(vfile, colab_env["vdb"], colab_env["kdb"])


def test_verify_index_reporta_cero_pendientes(colab_env):
    report = verify_index(colab_env["kdb"], colab_env["vdb"], run_control_queries=False)
    assert report["checks"]["pending_chunks"] == 1  # c_pend aún sin vector
    assert report["ok"] is False

    vfile = colab_env["out_dir"] / "vectors.jsonl"
    colab_env["out_dir"].mkdir(exist_ok=True)
    _write_vectors(vfile, [{"chunk_id": "c_pend", "notebook_id": "nb1", "vector": _unit_vector()}])
    sync_vectors(vfile, colab_env["vdb"], colab_env["kdb"])

    report = verify_index(colab_env["kdb"], colab_env["vdb"], run_control_queries=False)
    assert report["checks"]["pending_chunks"] == 0
    assert report["checks"]["integrity_knowledge_store"] == "ok"
    assert report["checks"]["integrity_vector_store"] == "ok"
    assert report["ok"] is True


def test_control_queries_definidas():
    labels = {lbl for lbl, _, _ in CONTROL_QUERIES}
    assert labels == {"in_scope", "ood", "coloquial"}
