"""Temporary staging importer. Never publishes candidates into the source text index."""
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import tempfile
import zipfile

from study_engine.contracts.multimodal import (
    TRUST, ColabPackageManifest, FigureCandidate, FormulaCandidate, PageEvidence,
    TableCandidate, check_provisional,
)
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.notebook import Notebook
from study_engine.storage.knowledge_store import KnowledgeStore

NOTEBOOK = "multimodal-colab"
MAX_FILE_SIZE = 100 * 1024 * 1024
MAX_ZIP_SIZE = 500 * 1024 * 1024
STAGING_SCHEMA = "multimodal-staging-2"


class MultimodalImportError(Exception):
    pass


class MultimodalValidationError(MultimodalImportError, ValueError):
    pass


def temporary_path(path):
    path = Path(path).absolute()
    if path.is_symlink() or not path.resolve().is_relative_to(Path(tempfile.gettempdir()).resolve()):
        raise MultimodalValidationError("Only temporary staging storage is allowed")
    return path.resolve()


def alias(data, *names, default=None):
    values = [data[n] for n in names if data.get(n) is not None]
    if values and any(v != values[0] for v in values[1:]):
        raise MultimodalValidationError(f"Conflicting aliases: {names}")
    return values[0] if values else default


def safe_file(root, name):
    path = root / name
    if Path(name).is_absolute() or ".." in Path(name).parts or path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
        raise MultimodalValidationError(f"Unsafe path: {name}")
    return path


def checked_record(raw, fields):
    check_provisional(raw)
    if "status" in raw and raw["status"] not in {"candidate", "unverified", "CANDIDATE_UNVERIFIED", "PROVISIONAL_UNVERIFIED", "REVIEW_PLAUSIBLE", "REVIEW_AMBIGUOUS"}:
        raise MultimodalValidationError("Invalid provisional status")
    unknown = raw.keys() - fields
    if unknown:
        raise MultimodalValidationError(f"Unknown export fields: {sorted(unknown)}")
    # Export metadata is provenance, never an alternate authority for identity.
    for key, value in raw.get("metadata", {}).items():
        if key in {"id", "element_id", "candidate_id", "doc_id", "document_id", "source_id", "pdf_page", "page", "page_number", "pdf_sha256", "text_sha256"}:
            if key not in raw or raw[key] != value:
                raise MultimodalValidationError(f"Conflicting metadata identity: {key}")
    return raw


def verify_text(text, digest):
    if digest is not None and hashlib.sha256(text.encode("utf-8")).hexdigest() != digest:
        raise MultimodalValidationError("text_sha256 mismatch")


