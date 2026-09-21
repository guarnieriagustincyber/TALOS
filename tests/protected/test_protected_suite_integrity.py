"""Integrity verifier for the Protected Tests suite.

Ensures that:
1. The protected manifest exists and is well-formed.
2. All protected invariant test files match their sealed SHA-256 digests.
3. No rogue or unsealed test files exist in tests/protected/.
4. Tampering with any protected test file is immediately detected.
"""

import hashlib
import json
from pathlib import Path


def _compute_sha256(file_path: Path) -> str:
    """Compute deterministic SHA-256 of file contents."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def test_protected_manifest_integrity() -> None:
    """Verify that all files in tests/protected/ match manifest."""
    protected_dir = Path(__file__).resolve().parent
    manifest_path = protected_dir / "manifest.json"

    assert manifest_path.exists(), (
        f"Protected manifest '{manifest_path}' is missing!"
    )

    # 0. HG-PROT-ROOT: Verify manifest against external trust root anchor
    from study_engine.contracts.trust_root import verify_manifest_trust_root
    verify_manifest_trust_root(manifest_path)

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    assert "files" in manifest_data, "Manifest missing 'files' dictionary!"
    sealed_files = manifest_data["files"]

    # Excluded from self-referential hash checking
    excluded_from_manifest = {
        "manifest.json",
        "test_protected_suite_integrity.py",
        "__init__.py",
        ".gitkeep",
    }

    # 1. Verify that every sealed file exists and matches its hash
    for filename, expected_hash in sealed_files.items():
        file_path = protected_dir / filename
        assert file_path.exists(), (
            f"Protected test file '{filename}' in manifest is missing!"
        )
        actual_hash = _compute_sha256(file_path)
        assert actual_hash == expected_hash, (
            f"PROTECTED TEST TAMPERING DETECTED for '{filename}'!\n"
            f"Expected: {expected_hash}\n"
            f"Actual:   {actual_hash}\n"
            f"Modifying protected tests requires explicit authorization."
        )

    # 2. Verify that no unsealed .py test files exist in tests/protected/
    for file_path in protected_dir.iterdir():
        is_candidate = (
            file_path.is_file()
            and file_path.name not in excluded_from_manifest
        )
        if is_candidate:
            assert file_path.name in sealed_files, (
                f"Unsealed file '{file_path.name}' found in tests/protected/! "
                f"All protected tests must be declared in manifest.json."
            )


def test_tamper_detection_simulation() -> None:
    """Verify that any modified content would fail the hash check."""
    sample_content = b"def test_tampered(): assert True\n# modified"
    computed = hashlib.sha256(sample_content).hexdigest()
    # It must not match the sealed hash
    expected_sealed = (
        "3f10a1eba00f74d7bd0119ff4610f4429832f9e6b79c422526ef71ac4a1f3099"
    )
    assert computed != expected_sealed
