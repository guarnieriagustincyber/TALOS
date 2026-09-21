"""Benchmark corpus and manifest builder based on the S1 Ingestion Pipeline."""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.notebook import Notebook
from study_engine.ingestion.chunking import ChunkConfig, chunk_document
from study_engine.ingestion.document_ingestion import ingest_document
from study_engine.ingestion.file_ingestion import create_source_manifest

SUPPORTED_EXTENSIONS = {".txt", ".pdf", ".md"}

# Experimental benchmark configuration disclaimer:
# ChunkConfig(chunk_size=450, chunk_overlap=50) is an experimental benchmark
# parameter, not a validated optimal pedagogical chunking strategy.
DEFAULT_CHUNK_CONFIG = ChunkConfig(chunk_size=450, chunk_overlap=50)


def detect_notebook_and_topic(file_path: Path) -> Tuple[str, str]:
    """Deterministically detect notebook and topic from filename."""
    name = file_path.stem.lower()
    if name.startswith("so_"):
        notebook_id = "fadena-so"
        if "proc" in name:
            topic = "processes"
        elif "planif" in name or "sched" in name:
            topic = "scheduling"
        elif "concurr" in name or "deadlock" in name or "sincro" in name:
            topic = "concurrency"
        elif "mem" in name or "pagin" in name:
            topic = "virtual_memory"
        else:
            topic = "general_so"
    elif name.startswith("prog_"):
        notebook_id = "fadena-prog"
        if "punt" in name or "ptr" in name:
            topic = "pointers"
        elif (
            "lin" in name
            or "list" in name
            or "pila" in name
            or "cola" in name
        ):
            topic = "linear_structs"
        elif "arbol" in name or "tree" in name:
            topic = "trees"
        elif "arch" in name or "file" in name or "io" in name:
            topic = "file_io"
        else:
            topic = "general_prog"
    else:
        raise ValueError(
            f"Filename '{file_path.name}' must start with 'so_' "
            f"(Sistemas Operativos) or 'prog_' (Programación en C) "
            f"to ensure strict curricular assignment."
        )
    return notebook_id, topic


