"""End-to-end Gate 2 diagnostic validation with synthetic data.

Validates: snapshots -> proposals -> facet coverage -> evidence relations -> segment validation.
All offline/diagnostic; no runtime consumer exists.
"""
import hashlib
import json
import sqlite3
import tempfile
from pathlib import Path

import pytest

from study_engine.contracts.gate2_oracle import Gate2Dataset, Gate2OracleType, Gate2Query
from study_engine.diagnostics.gate2_snapshots import (
    Gate2SnapshotError,
    create_snapshots,
    backup_read_only_database,
    authorized_source_ids,
)
from study_engine.diagnostics.gate2_facet_coverage import evaluate_facet_coverage
from study_engine.diagnostics.gate2_evidence_relations import (
    EvidenceRecord,
    compare_evidence_records,
    load_evidence_records,
)
from study_engine.diagnostics.gate2_proposals import generate_qrel_proposals
from study_engine.diagnostics.gate2_segment_validation import validate_gate2_segments
from study_engine.retrieval.gate2_oracle import validate_gate2_contract, evaluate_gate2_observations
from study_engine.storage.knowledge_store import KnowledgeStore
from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.notebook import Notebook


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


@pytest.fixture
def synthetic_data(tmp_path):
    """Create synthetic knowledge store and Gate 2 dataset."""
    state = tmp_path / "state"
    state.mkdir()
    
    store = KnowledgeStore(state / "knowledge_store.db")
    store.initialize()
    
    # Create notebook and synthetic content
    store.create_notebook(Notebook(id="synthetic-g2", name="Synthetic Gate 2"))
    content = "Los punteros contienen direcciones de memoria para acceder a objetos.\n" \
              "Los semaforos coordinan el acceso a recursos compartidos."
    source_hash = hashlib.sha256(content.encode()).hexdigest()
    
    store.store_ingestion_bundle(
        SourceRecord(source_id="src-local", manifest=SourceManifest(
            source_id="src-local", filename="synthetic.txt", byte_size=len(content.encode()),
            sha256=source_hash,
        )), [Document(id="doc-local", source_id="src-local", title="Synthetic", content=content)],
        [Chunk(id="chunk-local-1", source_id="src-local", document_id="doc-local", content=content,
               page_start=1, page_end=1, index=0)], notebook_id="synthetic-g2",
    )
    store.close()
    
    # Create vector store
    from study_engine.retrieval.embedding import DeterministicHashEmbedder
    from study_engine.retrieval.vector_store import SQLiteVectorStore, VectorRecord
    from study_engine.retrieval.vector_identity import vector_space_id
    
    vstore = SQLiteVectorStore(tmp_path / "state" / "vector_store.db", read_only=False)
    embedder = DeterministicHashEmbedder(dimensions=128)
    vec = embedder.embed_passages(["Los punteros contienen direcciones de memoria para acceder a objetos."])[0]
    space = vector_space_id(embedder)
    vstore.save_records([VectorRecord(
        chunk_id="chunk-local-1", notebook_id="synthetic-g2", source_id="src-local",
        provider_id=embedder.provider_id, model_id=embedder.model_id,
        dimensions=embedder.dimensions, vector=vec, space_id=space,
    )])
    vstore.close()
    
    # Create Gate 2 dataset
    dataset = Gate2Dataset(
        version="synthetic-g2-v1",
        queries=[
            Gate2Query(
                query_id="q1", scope="synthetic-g2", query="punteros",
                oracle_type=Gate2OracleType.POSITIVE_IN_SCOPE,
                qrels_status="approved", qrels_provenance="fixture",
            ),
            Gate2Query(
                query_id="q2", scope="synthetic-g2", query="semaforos",
                oracle_type=Gate2OracleType.NEGATIVE_BY_SCOPE,
                qrels_status="approved", qrels_provenance="fixture",
            ),
        ],
    )
    
    qrels = {
        "q1": {"chunk-local-1": 2},
        "q2": {},
    }
    
    return {
        "knowledge_db": tmp_path / "state" / "knowledge_store.db",
        "vector_db": tmp_path / "state" / "vector_store.db",
        "dataset": dataset,
        "qrels": qrels,
    }


def test_snapshots(synthetic_data):
    """Test snapshot creation and verification."""
    temporary, manifest = create_snapshots(synthetic_data["knowledge_db"], synthetic_data["vector_db"])
    
    # Verify snapshots
    knowledge_copy = Path(manifest["snapshots"]["knowledge_db"]["path"])
    vector_copy = Path(manifest["snapshots"]["vector_db"]["path"])
    
    assert knowledge_copy.exists() and vector_copy.exists()
    
    # Verify ACL reading
    sources = authorized_source_ids(knowledge_copy, "synthetic-g2")
    assert "src-local" in sources
    
    # Verify source unchanged
    from study_engine.diagnostics.gate2_snapshots import verify_sources_unchanged
    verify_sources_unchanged(manifest, synthetic_data["knowledge_db"], synthetic_data["vector_db"])
    
    temporary.cleanup()


