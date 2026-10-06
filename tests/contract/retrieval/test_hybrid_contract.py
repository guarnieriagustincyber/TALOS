"""Contract tests for HybridRetriever and FusionStrategy in S3.5."""

from pathlib import Path
import pytest

from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.contracts.retrieval import (
    RetrievalRequest,
    RetrievalResponse,
    RetrievalStrategy,
)
from study_engine.retrieval.base import BaseRetriever
from study_engine.retrieval.dense import DenseRetrievalError, DenseRetriever
from study_engine.retrieval.embedding import MockEmbeddingProvider
from study_engine.retrieval.fusion import FusedCandidate
from study_engine.retrieval.hybrid import HybridRetriever
from study_engine.retrieval.indexer import index_notebook_chunks
from study_engine.retrieval.lexical import LexicalRetriever
from study_engine.retrieval.vector_store import SQLiteVectorStore
from study_engine.storage.knowledge_store import KnowledgeStore


@pytest.fixture
def setup_hybrid_contract_env(tmp_path: Path):
    store = KnowledgeStore(tmp_path / "contract_hybrid.db")
    store.initialize()
    store.create_notebook(Notebook(id="nb-so", name="SO"))
    store.create_notebook(Notebook(id="nb-prog", name="Prog"))

    # Ingest nb-so bundle
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
            id="c-so-1",
            document_id="doc-so",
            source_id="src-so",
            content="Process",
            index=0,
        ),
        Chunk(
            id="c-so-2",
            document_id="doc-so",
            source_id="src-so",
            content="Memory",
            index=1,
        ),
    ]
    store.store_ingestion_bundle(
        rec_so, docs_so, chunks_so, notebook_id="nb-so"
    )

    # Ingest nb-prog bundle
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
        Document(
            id="doc-prog", source_id="src-prog", title="Prog", content="c"
        )
    ]

    chunks_prog = [
        Chunk(
            id="c-prog-1",
            document_id="doc-prog",
            source_id="src-prog",
            content="Pointer",
            index=0,
        ),
    ]
    store.store_ingestion_bundle(
        rec_prog, docs_prog, chunks_prog, notebook_id="nb-prog"
    )

    vec_store = SQLiteVectorStore(tmp_path / "contract_vecs.db", read_only=False)
    provider = MockEmbeddingProvider(dimensions=384)
    index_notebook_chunks(store, vec_store, provider, "nb-so")
    index_notebook_chunks(store, vec_store, provider, "nb-prog")

    lex = LexicalRetriever(store)
    dense = DenseRetriever(store, vec_store, provider)
    hybrid = HybridRetriever(store, lex, dense)

    return store, lex, dense, hybrid


def test_contract_hybrid_adherence_to_protocol(setup_hybrid_contract_env):
    _, _, _, hybrid = setup_hybrid_contract_env
    assert isinstance(hybrid, BaseRetriever)


def test_contract_hybrid_invariants(setup_hybrid_contract_env):
    _, _, _, hybrid = setup_hybrid_contract_env
    req = RetrievalRequest(
        query="Process",
        notebook_id="nb-so",
        top_k=2,
        strategy=RetrievalStrategy.HYBRID,
    )
    resp = hybrid.retrieve(req)

    assert isinstance(resp, RetrievalResponse)
    assert resp.notebook_id == "nb-so"
    assert len(resp.items) <= 2

    # Invariant 1: Curricular isolation
    for c in resp.items:
        assert c.notebook_id == "nb-so"

    # Invariant 2: Monotonic score ordering
    for i in range(len(resp.items) - 1):
        assert resp.items[i].score >= resp.items[i + 1].score

    # Invariant 3: 1-indexed ranks
    for idx, c in enumerate(resp.items):
        assert c.rank == idx + 1


def test_contract_hybrid_catches_cross_notebook_fused_candidate(
    setup_hybrid_contract_env,
):
    store, lex, dense, _ = setup_hybrid_contract_env

    class MaliciousFusion:
        def fuse(self, lexical_items, dense_items, top_k):
            # Emits a candidate claiming another notebook
            return [
                FusedCandidate(
                    chunk_id="c-so-1",
                    document_id="doc-so",
                    source_id="src-so",
                    notebook_id="nb-prog",  # Corrupted notebook!
                    score=1.0,
                    content="Corrupted",
                )
            ]

    bad_hybrid = HybridRetriever(
        store, lex, dense, fusion_strategy=MaliciousFusion()
    )
    req = RetrievalRequest(query="Process", notebook_id="nb-so", top_k=5)
    with pytest.raises(DenseRetrievalError) as exc:
        bad_hybrid.retrieve(req)
    assert "Curricular isolation violated" in str(exc.value)


def test_contract_hybrid_catches_unlinked_source_fused_candidate(
    setup_hybrid_contract_env,
):
    store, lex, dense, _ = setup_hybrid_contract_env

    class UnlinkedSourceFusion:
        def fuse(self, lexical_items, dense_items, top_k):
            # Emits chunk belonging to prog while query is for so
            return [
                FusedCandidate(
                    chunk_id="c-prog-1",
                    document_id="doc-prog",
                    source_id="src-prog",
                    notebook_id="nb-so",
                    score=1.0,
                    content="Unlinked",
                )
            ]

    bad_hybrid = HybridRetriever(
        store, lex, dense, fusion_strategy=UnlinkedSourceFusion()
    )
    req = RetrievalRequest(query="Process", notebook_id="nb-so", top_k=5)
    with pytest.raises(DenseRetrievalError) as exc:
        bad_hybrid.retrieve(req)
    assert "Curricular isolation violated" in str(exc.value)
    assert "not linked to 'nb-so'" in str(exc.value)


def test_contract_hybrid_catches_non_existent_chunk(setup_hybrid_contract_env):
    store, lex, dense, _ = setup_hybrid_contract_env

    class GhostChunkFusion:
        def fuse(self, lexical_items, dense_items, top_k):
            return [
                FusedCandidate(
                    chunk_id="ghost-chunk-999",
                    document_id="doc-so",
                    source_id="src-so",
                    notebook_id="nb-so",
                    score=1.0,
                    content="Ghost",
                )
            ]

    bad_hybrid = HybridRetriever(
        store, lex, dense, fusion_strategy=GhostChunkFusion()
    )
    req = RetrievalRequest(query="Process", notebook_id="nb-so", top_k=5)
    with pytest.raises(DenseRetrievalError) as exc:
        bad_hybrid.retrieve(req)
    assert "references non-existent chunk" in str(exc.value)
