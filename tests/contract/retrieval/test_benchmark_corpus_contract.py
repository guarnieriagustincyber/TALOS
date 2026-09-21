"""Contract tests for benchmark corpus generation and provenance in S3.6.1."""

import hashlib
import json
from pathlib import Path
import pytest

from study_engine.retrieval.benchmark_builder import (
    DEFAULT_CHUNK_CONFIG,
    build_benchmark_corpus,
)


@pytest.fixture
def sample_sources_env(tmp_path: Path):

    sources_dir = tmp_path / "sources"
    sources_dir.mkdir()

    # Create authentic sample text files with required naming prefixes
    so_proc = sources_dir / "so_procesos.txt"
    so_proc.write_text(
        "Un proceso en un SO es un programa en ejecucion.\n\n"
        "El PCB contiene el estado del proceso, el contador de programa, "
        "los registros de CPU y la informacion de memoria.\n\n"
        "Cuando un proceso finaliza con exit() y el padre no llama a wait(), "
        "se convierte en un proceso zombie.",
        encoding="utf-8",
    )

    prog_ptr = sources_dir / "prog_punteros.txt"
    prog_ptr.write_text(
        "En lenguaje C, un puntero almacena la direccion de memoria.\n\n"
        "La funcion malloc() reserva memoria dinamica en el heap.\n\n"
        "Es mandatorio invocar free() para evitar fugas de memoria.",
        encoding="utf-8",
    )

    out_corpus = tmp_path / "benchmark_corpus.json"
    out_manifest = tmp_path / "benchmark_manifest.json"

    return sources_dir, out_corpus, out_manifest


def test_contract_benchmark_builder_empty_sources(tmp_path: Path):
    empty_dir = tmp_path / "empty_sources"
    empty_dir.mkdir()
    with pytest.raises(FileNotFoundError) as exc:
        build_benchmark_corpus(
            sources_dir=empty_dir,
            output_corpus_path=tmp_path / "corpus.json",
            output_manifest_path=tmp_path / "manifest.json",
        )
    assert "No authentic source files found" in str(exc.value)


def test_contract_benchmark_builder_invalid_naming_prefix(tmp_path: Path):
    sources_dir = tmp_path / "bad_sources"
    sources_dir.mkdir()
    bad_file = sources_dir / "random_notes.txt"
    bad_file.write_text(
        "Texto sin prefijo curricular valido.", encoding="utf-8"
    )

    with pytest.raises(ValueError) as exc:
        build_benchmark_corpus(
            sources_dir=sources_dir,
            output_corpus_path=tmp_path / "corpus.json",
            output_manifest_path=tmp_path / "manifest.json",
        )
    assert "must start with 'so_'" in str(exc.value)


def test_contract_benchmark_provenance_chain(sample_sources_env):

    sources_dir, out_corpus, out_manifest = sample_sources_env

    manifest_data = build_benchmark_corpus(
        sources_dir=sources_dir,
        output_corpus_path=out_corpus,
        output_manifest_path=out_manifest,
        chunk_config=DEFAULT_CHUNK_CONFIG,
    )

    assert out_corpus.exists()
    assert out_manifest.exists()

    with open(out_corpus, "r", encoding="utf-8") as f:
        corpus = json.load(f)

    # 1. Verify Notebooks
    nb_ids = {nb["id"] for nb in corpus["notebooks"]}
    assert nb_ids == {"fadena-so", "fadena-prog"}

    # 2. Verify Cryptographic SHA256 chain of physical files
    for src in corpus["sources"]:
        file_path = sources_dir / src["filename"]
        assert file_path.exists()
        real_sha256 = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert src["sha256"] == real_sha256

    # 3. Verify Document -> Source link
    source_ids = {src["source_id"] for src in corpus["sources"]}
    for doc in corpus["documents"]:
        assert doc["source_id"] in source_ids

    # 4. Verify Chunk -> Document -> Notebook link
    doc_map = {doc["id"]: doc for doc in corpus["documents"]}
    for chunk in corpus["chunks"]:
        assert chunk["document_id"] in doc_map
        parent_doc = doc_map[chunk["document_id"]]
        assert chunk["source_id"] == parent_doc["source_id"]
        assert chunk["notebook_id"] in nb_ids
        assert len(chunk["content"].strip()) > 0

    # 5. Verify Manifest matches Corpus exactly
    assert manifest_data["total_source_files"] == len(corpus["sources"])
    assert manifest_data["total_documents"] == len(corpus["documents"])
    assert manifest_data["total_chunks"] == len(corpus["chunks"])
    assert "fadena-so" in manifest_data["thematic_breakdown"]
    assert "fadena-prog" in manifest_data["thematic_breakdown"]


