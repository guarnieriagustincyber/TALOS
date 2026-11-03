"""Tests for MultimodalImporter using synthetic Colab-compatible packages."""

import hashlib
import json
import tempfile
import zipfile
from pathlib import Path

import pytest
from pydantic import ValidationError

from study_engine.contracts.multimodal import (
    CandidateStatus,
    ChunkMultimodalRelation,
    ColabPackageManifest,
    FigureCandidate,
    FormulaCandidate,
    MultimodalElementType,
    MultimodalPackage,
    PageEvidence,
    RelationType,
    TableCandidate,
)
from study_engine.ingestion.multimodal_importer import (
    MultimodalImporter,
    MultimodalImportError,
    MultimodalValidationError,
)


def make_synthetic_package(tmp_path: Path) -> Path:
    """Create a valid synthetic Colab package for testing."""
    pkg_dir = tmp_path / "synthetic_pkg"
    pkg_dir.mkdir()
    
    # Create manifest
    pdf_content = b"synthetic pdf content for testing"
    pdf_hash = hashlib.sha256(pdf_content).hexdigest()
    
    manifest = ColabPackageManifest(
        schema="TALOS_RECONCILE_PARALLEL_1.0",
        package_id="test-pkg-001",
        created_at="2026-10-31T00:00:00Z",
        status="PROVISIONAL_UNVERIFIED",
        trusted_for_rag=False,
        production_import_authorized=False,
        fidelity_certified=False,
        documents_count=1,
        chunks_count=2,
        tables_baseline=1,
        tables_new=1,
        figures_count=1,
        formulas_count=1,
        pages_with_evidence=1,
        source_pdf_sha256=pdf_hash,
        file_sizes={"documents.json": 200, "chunks.jsonl": 300},
        file_sha256={},
    )
    
    (pkg_dir / "manifest.json").write_text(manifest.model_dump_json())
    
    # Documents
    documents = [{
        "id": "doc-1",
        "source_id": "src-1",
        "title": "Test Document",
        "content": "This is a test document with a table and figure.",
        "page_count": 2,
        "metadata": {},
    }]
    (pkg_dir / "documents.json").write_text(json.dumps(documents))
    
    # Chunks
    chunks = [
        {
            "id": "chunk-1",
            "document_id": "doc-1",
            "source_id": "src-1",
            "content": "This is a test document with a table and figure on page 1.",
            "page_start": 1,
            "page_end": 1,
            "index": 0,
            "metadata": {},
        },
        {
            "id": "chunk-2",
            "document_id": "doc-1",
            "source_id": "src-1",
            "content": "Page 2 has a formula and another table.",
            "page_start": 2,
            "page_end": 2,
            "index": 1,
            "metadata": {},
        },
    ]
    with open(pkg_dir / "chunks.jsonl", 'w') as f:
        for chunk in chunks:
            f.write(json.dumps(chunk) + "\n")
    
    # Baseline tables
    baseline_table = TableCandidate(
        element_id="table-b1",
        element_type=MultimodalElementType.TABLE,
        document_id="doc-1",
        source_id="src-1",
        page=1,
        candidate_section_id="sec-1",
        pdf_sha256="0" * 64,
        status=CandidateStatus.CANDIDATE,
        confidence=0.9,
        table_id="table_1",
        caption="Baseline Table",
        headers=["A", "B"],
        rows=[["1", "2"], ["3", "4"]],
        is_baseline=True,
    )
    (pkg_dir / "baseline_tables_candidates.jsonl").write_text(baseline_table.model_dump_json() + "\n")
    
    # Model tables
    model_table = TableCandidate(
        element_id="table-m1",
        element_type=MultimodalElementType.TABLE,
        document_id="doc-1",
        source_id="src-1",
        page=2,
        candidate_section_id="sec-2",
        pdf_sha256="0" * 64,
        status=CandidateStatus.CANDIDATE,
        confidence=0.8,
        table_id="table_2",
        caption="Model Table",
        headers=["X", "Y"],
        rows=[["a", "b"], ["c", "d"]],
        is_baseline=False,
    )
    (pkg_dir / "tables_model_candidates.jsonl").write_text(model_table.model_dump_json() + "\n")
    
    # Figures and formulas
    figure = FigureCandidate(
        element_id="fig-1",
        element_type=MultimodalElementType.FIGURE,
        document_id="doc-1",
        source_id="src-1",
        page=1,
        candidate_section_id="sec-1",
        pdf_sha256="0" * 64,
        status=CandidateStatus.CANDIDATE,
        confidence=0.85,
        figure_id="figure_1",
        caption="Test Figure",
        alt_text="A test figure",
    )
    
    formula = FormulaCandidate(
        element_id="form-1",
        element_type=MultimodalElementType.FORMULA,
        document_id="doc-1",
        source_id="src-1",
        page=2,
        candidate_section_id="sec-2",
        pdf_sha256="0" * 64,
        status=CandidateStatus.CANDIDATE,
        confidence=0.9,
        formula_id="formula_1",
        latex="E = mc^2",
        plain_text="E equals m c squared",
        variables=["E", "m", "c"],
    )
    
    with open(pkg_dir / "figures_formulas_candidates.jsonl", 'w') as f:
        f.write(figure.model_dump_json() + "\n")
        f.write(formula.model_dump_json() + "\n")
    
    # Pages
    page = PageEvidence(
        page_id="page-1",
        document_id="doc-1",
        source_id="src-1",
        page_number=1,
        pdf_sha256="0" * 64,
        text_content="This is a test document with a table and figure on page 1.",
        chunk_ids=["chunk-1"],
        table_ids=["table-b1"],
        figure_ids=["fig-1"],
        formula_ids=[],
        is_preliminary=False,
        multimodel_confidence=0.9,
        text_sha256=hashlib.sha256(b"This is a test document with a table and figure on page 1.").hexdigest(),
    )
    (pkg_dir / "pages_evidence.jsonl").write_text(page.model_dump_json() + "\n")
    
    # Quality report
    quality = {"completeness": 0.9, "accuracy": 0.85}
    (pkg_dir / "quality_report.json").write_text(json.dumps(quality))
    
    # Staging sqlite (placeholder)
    (pkg_dir / "staging.sqlite").write_bytes(b"placeholder")
    
    return pkg_dir


