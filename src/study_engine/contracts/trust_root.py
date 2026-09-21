"""External cryptographic root of trust for protected invariant suites.

Enforces:
- Manifest integrity cannot be self-referential or mutable.
- Quality Gate and Protected Suite verification are anchored in this module.
- Legitimate updates require deliberate modification of both manifest and
  this anchor.
"""

import hashlib
from pathlib import Path


# Authoritative Root of Trust Anchor
# To legitimately update this hash, execute:
# python scripts/seal_protected_suite.py --seal --confirm
PROTECTED_MANIFEST_VERSION: str = "1.0.0"
PROTECTED_MANIFEST_SHA256: str = (
    "d5d992d8edae5bd707a2970b461926978a7c79069468611e40042ddca30f0661"
)


class TrustRootViolationError(Exception):
    """Raised when protected manifest fails external root-of-trust anchor."""


def compute_file_sha256(file_path: Path) -> str:
    """Compute deterministic SHA-256 digest of file contents."""
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def verify_manifest_trust_root(manifest_path: Path) -> str:
    """Verify manifest.json matches the immutable external trust root anchor.

    Args:
        manifest_path: Path to tests/protected/manifest.json

    Returns:
        The validated SHA-256 digest string.

    Raises:
        TrustRootViolationError: If file is missing or hash does not match.
    """
    if not manifest_path.exists():
        raise TrustRootViolationError(
            f"Protected manifest missing at: {manifest_path}"
        )

    actual_digest = compute_file_sha256(manifest_path)
    if actual_digest != PROTECTED_MANIFEST_SHA256:
        raise TrustRootViolationError(
            f"TRUST ROOT BREACH DETECTED!\n"
            f"Manifest path:   {manifest_path}\n"
            f"Actual digest:   {actual_digest}\n"
            f"Expected anchor: {PROTECTED_MANIFEST_SHA256}\n"
            f"The manifest cannot validate itself. Any legitimate change to "
            f"protected invariants requires updating the external anchor in "
            f"study_engine.contracts.trust_root via "
            f"scripts/seal_protected_suite.py."
        )

    return actual_digest
