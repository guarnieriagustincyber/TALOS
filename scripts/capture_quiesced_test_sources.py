"""Capture the canonical B06 source set after verifying a quiescent window."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID, uuid4

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = REPOSITORY_ROOT / "data" / "web_state"
DATABASES = {
    "knowledge_store": "knowledge_store.db",
    "vector_store": "vector_store.db",
    "student_state": "student_state.db",
}
SCOPE = "talos.b06.snapshot.v1"
POLICY_ID = "talos.b06.quiesced-consistency.v1"
GATE_ID = "talos-p1.2-b06-quality-gate-v1"
SIDECARS = ("-wal", "-shm", "-journal")


class CaptureError(RuntimeError):
    pass


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    descriptor = os.open(
        path,
        os.O_RDONLY | os.O_CLOEXEC | os.O_NOATIME,
    )
    with os.fdopen(descriptor, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return f"sha256:{digest.hexdigest()}"


def _copy_source(source: Path, target: Path) -> None:
    source_fd = os.open(
        source,
        os.O_RDONLY | os.O_CLOEXEC | os.O_NOATIME,
    )
    target_fd = os.open(
        target,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_CLOEXEC,
        0o600,
    )
    with os.fdopen(source_fd, "rb") as reader, os.fdopen(target_fd, "wb") as writer:
        shutil.copyfileobj(reader, writer, length=1024 * 1024)
        writer.flush()
        os.fsync(writer.fileno())


def _source_record(path: Path) -> dict[str, object]:
    before = path.stat()
    if not stat.S_ISREG(before.st_mode) or path.is_symlink():
        raise CaptureError(f"Source is not a regular file: {path.name}")
    digest = _sha256(path)
    after = path.stat()
    stable_fields = (
        "st_dev",
        "st_ino",
        "st_size",
        "st_mtime_ns",
        "st_ctime_ns",
        "st_mode",
        "st_atime_ns",
    )
    if any(getattr(before, field) != getattr(after, field) for field in stable_fields):
        raise CaptureError(f"Source changed while being fingerprinted: {path.name}")
    return {
        "path": path.name,
        "sha256": digest,
        "size_bytes": before.st_size,
        "mode": stat.S_IMODE(before.st_mode),
        "mtime_ns": before.st_mtime_ns,
        "device": before.st_dev,
        "inode": before.st_ino,
        "ctime_ns": before.st_ctime_ns,
    }


def _source_paths() -> dict[str, Path]:
    if SOURCE_ROOT.is_symlink() or not SOURCE_ROOT.is_dir():
        raise CaptureError("B06 source root must be an existing real directory")

    paths: dict[str, Path] = {}
    for filename in DATABASES.values():
        database = SOURCE_ROOT / filename
        if not database.is_file() or database.is_symlink():
            raise CaptureError(f"Required source is missing: {database}")
        paths[filename] = database
        for suffix in SIDECARS:
            sidecar = SOURCE_ROOT / f"{filename}{suffix}"
            if sidecar.exists() or sidecar.is_symlink():
                if not sidecar.is_file() or sidecar.is_symlink():
                    raise CaptureError(
                        f"SQLite sidecar is not a regular file: {sidecar}"
                    )
                paths[sidecar.name] = sidecar
    return dict(sorted(paths.items()))


def _assert_no_open_handles(paths: list[Path]) -> None:
    lsof = shutil.which("lsof")
    if lsof is None:
        raise CaptureError("Cannot verify quiescence: lsof is unavailable")
    result = subprocess.run(
        [lsof, "-nP", "-F", "pfn", "--", *(str(path) for path in paths)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.stdout.strip():
        raise CaptureError("Open file handles found for B06 source files")
    if result.returncode != 1 or result.stdout.strip() or result.stderr.strip():
        raise CaptureError(
            "Open-handle inspection was inconclusive; capture blocked: "
            f"exit={result.returncode}, stderr={result.stderr.strip()!r}"
        )


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")


def _capture(destination: Path, run_id: str) -> tuple[Path, str]:
    try:
        parsed_run_id = UUID(run_id)
    except ValueError as exc:
        raise CaptureError("run-id must be a canonical UUIDv4") from exc
    if parsed_run_id.version != 4 or str(parsed_run_id) != run_id:
        raise CaptureError("run-id must be a canonical UUIDv4")

    destination = destination.resolve()
    repository_root = REPOSITORY_ROOT.resolve()
    if destination == repository_root or repository_root in destination.parents:
        raise CaptureError("Capture destination must be outside the repository")
    if destination.exists() or destination.is_symlink():
        raise CaptureError(f"Capture destination already exists: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        destination.relative_to(SOURCE_ROOT.resolve())
    except ValueError:
        pass
    else:
        raise CaptureError("Capture destination overlaps the live source")

    paths = _source_paths()
    path_list = list(paths.values())
    _assert_no_open_handles(path_list)
    initial = {name: _source_record(path) for name, path in paths.items()}
    created_at = datetime.now(timezone.utc).isoformat()
    staging = Path(
        tempfile.mkdtemp(
            prefix=".talos-b06-quiesced-",
            dir=destination.parent,
        )
    )
    try:
        for name, source in paths.items():
            target = staging / name
            _copy_source(source, target)
            target.chmod(0o444)
            metadata = source.stat()
            os.utime(target, ns=(metadata.st_atime_ns, metadata.st_mtime_ns))

        final_paths = _source_paths()
        if set(final_paths) != set(paths):
            raise CaptureError(
                "B06 database or sidecar inventory changed during capture"
            )
        _assert_no_open_handles(list(final_paths.values()))
        final = {
            name: _source_record(path) for name, path in final_paths.items()
        }
        if initial != final:
            raise CaptureError("A B06 source changed during the capture window")

        captured_records: list[dict[str, object]] = []
        for name in paths:
            captured = _source_record(staging / name)
            source = initial[name]
            if (
                captured["sha256"] != source["sha256"]
                or captured["size_bytes"] != source["size_bytes"]
                or captured["mtime_ns"] != source["mtime_ns"]
                or captured["mode"] != 0o444
            ):
                raise CaptureError(f"Captured file does not match source: {name}")
            captured_records.append(captured)

        manifest_source_records = [
            {
                key: record[key]
                for key in ("path", "sha256", "size_bytes", "mode", "mtime_ns")
            }
            for record in captured_records
        ]
        capture_id = str(uuid4())
        attestation = {
            "capture_id": capture_id,
            "capture_method": "quiesced_file_copy",
            "consistency": "quiesced",
            "created_at": created_at,
            "read_only": True,
            "read_only_semantics": "capture_copy_does_not_write_source_files",
            "attestation_authority": "project-delegated-local-executor",
            "authentication_model": "local_integrity_only",
            "scope": SCOPE,
            "source_identity": "talos-runtime-web:data/web_state",
            "run_identity": run_id,
            "gate_identity": GATE_ID,
            "policy_identity": POLICY_ID,
            "source_files": manifest_source_records,
            "quiescence": {
                "mode": "no_open_handles",
                "verification": "lsof_before_and_after_copy",
                "source_stability": (
                    "source_file_fingerprints_match_before_and_after"
                ),
            },
        }
        (staging / "capture-attestation.json").write_bytes(
            _canonical_json(attestation) + b"\n"
        )
        (staging / "capture-attestation.json").chmod(0o444)
        staging.chmod(0o555)
        staging.rename(destination)
        return destination, capture_id
    finally:
        if staging.exists():
            staging.chmod(0o700)
            shutil.rmtree(staging)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Copy the canonical B06 databases and sidecars only when no "
            "process has them open; this is not an atomic filesystem snapshot."
        )
    )
    parser.add_argument("--capture-root", required=True, type=Path)
    parser.add_argument("--run-id", required=True)
    args = parser.parse_args()
    try:
        capture_root, capture_id = _capture(args.capture_root, args.run_id)
    except (CaptureError, OSError) as exc:
        print(f"capture blocked: {exc}", file=sys.stderr)
        return 2
    print(f"capture_root={capture_root}")
    print(f"capture_id={capture_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