def create_zip_package(pkg_dir: Path, zip_path: Path) -> None:
    """Create a ZIP package from a directory."""
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for file_path in pkg_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(pkg_dir)
                zf.write(file_path, arcname)


class TestMultimodalImporter:
    """Tests for MultimodalImporter."""
    
    def test_import_directory_package(self, tmp_path):
        """Test importing an extracted package directory."""
        pkg_dir = make_synthetic_package(tmp_path)
        db_path = tmp_path / "test_import.db"
        
        with MultimodalImporter(db_path) as importer:
            result = importer.import_package(pkg_dir)
        
        assert result["status"] in ("IMPORTED", "PARTIAL")
        assert result["imported"]["documents"] == 1
        assert result["imported"]["chunks"] == 2
        assert result["imported"]["tables"] == 2
        assert result["imported"]["figures"] == 1
        assert result["imported"]["formulas"] == 1
        assert result["imported"]["pages"] == 1
        assert result["verification"]["all_passed"] is True
    
    def test_import_zip_package(self, tmp_path):
        """Test importing a ZIP package."""
        pkg_dir = make_synthetic_package(tmp_path)
        zip_path = tmp_path / "test_package.zip"
        create_zip_package(pkg_dir, zip_path)
        
        db_path = tmp_path / "test_import.zip.db"
        
        with MultimodalImporter(db_path) as importer:
            result = importer.import_package(zip_path)
        
        assert result["status"] in ("IMPORTED", "PARTIAL")
        assert result["imported"]["documents"] == 1
        assert result["verification"]["all_passed"] is True
    
    def test_reject_trusted_for_rag(self, tmp_path):
        """Reject manifest with trusted_for_rag=true at validation time."""
        pkg_dir = make_synthetic_package(tmp_path)
        # Manifest validation now happens at creation time
        with pytest.raises(ValidationError, match="trusted_for_rag"):
            manifest = ColabPackageManifest(
                schema="TALOS_RECONCILE_PARALLEL_1.0",
                package_id="test-pkg-001",
                created_at="2026-10-31T00:00:00Z",
                status="PROVISIONAL_UNVERIFIED",
                trusted_for_rag=True,  # VIOLATION
                production_import_authorized=False,
                fidelity_certified=False,
                documents_count=1,
                chunks_count=2,
                tables_baseline=1,
                tables_new=1,
                figures_count=1,
                formulas_count=1,
                pages_with_evidence=1,
                source_pdf_sha256="0" * 64,
            )
            (pkg_dir / "manifest.json").write_text(manifest.model_dump_json())
    
    def test_reject_production_authorized(self, tmp_path):
        """Reject manifest with production_import_authorized=true at validation time."""
        with pytest.raises(ValidationError, match="production_import_authorized"):
            ColabPackageManifest(
                schema="TALOS_RECONCILE_PARALLEL_1.0",
                package_id="test-pkg-001",
                created_at="2026-10-31T00:00:00Z",
                status="PROVISIONAL_UNVERIFIED",
                trusted_for_rag=False,
                production_import_authorized=True,  # VIOLATION
                fidelity_certified=False,
                documents_count=1,
                chunks_count=2,
                tables_baseline=1,
                tables_new=1,
                figures_count=1,
                formulas_count=1,
                pages_with_evidence=1,
                source_pdf_sha256="0" * 64,
            )
    
    def test_reject_fidelity_certified(self, tmp_path):
        """Reject manifest with fidelity_certified=true at validation time."""
        with pytest.raises(ValidationError, match="fidelity_certified"):
            ColabPackageManifest(
                schema="TALOS_RECONCILE_PARALLEL_1.0",
                package_id="test-pkg-001",
                created_at="2026-10-31T00:00:00Z",
                status="PROVISIONAL_UNVERIFIED",
                trusted_for_rag=False,
                production_import_authorized=False,
                fidelity_certified=True,  # VIOLATION
                documents_count=1,
                chunks_count=2,
                tables_baseline=1,
                tables_new=1,
                figures_count=1,
                formulas_count=1,
                pages_with_evidence=1,
                source_pdf_sha256="0" * 64,
            )
    
    def test_reject_wrong_schema(self, tmp_path):
        """Reject manifest with wrong schema version."""
        pkg_dir = make_synthetic_package(tmp_path)
        manifest = json.loads((pkg_dir / "manifest.json").read_text())
        manifest["schema_version"] = "WRONG_SCHEMA"
        (pkg_dir / "manifest.json").write_text(json.dumps(manifest))
        
        db_path = tmp_path / "test_reject4.db"
        
        with MultimodalImporter(db_path) as importer:
            with pytest.raises(ValidationError):
                importer.import_package(pkg_dir)
    
    def test_reject_unsafe_zip(self, tmp_path):
        """Reject ZIP with path traversal."""
        zip_path = tmp_path / "unsafe.zip"
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("../escape.txt", "malicious")
        
        db_path = tmp_path / "test_unsafe.db"
        
        with MultimodalImporter(db_path) as importer:
            with pytest.raises(MultimodalValidationError, match="Unsafe path"):
                importer.import_package(zip_path)
    
    def test_reject_large_file_in_zip(self, tmp_path):
        """Reject ZIP with oversized file."""
        zip_path = tmp_path / "large.zip"
        large_content = "x" * (101 * 1024 * 1024)  # > 100MB
        with zipfile.ZipFile(zip_path, 'w') as zf:
            zf.writestr("large.txt", large_content)
        
        db_path = tmp_path / "test_large.db"
        
        with MultimodalImporter(db_path) as importer:
            with pytest.raises(MultimodalValidationError, match="too large"):
                importer.import_package(zip_path)
    
    def test_idempotent_import(self, tmp_path):
        """Test that importing twice produces same results."""
        pkg_dir = make_synthetic_package(tmp_path)
        db_path = tmp_path / "test_idempotent.db"
        
        with MultimodalImporter(db_path) as importer:
            result1 = importer.import_package(pkg_dir)
        
        # Re-import same package
        with MultimodalImporter(db_path) as importer:
            result2 = importer.import_package(pkg_dir)
        
        # Should have same counts (idempotent)
        assert result1["imported"]["documents"] == result2["imported"]["documents"]
        assert result1["imported"]["chunks"] == result2["imported"]["chunks"]
    
    def test_missing_manifest(self, tmp_path):
        """Reject package without manifest."""
        pkg_dir = tmp_path / "no_manifest"
        pkg_dir.mkdir()
        (pkg_dir / "documents.json").write_text("[]")
        
        db_path = tmp_path / "test_no_manifest.db"
        
        with MultimodalImporter(db_path) as importer:
            with pytest.raises(MultimodalValidationError, match="manifest.json not found"):
                importer.import_package(pkg_dir)
    
    def test_hash_mismatch(self, tmp_path):
        """Reject package with hash mismatch."""
        pkg_dir = make_synthetic_package(tmp_path)
        # Corrupt a file hash
        manifest = ColabPackageManifest(
            schema="TALOS_RECONCILE_PARALLEL_1.0",
            package_id="test-pkg-001",
            created_at="2026-10-31T00:00:00Z",
            status="PROVISIONAL_UNVERIFIED",
            trusted_for_rag=False,
            production_import_authorized=False,
            fidelity_certified=False,
            documents_count=1,
            chunks_count=2,
            tables_baseline=1,
            tables_new=1,
            figures_count=1,
            formulas_count=1,
            pages_with_evidence=1,
            source_pdf_sha256="0" * 64,
            file_sha256={"documents.json": "wrong_hash"},
        )
        (pkg_dir / "manifest.json").write_text(manifest.model_dump_json())
        
        db_path = tmp_path / "test_hash.db"
        
        with MultimodalImporter(db_path) as importer:
            with pytest.raises(MultimodalValidationError, match="Hash mismatch"):
                importer.import_package(pkg_dir)


