"""Hermetic tests for ConversionStorage: raw source immutability and closed chunk schema."""

import hashlib
from pathlib import Path
import tempfile
import pytest

from study_engine.ingestion.conversion_arbiter import ArbitrationDecision
from study_engine.ingestion.conversion_audit import AuditStatus, ConversionAuditReport
from study_engine.ingestion.conversion_probe import ConversionProbe, ConversionProfile
from study_engine.ingestion.conversion_storage import CALChunk, ConversionStorage
from study_engine.ingestion.converters.base import ConversionResult


def test_raw_source_immutability_invariant():
    """CAL Invariant: SHA-256 of the raw physical file must be identical before and after conversion."""
    probe = ConversionProbe()
    storage = ConversionStorage(":memory:")

    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
        f.write("# Operating Systems Concepts\nProcess Scheduling and Threads.\n")
        temp_path = f.name

    try:
        # 1. Measure SHA-256 before any operation
        initial_hash = ConversionProbe.compute_sha256(temp_path)

        # 2. Perform probe and conversion
        profile = probe.probe(temp_path)
        raw_text = Path(temp_path).read_text(encoding="utf-8")
        dummy_result = ConversionResult(
            converter_id="markitdown",
            converter_version="1.0.0",
            markdown_content=raw_text,
            tokens_count=len(raw_text.split()),
            sha256_output=hashlib.sha256(raw_text.encode("utf-8")).hexdigest(),
        )
        audit_rep = ConversionAuditReport(
            readability_score=1.0,
            table_integrity=1.0,
            code_integrity=1.0,
            header_hierarchy=1.0,
            yield_tokens_per_page=1.0,
            overall_quality_score=0.95,
            status=AuditStatus.PASSED,
        )
        decision = ArbitrationDecision(
            canonical_result=dummy_result,
            canonical_audit=audit_rep,
            conflict_flag=False,
            all_candidates=[dummy_result],
        )

        storage.store_conversion_decision(profile, decision)
        chunks = storage.chunk_and_store(
            profile,
            decision,
            curricular_meta={
                "subject": "Sistemas Operativos",
                "level": "Grado",
                "book": "Silberschatz",
                "chapter": "Capítulo 3",
                "section": "3.1",
                "page_start": 10,
                "page_end": 12,
            },
        )

        # 3. Measure SHA-256 after all operations
        final_hash = ConversionProbe.compute_sha256(temp_path)

        assert initial_hash == final_hash, "MUTATION DETECTED: Raw source SHA-256 altered!"
        assert len(chunks) >= 1
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_closed_chunk_schema_curricular_metadata():
    """Every emitted chunk MUST contain converter provenance AND curricular metadata."""
    storage = ConversionStorage(":memory:")

    profile = ConversionProfile(
        source_sha256="src_sha_" + "a" * 56,
        format="pdf",
        has_text_layer=True,
        scan_ratio=0.0,
        table_density=0.1,
        code_density=0.1,
        formula_density=0.0,
        language="es",
        pages=2,
        probe_version="1.0.0",
        profile_hash="prof_hash_" + "b" * 54,
    )
    content = "# Chapter 1: Introduction\n\nOperating systems manage hardware.\n\n# Chapter 2: Hardware\n\nCPUs execute instructions."
    res = ConversionResult(
        converter_id="markitdown",
        converter_version="1.0.0",
        markdown_content=content,
        tokens_count=len(content.split()),
        sha256_output=hashlib.sha256(content.encode("utf-8")).hexdigest(),
    )
    audit_rep = ConversionAuditReport(
        readability_score=1.0,
        table_integrity=1.0,
        code_integrity=1.0,
        header_hierarchy=1.0,
        yield_tokens_per_page=1.0,
        overall_quality_score=0.92,
        status=AuditStatus.PASSED,
    )
    decision = ArbitrationDecision(
        canonical_result=res,
        canonical_audit=audit_rep,
        conflict_flag=False,
        all_candidates=[res],
    )

    curr_meta = {
        "subject": "Arquitectura de Computadoras",
        "level": "Grado",
        "book": "Patterson & Hennessy",
        "chapter": "Capítulo 1",
        "section": "1.1",
        "page_start": 20,
        "page_end": 25,
    }

    chunks = storage.chunk_and_store(profile, decision, curricular_meta=curr_meta)

    assert len(chunks) > 0
    for chunk in chunks:
        # Check closed schema attributes
        assert chunk.converter_id == "markitdown"
        assert chunk.converter_version == "1.0.0"
        assert chunk.probe_version == "1.0.0"
        assert chunk.conversion_score == 0.92
        assert chunk.conflict_flag is False
        assert chunk.subject == "Arquitectura de Computadoras"
        assert chunk.level == "Grado"
        assert chunk.book == "Patterson & Hennessy"
        assert chunk.chapter == "Capítulo 1"
        assert chunk.section == "1.1"
        assert chunk.page_start >= 20
        assert chunk.page_end <= 25
