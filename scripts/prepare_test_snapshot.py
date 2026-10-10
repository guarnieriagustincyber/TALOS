"""Seal an externally captured, read-only filesystem snapshot for pytest."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_MODULE_PATH = (
    REPOSITORY_ROOT
    / "src/study_engine/diagnostics/test_isolation_snapshots.py"
)
SNAPSHOT_MODULE_SPEC = importlib.util.spec_from_file_location(
    "talos_test_isolation_snapshots", SNAPSHOT_MODULE_PATH
)
if SNAPSHOT_MODULE_SPEC is None or SNAPSHOT_MODULE_SPEC.loader is None:
    raise RuntimeError(f"Cannot load snapshot module: {SNAPSHOT_MODULE_PATH}")
SNAPSHOT_MODULE = importlib.util.module_from_spec(SNAPSHOT_MODULE_SPEC)
sys.modules[SNAPSHOT_MODULE_SPEC.name] = SNAPSHOT_MODULE
SNAPSHOT_MODULE_SPEC.loader.exec_module(SNAPSHOT_MODULE)
TestSnapshotError = SNAPSHOT_MODULE.TestSnapshotError
prepare_sealed_snapshot = SNAPSHOT_MODULE.prepare_sealed_snapshot


def _database_identity(value: str) -> tuple[str, str]:
    identity, separator, filename = value.partition("=")
    if not separator or not identity or not filename:
        raise argparse.ArgumentTypeError(
            "database must use the form IDENTITY=FILENAME.db"
        )
    return identity, filename


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Package an externally created atomic filesystem snapshot. "
            "This command does not open SQLite files in the capture source."
        )
    )
    parser.add_argument("--capture-root", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--attestation-sha256", required=True)
    parser.add_argument("--scope", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--gate-id", required=True)
    parser.add_argument("--policy-id", required=True)
    parser.add_argument("--freshness-seconds", type=int, required=True)
    parser.add_argument(
        "--database",
        type=_database_identity,
        action="append",
        default=[],
        metavar="IDENTITY=FILENAME.db",
        help=(
            "Required database and logical identity; repeat for each database."
        ),
    )
    parser.add_argument(
        "--repository-root", type=Path, default=REPOSITORY_ROOT
    )
    args = parser.parse_args()
    database_names = dict(args.database)
    if not database_names:
        parser.error(
            "at least one --database IDENTITY=FILENAME.db is required"
        )
    if len(database_names) != len(args.database):
        parser.error("database identities must be unique")

    try:
        artifact, digest = prepare_sealed_snapshot(
            args.capture_root,
            args.artifact_root,
            attestation_sha256=args.attestation_sha256,
            database_names=database_names,
            scope=args.scope,
            run_identity=args.run_id,
            gate_identity=args.gate_id,
            policy_identity=args.policy_id,
            freshness_seconds=args.freshness_seconds,
            repository_root=args.repository_root,
        )
    except TestSnapshotError as exc:
        parser.exit(2, f"snapshot preparation blocked: {exc}\n")

    print(f"snapshot_root={artifact}")
    print(f"manifest_sha256={digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
