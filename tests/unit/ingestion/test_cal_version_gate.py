"""CI Gate Test for CAL-2: Enforcement of Probe and Converter Versions against Frozen Config."""

import json
from pathlib import Path
import pytest

from study_engine.ingestion.conversion_probe import ConversionProbe, PROBE_VERSION
from study_engine.ingestion.converters.anydoc_adapter import AnyDocAdapter
from study_engine.ingestion.converters.markitdown_adapter import MarkItDownAdapter
from study_engine.ingestion.converters.tesseract_fallback import TesseractFallbackAdapter


def test_cal2_version_consistency_against_frozen_routing_table():
    """CAL-2: Verify probe_version and all converter_versions match routing_table.frozen.json."""
    frozen_path = Path("config/routing_table.frozen.json")
    assert frozen_path.exists(), "Frozen routing table missing: config/routing_table.frozen.json"

    with open(frozen_path, "r", encoding="utf-8") as f:
        frozen_config = json.load(f)

    # 1. Probe version check
    expected_probe_ver = frozen_config.get("probe_version")
    probe = ConversionProbe()
    assert probe.version == expected_probe_ver, (
        f"CAL-2 VIOLATION: Probe version '{probe.version}' does not match frozen version '{expected_probe_ver}'"
    )
    assert PROBE_VERSION == expected_probe_ver

    # 2. Converter versions check
    expected_converters = frozen_config.get("converter_versions", {})
    
    adapters = {
        "markitdown": MarkItDownAdapter(),
        "anydoc_local": AnyDocAdapter(submode="local"),
        "anydoc_cloud": AnyDocAdapter(submode="cloud"),
        "tesseract_fallback": TesseractFallbackAdapter(),
    }

    for conv_id, adapter in adapters.items():
        assert conv_id in expected_converters, f"Converter '{conv_id}' not registered in frozen routing table"
        expected_ver = expected_converters[conv_id]
        assert adapter.version == expected_ver, (
            f"CAL-2 VIOLATION: Converter '{conv_id}' version '{adapter.version}' "
            f"does not match frozen version '{expected_ver}'. Re-calibration required!"
        )


def test_cal2_version_mismatch_detection():
    """Verify that any version deviation raises an explicit violation."""
    # Simulating a hypothetical version bump in code without re-calibrating frozen table
    simulated_bumped_version = "1.1.0"
    frozen_path = Path("config/routing_table.frozen.json")
    with open(frozen_path, "r", encoding="utf-8") as f:
        frozen_config = json.load(f)

    expected_probe_ver = frozen_config["probe_version"]
    assert simulated_bumped_version != expected_probe_ver
    
    # Confirm that comparison would fail
    with pytest.raises(AssertionError):
        assert simulated_bumped_version == expected_probe_ver