class TestMultimodalPackageContracts:
    """Tests for multimodal contract validation."""
    
    def test_table_candidate_validation(self):
        """Test TableCandidate validation."""
        table = TableCandidate(
            element_id="t1",
            element_type=MultimodalElementType.TABLE,
            document_id="doc-1",
            source_id="src-1",
            page=1,
            candidate_section_id="sec-1",
            pdf_sha256="0" * 64,
            table_id="table_1",
            headers=["A", "B"],
            rows=[["1", "2"]],
        )
        assert table.row_count == 1
        assert table.col_count == 2
        assert table.is_baseline is False
    
    def test_table_candidate_baseline(self):
        """Test baseline table candidate."""
        table = TableCandidate(
            element_id="t1",
            element_type=MultimodalElementType.TABLE,
            document_id="doc-1",
            source_id="src-1",
            page=1,
            candidate_section_id="sec-1",
            pdf_sha256="0" * 64,
            table_id="table_1",
            headers=["A", "B"],
            rows=[["1", "2"]],
            is_baseline=True,
        )
        assert table.is_baseline is True
    
    def test_figure_candidate_validation(self):
        """Test FigureCandidate validation."""
        fig = FigureCandidate(
            element_id="f1",
            element_type=MultimodalElementType.FIGURE,
            document_id="doc-1",
            source_id="src-1",
            page=1,
            candidate_section_id="sec-1",
            pdf_sha256="0" * 64,
            figure_id="fig_1",
            caption="Test Figure",
            alt_text="A test figure",
        )
        assert fig.figure_id == "fig_1"
        assert fig.mime_type == "image/png"
    
    def test_formula_candidate_validation(self):
        """Test FormulaCandidate validation."""
        formula = FormulaCandidate(
            element_id="form-1",
            element_type=MultimodalElementType.FORMULA,
            document_id="doc-1",
            source_id="src-1",
            page=1,
            candidate_section_id="sec-1",
            pdf_sha256="0" * 64,
            formula_id="formula_1",
            latex="E = mc^2",
            variables=["E", "m", "c"],
        )
        assert formula.latex == "E = mc^2"
        assert formula.variables == ["E", "m", "c"]
    
    def test_page_evidence_validation(self):
        """Test PageEvidence validation."""
        page = PageEvidence(
            page_id="page-1",
            document_id="doc-1",
            source_id="src-1",
            page_number=1,
            pdf_sha256="0" * 64,
            chunk_ids=["chunk-1"],
            table_ids=["table-1"],
            figure_ids=["fig-1"],
            formula_ids=["form-1"],
            is_preliminary=False,
        )
        assert page.page_number == 1
        assert page.is_preliminary is False
    
    def test_manifest_rejects_trusted_for_rag(self):
        """Manifest rejects trusted_for_rag=true."""
        with pytest.raises(ValidationError):
            ColabPackageManifest(
                schema="TALOS_RECONCILE_PARALLEL_1.0",
                package_id="test",
                created_at="2026-10-31T00:00:00Z",
                status="PROVISIONAL_UNVERIFIED",
                trusted_for_rag=True,
                production_import_authorized=False,
                fidelity_certified=False,
                documents_count=0,
                chunks_count=0,
                tables_baseline=0,
                tables_new=0,
                figures_count=0,
                formulas_count=0,
                pages_with_evidence=0,
                source_pdf_sha256="0" * 64,
            )
    
    def test_manifest_rejects_production_authorized(self):
        """Manifest rejects production_import_authorized=true."""
        with pytest.raises(ValidationError):
            ColabPackageManifest(
                schema="TALOS_RECONCILE_PARALLEL_1.0",
                package_id="test",
                created_at="2026-10-31T00:00:00Z",
                status="PROVISIONAL_UNVERIFIED",
                trusted_for_rag=False,
                production_import_authorized=True,
                fidelity_certified=False,
                documents_count=0,
                chunks_count=0,
                tables_baseline=0,
                tables_new=0,
                figures_count=0,
                formulas_count=0,
                pages_with_evidence=0,
                source_pdf_sha256="0" * 64,
            )
    
    def test_manifest_rejects_fidelity_certified(self):
        """Manifest rejects fidelity_certified=true."""
        with pytest.raises(ValidationError):
            ColabPackageManifest(
                schema="TALOS_RECONCILE_PARALLEL_1.0",
                package_id="test",
                created_at="2026-10-31T00:00:00Z",
                status="PROVISIONAL_UNVERIFIED",
                trusted_for_rag=False,
                production_import_authorized=False,
                fidelity_certified=True,
                documents_count=0,
                chunks_count=0,
                tables_baseline=0,
                tables_new=0,
                figures_count=0,
                formulas_count=0,
                pages_with_evidence=0,
                source_pdf_sha256="0" * 64,
            )


