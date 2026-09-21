"""Artifact discovery, SHA-256 hashing, and policy enforcement for S6.1.

INVARIANTS:
1. Workspace Isolation: Scans strictly scratch/workspace/, ignoring .engine/.
2. Symlink Rejection: Symlink files or directories are immediately rejected.
3. Size Ceiling: Files exceeding max_artifact_bytes are omitted and logged.
4. Count Ceiling: Excess files beyond max_artifact_count are recorded as
   truncated in ArtifactCollectionSummary.
5. Deterministic Provenance: SHA-256 is computed for all accepted artifacts.
"""

from datetime import datetime, timezone
import hashlib
from pathlib import Path
from typing import Tuple

from study_engine.contracts.execution import (
    ArtifactCollectionSummary,
    ArtifactOmissionReason,
    ExecutionPolicy,
    ObservedArtifact,
    OmittedArtifact,
)


def collect_workspace_artifacts(
    workspace_dir: Path,
    policy: ExecutionPolicy,
) -> Tuple[
    Tuple[ObservedArtifact, ...],
    Tuple[OmittedArtifact, ...],
    ArtifactCollectionSummary,
]:
    """Scan scratch/workspace/ directory for produced artifacts under policy.

    Args:
        workspace_dir: Path to scratch/workspace/ directory.
        policy: ExecutionPolicy declaring size and count constraints.

    Returns:
        Tuple of (collected_artifacts, omitted_artifacts, summary).
    """
    if not workspace_dir.exists() or not workspace_dir.is_dir():
        return (), (), ArtifactCollectionSummary()

    collected: list[ObservedArtifact] = []
    omitted: list[OmittedArtifact] = []
    discovered_count = 0

    # Walk directory in deterministic sorted order
    all_paths = sorted(workspace_dir.rglob("*"))

    for path in all_paths:
        if path.is_dir() and not path.is_symlink():
            continue

        rel_path = str(path.relative_to(workspace_dir))
        discovered_count += 1

        # 1. Symlink Policy: Reject all symlinks
        if path.is_symlink():
            omitted.append(
                OmittedArtifact(
                    relative_path=rel_path,
                    reason=ArtifactOmissionReason.SYMLINK_REJECTED,
                    details="Symlinks are strictly rejected in Tier 0",
                )
            )
            continue

        # 2. File read / existence check
        try:
            file_stat = path.stat()
            file_size = file_stat.st_size
        except OSError as e:
            omitted.append(
                OmittedArtifact(
                    relative_path=rel_path,
                    reason=ArtifactOmissionReason.UNREADABLE_FILE,
                    details=f"Cannot stat file: {e}",
                )
            )
            continue

        # 3. File size limit check
        if file_size > policy.max_artifact_bytes:
            omitted.append(
                OmittedArtifact(
                    relative_path=rel_path,
                    reason=ArtifactOmissionReason.EXCEEDS_SIZE_LIMIT,
                    file_size_bytes=file_size,
                    details=(
                        f"Size {file_size} exceeds maximum "
                        f"{policy.max_artifact_bytes}"
                    ),
                )
            )
            continue

        # 4. Artifact count limit check
        if len(collected) >= policy.max_artifact_count:
            omitted.append(
                OmittedArtifact(
                    relative_path=rel_path,
                    reason=ArtifactOmissionReason.EXCEEDS_COUNT_LIMIT,
                    file_size_bytes=file_size,
                    details="Maximum artifact count exceeded",
                )
            )
            continue

        # 5. Compute SHA-256 digest
        hasher = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                while chunk := f.read(65536):
                    hasher.update(chunk)
            digest = hasher.hexdigest()
        except OSError as e:
            omitted.append(
                OmittedArtifact(
                    relative_path=rel_path,
                    reason=ArtifactOmissionReason.UNREADABLE_FILE,
                    file_size_bytes=file_size,
                    details=f"Read error during hashing: {e}",
                )
            )
            continue

        # Guess mime type simply by extension
        ext = path.suffix.lower()
        mime_map = {
            ".pcap": "application/vnd.tcpdump.pcap",
            ".json": "application/json",
            ".txt": "text/plain",
            ".log": "text/plain",
            ".bin": "application/octet-stream",
            ".csv": "text/csv",
        }
        mime = mime_map.get(ext, "application/octet-stream")

        collected.append(
            ObservedArtifact(
                artifact_id=f"art-{len(collected):03d}",
                relative_path=rel_path,
                file_size_bytes=file_size,
                sha256_digest=digest,
                mime_type=mime,
                created_at=datetime.fromtimestamp(
                    file_stat.st_ctime, tz=timezone.utc
                ),
            )
        )

    summary = ArtifactCollectionSummary(
        artifacts_discovered=discovered_count,
        artifacts_collected=len(collected),
        artifacts_omitted=len(omitted),
        collection_truncated=len(omitted) > 0,
    )

    return tuple(collected), tuple(omitted), summary
