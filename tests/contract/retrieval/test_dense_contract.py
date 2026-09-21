"""Contract tests for DenseRetriever in S3.4."""

from pathlib import Path
import pytest

from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.contracts.retrieval import RetrievalRequest
from study_engine.retrieval.dense import DenseRetrievalError, DenseRetriever
from study_engine.retrieval.embedding import MockEmbeddingProvider
from study_engine.retrieval.indexer import index_notebook_chunks
from study_engine.retrieval.vector_store import SQLiteVectorStore, VectorRecord
from study_engine.storage.knowledge_store import KnowledgeStore


@pytest.fixture
def setup_isolation_env(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "dense_contract.db")
    store.initialize()

    # Notebook SO
    store.create_notebook(Notebook(id="nb-so", name="SO"))
    rec_so = SourceRecord(
        source_id="src-so",
        manifest=SourceManifest(
            source_id="src-so",
            filename="so.pdf",
            byte_size=10,
            sha256="a" * 64,
        ),
    )
    docs_so = [
        Document(id="doc-so", source_id="src-so", title="SO", content="c")
    ]
    chunks_so = [
        Chunk(
            id="c-so",
            document_id="doc-so",
            source_id="src-so",
            content="SO chunk",
            index=0,
        )
    ]
    store.store_ingestion_bundle(
        rec_so, docs_so, chunks_so, notebook_id="nb-so"
    )

    # Notebook PROG
    store.create_notebook(Notebook(id="nb-prog", name="Prog"))
    rec_prog = SourceRecord(
        source_id="src-prog",
        manifest=SourceManifest(
            source_id="src-prog",
            filename="prog.pdf",
            byte_size=10,
            sha256="b" * 64,
        ),
    )
    docs_prog = [
        Document(id="doc-prog", source_id="src-prog", title="Prog", content="c")
    ]
    chunks_prog = [
        Chunk(
            id="c-prog",
            document_id="doc-prog",
            source_id="src-prog",
            content="Prog chunk",
            index=0,
        )
    ]
    store.store_ingestion_bundle(
        rec_prog, docs_prog, chunks_prog, notebook_id="nb-prog"
    )

    vec_store = SQLiteVectorStore(tmp_path / "vecs.db")
    provider = MockEmbeddingProvider(dimensions=384)

    index_notebook_chunks(store, vec_store, provider, "nb-so")
    index_notebook_chunks(store, vec_store, provider, "nb-prog")

    retriever = DenseRetriever(store, vec_store, provider)
    return store, vec_store, provider, retriever


def test_layer1_store_level_isolation(setup_isolation_env):
    """Layer 1: Vector Store query only retrieves vectors for requested notebook."""
    store, vec_store, provider, retriever = setup_isolation_env
    assert len(vec_store.get_by_notebook("nb-so")) == 1
    assert len(vec_store.get_by_notebook("nb-prog")) == 1

    so_recs = vec_store.get_by_notebook("nb-so")
    assert so_recs[0].chunk_id == "c-so"
    assert so_recs[0].notebook_id == "nb-so"


def test_layer2_candidate_level_isolation(setup_isolation_env, monkeypatch):
    """Layer 2: DenseRetriever validates all candidates belong to requested notebook."""
    store, vec_store, provider, retriever = setup_isolation_env

    # Maliciously supply a vector with mismatched notebook_id in nb-so scope
    corrupted_vec = VectorRecord(
        chunk_id="c-so-corrupt",
        notebook_id="nb-prog",  # Wrong notebook!
        source_id="src-so",
        provider_id="mock",
        model_id="mock-sha256-v1",
        dimensions=384,
        vector=[0.1] * 384,
    )
    monkeypatch.setattr(
        vec_store, "get_by_notebook", lambda *args, **kwargs: [corrupted_vec]
    )



    req = RetrievalRequest(query="test", notebook_id="nb-so", top_k=5)
    with pytest.raises(DenseRetrievalError) as exc:
        retriever.retrieve(req)
    assert "Curricular isolation violated" in str(exc.value)



def test_layer3_relational_isolation(setup_isolation_env):
    """Layer 3: Relational verification catches chunks not linked to notebook sources."""
    store, vec_store, provider, retriever = setup_isolation_env

    # Ingest a third notebook with unlinked chunk
    store.create_notebook(Notebook(id="nb-rogue", name="Rogue"))
    rec_rogue = SourceRecord(
        source_id="src-rogue",
        manifest=SourceManifest(
            source_id="src-rogue",
            filename="rogue.pdf",
            byte_size=1,
            sha256="c" * 64,
        ),
    )
    docs_rogue = [
        Document(id="doc-rogue", source_id="src-rogue", title="R", content="c")
    ]
    chunks_rogue = [
        Chunk(
            id="c-rogue",
            document_id="doc-rogue",
            source_id="src-rogue",
            content="Rogue",
            index=0,
        )
    ]
    store.store_ingestion_bundle(
        rec_rogue, docs_rogue, chunks_rogue, notebook_id="nb-rogue"
    )

    # Maliciously save rogue chunk into nb-so vector store with claimed notebook_id="nb-so"
    forged_vec = VectorRecord(
        chunk_id="c-rogue",
        notebook_id="nb-so",  # Forged notebook_id to bypass Layer 2
        source_id="src-rogue",
        provider_id="mock",
        model_id="mock-sha256-v1",
        dimensions=384,
        vector=[0.9] * 384,
    )
    vec_store.save_records([forged_vec])

    req = RetrievalRequest(query="test", notebook_id="nb-so", top_k=5)
    with pytest.raises(DenseRetrievalError) as exc:
        retriever.retrieve(req)
    assert "not linked to 'nb-so'" in str(exc.value)


def test_missing_chunk_in_knowledge_store(setup_isolation_env):
    """Retriever fails fast if vector store has orphan vector with no chunk in store."""
    store, vec_store, provider, retriever = setup_isolation_env

    orphan_vec = VectorRecord(
        chunk_id="c-ghost",
        notebook_id="nb-so",
        source_id="src-so",
        provider_id="mock",
        model_id="mock-sha256-v1",
        dimensions=384,
        vector=[0.5] * 384,
    )
    vec_store.save_records([orphan_vec])

    req = RetrievalRequest(query="test", notebook_id="nb-so", top_k=5)
    with pytest.raises(DenseRetrievalError) as exc:
        retriever.retrieve(req)
    assert "references non-existent chunk" in str(exc.value)