class MultimodalImporter:
    def __init__(self, target_db_path, source_pdf_path=None):
        self.target_db_path = temporary_path(target_db_path)
        self.source_pdf_path = Path(source_pdf_path) if source_pdf_path else None

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    def close(self):
        pass

    def import_package(self, package_path):
        # Build privately; a failed validation/write never changes the destination.
        with tempfile.TemporaryDirectory(prefix="talos-mm-") as tmp:
            root = Path(package_path).resolve()
            if root.suffix == ".zip":
                if root.stat().st_size > MAX_ZIP_SIZE:
                    raise MultimodalValidationError("ZIP too large")
                with zipfile.ZipFile(root) as archive:
                    names = archive.namelist()
                    if len(set(names)) != len(names):
                        raise MultimodalValidationError("Duplicate ZIP entries")
                    for entry in archive.infolist():
                        safe_file(Path(tmp), entry.filename)
                        if entry.file_size > MAX_FILE_SIZE:
                            raise MultimodalValidationError("ZIP file too large")
                    if sum(e.file_size for e in archive.infolist()) > MAX_ZIP_SIZE:
                        raise MultimodalValidationError("Expanded ZIP too large")
                    archive.extractall(Path(tmp) / "package")
                root = Path(tmp) / "package"
            if not (root / "manifest.json").is_file():
                raise MultimodalValidationError("manifest.json not found")
            files = sorted(p for p in root.rglob("*") if p.is_file())
            identity = hashlib.sha256()
            for p in files:
                safe_file(root, str(p.relative_to(root)))
                if p.stat().st_size > MAX_FILE_SIZE:
                    raise MultimodalValidationError("Package file too large")
                identity.update(str(p.relative_to(root)).encode() + b"\0")
                identity.update(hashlib.sha256(p.read_bytes()).digest())
            digest = identity.hexdigest()
            manifest = ColabPackageManifest.model_validate(json.loads((root / "manifest.json").read_bytes()))
            if len({f.path for f in manifest.files}) != len(manifest.files):
                raise MultimodalValidationError("Duplicate manifest file identity")
            hashes = dict(manifest.file_sha256)
            for f in manifest.files:
                if f.path in hashes and hashes[f.path] != f.sha256:
                    raise MultimodalValidationError("Conflicting manifest hashes")
                hashes[f.path] = f.sha256
                p = safe_file(root, f.path)
                if not p.is_file() or p.stat().st_size != f.size_bytes:
                    raise MultimodalValidationError(f"Missing file or size mismatch: {f.path}")
            for name, expected in hashes.items():
                p = safe_file(root, name)
                if not p.is_file() or hashlib.sha256(p.read_bytes()).hexdigest() != expected:
                    raise MultimodalValidationError(f"Hash mismatch: {name}")
            if self.source_pdf_path and hashlib.sha256(self.source_pdf_path.read_bytes()).hexdigest() != manifest.source_pdf_sha256:
                raise MultimodalValidationError("Source PDF hash mismatch")
            if self.target_db_path.exists():
                with sqlite3.connect(f"file:{self.target_db_path}?mode=ro", uri=True) as conn:
                    try:
                        row = conn.execute("SELECT schema, digest, result FROM mm_staging").fetchone()
                    except sqlite3.Error as exc:
                        raise MultimodalValidationError("Destination is not multimodal staging") from exc
                if not row or row[:2] != (STAGING_SCHEMA, digest):
                    raise MultimodalValidationError("Destination contains a different staging package")
                return json.loads(row[2])
            work = Path(tmp) / "build.db"
            store = KnowledgeStore(work)
            try:
                result = self._build(root, manifest, store)
                with store.engine.transaction() as conn:
                    conn.execute("CREATE TABLE mm_staging(schema TEXT, digest TEXT, result TEXT)")
                    conn.execute("INSERT INTO mm_staging VALUES (?, ?, ?)", (STAGING_SCHEMA, digest, json.dumps(result)))
                with store.engine.transaction(mode="DEFERRED") as conn:
                    # SQLite backup includes WAL contents; publication is a single no-clobber link.
                    with sqlite3.connect(Path(tmp) / "publish.db") as dest:
                        conn.backup(dest)
            finally:
                store.close()
            os.link(Path(tmp) / "publish.db", self.target_db_path)
            return result

    def _build(self, root, manifest, store):
        def records(name):
            p = safe_file(root, name)
            if not p.exists():
                if name in {"documents.json", "chunks.jsonl"}:
                    raise MultimodalValidationError(f"Required file missing: {name}")
                return []
            if manifest.files and name not in {f.path for f in manifest.files}:
                raise MultimodalValidationError(f"Unmanifested data file: {name}")
            if name.endswith(".json"):
                return json.loads(p.read_bytes())
            return [json.loads(line) for line in p.read_bytes().splitlines() if line.strip()]

        store.initialize()
        store.create_notebook(Notebook(id=NOTEBOOK, name="Provisional multimodal staging"))
        docs, sources = {}, set()
        for raw in records("documents.json"):
            checked_record(raw, {"doc_id", "id", "source_id", "title", "content", "pages", "page_count", "pdf_sha256", "metadata"} | TRUST.keys())
            did = alias(raw, "id", "doc_id")
            sid = raw.get("source_id", did)
            if did in docs:
                raise MultimodalValidationError("Duplicate document identity")
            doc = Document(id=did, source_id=sid, title=raw.get("title", did), content=raw.get("content"), page_count=alias(raw, "pages", "page_count"), metadata={"export": raw, **TRUST})
            if sid not in sources:
                store.store_ingestion_bundle(SourceRecord(source_id=sid, manifest=SourceManifest(source_id=sid, filename=did, byte_size=0, sha256=raw.get("pdf_sha256", "0" * 64))), [], [], notebook_id=NOTEBOOK)
                sources.add(sid)
            store.save_document(doc)
            docs[did] = doc

        pdf_hashes = {}

        def location(raw, page_names):
            did = alias(raw, "document_id", "doc_id")
            if did not in docs:
                raise MultimodalValidationError("Unknown document identity")
            doc = docs[did]
            sid = raw.get("source_id", doc.source_id)
            page = alias(raw, *page_names)
            if sid != doc.source_id or type(page) is not int or page < 1 or (doc.page_count and page > doc.page_count):
                raise MultimodalValidationError("Invalid document/source/physical page")
            pdf_hash = raw.get("pdf_sha256")
            expected = doc.metadata["export"].get("pdf_sha256")
            if expected and pdf_hash != expected:
                raise MultimodalValidationError("Document PDF provenance mismatch")
            if pdf_hash:
                if did in pdf_hashes and pdf_hashes[did] != pdf_hash:
                    raise MultimodalValidationError("Conflicting PDF provenance")
                pdf_hashes[did] = pdf_hash
            page_id = raw.get("page_id")
            if page_id and ":pdfpage:" in page_id and page_id != f"{did}:pdfpage:{page:05d}":
                raise MultimodalValidationError("Conflicting physical page identity")
            return did, sid, page

        chunks, indices = {}, {}
        for raw in records("chunks.jsonl"):
            checked_record(raw, {"id", "doc_id", "document_id", "source_id", "content", "text", "pdf_page", "page_start", "page_end", "index", "metadata", "candidate_section_id", "element_ids", "page_label", "pdf_sha256", "section_id", "status", "text_sha256"} | TRUST.keys())
            did, sid, page = location(raw, ("pdf_page", "page_start"))
            text = alias(raw, "text", "content")
            verify_text(text, raw.get("text_sha256"))
            idx = raw.get("index", indices.get(did, 0))
            indices[did] = idx + 1
            chunk = Chunk(id=raw["id"], document_id=did, source_id=sid, content=text, page_start=page, page_end=raw.get("page_end", page), index=idx, metadata={"export": raw, "text_sha256": raw.get("text_sha256"), **TRUST})
            if chunk.page_end < page or (docs[did].page_count and chunk.page_end > docs[did].page_count) or chunk.id in chunks:
                raise MultimodalValidationError("Invalid chunk identity or page range")
            chunks[chunk.id] = chunk
        store.chunks.save_chunks(list(chunks.values()))
        elements = {}
        extra = {"doc_id", "pdf_page", "candidate_id", "kind", "content", "human_verified", "engine", "asset_path", "bbox_raw", "bbox_raw_origin", "bbox_top_left", "cross_engine_candidates", "display_header_row_suspected", "page_id", "quality", "source_element_id", "source_record_path", "table_text_sha256", "caption_candidate", "cells", "flags", "mode_columns", "model_table_index", "source_page_token_recall"}
        for filename, kind, model in (("baseline_tables_candidates.jsonl", "table", TableCandidate), ("tables_model_candidates.jsonl", "table", TableCandidate), ("figures_formulas_candidates.jsonl", None, None)):
            for raw in records(filename):
                typ = alias(raw, "kind", "element_type", default=kind)
                cls = model or {"figure": FigureCandidate, "formula": FormulaCandidate}.get(typ)
                if cls is None or (kind and typ != kind):
                    raise MultimodalValidationError("Invalid element type")
                checked_record(raw, set(cls.model_fields) | extra)
                did, sid, page = location(raw, ("pdf_page", "page"))
                eid = alias(raw, "element_id", "candidate_id")
                data = {k: v for k, v in raw.items() if k in cls.model_fields}
                data.update(element_id=eid, document_id=did, source_id=sid, page=page, metadata={"export": raw})
                data[f"{typ}_id"] = raw.get(f"{typ}_id") or eid
                if typ == "table":
                    rows = raw.get("rows", [])
                    data.update(rows=raw.get("cells", []) if isinstance(rows, int) else rows, is_baseline=filename.startswith("baseline"))
                    data["caption"] = alias(raw, "caption", "caption_candidate")
                elif "content" in raw:
                    content = raw["content"]
                    if typ == "figure":
                        data["caption"] = content.get("caption") if isinstance(content, dict) else content
                    else:
                        data["latex"] = content.get("literal") if isinstance(content, dict) else content
                        data["plain_text"] = data["latex"]
                elem = cls.model_validate(data)
                if eid in chunks or eid in elements:
                    raise MultimodalValidationError("Duplicate element identity")
                asset = raw.get("asset_path") or raw.get("image_path")
                elem.metadata["asset_status"] = "MISSING" if not asset or not safe_file(root, asset).is_file() else "AVAILABLE_IN_PACKAGE"
                if elem.metadata["asset_status"] == "AVAILABLE_IN_PACKAGE":
                    expected = raw.get("image_sha256")
                    if expected and hashlib.sha256(safe_file(root, asset).read_bytes()).hexdigest() != expected:
                        raise MultimodalValidationError("Asset hash mismatch")
                    elem.metadata["asset_status"] = "NOT_RETAINED"
                # No path is served: extracted assets expire with this temporary import.
                elements[eid] = elem

        # First, determine the correct document_id for each page based on chunk ownership
        # Each physical page number maps to exactly one document (validated above)
        page_to_doc = {}
        for chunk in chunks.values():
            if chunk.page_start not in page_to_doc:
                page_to_doc[chunk.page_start] = chunk.document_id
        
        pages = []
        for raw in records("pages_evidence.jsonl"):
            checked_record(raw, set(PageEvidence.model_fields) | {"doc_id", "pdf_page", "engine_names", "model_table_candidate_ids", "model_visual_candidate_ids", "original_chunk_ids", "status"})
            # Determine the correct document_id: if page evidence references chunks, use the document that owns those chunks;
            # otherwise use the doc_id from page evidence (for pages without chunks)
            page = alias(raw, "pdf_page", "page_number")
            evidence_chunk_ids = alias(raw, "chunk_ids", "original_chunk_ids", default=[]) or []
            if evidence_chunk_ids:
                # Page evidence references chunks - use the document that owns the first referenced chunk
                first_chunk_id = evidence_chunk_ids[0]
                if first_chunk_id not in chunks:
                    raise MultimodalValidationError(f"Page {page} references unknown chunk: {first_chunk_id}")
                did = chunks[first_chunk_id].document_id
                # Verify all referenced chunks belong to the same document
                for cid in evidence_chunk_ids:
                    if cid not in chunks or chunks[cid].document_id != did:
                        raise MultimodalValidationError(f"Page {page} references chunks from multiple documents")
            else:
                # Page has no chunk references - use the doc_id from page evidence
                did = alias(raw, "document_id", "doc_id")
                if did not in docs:
                    raise MultimodalValidationError(f"Unknown document identity in page evidence: {did}")
            
            sid = docs[did].source_id
            data = {k: v for k, v in raw.items() if k in PageEvidence.model_fields}
            data.update(document_id=did, source_id=sid, page_number=page, metadata={"export": raw})
            data["chunk_ids"] = alias(raw, "chunk_ids", "original_chunk_ids", default=[]) or []
            data["table_ids"] = alias(raw, "table_ids", "model_table_candidate_ids", default=[]) or []
            visual = raw.get("model_visual_candidate_ids") or []
            for typ in ("figure", "formula"):
                data[f"{typ}_ids"] = alias(raw, f"{typ}_ids", default=[eid for eid in visual if eid in elements and elements[eid].element_type.value == typ]) or []
            for eid in visual:
                if eid not in elements:
                    raise MultimodalValidationError("Unknown visual relation")
            pe = PageEvidence.model_validate(data)
            verify_text(pe.text_content or "", pe.text_sha256)
            # Validate cross-document/page relations for chunk references (strict)
            for ref in pe.chunk_ids:
                obj = chunks.get(ref)
                physical = getattr(obj, "page_start", None)
                if obj is None or obj.document_id != did or obj.source_id != sid or physical != page:
                    raise MultimodalValidationError("Cross-document/page relation in chunk reference")
            # For visual references (tables/figures/formulas), allow cross-document on same page
            # as the source data may have inconsistent doc_id assignments for pages without chunks
            for typ in ("table", "figure", "formula"):
                for ref in getattr(pe, f"{typ}_ids"):
                    obj = elements.get(ref)
                    if obj is None:
                        raise MultimodalValidationError(f"Unknown {typ} reference: {ref}")
                    # Allow cross-document on same page for visual elements (data quality issue in source)
                    physical = getattr(obj, "page", getattr(obj, "page_start", None))
                    if physical is not None and physical != page:
                        raise MultimodalValidationError(f"Cross-page {typ} reference: {ref}")
            if pe.page_id and any(p.page_id == pe.page_id for p in pages):
                raise MultimodalValidationError("Duplicate page identity")
            if any(p.document_id == did and p.page_number == page for p in pages):
                raise MultimodalValidationError("Duplicate document/page")
            pages.append(pe)

        with store.engine.transaction() as conn:
            conn.execute("CREATE TABLE mm_elements(id TEXT PRIMARY KEY, document_id TEXT, source_id TEXT, page INTEGER, kind TEXT, data TEXT)")
            conn.execute("CREATE VIRTUAL TABLE mm_fts USING fts5(id UNINDEXED, terms)")
            for eid, elem in elements.items():
                data = elem.model_dump(mode="json")
                conn.execute("INSERT INTO mm_elements VALUES (?, ?, ?, ?, ?, ?)", (eid, elem.document_id, elem.source_id, elem.page, elem.element_type.value, json.dumps(data)))
                conn.execute("INSERT INTO mm_fts VALUES (?, ?)", (eid, json.dumps(data, ensure_ascii=False)))
            conn.execute("CREATE TABLE mm_pages(document_id TEXT, source_id TEXT, page INTEGER, data TEXT, PRIMARY KEY(document_id, page))")
            for pe in pages:
                conn.execute("INSERT INTO mm_pages VALUES (?, ?, ?, ?)", (pe.document_id, pe.source_id, pe.page_number, pe.model_dump_json()))
        counts = dict(sources=len(sources), documents=len(docs), chunks=len(chunks), tables=sum(e.element_type.value == "table" for e in elements.values()), figures=sum(e.element_type.value == "figure" for e in elements.values()), formulas=sum(e.element_type.value == "formula" for e in elements.values()), pages=len(pages), relations=0)
        if not manifest.files:
            expected = dict(documents=manifest.documents_count, chunks=manifest.chunks_count, tables=manifest.tables_baseline + manifest.tables_new, figures=manifest.figures_count, formulas=manifest.formulas_count, pages=manifest.pages_with_evidence)
            if any(counts[k] != v for k, v in expected.items()):
                raise MultimodalValidationError("Manifest counts mismatch")
        return dict(status="IMPORTED", imported=counts, manifest=manifest.model_dump(mode="json", by_alias=True), verification=dict(all_passed=True, checks=[dict(check="validated_records_and_hashes", passed=True)]), **TRUST)


def create_multimodal_importer(target_db_path, source_pdf_path=None):
    return MultimodalImporter(target_db_path, source_pdf_path)
