"""Hermetic unit tests for ConversionAuditor (Subsystem S1)."""

import pytest

from study_engine.ingestion.conversion_audit import (
    AuditStatus,
    ConversionAuditor,
    TAU_CLOUD_REINFORCED,
    TAU_LOCAL_ADMISSION,
)
from study_engine.ingestion.converters.base import ConversionResult


def _make_result(
    text: str,
    ocr_provenance: str = "none",
    trust_level: str = "verified",
    converter_id: str = "markitdown",
) -> ConversionResult:
    return ConversionResult(
        converter_id=converter_id,
        converter_version="1.0.0",
        markdown_content=text,
        tables_count=0,
        code_blocks_count=0,
        headers_count=0,
        tokens_count=len(text.split()),
        page_count=1,
        page_map={1: text},
        has_ocr=(ocr_provenance != "none"),
        ocr_provenance=ocr_provenance,
        trust_level=trust_level,
        formulas_detected=False,
        formulas_unextracted=False,
        sha256_output="dummy_sha256" + "0" * 52,
    )


def test_legacy_p4_low_char_count():
    """Text length < 40 characters triggers LOW_OCR."""
    auditor = ConversionAuditor()
    short_result = _make_result("Too short")
    report = auditor.audit(short_result)
    assert report.status == AuditStatus.LOW_OCR
    assert report.overall_quality_score == 0.0


def test_legacy_p4_low_readability_ratio():
    """Readability < 0.75 printable characters triggers LOW_OCR."""
    auditor = ConversionAuditor()
    garbage_text = "\x00\x01\x02\x03\x04\x05\x06\x07\x08" * 10 + "some text here that is 50 chars long"
    report = auditor.audit(_make_result(garbage_text))
    assert report.status == AuditStatus.LOW_OCR
    assert report.readability_score < 0.75


def test_table_integrity_unbalanced():
    """Broken table without separator row receives penalty."""
    auditor = ConversionAuditor()
    broken_table = """# Document With Broken Table
Some text before the table to satisfy the minimum length requirement.
| Header 1 | Header 2 |
| Data 1   | Data 2   |
Text after table.
"""
    rep_broken = auditor.audit(_make_result(broken_table))
    assert rep_broken.table_integrity == 0.40

    well_formed_table = """# Document With Well Formed Table
Some text before the table to satisfy the minimum length requirement.
| Header 1 | Header 2 |
| :--- | :--- |
| Data 1   | Data 2   |
Text after table.
"""
    rep_good = auditor.audit(_make_result(well_formed_table))
    assert rep_good.table_integrity == 1.0


def test_code_block_integrity_unbalanced():
    """Unbalanced code fences receive score 0.0."""
    auditor = ConversionAuditor()
    unbalanced_code = """# Coding Guide
Text introducing the code block here to satisfy the character length minimum.
```python
def unclosed():
    return True
Text after unclosed fence.
"""
    report = auditor.audit(_make_result(unbalanced_code))
    assert report.code_integrity == 0.0


def test_header_hierarchy():
    """Wild skip in header depth (# to ####) receives a penalty."""
    auditor = ConversionAuditor()
    wild_headers = """# Top Header
Some paragraphs in the document describing operating systems principles and processes.
#### Far Deep Header
Paragraph text continuing here.
"""
    report = auditor.audit(_make_result(wild_headers))
    assert report.header_hierarchy < 1.0


def test_cal3_cloud_ocr_promotion():
    """CAL-3: Cloud OCR promoted to trust=verified only when overall >= tau_cloud (0.85)."""
    auditor = ConversionAuditor(tau_cloud=TAU_CLOUD_REINFORCED, tau_local=TAU_LOCAL_ADMISSION)

    # High quality cloud conversion
    high_quality_text = """# Virtual Memory Management

In modern architectures, virtual memory provides an illusion of vast contiguous address spaces.

| Component | Function | Access Time |
| :--- | :--- | :--- |
| TLB | Cache for page table entries | < 1 ns |
| Page Table | Maps virtual to physical frames | 10-50 ns |
| Swap Disk | Secondary storage backing | 5-10 ms |

The Memory Management Unit (MMU) handles translation transparently.
""" + ("\nExplanation paragraph describing paging mechanisms. " * 10)

    res_cloud = _make_result(
        high_quality_text,
        ocr_provenance="cloud",
        trust_level="unverified",
        converter_id="anydoc_cloud",
    )

    report = auditor.audit(res_cloud)
    assert report.overall_quality_score >= TAU_CLOUD_REINFORCED
    assert report.is_promoted_cloud is True

    # Marginal cloud conversion (< 0.85) with broken table remains unverified
    marginal_text = """# Minimal Header
Only short explanation without enough depth.
| Unfinished Table Header | Second Column |
| Row 1 | Row 2 |
""" + ("Short line. " * 10)
    res_marginal = _make_result(
        marginal_text,
        ocr_provenance="cloud",
        trust_level="unverified",
        converter_id="anydoc_cloud",
    )
    rep_marginal = auditor.audit(res_marginal)
    assert rep_marginal.is_promoted_cloud is False
