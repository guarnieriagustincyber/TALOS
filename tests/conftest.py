import os
from pathlib import Path
import tempfile
from typing import Iterator

import pytest
from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.source import Source, SourceRole
from study_engine.diagnostics.gate2_snapshots import backup_read_only_database
from study_engine.diagnostics.test_isolation_snapshots import (
    TestSnapshotError,
    database_files_for_workspace,
    derive_test_workspace,
    verify_sealed_snapshot,
)


@pytest.fixture(scope="session")
def _test_isolated_workspace(
    tmp_path_factory: pytest.TempPathFactory,
) -> Iterator[Path]:
    required_environment = {
        "TALOS_TEST_SNAPSHOT_ROOT": os.getenv("TALOS_TEST_SNAPSHOT_ROOT"),
        "TALOS_TEST_SNAPSHOT_MANIFEST_SHA256": os.getenv(
            "TALOS_TEST_SNAPSHOT_MANIFEST_SHA256"
        ),
        "TALOS_TEST_SNAPSHOT_SCOPE": os.getenv("TALOS_TEST_SNAPSHOT_SCOPE"),
        "TALOS_TEST_RUN_ID": os.getenv("TALOS_TEST_RUN_ID"),
        "TALOS_TEST_GATE_ID": os.getenv("TALOS_TEST_GATE_ID"),
        "TALOS_TEST_POLICY_ID": os.getenv("TALOS_TEST_POLICY_ID"),
    }
    missing = [
        name for name, value in required_environment.items() if not value
    ]
    if missing:
        raise pytest.UsageError(
            "Protected-data fixtures require a sealed snapshot and explicit "
            "provenance; missing environment: " + ", ".join(missing)
        )

    snapshot_root_value = required_environment["TALOS_TEST_SNAPSHOT_ROOT"]
    manifest_digest = required_environment[
        "TALOS_TEST_SNAPSHOT_MANIFEST_SHA256"
    ]
    scope = required_environment["TALOS_TEST_SNAPSHOT_SCOPE"]
    run_id = required_environment["TALOS_TEST_RUN_ID"]
    gate_id = required_environment["TALOS_TEST_GATE_ID"]
    policy_id = required_environment["TALOS_TEST_POLICY_ID"]
    assert all(
        value is not None
        for value in (
            snapshot_root_value,
            manifest_digest,
            scope,
            run_id,
            gate_id,
            policy_id,
        )
    )
    snapshot_root = Path(snapshot_root_value)
    workspace_parent = Path(tmp_path_factory.getbasetemp())
    temporary = tempfile.TemporaryDirectory(
        prefix="talos-test-workspace-", dir=workspace_parent
    )
    workspace = Path(temporary.name) / "web_state"
    try:
        derive_test_workspace(
            snapshot_root,
            workspace,
            expected_manifest_sha256=manifest_digest,
            scope=scope,
            run_identity=run_id,
            gate_identity=gate_id,
            policy_identity=policy_id,
        )
    except TestSnapshotError as exc:
        raise pytest.UsageError(
            f"Protected-data snapshot is invalid: {exc}"
        ) from exc

    try:
        yield workspace
        verify_sealed_snapshot(snapshot_root, manifest_digest)
    finally:
        temporary.cleanup()


@pytest.fixture(scope="session")
def web_state_test_copy(_test_isolated_workspace: Path) -> Path:
    """Provide a writable per-run copy derived from the sealed snapshot."""
    database_files_for_workspace(
        _test_isolated_workspace,
        {
            "knowledge_store": "knowledge_store.db",
            "vector_store": "vector_store.db",
            "student_state": "student_state.db",
        },
    )
    return _test_isolated_workspace


@pytest.fixture(scope="session")
def knowledge_store_test_copy(_test_isolated_workspace: Path) -> Path:
    """Provide the knowledge database from the isolated per-run workspace."""
    source = database_files_for_workspace(
        _test_isolated_workspace, {"knowledge_store": "knowledge_store.db"}
    )["knowledge_store"]
    standalone_copy = _test_isolated_workspace / "knowledge_store_fixture.db"
    backup_read_only_database(source, standalone_copy)
    return standalone_copy


@pytest.fixture(scope="module", autouse=True)
def ensure_src_so_concurrencia_source(request):
    """Ensure that the source `src_so_concurrencia.pdf` exists in the KnowledgeStore.
    This fixture runs automatically for all module-scoped tests that use the KnowledgeStore.
    It inserts a minimal SourceRecord into the store's source repository.
    """
    # Try to retrieve the KnowledgeStore from the `retrieval_env` fixture if available.
    try:
        store = request.getfixturevalue("retrieval_env")[2]
    except Exception:
        # No retrieval_env fixture; nothing to do.
        return

    source_id = "src_so_concurrencia.pdf"
    if store.sources.contains(source_id):
        return

    # Create a dummy manifest with a placeholder SHA-256 and zero size.
    manifest = SourceManifest(
        source_id=source_id,
        filename="so_concurrencia.pdf",
        sha256="0" * 64,
        byte_size=0,
        media_type="application/pdf",
    )
    source_obj = Source(
        source_id=source_id,
        title="Concurrencia",
        author="Cátedra de Sistemas",
        role=SourceRole.PRIMARY,
        priority=1,
        subject="Operating Systems",
    )
    record = SourceRecord(
        source_id=source_id,
        manifest=manifest,
        source=source_obj,
        metadata={},
    )
    store.sources.save(record)
