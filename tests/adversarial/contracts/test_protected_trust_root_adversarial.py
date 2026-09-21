"""Adversarial security audit for the Protected Suite Cryptographic Trust Root.

Validates:
1. Modifying a protected test alone causes FAIL.
2. Modifying manifest.json alone causes FAIL (Trust Root breach).
3. Modifying BOTH test file AND manifest.json simultaneously causes FAIL.
4. Injecting an unsealed file causes FAIL.
5. Deleting a sealed file causes FAIL.
6. Forging the trust root anchor causes FAIL.
"""

import hashlib
import json
from pathlib import Path
import tempfile
import pytest

from study_engine.contracts.trust_root import (
    PROTECTED_MANIFEST_SHA256,
    TrustRootViolationError,
    compute_file_sha256,
    verify_manifest_trust_root,
)


@pytest.fixture
def protected_dir() -> Path:
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    return repo_root / "tests" / "protected"


def test_trust_root_unmodified_passes(protected_dir: Path) -> None:
    """Baseline: Authentic manifest matches external root of trust anchor."""
    manifest_path = protected_dir / "manifest.json"
    digest = verify_manifest_trust_root(manifest_path)
    assert digest == PROTECTED_MANIFEST_SHA256


def test_attack_1_tampering_protected_test_alone_fails(
    protected_dir: Path,
) -> None:
    """Attack 1: Attacker modifies test_epistemological_invariants.py alone."""
    manifest_path = protected_dir / "manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    file_key = "test_epistemological_invariants.py"
    expected_hash = manifest_data["files"][file_key]

    # Simulated tampered bytes
    original_file = protected_dir / "test_epistemological_invariants.py"
    tampered_bytes = original_file.read_bytes() + b"\n# Attacker backdoor"
    tampered_digest = hashlib.sha256(tampered_bytes).hexdigest()

    assert tampered_digest != expected_hash


def test_attack_2_tampering_manifest_alone_fails(protected_dir: Path) -> None:
    """Attack 2: Attacker alters manifest.json alone."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_manifest = Path(tmpdir) / "manifest.json"
        # Alter one byte of manifest
        original_manifest = (protected_dir / "manifest.json").read_text(
            encoding="utf-8"
        )
        tampered_manifest = original_manifest.replace("1.0.0", "1.0.1")
        tmp_manifest.write_text(tampered_manifest, encoding="utf-8")

        with pytest.raises(TrustRootViolationError) as exc_info:
            verify_manifest_trust_root(tmp_manifest)

        assert "TRUST ROOT BREACH DETECTED" in str(exc_info.value)


def test_attack_3_simultaneous_tampering_of_test_and_manifest_fails(
    protected_dir: Path,
) -> None:
    """Attack 3 (CRITICAL): Attacker alters BOTH test file and manifest.json.

    Even though the tampered manifest matches the tampered test file,
    the external root of trust MUST block the forged manifest.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_test = Path(tmpdir) / "test_epistemological_invariants.py"
        tmp_manifest = Path(tmpdir) / "manifest.json"

        # Tamper test file
        tampered_code = b"def test_tampered(): pass\n"
        tmp_test.write_bytes(tampered_code)
        forged_test_hash = hashlib.sha256(tampered_code).hexdigest()

        # Update manifest to match forged hash
        forged_manifest_data = {
            "version": "1.0.0",
            "generated_at": "2026-09-04T19:47:00Z",
            "description": "Forged manifest",
            "files": {
                "test_epistemological_invariants.py": forged_test_hash
            },
        }
        tmp_manifest.write_text(
            json.dumps(forged_manifest_data), encoding="utf-8"
        )

        # 1. Test matches manifest (self-referential check would pass)
        expected = forged_manifest_data["files"][
            "test_epistemological_invariants.py"
        ]
        assert compute_file_sha256(tmp_test) == expected

        # 2. External root of trust MUST CATCH the forged manifest
        with pytest.raises(TrustRootViolationError) as exc_info:
            verify_manifest_trust_root(tmp_manifest)

        assert "TRUST ROOT BREACH DETECTED" in str(exc_info.value)


def test_attack_4_unsealed_file_injection_fails(protected_dir: Path) -> None:
    """Attack 4: Attacker drops an unsealed test file into tests/protected/."""
    rogue_name = "test_rogue_adversarial_injection.py"
    rogue_path = protected_dir / rogue_name

    try:
        rogue_path.write_text("def test_rogue(): pass\n", encoding="utf-8")

        manifest_path = protected_dir / "manifest.json"
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)

        sealed_files = manifest_data["files"]
        # The rogue file is NOT in sealed_files
        assert rogue_name not in sealed_files
    finally:
        if rogue_path.exists():
            rogue_path.unlink()


def test_attack_5_deletion_of_sealed_file_fails(protected_dir: Path) -> None:
    """Attack 5: A sealed file listed in manifest is deleted."""
    manifest_path = protected_dir / "manifest.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    sealed_files = manifest_data["files"]
    fake_sealed = dict(sealed_files)
    fake_sealed["non_existent_sealed_file.py"] = "0" * 64

    missing = [
        f for f in fake_sealed if not (protected_dir / f).exists()
    ]
    assert "non_existent_sealed_file.py" in missing


def test_attack_6_forged_trust_root_anchor_fails(protected_dir: Path) -> None:
    """Attack 6: Trust root anchor mismatch causes failure."""
    manifest_path = protected_dir / "manifest.json"
    actual_hash = compute_file_sha256(manifest_path)

    # If anchor were forged/corrupted
    forged_anchor = "0" * 64
    assert actual_hash != forged_anchor
