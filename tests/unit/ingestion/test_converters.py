"""Hermetic tests for CAL converter adapters and credits manager."""

import tempfile
from pathlib import Path
import pytest

from study_engine.ingestion.conversion_probe import ConversionProfile
from study_engine.ingestion.converters.markitdown_adapter import MarkItDownAdapter
from study_engine.ingestion.converters.anydoc_adapter import AnyDocAdapter
from study_engine.ingestion.converters.tesseract_fallback import TesseractFallbackAdapter
from study_engine.ingestion.converters.credits_manager import ConversionCreditsManager


def test_credits_manager_authorization_and_limits():
    """Verify credits manager rejects unauthorized sources and enforces daily quota."""
    cm = ConversionCreditsManager(daily_budget=10)
    source_id = "test_source_123"

    assert not cm.is_authorized(source_id)
    assert not cm.can_consume(source_id, 1)
    assert not cm.consume(source_id, 1)

    cm.authorize_source(source_id)
    assert cm.is_authorized(source_id)
    assert cm.can_consume(source_id, 5)
    assert cm.consume(source_id, 5)
    assert cm.get_remaining_credits() == 5

    # Cannot exceed budget
    assert not cm.can_consume(source_id, 10)
    assert not cm.consume(source_id, 10)
    assert cm.get_remaining_credits() == 5

    # Revoke authorization
    cm.revoke_source(source_id)
    assert not cm.is_authorized(source_id)
    assert not cm.can_consume(source_id, 1)


def test_anydoc_cloud_requires_authorization():
    """AnyDoc in cloud mode must raise PermissionError if unauthorized."""
    cm = ConversionCreditsManager(daily_budget=100)
    adapter = AnyDocAdapter(submode="cloud", credits_manager=cm)

    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
        f.write("Scanned text simulated.\n")
        temp_path = f.name

    try:
        prof = ConversionProfile(
            source_sha256="hash123",
            format="pdf",
            has_text_layer=False,
            scan_ratio=1.0,
            table_density=0.0,
            code_density=0.0,
            formula_density=0.0,
            language="es",
            pages=2,
            probe_version="1.0.0",
            profile_hash="profhash123",
        )
        with pytest.raises(PermissionError):
            adapter.convert(temp_path, profile=prof)

        # Now authorize and succeed
        cm.authorize_source(prof.source_sha256)
        res = adapter.convert(temp_path, profile=prof)
        assert res.has_ocr is True
        assert res.ocr_provenance == "cloud"
        assert res.trust_level == "unverified"
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_tesseract_fallback_trust_unverified():
    """Tesseract fallback emits local_tesseract provenance and unverified trust."""
    adapter = TesseractFallbackAdapter()
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
        f.write("Fallback scanned text line 1\nFallback scanned text line 2\n")
        temp_path = f.name

    try:
        res = adapter.convert(temp_path)
        assert res.converter_id == "tesseract_fallback"
        assert res.has_ocr is True
        assert res.ocr_provenance == "local_tesseract"
        assert res.trust_level == "unverified"
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_markitdown_cal5_formulas_unextracted_flag():
    """CAL-5: Flag formulas_unextracted=True when formula_density > 0.05 but no LaTeX/MathML."""
    adapter = MarkItDownAdapter()
    plain_math_text = "T(n) = 2 * T(n/2) + c * n. Recurrence relation without LaTeX."
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
        f.write(plain_math_text)
        temp_path = f.name

    try:
        prof_high_formula = ConversionProfile(
            source_sha256="math_source_1",
            format="txt",
            has_text_layer=True,
            scan_ratio=0.0,
            table_density=0.0,
            code_density=0.0,
            formula_density=0.20,  # > 0.05
            language="es",
            pages=1,
            probe_version="1.0.0",
            profile_hash="math_prof_1",
        )
        res = adapter.convert(temp_path, profile=prof_high_formula)
        assert res.formulas_detected is False
        assert res.formulas_unextracted is True

        # When LaTeX is present, formulas_unextracted is False
        latex_text = "$$T(n) = 2T(n/2) + cn$$"
        Path(temp_path).write_text(latex_text, encoding="utf-8")
        res_latex = adapter.convert(temp_path, profile=prof_high_formula)
        assert res_latex.formulas_detected is True
        assert res_latex.formulas_unextracted is False
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_markitdown_cal7_ordinal_mapping():
    """CAL-7: Verify ordinal mapping for PPTX slides and XLSX sheets."""
    adapter = MarkItDownAdapter()
    
    # PPTX with 2 slides
    pptx_content = "<!-- slide -->\n# Slide 1 Content\n<!-- slide -->\n# Slide 2 Content\n"
    with tempfile.NamedTemporaryFile(suffix=".pptx", mode="w", delete=False) as f:
        f.write(pptx_content)
        temp_pptx = f.name

    # XLSX with 2 sheets
    xlsx_content = "# Hoja 1: Primer Parcial\nColA | ColB\n# Hoja 2: Segundo Parcial\nColX | ColY\n"
    with tempfile.NamedTemporaryFile(suffix=".xlsx", mode="w", delete=False) as f:
        f.write(xlsx_content)
        temp_xlsx = f.name

    try:
        res_pptx = adapter.convert(temp_pptx)
        assert res_pptx.page_count == 2
        assert 1 in res_pptx.page_map
        assert 2 in res_pptx.page_map
        assert "Slide 1 Content" in res_pptx.page_map[1]
        assert "Slide 2 Content" in res_pptx.page_map[2]

        res_xlsx = adapter.convert(temp_xlsx)
        assert res_xlsx.page_count == 2
        assert 1 in res_xlsx.page_map
        assert 2 in res_xlsx.page_map
        assert "Primer Parcial" in res_xlsx.page_map[1]
        assert "Segundo Parcial" in res_xlsx.page_map[2]
    finally:
        Path(temp_pptx).unlink(missing_ok=True)
        Path(temp_xlsx).unlink(missing_ok=True)
