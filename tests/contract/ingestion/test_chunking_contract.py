"""Contract tests for S1.6 Chunking output and ChunkConfig."""

import json
import pytest
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.ingestion.chunking import ChunkConfig, chunk_document


def test_chunk_config_contract():
    config = ChunkConfig(chunk_size=500, chunk_overlap=50)
    assert config.chunk_size == 500
    assert config.chunk_overlap == 50
    assert len(config.delimiters) > 0

    json_data = config.model_dump_json()
    reconstructed = ChunkConfig.model_validate_json(json_data)
    assert reconstructed == config


def test_chunk_output_contract_conformance():
    doc = Document(
        id="contract-doc-001",
        source_id="src-contract",
        title="Contract Test",
        content="Texto de prueba para verificar que cada chunk cumple estrictamente el contrato Chunk.",
        metadata={"chapter": "Ch 1", "section": "Sec 1"},
    )
    config = ChunkConfig(chunk_size=40, chunk_overlap=10)
    chunks = chunk_document(doc, config)

    assert len(chunks) > 1
    for idx, chunk in enumerate(chunks):
        assert isinstance(chunk, Chunk)
        assert chunk.id == f"contract-doc-001:chunk_{idx:04d}"
        assert chunk.document_id == "contract-doc-001"
        assert chunk.source_id == "src-contract"
        assert len(chunk.content) >= 1
        assert len(chunk.content) <= 40
        assert chunk.index == idx
        assert chunk.token_count is None
        assert chunk.chapter == "Ch 1"
        assert chunk.section == "Sec 1"

        # JSON roundtrip
        json_str = chunk.model_dump_json()
        reconstructed = Chunk.model_validate_json(json_str)
        assert reconstructed == chunk
