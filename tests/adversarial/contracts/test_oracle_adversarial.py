"""Adversarial and relational integrity testing for Oracle Benchmark in S3.2."""

import json
from pathlib import Path
import pytest

from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.contracts.oracle import (
    BenchmarkCategory,
    OracleDataset,
    OracleQuery,
    RelevanceGrade,
    RelevantChunk,
)
from study_engine.retrieval.oracle import (
    OracleIntegrityError,
    OracleValidationError,
    validate_oracle_dataset,
)
from study_engine.storage.knowledge_store import KnowledgeStore


@pytest.fixture
def populated_knowledge_store(tmp_path: Path) -> KnowledgeStore:
    """Populates a temporary KnowledgeStore using the authentic data/fixtures/reference_corpus.json."""
    corpus_path = Path("data/fixtures/reference_corpus.json")
    with open(corpus_path, "r", encoding="utf-8") as f:
        corpus_data = json.load(f)

    store = KnowledgeStore(tmp_path / "reference_corpus.db")
    store.initialize()

    # Ingest notebooks
    for nb in corpus_data["notebooks"]:
        store.create_notebook(Notebook(
            id=nb["id"], name=nb["name"], description=nb["description"], subject=nb["subject"]
        ))

    # Ingest sources and link to notebooks
    for src in corpus_data["sources"]:
        manifest = SourceManifest(
            source_id=src["source_id"],
            filename=src["filename"],
            byte_size=src["byte_size"],
            sha256=src["sha256"],
        )
        store.save_source(SourceRecord(source_id=src["source_id"], manifest=manifest))
        store.link_source_to_notebook(src["notebook_id"], src["source_id"])

    # Ingest documents
    for doc in corpus_data["documents"]:
        store.save_document(Document(
            id=doc["id"], source_id=doc["source_id"], title=doc["title"], content=doc["content"]
        ))

    # Ingest chunks
    chunks = [
        Chunk(
            id=c["id"],
            document_id=c["document_id"],
            source_id=c["source_id"],
            content=c["content"],
            index=c["index"],
        )
        for c in corpus_data["chunks"]
    ]
    store.save_chunks(chunks)

    return store


def test_adversarial_oracle_reference_fixture_passes_validation(populated_knowledge_store: KnowledgeStore):
    """Verify that the authentic data/fixtures/reference_oracle.json passes 100% relational validation."""
    oracle_path = Path("data/fixtures/reference_oracle.json")
    with open(oracle_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)

    dataset = OracleDataset.model_validate(raw_data)
    assert dataset.version == "1.0.0"
    assert len(dataset.queries) == 6

    # Validate against physical KnowledgeStore
    validate_oracle_dataset(dataset, store=populated_knowledge_store)


def test_adversarial_oracle_detects_non_existent_chunk(populated_knowledge_store: KnowledgeStore):
    """Integrity check: detect when an Oracle query references a fake or non-existent chunk_id."""
    fake_query = OracleQuery(
        id="q-fake-chunk",
        notebook_id="fadena-so",
        query="proceso fantasma",
        category=BenchmarkCategory.DEFINITION,
        relevant=[
            RelevantChunk(chunk_id="chunk_non_existent_999", grade=RelevanceGrade.DIRECT, rationale="Fake")
        ],
        rationale="Test detecting non-existent chunk in knowledge store",
    )
    dataset = OracleDataset(version="1.0.0", queries=[fake_query])

    with pytest.raises(OracleIntegrityError) as exc_info:
        validate_oracle_dataset(dataset, store=populated_knowledge_store)

    assert "chunk_non_existent_999" in str(exc_info.value)
    assert "does not exist in store" in str(exc_info.value)


def test_adversarial_oracle_detects_non_existent_notebook(populated_knowledge_store: KnowledgeStore):
    """Integrity check: detect when an Oracle query references a notebook that does not exist."""
    fake_query = OracleQuery(
        id="q-fake-nb",
        notebook_id="notebook_inexistente_xyz",
        query="consulta",
        category=BenchmarkCategory.DEFINITION,
        relevant=[],
        rationale="Test detecting non-existent notebook",
    )
    dataset = OracleDataset(version="1.0.0", queries=[fake_query])

    with pytest.raises(OracleIntegrityError) as exc_info:
        validate_oracle_dataset(dataset, store=populated_knowledge_store)

    assert "notebook_inexistente_xyz" in str(exc_info.value)
    assert "does not exist in store" in str(exc_info.value)


def test_adversarial_oracle_detects_cross_notebook_curricular_leakage(populated_knowledge_store: KnowledgeStore):
    """Integrity check: detect when an Oracle query assigns a chunk belonging to a DIFFERENT notebook."""
    # prog:tree:01 belongs to fadena-prog, but query is scoped to fadena-so!
    illegal_query = OracleQuery(
        id="q-illegal-cross",
        notebook_id="fadena-so",
        query="árboles en SO",
        category=BenchmarkCategory.DEFINITION,
        relevant=[
            RelevantChunk(chunk_id="prog:tree:01", grade=RelevanceGrade.DIRECT, rationale="Illegal cross-assignment")
        ],
        rationale="Testing cross-notebook contamination detection",
    )
    dataset = OracleDataset(version="1.0.0", queries=[illegal_query])

    with pytest.raises(OracleIntegrityError) as exc_info:
        validate_oracle_dataset(dataset, store=populated_knowledge_store)

    assert "Curricular isolation violated" in str(exc_info.value)
    assert "prog:tree:01" in str(exc_info.value)
    assert "NOT linked to notebook 'fadena-so'" in str(exc_info.value)


def test_adversarial_oracle_query_payload_fuzzing():
    """Fuzzing query strings with C syntax, pointers, big strings, and diacritics."""
    fuzz_strings = [
        "malloc(sizeof(struct Node*))",
        "O(N * log(N)) + O(1)",
        "ÁRBOL BINARIO DE BÚSQUEDA Y PAGINACIÓN",
        "💻 Procesos y Memoria Virtual ⚡",
        "x" * 3000,
    ]
    for idx, s in enumerate(fuzz_strings):
        q = OracleQuery(
            id=f"q-fuzz-{idx}",
            notebook_id="fadena-prog",
            query=s,
            category=BenchmarkCategory.CODE_SYMBOL,
            relevant=[],
            rationale="Fuzz testing string resilience",
        )
        assert len(q.query) > 0


def test_adversarial_oracle_validation_standalone_without_store():
    """Verify that validate_oracle_dataset executes standalone syntax checks when store is None."""
    q_valid = OracleQuery(
        id="q-standalone",
        notebook_id="fadena-so",
        query="proceso",
        category=BenchmarkCategory.DEFINITION,
        relevant=[RelevantChunk(chunk_id="c1", grade=RelevanceGrade.DIRECT, rationale="r")],
        rationale="r",
    )
    ds = OracleDataset(version="1.0.0", queries=[q_valid])
    # Must pass without store
    validate_oracle_dataset(ds, store=None)

    # Empty version check
    ds_bad_version = OracleDataset.model_construct(version="  ", queries=[q_valid], metadata={})
    with pytest.raises(OracleValidationError) as exc_info:
        validate_oracle_dataset(ds_bad_version, store=None)
    assert "version cannot be empty" in str(exc_info.value)
