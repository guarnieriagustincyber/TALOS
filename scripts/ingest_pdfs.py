#!/usr/bin/env python3
"""
Script to ingest all PDFs from the benchmark into the knowledge store.
"""
import sys
from pathlib import Path

# Remove sys.path manipulation to avoid duplicate imports

# Absolute imports
from study_engine.contracts.catalog import NotebookNotFoundError, SourceManifest, SourceRecord
from study_engine.contracts.notebook import Notebook
from study_engine.ingestion.document_ingestion import ingest_document
from study_engine.ingestion.chunking import ChunkConfig, chunk_document
from study_engine.storage.knowledge_store import KnowledgeStore


def main() -> None:
    print("🚀 Iniciando ingestión de PDFs...")
    # Directories
    pdf_dir = Path("data/benchmark/sources")
    db_path = Path("data/storage/knowledge.db")
    if not pdf_dir.exists():
        print(f"❌ No existe el directorio {pdf_dir}")
        sys.exit(1)
    pdfs = list(pdf_dir.glob("*.pdf"))
    print(f"📚 Encontrados {len(pdfs)} PDFs para ingestar")
    if not pdfs:
        print("❌ No hay PDFs para ingestar")
        sys.exit(1)
    for pdf in pdfs:
        print(f"  - {pdf.name} ({pdf.stat().st_size / 1024:.1f} KB)")

    # Ensure storage directory exists
    db_path.parent.mkdir(parents=True, exist_ok=True)
    # Initialize knowledge store
    print(f"\n📦 Creando knowledge store en {db_path}...")
    ks = KnowledgeStore(db_path=str(db_path))
    ks.initialize()
    print("✅ Knowledge store inicializado")
    # Notebook auto‑creation (configurable via env var)
    import os
    NOTEBOOK_ID = os.getenv("STUDY_ENGINE_NOTEBOOK_ID", "NB-CYBERSECURITY-V1")
    try:
        ks.get_notebook(NOTEBOOK_ID)
        print(f"ℹ️  Notebook '{NOTEBOOK_ID}' ya existe")
    except NotebookNotFoundError:
        ks.create_notebook(
            Notebook(
                id=NOTEBOOK_ID,
                name="Cybersecurity Benchmark",
                description="Colección de PDFs del benchmark académico",
            )
        )
        print(f"✅ Notebook '{NOTEBOOK_ID}' creado")
    # Register benchmark source in catalog
    import hashlib
    source_id = "benchmark"
    empty_sha256 = hashlib.sha256(b'').hexdigest()
    manifest = SourceManifest(
        source_id=source_id,
        filename="benchmark",
        byte_size=0,
        sha256=empty_sha256,
        file_path=None,
    )
    source_record = SourceRecord(
        source_id=source_id,
        manifest=manifest,
        metadata={},
    )
    try:
        ks.save_source(source_record)
        print(f"✅ Source '{source_id}' registrado en el catálogo")
    except Exception as e:
        print(f"⚠️  No se pudo registrar el source: {e}")

    # Link source to notebook
    try:
        ks.link_source_to_notebook(notebook_id=NOTEBOOK_ID, source_id=source_id)
        print(f"✅ Source '{source_id}' vinculado al notebook '{NOTEBOOK_ID}'")
    except Exception as e:
        print(f"⚠️  No se pudo vincular el source al notebook: {e}")

    # Chunk configuration
    chunk_cfg = ChunkConfig(chunk_size=512, chunk_overlap=50)
    total_chunks = 0
    print("\n📖 Ingestando PDFs...")
    for i, pdf_path in enumerate(pdfs, 1):
        print(f"\n[{i}/{len(pdfs)}] Procesando: {pdf_path.name}")
        try:
            doc_id = pdf_path.stem
            # Ingest document (returns IngestionResult)
            result = ingest_document(
                file_path=str(pdf_path),
                source_id="benchmark",
                document_id=doc_id,
                metadata=None,
            )
            if result.status != "COMPLETED":
                print(f"  ❌ Ingestión falló: {getattr(result.error, 'message', 'Desconocido')}")
                continue
            document = result.document
            # Save document
            ks.save_document(document)
            # Chunk document
            chunks = chunk_document(document, config=chunk_cfg)
            ks.save_chunks(chunks)
            chunks_created = len(chunks)
            total_chunks += chunks_created
            print(f"  ✅ Creados {chunks_created} chunks")
        except Exception as e:
            print(f"  ❌ Error: {e}")
            import traceback
            traceback.print_exc()

    # Final verification
    print("\n" + "=" * 60)
    print("📊 VERIFICACIÓN FINAL")
    print("=" * 60)
    try:
        stats = ks.get_stats()
        count_docs = stats.get("documents_count", 0)
        count_chunks = stats.get("chunks_count", 0)
        print(f"📚 Documentos en knowledge store: {count_docs}")
        print(f"📝 Total de chunks: {count_chunks}")
        print(f"💾 Base de datos: {db_path} ({db_path.stat().st_size / 1024:.1f} KB)")
        if count_chunks > 0:
            print("\n✅ INGESTIÓN EXITOSA")
        else:
            print("\n⚠️  INGESTIÓN COMPLETADA PERO SIN CHUNKS")
    except Exception as e:
        print(f"❌ Error en verificación: {e}")


if __name__ == "__main__":
    main()
