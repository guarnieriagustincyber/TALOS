"""Governance and sealing utility for the protected invariant suite.

Usage:
  python scripts/seal_protected_suite.py --check
  python scripts/seal_protected_suite.py --seal --confirm
"""

import argparse
import hashlib
import json
from pathlib import Path
import sys

from study_engine.contracts.trust_root import (
    compute_file_sha256,
    verify_manifest_trust_root,
)


def compute_dir_hashes(protected_dir: Path) -> dict:
    """Compute sha256 for all test_*.py files in tests/protected/."""
    excluded = {
        "manifest.json",
        "test_protected_suite_integrity.py",
        "__init__.py",
        ".gitkeep",
    }
    files = {}
    for p in sorted(protected_dir.iterdir()):
        if p.is_file() and p.name not in excluded and p.suffix == ".py":
            files[p.name] = compute_file_sha256(p)
    return files


def check_suite(protected_dir: Path) -> bool:
    manifest_path = protected_dir / "manifest.json"
    print("--> 1. Checking external Trust Root anchor...")
    try:
        verify_manifest_trust_root(manifest_path)
        print("    [OK] Manifest matches external anchor.")
    except Exception as e:
        print(f"    [FAIL] {e}")
        return False

    print("--> 2. Checking individual test file digests against manifest...")
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    sealed_files = data.get("files", {})
    actual_files = compute_dir_hashes(protected_dir)

    all_ok = True
    for fname, exp_hash in sealed_files.items():
        act_hash = actual_files.get(fname)
        if act_hash == exp_hash:
            print(f"    [OK] {fname}: {exp_hash[:16]}...")
        else:
            print(
                f"    [MISMATCH] {fname}: actual={act_hash} != exp={exp_hash}"
            )
            all_ok = False

    for fname in actual_files:
        if fname not in sealed_files:
            print(f"    [UNSEALED] {fname} is not in manifest!")
            all_ok = False

    return all_ok


def seal_suite(protected_dir: Path, confirm: bool) -> bool:
    if not confirm:
        print(
            "Error: --seal requires --confirm to prevent resealing.",
            file=sys.stderr,
        )
        return False

    manifest_path = protected_dir / "manifest.json"
    actual_files = compute_dir_hashes(protected_dir)

    manifest_data = {
        "version": "1.0.0",
        "generated_at": "2026-09-04T19:47:00Z",
        "description": (
            "Cryptographic manifest of protected invariant tests "
            "for Study Engine"
        ),
        "files": actual_files,
    }

    content_str = json.dumps(manifest_data, indent=2) + "\n"
    manifest_path.write_text(content_str, encoding="utf-8")
    new_manifest_hash = hashlib.sha256(content_str.encode("utf-8")).hexdigest()

    print("=" * 60)
    print("SEALED PROTECTED SUITE MANIFEST")
    print("=" * 60)
    print(f"Manifest Path: {manifest_path}")
    print(f"New Manifest SHA-256: {new_manifest_hash}")
    print("\nFiles sealed:")
    for fname, h in actual_files.items():
        print(f"  - {fname}: {h}")

    print("\n" + "=" * 60)
    print("REQUIRED ACTION TO UPDATE ROOT OF TRUST ANCHOR:")
    print("=" * 60)
    print(
        "Update `PROTECTED_MANIFEST_SHA256` in "
        "`src/study_engine/contracts/trust_root.py` to:"
    )
    print(f'PROTECTED_MANIFEST_SHA256: str = "{new_manifest_hash}"')
    print("=" * 60)
    return True


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Protected Suite Sealing & Audit Tool"
    )
    parser.add_argument(
        "--check", action="store_true", help="Check manifest and trust root"
    )
    parser.add_argument(
        "--seal", action="store_true", help="Reseal manifest from files"
    )
    parser.add_argument(
        "--confirm", action="store_true", help="Confirm reseal operation"
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    protected_dir = repo_root / "tests" / "protected"

    if args.seal:
        success = seal_suite(protected_dir, args.confirm)
        return 0 if success else 1
    else:
        success = check_suite(protected_dir)
        return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
