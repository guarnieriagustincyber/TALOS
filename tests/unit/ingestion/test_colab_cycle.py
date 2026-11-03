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


def _unit_vector(dim: int = 1024) -> list:
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

    vstore = SQLiteVectorStore(vdb, read_only=False)
    vstore.save_records([
        VectorRecord(
            chunk_id="c_done", notebook_id="nb1", source_id="src1",
            provider_id="sentence_transformers", model_id="Qwen3-Embedding-0.6B",
            dimensions=1024, vector=_unit_vector(),
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
    assert rows[0]["_meta"]["contract"]["dimensions"] == 1024
    assert rows[1:] == [{"chunk_id": "c_pend", "notebook_id": "nb1", "text": "texto pendiente"}]



def test_export_pending_esquema_moderno_space_id_null(colab_env):
    """
    Regresión para esquema moderno con columna space_id pero vector legacy NULL.
    
    En esquema moderno (columna space_id presente), un vector con space_id=NULL
    NO acredita cobertura T07 para ningún espacio. Ambos chunks (c_done con 
    vector legacy NULL y c_pend sin vector) deben reportarse como pendientes.
    
    Este test valida el comportamiento correcto T07: un vector sin space_id
    explícito en esquema moderno NO acredita cobertura para ningún espacio T07.
    """
    from study_engine.retrieval.vector_store import SQLiteVectorStore, VectorRecord
    from study_engine.cli import DEFAULT_CONTRACT_PATH, load_contract
    
    # Reutilizar el fixture pero verificar el esquema del vector store
    vstore = SQLiteVectorStore(colab_env["vdb"], read_only=True)
    try:
        # Verificar que el esquema tiene columna space_id
        assert vstore._has_space_id, "Esquema moderno debe tener columna space_id"
        # Verificar que el vector existente tiene space_id NULL
        record = vstore.get_by_chunk_id("c_done")
        assert record is not None
        assert record.space_id is None, "Vector legacy debe tener space_id NULL"
    finally:
        vstore.close()
    
    # Con espacio T07 no identificado (space_id=None), _pending_pairs debe
    # reportar AMBOS chunks como pendientes porque el vector legacy NULL
    # NO acredita cobertura para ningún espacio T07
    contract = load_contract() if DEFAULT_CONTRACT_PATH.exists() else None
    out, count = export_pending(colab_env["kdb"], colab_env["vdb"], colab_env["out_dir"], contract_path=DEFAULT_CONTRACT_PATH if DEFAULT_CONTRACT_PATH.exists() else None)
    
    # Resultado correcto T07: ambos chunks pendientes (c_done con space_id=NULL no acredita cobertura)
    assert count == 2, f"Esperado 2 pendientes (legacy NULL no cubre T07), obtuvo {count}"
    
    rows = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["_meta"]["schema"] == "talos-pending-v1"
    assert rows[0]["_meta"]["contract"]["dimensions"] == 1024
    # Ambos chunks deben aparecer como pendientes
    pending_chunks = {row["chunk_id"] for row in rows[1:]}
    assert pending_chunks == {"c_done", "c_pend"}



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


@pytest.fixture
def pending_identity_env(tmp_path):
    """Agent-authored synthetic databases and canonical deterministic test space."""
    from study_engine.retrieval.embedding import DeterministicHashEmbedder
    from study_engine.retrieval.vector_identity import vector_space_id

    provider = DeterministicHashEmbedder()
    sid = vector_space_id(provider)
    assert sid is not None
    kdb, vdb = tmp_path / "knowledge.db", tmp_path / "vectors.db"
    con = sqlite3.connect(kdb)
    con.executescript("""
        CREATE TABLE chunks (id TEXT PRIMARY KEY, source_id TEXT, content TEXT);
        CREATE TABLE notebook_sources (notebook_id TEXT, source_id TEXT);
        INSERT INTO chunks VALUES ('done', 'synthetic', 'indexed'), ('pending', 'synthetic', 'pending');
        INSERT INTO notebook_sources VALUES ('nb', 'synthetic');
    """)
    con.commit()
    con.close()
    store = SQLiteVectorStore(vdb, read_only=False)
    vector = provider.embed_passages(["indexed"])[0]
    store.save_records([VectorRecord(
        chunk_id="done", notebook_id="nb", source_id="synthetic",
        provider_id=provider.provider_id, model_id=provider.model_id,
        dimensions=provider.dimensions, vector=vector, space_id=sid,
    )])
    store.close()
    contract = {"provider_id": provider.provider_id, "model_id": provider.model_id,
                "dimensions": provider.dimensions, "space_id": sid}
    contract_path = tmp_path / "contract.json"
    contract_path.write_text(json.dumps(contract))
    from study_engine.cli import VECTORS_SCHEMA
    upload = tmp_path / "vectors.jsonl"
    upload.write_text(json.dumps({"_meta": {"schema": VECTORS_SCHEMA, "contract": contract}}) + "\n" +
                      json.dumps({"chunk_id": "pending", "notebook_id": "nb", "vector": vector, "space_id": sid}) + "\n")
    return kdb, vdb, contract_path, upload, sid


def test_pending_identity_sync_and_idempotency(pending_identity_env):
    kdb, vdb, contract, upload, sid = pending_identity_env
    first = sync_vectors(upload, vdb, kdb, contract_path=contract)
    assert first == {"synced": 1, "inserted": 1, "updated": 0, "pending_after": 0}
    second = sync_vectors(upload, vdb, kdb, contract_path=contract)
    assert second == {"synced": 1, "inserted": 0, "updated": 1, "pending_after": 0}
    with sqlite3.connect(vdb) as con:
        assert con.execute("SELECT count(*), count(DISTINCT space_id) FROM chunk_embeddings").fetchone() == (2, 1)
        assert con.execute("SELECT DISTINCT space_id FROM chunk_embeddings").fetchall() == [(sid,)]


@pytest.mark.parametrize("identity", [None, "different"])
def test_pending_identity_excludes_null_and_other_space(pending_identity_env, identity):
    from study_engine.cli import _pending_pairs
    from study_engine.retrieval.embedding import DeterministicHashEmbedder
    from study_engine.retrieval.vector_identity import vector_space_id

    kdb, vdb, _, _, sid = pending_identity_env
    other = vector_space_id(DeterministicHashEmbedder(model_id="synthetic-other")) if identity else None
    with sqlite3.connect(vdb) as con:
        con.execute("UPDATE chunk_embeddings SET space_id = ?", (other,))
    assert len(_pending_pairs(kdb, vdb, dimensions=128, space_id=sid)) == 2
    assert len(_pending_pairs(kdb, vdb, dimensions=128, space_id=None)) == 2


def test_pending_identity_rejection_preserves_rows_and_pending(pending_identity_env):
    from study_engine.cli import _pending_pairs

    kdb, vdb, contract, upload, sid = pending_identity_env
    rows = upload.read_text().splitlines()
    invalid = json.loads(rows[1])
    invalid["space_id"] = "incompatible"
    upload.write_text("\n".join([*rows, json.dumps(invalid)]) + "\n")
    with sqlite3.connect(vdb) as con:
        before = con.execute("SELECT * FROM chunk_embeddings").fetchall()
    with pytest.raises(ValueError, match="incompatible"):
        sync_vectors(upload, vdb, kdb, contract_path=contract)
    with sqlite3.connect(vdb) as con:
        assert con.execute("SELECT * FROM chunk_embeddings").fetchall() == before
    assert [r[0] for r in _pending_pairs(kdb, vdb, dimensions=128, space_id=sid)] == ["pending"]


def test_pending_identity_ambiguous_index_rejected(pending_identity_env):
    kdb, vdb, contract, upload, _ = pending_identity_env
    with sqlite3.connect(vdb) as con:
        con.execute("INSERT INTO chunk_embeddings SELECT 'pending', notebook_id, source_id, provider_id, model_id, dimensions, vector, 'other' FROM chunk_embeddings")
        before = con.execute("SELECT * FROM chunk_embeddings ORDER BY chunk_id").fetchall()
    with pytest.raises(ValueError, match="Ambiguous"):
        sync_vectors(upload, vdb, kdb, contract_path=contract)
    with sqlite3.connect(vdb) as con:
        assert con.execute("SELECT * FROM chunk_embeddings ORDER BY chunk_id").fetchall() == before


def test_pending_identity_modern_unknown_remains_pending(pending_identity_env):
    kdb, vdb, contract, upload, _ = pending_identity_env
    with sqlite3.connect(vdb) as con:
        con.execute("UPDATE chunk_embeddings SET space_id = NULL")
    rows = upload.read_text().splitlines()
    record = json.loads(rows[1])
    record.pop("space_id")
    upload.write_text(rows[0] + "\n" + json.dumps(record) + "\n")
    result = sync_vectors(upload, vdb, kdb, contract_path=contract)
    assert result["pending_after"] == 2  # Modern NULL is not T07 coverage.


def test_pending_identity_explicit_legacy_schema(pending_identity_env):
    from study_engine.cli import _pending_pairs

    kdb, vdb, contract, upload, _ = pending_identity_env
    with sqlite3.connect(vdb) as con:
        con.execute("ALTER TABLE chunk_embeddings DROP COLUMN space_id")
    # The existing legacy read contract remains dimension-based, not T07.
    assert [r[0] for r in _pending_pairs(kdb, vdb, dimensions=128)] == ["pending"]
    with pytest.raises(ValueError, match="migration required"):
        sync_vectors(upload, vdb, kdb, contract_path=contract)


@pytest.mark.parametrize("stored_identity, expected_pending", [("target", 0), ("other", 2), (None, 2)])
def test_verify_identity_exact_scope_read_only(pending_identity_env, monkeypatch, stored_identity, expected_pending):
    import hashlib
    from study_engine.retrieval.embedding import DeterministicHashEmbedder
    from study_engine.retrieval.vector_identity import vector_space_id

    kdb, vdb, contract, _, sid = pending_identity_env
    identity = sid if stored_identity == "target" else vector_space_id(
        DeterministicHashEmbedder(model_id="synthetic-other")
    ) if stored_identity == "other" else None
    with sqlite3.connect(vdb) as con:
        con.execute("INSERT INTO chunk_embeddings SELECT 'pending', notebook_id, source_id, provider_id, model_id, dimensions, vector, space_id FROM chunk_embeddings")
        con.execute("UPDATE chunk_embeddings SET space_id = ?", (identity,))
    before = [hashlib.sha256(p.read_bytes()).hexdigest() for p in (kdb, vdb)]
    connect = sqlite3.connect
    opened = []

    def read_only_connect(database, *args, **kwargs):
        assert kwargs.get("uri") is True and "mode=ro" in str(database)
        opened.append(str(database))
        return connect(database, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", read_only_connect)
    report = verify_index(kdb, vdb, run_control_queries=False, contract_path=contract)
    assert report["checks"]["pending_chunks"] == expected_pending
    assert report["checks"]["space_id"] == sid
    assert report["checks"]["coverage_scope"] == "T07"
    assert report["ok"] is (expected_pending == 0)
    assert opened
    assert [hashlib.sha256(p.read_bytes()).hexdigest() for p in (kdb, vdb)] == before


@pytest.mark.parametrize("empty", [False, True])
def test_verify_identity_unknown_never_approves(pending_identity_env, empty):
    kdb, vdb, _, _, _ = pending_identity_env
    with sqlite3.connect(vdb) as con:
        if empty:
            con.execute("DELETE FROM chunk_embeddings")
        else:
            con.execute("INSERT INTO chunk_embeddings SELECT 'pending', notebook_id, source_id, provider_id, model_id, dimensions, vector, 'other' FROM chunk_embeddings")
    if empty:
        with sqlite3.connect(kdb) as con:
            con.execute("DELETE FROM chunks")
    report = verify_index(kdb, vdb, run_control_queries=False)
    assert report["checks"]["coverage_scope"] == "UNKNOWN"
    assert report["checks"]["pending_chunks"] == (0 if empty else 2)
    assert report["ok"] is False


def test_verify_identity_ambiguous_target_rejected(pending_identity_env):
    kdb, vdb, contract, _, sid = pending_identity_env
    data = json.loads(contract.read_text())
    data["space_id"] = [sid, "other"]
    contract.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="unambiguous"):
        verify_index(kdb, vdb, run_control_queries=False, contract_path=contract)


def test_verify_identity_legacy_not_t07(pending_identity_env):
    kdb, vdb, contract, _, sid = pending_identity_env
    with sqlite3.connect(vdb) as con:
        con.execute("INSERT INTO chunk_embeddings SELECT 'pending', notebook_id, source_id, provider_id, model_id, dimensions, vector, space_id FROM chunk_embeddings")
        con.execute("ALTER TABLE chunk_embeddings DROP COLUMN space_id")
    data = json.loads(contract.read_text())
    data.pop("space_id")
    contract.write_text(json.dumps(data))
    legacy = verify_index(kdb, vdb, run_control_queries=False, contract_path=contract)
    assert legacy["checks"]["coverage_scope"] == "LEGACY"
    assert legacy["checks"]["pending_chunks"] == 0 and legacy["ok"] is True
    data["space_id"] = sid
    contract.write_text(json.dumps(data))
    t07 = verify_index(kdb, vdb, run_control_queries=False, contract_path=contract)
    assert t07["checks"]["coverage_scope"] == "LEGACY"
    assert t07["ok"] is False


def test_verify_identity_cli_contract_forwarded(pending_identity_env, capsys):
    from argparse import Namespace
    from study_engine.cli import _cmd_verify_index

    kdb, vdb, contract, _, sid = pending_identity_env
    result = _cmd_verify_index(Namespace(knowledge_db=kdb, vector_db=vdb, contract=contract, no_control_queries=True))
    assert result == 1  # One genuine pending chunk in the requested space.
    assert sid in capsys.readouterr().out