def build_benchmark_corpus(
    sources_dir: Path,
    output_corpus_path: Path,
    output_manifest_path: Path,
    chunk_config: ChunkConfig = DEFAULT_CHUNK_CONFIG,
) -> Dict[str, Any]:
    """Execute S1 ingestion pipeline on authentic source files."""
    if not sources_dir.exists() or not sources_dir.is_dir():
        raise FileNotFoundError(f"Sources directory not found: {sources_dir}")

    source_files = sorted(
        [
            p
            for p in sources_dir.iterdir()
            if p.is_file() and p.suffix.lower() in SUPPORTED_EXTENSIONS
        ]
    )

    if not source_files:
        ext_list = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise FileNotFoundError(
            f"No authentic source files found in '{sources_dir}'. "
            f"Please place authentic course documents ({ext_list}) "
            f"in '{sources_dir}'."
        )

    notebook_definitions = [
        Notebook(
            id="fadena-so",
            name="Sistemas Operativos (FADENA)",
            description="Conceptos de SO, procesos, concurrencia y memoria.",
            subject="Sistemas Operativos",
        ),
        Notebook(
            id="fadena-prog",
            name="Programación en C (FADENA)",
            description=(
                "Lenguaje C, memoria, estructuras de datos y archivos."
            ),
            subject="Programación",
        ),
    ]

    corpus_notebooks = [nb.model_dump() for nb in notebook_definitions]
    corpus_sources: List[Dict[str, Any]] = []
    corpus_documents: List[Dict[str, Any]] = []
    corpus_chunks: List[Dict[str, Any]] = []

    thematic_breakdown: Dict[str, Dict[str, int]] = {
        "fadena-so": {},
        "fadena-prog": {},
    }
    manifest_sources: List[Dict[str, Any]] = []

    global_chunk_idx = 0

    for file_path in source_files:
        notebook_id, topic = detect_notebook_and_topic(file_path)
        slug = file_path.stem.lower().replace("_", "-")
        source_id = f"src-{slug}"
        doc_id = f"doc-{slug}"

        # 1. Physical Source Manifest via S1 (SHA256 of physical file)
        manifest = create_source_manifest(
            file_path=file_path,
            source_id=source_id,
            corpus_root=sources_dir,
            metadata={"notebook_id": notebook_id, "topic": topic},
        )
        source_rec = SourceRecord(source_id=source_id, manifest=manifest)
        corpus_sources.append(
            {
                "source_id": source_rec.source_id,
                "filename": manifest.filename,
                "byte_size": manifest.byte_size,
                "sha256": manifest.sha256,
                "notebook_id": notebook_id,
                "topic": topic,
            }
        )

        # 2. Ingest Document via S1
        ingest_res = ingest_document(
            file_path=file_path,
            source_id=source_id,
            document_id=doc_id,
            corpus_root=sources_dir,
            metadata={"notebook_id": notebook_id, "topic": topic},
        )
        if ingest_res.document is None:
            raise RuntimeError(
                f"S1 Ingestion failed for '{file_path}': {ingest_res.error}"
            )
        doc = ingest_res.document
        corpus_documents.append(
            {
                "id": doc.id,
                "source_id": doc.source_id,
                "title": doc.title,
                "content": doc.content,
            }
        )

        # 3. Chunk Document via S1
        chunks = chunk_document(doc, chunk_config)
        doc_chunk_count = len(chunks)
        thematic_breakdown[notebook_id][topic] = (
            thematic_breakdown[notebook_id].get(topic, 0) + doc_chunk_count
        )

        for c in chunks:
            # Deterministic chunk ID prefix based on notebook and topic
            nb_prefix = "so" if notebook_id == "fadena-so" else "prog"
            cid = f"{nb_prefix}:{topic[:4]}:{global_chunk_idx:02d}"
            corpus_chunks.append(
                {
                    "id": cid,
                    "document_id": c.document_id,
                    "source_id": c.source_id,
                    "content": c.content,
                    "index": c.index,
                    "page_start": c.page_start,
                    "page_end": c.page_end,
                    "notebook_id": notebook_id,
                    "topic": topic,
                }
            )

            global_chunk_idx += 1

        manifest_sources.append(
            {
                "source_id": source_id,
                "filename": manifest.filename,
                "sha256": manifest.sha256,
                "byte_size": manifest.byte_size,
                "document_id": doc_id,
                "notebook_id": notebook_id,
                "topic": topic,
                "chunk_count": doc_chunk_count,
            }
        )

    # Compile Benchmark Corpus
    benchmark_corpus = {
        "benchmark_version": "S3.6.1",
        "notebooks": corpus_notebooks,
        "sources": corpus_sources,
        "documents": corpus_documents,
        "chunks": corpus_chunks,
    }

    # Compile Benchmark Manifest
    nb_counts = {
        "fadena-so": sum(thematic_breakdown["fadena-so"].values()),
        "fadena-prog": sum(thematic_breakdown["fadena-prog"].values()),
    }
    total_chunks = len(corpus_chunks)

    benchmark_manifest = {
        "benchmark_version": "S3.6.1",
        "build_timestamp": datetime.now(timezone.utc).isoformat(),
        "chunk_config": {
            "chunk_size": chunk_config.chunk_size,
            "chunk_overlap": chunk_config.chunk_overlap,
            "is_experimental_benchmark": True,
            "disclaimer": (
                "Experimental benchmark configuration, "
                "not a validated pedagogical optimum."
            ),
        },
        "total_source_files": len(source_files),
        "total_documents": len(corpus_documents),
        "total_chunks": total_chunks,
        "notebook_chunk_counts": nb_counts,
        "thematic_breakdown": thematic_breakdown,
        "sources": manifest_sources,
    }

    # Save artifacts
    output_corpus_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_corpus_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_corpus, f, indent=2, ensure_ascii=False)

    with open(output_manifest_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_manifest, f, indent=2, ensure_ascii=False)

    return benchmark_manifest
