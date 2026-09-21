import pytest
from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.source import Source, SourceRole


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
