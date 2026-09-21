"""Adversarial Red Team Suite for CAL (Subsystem S1).

Evaluates 5 attack and stress vectors:
1. Forced Representation Conflicts (never smoothed or averaged).
2. Corrupt and Truncated Files (fails closed or graceful degradation).
3. Unauthorized Cloud OCR on Scanned PDFs (strictly blocked).
4. Credit Budget Exhaustion (fail-safe local fallback).
5. Broken Tables and Syntax Degradation (proportionate penalty).
"""

import hashlib
from pathlib import Path
import tempfile
import pytest

from study_engine.ingestion.conversion_arbiter import ConversionArbiter
from study_engine.ingestion.conversion_audit import AuditStatus, ConversionAuditor
from study_engine.ingestion.conversion_probe import ConversionProbe, ConversionProfile
from study_engine.ingestion.converters.anydoc_adapter import AnyDocAdapter
from study_engine.ingestion.converters.base import ConversionResult
from study_engine.ingestion.converters.credits_manager import ConversionCreditsManager
from study_engine.ingestion.converters.markitdown_adapter import MarkItDownAdapter
from study_engine.ingestion.converters.tesseract_fallback import TesseractFallbackAdapter


def _create_result(converter_id: str, content: str) -> ConversionResult:
    return ConversionResult(
        converter_id=converter_id,
        converter_version="1.0.0",
        markdown_content=content,
        tables_count=1 if "|" in content else 0,
        code_blocks_count=1 if "```" in content else 0,
        headers_count=1 if "#" in content else 0,
        tokens_count=len(content.split()),
        page_count=1,
        page_map={1: content},
        has_ocr=False,
        ocr_provenance="none",
        trust_level="verified",
        formulas_detected=False,
        formulas_unextracted=False,
        sha256_output=hashlib.sha256(content.encode("utf-8")).hexdigest(),
    )


def test_vector_1_forced_conflicts_never_smoothed():
    """Vector 1: High-divergence outputs must produce CONVERSION_CONFLICT and remain distinct."""
    arbiter = ConversionArbiter(tau_conflict=0.12)

    # Converter A and B output diverging semantic content
    out_a = """# Process Scheduling
Algoritmo FCFS (First-Come First-Served):
- Tiempo de espera alto.
- No apropiativo (non-preemptive).
- Vulnerable a efecto convoy.
"""
    out_b = """# Memory Allocation Strategies
Algoritmos de asignación dinámica de memoria:
- First-fit: asigna el primer bloque suficiente.
- Best-fit: asigna el bloque más ajustado.
- Worst-fit: asigna el bloque más grande disponible.
"""
    res_a = _create_result("markitdown", out_a)
    res_b = _create_result("anydoc_local", out_b)

    decision = arbiter.arbitrate(res_a, res_b)

    assert decision.conflict_flag is True
    assert decision.conflict is not None
    assert decision.conflict.diff_stat > 0.50

    # Invariant: Output candidate texts must not be merged or averaged
    assert len(decision.all_candidates) == 2
    assert decision.all_candidates[0].markdown_content == out_a
    assert decision.all_candidates[1].markdown_content == out_b
    assert decision.canonical_result.markdown_content in (out_a, out_b)


def test_vector_2_corrupt_truncated_files():
    """Vector 2: Corrupt or truncated file must fail closed or degrade to LOW_OCR / SOURCE_DEGRADED."""
    probe = ConversionProbe()
    auditor = ConversionAuditor()

    # Create corrupt file with null bytes
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="wb", delete=False) as f:
        f.write(b"\x00\x01\x02\x03\xff\xfe\x00\x00")
        temp_path = f.name

    try:
        profile = probe.probe(temp_path)
        adapter = MarkItDownAdapter()
        res = adapter.convert(temp_path, profile=profile)
        audit_rep = auditor.audit(res)

        # Must trigger LOW_OCR due to length < 40 or low readability
        assert audit_rep.status in (AuditStatus.LOW_OCR, AuditStatus.SOURCE_DEGRADED)
        assert audit_rep.overall_quality_score < 0.40
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_vector_3_scanned_pdf_unauthorized_cloud_blocked():
    """Vector 3: Scanned PDF without cloud authorization must strictly reject cloud OCR."""
    cm = ConversionCreditsManager(daily_budget=500)
    # Source is NOT authorized in cm
    adapter = AnyDocAdapter(submode="cloud", credits_manager=cm)

    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
        f.write("Scanned simulated page\n")
        temp_path = f.name

    try:
        profile = ConversionProfile(
            source_sha256="unauthorized_source_sha256",
            format="pdf",
            has_text_layer=False,
            scan_ratio=1.0,
            table_density=0.0,
            code_density=0.0,
            formula_density=0.0,
            language="es",
            pages=10,
            probe_version="1.0.0",
            profile_hash="profile_unauth_hash",
        )

        with pytest.raises(PermissionError) as exc_info:
            adapter.convert(temp_path, profile=profile)

        assert "unauthorized or daily credit budget exhausted" in str(exc_info.value)
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_vector_4_credit_budget_exhaustion():
    """Vector 4: When credits are exhausted, cloud conversion blocks and local fallback functions."""
    cm = ConversionCreditsManager(daily_budget=5)
    source_id = "authorized_source_42"
    cm.authorize_source(source_id)

    # Consume all credits
    consumed = cm.consume(source_id, 5)
    assert consumed is True
    assert cm.get_remaining_credits() == 0

    # Attempting to consume more must fail
    assert cm.can_consume(source_id, 1) is False
    assert cm.consume(source_id, 1) is False

    # Local fallback adapter remains 100% operational
    fallback_adapter = TesseractFallbackAdapter()
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
        f.write("Emergency local OCR text\n")
        temp_path = f.name

    try:
        res = fallback_adapter.convert(temp_path)
        assert res.converter_id == "tesseract_fallback"
        assert res.trust_level == "unverified"
        assert res.has_ocr is True
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_vector_5_broken_tables_syntax_degradation():
    """Vector 5: Broken tables and unclosed code fences trigger proportionate audit penalty."""
    auditor = ConversionAuditor()

    # Malformed markdown table (missing closing delimiter and malformed rows)
    broken_table_text = """# Chapter 4: File Systems
Overview of inodes and directory structures.
| Inode Number | File Type | Permissions
1001 | Regular | -rw-r--r--
1002 | Directory
Text following broken table without closing bars.
""" + ("\nAdditional explanation to ensure length > 40 chars." * 5)

    res = _create_result("markitdown", broken_table_text)
    audit_rep = auditor.audit(res)

    # Table integrity penalty applied
    assert audit_rep.table_integrity == 0.40
    # Overall score degraded
    assert audit_rep.overall_quality_score < 0.90