def test_facet_coverage():
    """Test facet coverage evaluation."""
    facets = [
        {"facet_id": "f1", "evidence_ids": ["e1", "e2"]},
        {"facet_id": "f2", "evidence_ids": ["e3"]},
    ]
    grades = {"e1": 2, "e2": 1, "e3": 2}
    
    result = evaluate_facet_coverage(facets, grades, minimum_grade=2)
    
    assert result["minimum_grade"] == 2
    assert len(result["facets"]) == 2
    assert result["facets"][0]["covered"] == True  # e1 grade 2 >= 2
    assert result["facets"][1]["covered"] == True  # e3 grade 2 >= 2
    assert result["all_facets_covered"] == True
    
    # Test uncovered
    grades2 = {"e1": 1, "e2": 1, "e3": 1}
    result2 = evaluate_facet_coverage(facets, grades2, minimum_grade=2)
    assert result2["all_facets_covered"] == False
    assert "f1" in result2["uncovered_facets"]
    assert "f2" in result2["uncovered_facets"]


def test_evidence_relations():
    """Test evidence duplicate detection."""
    e1 = EvidenceRecord(
        evidence_id="e1", text="Los punteros contienen direcciones de memoria.",
        source_id="src1", document_id="doc1", author="author1", page_start=1, page_end=1,
    )
    e2 = EvidenceRecord(
        evidence_id="e2", text="Los punteros contienen direcciones de memoria para acceder.",
        source_id="src1", document_id="doc1", author="author1", page_start=1, page_end=1,
    )
    
    result = compare_evidence_records(e1, e2, minimum_text_similarity=0.8, maximum_simhash_distance=16)
    
    assert result["relation"] in ("REVIEW_POSSIBLE_DUPLICATE", "REVIEW_SHARED_PROVENANCE")
    assert result["provenance"]["same_source_id"] == True
    assert result["provenance"]["same_document"] == True
    assert result["human_review_required"] == True


def test_proposals(synthetic_data):
    """Test qrel proposal generation."""
    # Create snapshots
    temporary, manifest = create_snapshots(synthetic_data["knowledge_db"], synthetic_data["vector_db"])
    
    # Simple FTS retriever
    from study_engine.storage.knowledge_store import KnowledgeStore
    store = KnowledgeStore(Path(manifest["snapshots"]["knowledge_db"]["path"]))
    
    def retriever(query, notebook_id, source_ids, top_k):
        rows = store.fts_search(query, notebook_id=notebook_id, limit=top_k, source_ids=source_ids)
        return [
            {
                "chunk_id": row.chunk_id,
                "source_id": row.source_id,
                "score": getattr(row, "score", 1.0),
            }
            for row in rows
        ]
    
    report = generate_qrel_proposals(
        synthetic_data["dataset"],
        Path(manifest["snapshots"]["knowledge_db"]["path"]),
        retriever,
        top_k=3,
    )
    
    assert "qrels" in report
    assert "observations" in report
    assert "candidate_proposals" in report
    assert report["metadata"]["retrieval_executed"] == True
    
    # Check q1 (positive) has proposals
    assert "q1" in report["qrels"]
    assert len(report["qrels"]["q1"]) > 0
    
    # Check q2 (negative) has empty qrels
    assert "q2" in report["qrels"]
    assert report["qrels"]["q2"] == {}
    
    store.close()
    temporary.cleanup()


def test_segment_validation(synthetic_data, tmp_path):
    """Test segment validation."""
    # Write dataset and qrels to temp files
    dataset_path = tmp_path / "dataset.json"
    qrels_path = tmp_path / "qrels.json"
    
    write_json(dataset_path, synthetic_data["dataset"].model_dump())
    # qrels file must have top-level "qrels" key for validate_gate2_segments
    write_json(qrels_path, {"qrels": synthetic_data["qrels"]})
    
    report = validate_gate2_segments(dataset_path, qrels_path, synthetic_data["knowledge_db"])
    
    assert report["status"] == "passed"
    assert report["retrieval_executed"] == False
    assert "segments" in report
    assert len(report["segments"]) > 0


def test_contract_validation(synthetic_data):
    """Test contract validation."""
    # Build fixture chunks
    fixture_chunks = {"chunk-local-1": "src-local"}
    
    # Build ACL
    acl = {"synthetic-g2": {"src-local"}}
    
    counts = validate_gate2_contract(synthetic_data["dataset"], synthetic_data["qrels"], fixture_chunks, acl)
    
    assert counts["total_queries"] == 2
    assert counts["by_oracle_type"]["positive_in_scope"] == 1
    assert counts["by_oracle_type"]["negative_by_scope"] == 1


def test_observation_evaluation(synthetic_data):
    """Test observation evaluation."""
    observations = {
        "q1": {"retrieved_chunk_ids": ["chunk-local-1"], "citation_ids": ["E1"]},
        "q2": {"retrieved_chunk_ids": [], "citation_ids": []},
    }
    
    result = evaluate_gate2_observations(synthetic_data["dataset"], observations)
    
    assert result["total_queries"] == 2
    assert result["passed_queries"] == 2
    assert result["results"]["q1"]["passed"] == True
    assert result["results"]["q2"]["passed"] == True
    
    # Test failure case
    bad_obs = {
        "q1": {"retrieved_chunk_ids": [], "citation_ids": []},  # Should fail for positive
    }
    result2 = evaluate_gate2_observations(synthetic_data["dataset"], bad_obs)
    assert result2["results"]["q1"]["passed"] == False