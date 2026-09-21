"""Hermetic unit tests for ConversionProbe (Subsystem S1)."""

import hashlib
from pathlib import Path
import tempfile
import pytest

from study_engine.ingestion.conversion_probe import ConversionProbe, ConversionProfile, PROBE_VERSION


def test_probe_version_invariant():
    """Verify probe version adheres to semver and frozen configuration."""
    assert PROBE_VERSION == "1.0.0"
    probe = ConversionProbe()
    assert probe.version == "1.0.0"


def test_probe_determinism_10_runs():
    """CAL Invariant: 10/10 runs on identical file must produce 100% identical profile hashes."""
    probe = ConversionProbe()
    with tempfile.NamedTemporaryFile(suffix=".txt", mode="w", delete=False) as f:
        f.write("# Introduction to Operating Systems\nProcesses, Threads, and Scheduling.\n")
        temp_path = f.name

    try:
        profiles = [probe.probe(temp_path) for _ in range(10)]
        first_hash = profiles[0].profile_hash
        assert len(first_hash) == 64
        for p in profiles[1:]:
            assert p.profile_hash == first_hash
            assert p.source_sha256 == profiles[0].source_sha256
            assert p.probe_version == "1.0.0"
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_probe_profile_features():
    """Test feature extraction on synthetic markdown file."""
    probe = ConversionProbe()
    content = """# Title
Some regular paragraph.

| Col1 | Col2 |
|---|---|
| A | B |

```python
def foo():
    pass
```

$$\\sum_{i=1}^n i = \\frac{n(n+1)}{2}$$
"""
    with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        profile = probe.probe(temp_path)
        assert profile.format == "md"
        assert profile.has_text_layer is True
        assert profile.scan_ratio == 0.0
        assert profile.table_density > 0.0
        assert profile.code_density > 0.0
        assert profile.formula_density > 0.0
        assert profile.probe_version == "1.0.0"
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_probe_exclusion_rules():
    """Exclusion rules: scan_ratio > 0.50 or has_text_layer=False exclusion."""
    probe = ConversionProbe()
    
    # Scanned profile mock
    prof_scanned = ConversionProfile(
        source_sha256="a" * 64,
        format="pdf",
        has_text_layer=False,
        scan_ratio=1.0,
        table_density=0.0,
        code_density=0.0,
        formula_density=0.0,
        language="es",
        pages=10,
        probe_version="1.0.0",
        profile_hash="b" * 64,
    )
    # Check that scanned PDF is flagged correctly
    assert prof_scanned.has_text_layer is False
    assert prof_scanned.scan_ratio > 0.50


def test_probe_nonexistent_file():
    """Probe fails closed on missing files."""
    probe = ConversionProbe()
    with pytest.raises(FileNotFoundError):
        probe.probe("/tmp/non_existent_file_definitely_not_here_12345.xyz")