def test_production_benchmark_corpus_integrity():
    """Verify production benchmark corpus if physically present."""
    corpus_file = Path("data/benchmark/benchmark_corpus.json")
    manifest_file = Path("data/benchmark/benchmark_manifest.json")
    sources_dir = Path("data/benchmark/sources")

    if not (corpus_file.exists() and manifest_file.exists()):
        pytest.skip(
            "Production benchmark corpus not yet generated "
            "(waiting for authentic sources)."
        )

    with open(corpus_file, "r", encoding="utf-8") as f:
        corpus = json.load(f)
    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Operational requirement: 40 to 60 chunks
    assert 40 <= len(corpus["chunks"]) <= 60
    assert manifest["total_chunks"] == len(corpus["chunks"])

    # Both notebooks represented
    nb_counts = manifest["notebook_chunk_counts"]
    assert nb_counts.get("fadena-so", 0) > 0
    assert nb_counts.get("fadena-prog", 0) > 0

    # Physical SHA256 integrity
    for s in manifest["sources"]:
        file_path = sources_dir / s["filename"]
        assert file_path.exists()
        real_sha256 = hashlib.sha256(file_path.read_bytes()).hexdigest()
        assert s["sha256"] == real_sha256


def test_detect_notebook_and_topic_branches():
    from study_engine.retrieval.benchmark_builder import (
        detect_notebook_and_topic,
    )

    assert detect_notebook_and_topic(Path("so_planif.txt")) == (
        "fadena-so",
        "scheduling",
    )
    assert detect_notebook_and_topic(Path("so_deadlock.txt")) == (
        "fadena-so",
        "concurrency",
    )
    assert detect_notebook_and_topic(Path("so_memoria.txt")) == (
        "fadena-so",
        "virtual_memory",
    )
    assert detect_notebook_and_topic(Path("so_misc.txt")) == (
        "fadena-so",
        "general_so",
    )

    assert detect_notebook_and_topic(Path("prog_ptr.txt")) == (
        "fadena-prog",
        "pointers",
    )
    assert detect_notebook_and_topic(Path("prog_listas.txt")) == (
        "fadena-prog",
        "linear_structs",
    )
    assert detect_notebook_and_topic(Path("prog_arboles.txt")) == (
        "fadena-prog",
        "trees",
    )
    assert detect_notebook_and_topic(Path("prog_archivos.txt")) == (
        "fadena-prog",
        "file_io",
    )
    assert detect_notebook_and_topic(Path("prog_misc.txt")) == (
        "fadena-prog",
        "general_prog",
    )


def test_contract_benchmark_builder_non_existent_sources_dir(tmp_path: Path):
    non_existent = tmp_path / "does_not_exist"
    with pytest.raises(FileNotFoundError) as exc:
        build_benchmark_corpus(
            sources_dir=non_existent,
            output_corpus_path=tmp_path / "corpus.json",
            output_manifest_path=tmp_path / "manifest.json",
        )
    assert "Sources directory not found" in str(exc.value)


def test_contract_benchmark_builder_ingestion_failure(
    sample_sources_env, monkeypatch
):
    sources_dir, out_corpus, out_manifest = sample_sources_env

    from study_engine.contracts.enums import IngestionStatus
    from study_engine.contracts.ingestion import (
        IngestionError,
        IngestionResult,
    )
    import study_engine.retrieval.benchmark_builder as bb

    def mock_bad_ingest(*args, **kwargs):
        return IngestionResult(
            source_id="src-test",
            status=IngestionStatus.FAILED,
            error=IngestionError(
                code="ERR_EXTRACTION",
                message="Simulated ingestion extraction error",
            ),
        )

    monkeypatch.setattr(bb, "ingest_document", mock_bad_ingest)

    with pytest.raises(RuntimeError) as exc:

        build_benchmark_corpus(
            sources_dir=sources_dir,
            output_corpus_path=out_corpus,
            output_manifest_path=out_manifest,
        )
    assert "S1 Ingestion failed" in str(exc.value)