@pytest.fixture
def loaded_store(tmp_path):
    """Create a store with synthetic multimodal data."""
    pkg_dir = make_synthetic_package(tmp_path)
    db_path = tmp_path / "test_retrieval.db"
    
    with MultimodalImporter(db_path) as importer:
        importer.import_package(tmp_path / "synthetic_pkg")
    
    from study_engine.storage.knowledge_store import KnowledgeStore
    store = KnowledgeStore(db_path)
    # Synthetic inspection grant, not a production/source promotion.
    acl = tmp_path / "staging_acl.json"
    acl.write_text(json.dumps({"grants": [{"notebook_id": "multimodal-colab", "source_id": "src-1", "status": "AUTHORIZED"}]}))
    store.l3_manifest_path = str(acl)
    return store


class TestMultimodalRetrieval:
    """Tests for multimodal retrieval (requires database setup)."""
    
    def test_search_finds_table(self, loaded_store):
        """Search should find table content."""
        from study_engine.retrieval.multimodal_retrieval import MultimodalRetriever
        
        retriever = MultimodalRetriever(loaded_store, notebook_id="multimodal-colab")
        hits = retriever.search_multimodal("table", limit=5)
        
        assert len(hits) > 0
        found_table = False
        for hit in hits:
            for elem in hit.multimodal_elements or []:
                if elem.get("type") == "table":
                    found_table = True
        assert found_table
    
    def test_search_finds_figure(self, loaded_store):
        """Search should find figure content."""
        from study_engine.retrieval.multimodal_retrieval import MultimodalRetriever
        
        retriever = MultimodalRetriever(loaded_store, notebook_id="multimodal-colab")
        hits = retriever.search_multimodal("figure", limit=5)
        
        found_figure = False
        for hit in hits:
            for elem in hit.multimodal_elements or []:
                if elem.get("type") == "figure":
                    found_figure = True
        assert found_figure
    
    def test_search_finds_formula(self, loaded_store):
        """Search should find formula content."""
        from study_engine.retrieval.multimodal_retrieval import MultimodalRetriever
        
        retriever = MultimodalRetriever(loaded_store, notebook_id="multimodal-colab")
        hits = retriever.search_multimodal("formula", limit=5)
        
        found_formula = False
        for hit in hits:
            for elem in hit.multimodal_elements or []:
                if elem.get("type") == "formula":
                    found_formula = True
        assert found_formula
    
    def test_page_context(self, loaded_store):
        """Page context retrieval works."""
        from study_engine.retrieval.multimodal_retrieval import MultimodalRetriever
        
        retriever = MultimodalRetriever(loaded_store, notebook_id="multimodal-colab")
        ctx = retriever.get_page_context(1)
        
        assert ctx is not None
        assert ctx["page_evidence"] is not None
        assert ctx["page_evidence"].page_number == 1
        assert len(ctx["chunks"]) > 0
        assert len(ctx["tables"]) > 0
        assert len(ctx["figures"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
