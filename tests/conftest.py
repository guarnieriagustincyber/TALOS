import hashlib
import shutil
from pathlib import Path
from typing import Optional

import pytest
from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.source import Source, SourceRole


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@pytest.fixture(scope="session")
def web_state_test_copy(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Provide a verified snapshot for tests needing the populated web state."""
    source_dir = Path(__file__).resolve().parents[1] / "data/web_state"
    snapshot_dir = tmp_path_factory.mktemp("web_state_test_copy")

    for filename in ("knowledge_store.db", "vector_store.db"):
        source = source_dir / filename
        if not source.is_file():
            raise FileNotFoundError(
                f"Required web-state test database is missing: {source}"
            )

        wal_path = Path(f"{source}-wal")
        if wal_path.exists() and wal_path.stat().st_size:
            raise RuntimeError(
                "Cannot snapshot web-state database with a non-empty WAL: "
                f"{wal_path}"
            )

        source_hash = _sha256(source)
        snapshot = snapshot_dir / filename
        shutil.copyfile(source, snapshot)
        if wal_path.exists() and wal_path.stat().st_size:
            raise RuntimeError(
                "Web-state database WAL became non-empty during snapshot: "
                f"{wal_path}"
            )
        if _sha256(source) != source_hash or _sha256(snapshot) != source_hash:
            raise RuntimeError(
                "Web-state database changed while creating its test snapshot: "
                f"{filename}"
            )
    return snapshot_dir


@pytest.fixture(scope="session")
def knowledge_store_test_copy(
    tmp_path_factory: pytest.TempPathFactory,
) -> Optional[Path]:
    """Provide a verified temporary copy of the versioned knowledge store."""
    source = Path(__file__).resolve().parents[1] / "data/web_state/knowledge_store.db"
    if not source.is_file():
        return None

    wal_path = Path(f"{source}-wal")
    if wal_path.exists() and wal_path.stat().st_size:
        raise RuntimeError(
            f"Cannot snapshot knowledge store with a non-empty WAL: {wal_path}"
        )

    source_hash = _sha256(source)
    snapshot = tmp_path_factory.mktemp("knowledge_store_test_copy") / source.name
    shutil.copyfile(source, snapshot)

    if wal_path.exists() and wal_path.stat().st_size:
        raise RuntimeError(
            f"Knowledge store WAL became non-empty during snapshot: {wal_path}"
        )
    if _sha256(source) != source_hash or _sha256(snapshot) != source_hash:
        raise RuntimeError(
            "Knowledge store changed while creating its test snapshot"
        )
    return snapshot


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
