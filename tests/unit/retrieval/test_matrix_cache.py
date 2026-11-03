"""Tests del caché de matrices vectoriales por notebook (COMMIT 0 perf slice).

Contrato:
- Dos llamadas a get_vector_matrix sin cambios devuelven LA MISMA matriz
  (misma instancia, sin recarga).
- save_records en la misma conexión invalida el notebook afectado.
- Un commit desde OTRA conexión/proceso (simula `talos sync-vectors`)
  se detecta vía PRAGMA data_version y fuerza recarga.
- Notebooks no afectados siguen sirviendo desde caché.
"""

import sqlite3
import time

from study_engine.retrieval.vector_store import SQLiteVectorStore, VectorRecord


def _rec(chunk_id: str, nb: str, dim: int = 8) -> VectorRecord:
    return VectorRecord(
        chunk_id=chunk_id,
        notebook_id=nb,
        source_id="src1",
        provider_id="local_onnx",
        model_id="m",
        dimensions=dim,
        vector=[0.1] * dim,
    )


def test_segunda_llamada_usa_cache_misma_instancia():
    store = SQLiteVectorStore(":memory:", read_only=False)
    store.save_records([_rec("c1", "nb1"), _rec("c2", "nb1")])
    ids1, m1 = store.get_vector_matrix("nb1")
    ids2, m2 = store.get_vector_matrix("nb1")
    assert m1 is m2  # misma instancia => no se recargó
    assert ids1 == ids2 == ["c1", "c2"]
    store.close()


def test_save_records_invalida_notebook_afectado():
    store = SQLiteVectorStore(":memory:", read_only=False)
    store.save_records([_rec("c1", "nb1"), _rec("c9", "nb_otro")])
    _, m1 = store.get_vector_matrix("nb1")
    _, m_otro1 = store.get_vector_matrix("nb_otro")

    store.save_records([_rec("c2", "nb1")])

    ids2, m2 = store.get_vector_matrix("nb1")
    _, m_otro2 = store.get_vector_matrix("nb_otro")
    assert m2 is not m1                    # nb1 recargado
    assert ids2 == ["c1", "c2"]            # y ve el vector nuevo
    assert m_otro2 is m_otro1              # nb_otro intacto en caché
    store.close()


def test_commit_externo_invalida_por_data_version(tmp_path):
    """Simula `talos sync-vectors` en otro proceso: commit por otra conexión."""
    db = tmp_path / "vectors.db"
    store = SQLiteVectorStore(db, read_only=False)
    store.save_records([_rec("c1", "nb1")])
    _, m1 = store.get_vector_matrix("nb1")

    # Otra conexión (otro "proceso") inserta y commitea
    other = SQLiteVectorStore(db, read_only=False)
    other.save_records([_rec("c2", "nb1")])
    other.close()

    ids2, m2 = store.get_vector_matrix("nb1")
    assert m2 is not m1
    assert ids2 == ["c1", "c2"]
    store.close()
