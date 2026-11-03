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
    if os.getenv("TALOS_TEST_ISOLATED") == "1":
        workspace_value = os.getenv("TALOS_TEST_WORKSPACE_ROOT")
        workspace_identity = os.getenv("TALOS_TEST_WORKSPACE_IDENTITY")
        if not workspace_value or not workspace_identity:
            raise pytest.UsageError(
                "Isolated Quality Gate requires a pre-derived writable "
                "workspace and its identity"
            )
        workspace = Path(workspace_value)
        try:
            database_files_for_workspace(
                workspace,
                {
                    "knowledge_store": "knowledge_store.db",
                    "vector_store": "vector_store.db",
                    "student_state": "student_state.db",
                },
                expected_workspace_identity=workspace_identity,
            )
        except TestSnapshotError as exc:
            raise pytest.UsageError(
                f"Isolated Quality Gate workspace is invalid: {exc}"
            ) from exc
        yield workspace
        return

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
        expected_workspace_identity=os.getenv(
            "TALOS_TEST_WORKSPACE_IDENTITY"
        ),
    )
    return _test_isolated_workspace


def _build_b06_synthetic_state(workspace: Path) -> Path:
    """Agent-authored deterministic test data, never captured/student data."""
    import hashlib
    from study_engine.contracts.chunk import Chunk
    from study_engine.contracts.document import Document
    from study_engine.contracts.notebook import Notebook
    from study_engine.retrieval.embedding import DeterministicHashEmbedder
    from study_engine.retrieval.vector_identity import vector_space_id
    from study_engine.retrieval.vector_store import SQLiteVectorStore, VectorRecord
    from study_engine.storage.knowledge_store import KnowledgeStore

    if workspace.is_symlink() or workspace.exists():
        raise ValueError("B06 synthetic workspace must be new")
    workspace.mkdir()
    text = "Los punteros en C contienen direcciones de memoria."
    source_id = "b06-synthetic-pointers"
    digest = hashlib.sha256(text.encode()).hexdigest()
    source = SourceRecord(
        source_id=source_id,
        manifest=SourceManifest(source_id=source_id, filename="b06-synthetic.txt",
                                byte_size=len(text.encode()), sha256=digest),
        source=Source(source_id=source_id, title="Synthetic pointer vocabulary",
                      author="B06 deterministic fixture", role=SourceRole.PRIMARY),
    )
    document = Document(id="b06-synthetic-document", source_id=source_id,
                        title="Synthetic pointer vocabulary")
    chunk = Chunk(id="b06-synthetic-chunk", document_id=document.id,
                  source_id=source_id, content=text, page_start=1,
                  token_count=len(text.split()), index=0)
    store = KnowledgeStore(db_path=workspace / "knowledge_store.db")
    store.initialize()
    store.create_notebook(Notebook(id="fase0-soc", name="B06 synthetic notebook"))
    store.store_ingestion_bundle(source, [document], [chunk], notebook_id="fase0-soc")
    store.close()
    embedder = DeterministicHashEmbedder(dimensions=128)
    space = vector_space_id(embedder)
    assert space is not None
    vectors = SQLiteVectorStore(workspace / "vector_store.db", read_only=False)
    vectors.save_records([VectorRecord(
        chunk_id=chunk.id, notebook_id="fase0-soc", source_id=source_id,
        provider_id=embedder.provider_id, model_id=embedder.model_id,
        dimensions=embedder.dimensions, vector=embedder.embed_passages([text])[0],
        space_id=space,
    )])
    assert vectors.list_space_ids("fase0-soc") == {space}
    vectors._conn.close()
    return workspace


@pytest.fixture
def b06_synthetic_state(request, tmp_path: Path) -> Iterator[Path]:
    """Only B06 may select this explicit synthetic sibling of captured inputs."""
    import hashlib
    import json
    from scripts.quality_gate import (
        B06_SYNTHETIC_EXCEPTION, FOCAL_B06_NODEID, b06_synthetic_workspace,
        validate_b06_synthetic_state,
    )
    from study_engine.retrieval.embedding import DeterministicHashEmbedder
    from study_engine.retrieval.vector_identity import vector_space_id

    if request.node.nodeid != FOCAL_B06_NODEID:
        raise pytest.UsageError("B06 synthetic state is restricted to the exact B06 nodeid")
    if os.getenv("TALOS_TEST_ISOLATED") == "1":
        captured = request.getfixturevalue("web_state_test_copy")
        workspace = b06_synthetic_workspace(captured, request.node.nodeid)
        def fingerprints():
            return {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in captured.iterdir() if p.is_file()}
        before = fingerprints()
    else:
        captured = None
        workspace = tmp_path / "b06-synthetic"
    _build_b06_synthetic_state(workspace)
    if captured is not None:
        parent_receipt = json.loads((captured / ".talos-test-workspace.json").read_text())
        (workspace / ".b06-synthetic.json").write_text(json.dumps({
            **B06_SYNTHETIC_EXCEPTION,
            "run_id": os.getenv("TALOS_TEST_RUN_ID"),
            "captured_manifest_sha256": parent_receipt["manifest_sha256"],
            "captured_workspace": str(captured),
            "workspace": str(workspace),
            "space_id": vector_space_id(DeterministicHashEmbedder(dimensions=128)),
        }, sort_keys=True))
    try:
        yield workspace
    finally:
        if captured is not None:
            assert fingerprints() == before, "B06 modified captured inputs"
            validate_b06_synthetic_state(captured, request.node.nodeid)


@pytest.fixture(scope="session")
def knowledge_store_test_copy(_test_isolated_workspace: Path) -> Path:
    """Provide the knowledge database from the isolated per-run workspace."""
    source = database_files_for_workspace(
        _test_isolated_workspace,
        {"knowledge_store": "knowledge_store.db"},
        expected_workspace_identity=os.getenv(
            "TALOS_TEST_WORKSPACE_IDENTITY"
        ),
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
