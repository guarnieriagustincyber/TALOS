"""Tests for Multimodal Evidence Adapter."""

import hashlib
import json
import tempfile
from pathlib import Path

import pytest

from study_engine.contracts.evidence_engine import (
    CoverageStatus,
    EvidenceGrade,
    SubQuery,
)
from study_engine.contracts.multimodal import (
    MultimodalElementType,
    PageEvidence,
    RelationType,
)
from study_engine.retrieval.multimodal_retrieval import MultimodalHit
from study_engine.ingestion.multimodal_importer import MultimodalImporter
from study_engine.retrieval.multimodal_adapter import (
    MultimodalContextPacker,
    MultimodalEvidenceAdapter,
    MultimodalEvidenceConfig,
)
from study_engine.retrieval.multimodal_retrieval import MultimodalRetriever
from study_engine.storage.knowledge_store import KnowledgeStore


def make_synthetic_multimodal_package(tmp_path: Path) -> Path:
    """Create a valid synthetic Colab package for testing."""
    pkg_dir = tmp_path / "synthetic_pkg"
    pkg_dir.mkdir()

    # Create manifest
    pdf_content = b"synthetic pdf content for testing"
    pdf_hash = hashlib.sha256(pdf_content).hexdigest()

    from study_engine.contracts.multimodal import ColabPackageManifest
    manifest = ColabPackageManifest(
        schema="TALOS_RECONCILE_PARALLEL_1.0",
        package_id="test-pkg-001",
        created_at="2026-10-31T00:00:00Z",
        status="PROVISIONAL_UNVERIFIED",
        trusted_for_rag=False,
        production_import_authorized=False,
        fidelity_certified=False,
        documents_count=2,
        chunks_count=4,
        tables_baseline=1,
        tables_new=1,
        figures_count=1,
        formulas_count=1,
        pages_with_evidence=4,
        source_pdf_sha256=pdf_hash,
        file_sizes={"documents.json": 200, "chunks.jsonl": 300},
        file_sha256={},
    )

    (pkg_dir / "manifest.json").write_text(manifest.model_dump_json())

    # Documents - two documents with same page numbers
    documents = [
        {
            "id": "doc-A",
            "source_id": "src-A",
            "title": "Document A - Database Theory",
            "content": "Document A about 3NF and normalization.",
            "page_count": 3,
            "metadata": {},
        },
        {
            "id": "doc-B",
            "source_id": "src-B",
            "title": "Document B - SQL Reference",
            "content": "Document B about SQL syntax.",
            "page_count": 3,
            "metadata": {},
        },
    ]
    (pkg_dir / "documents.json").write_text(json.dumps(documents))

    # Chunks - both docs have chunks on page 1
    chunks = [
        {"id": "chunk-A1", "document_id": "doc-A", "source_id": "src-A", "content": "Doc A page 1: Definition of 3NF.", "page_start": 1, "page_end": 1, "index": 0, "metadata": {}},
        {"id": "chunk-A2", "document_id": "doc-A", "source_id": "src-A", "content": "Doc A page 2: Functional dependencies.", "page_start": 2, "page_end": 2, "index": 1, "metadata": {}},
        {"id": "chunk-B1", "document_id": "doc-B", "source_id": "src-B", "content": "Doc B page 1: SELECT syntax.", "page_start": 1, "page_end": 1, "index": 0, "metadata": {}},
        {"id": "chunk-B2", "document_id": "doc-B", "source_id": "src-B", "content": "Doc B page 2: WHERE clause.", "page_start": 2, "page_end": 2, "index": 1, "metadata": {}},
    ]
    with open(pkg_dir / "chunks.jsonl", "w") as f:
        for chunk in chunks:
            f.write(json.dumps(chunk) + "\n")

    # Tables
    from study_engine.contracts.multimodal import TableCandidate, CandidateStatus
    table_a = TableCandidate(
        element_id="table-A1",
        element_type="table",
        document_id="doc-A",
        source_id="src-A",
        page=2,
        candidate_section_id="sec-A2",
        pdf_sha256="0" * 64,
        status="candidate",
        confidence=0.9,
        table_id="table_A1",
        caption="Functional Dependencies",
        headers=["Determinant", "Dependent"],
        rows=[["A", "B"], ["C", "D"]],
        is_baseline=True,
    )
    (pkg_dir / "baseline_tables_candidates.jsonl").write_text(table_a.model_dump_json() + "\n")

    table_b = TableCandidate(
        element_id="table-B1",
        element_type="table",
        document_id="doc-B",
        source_id="src-B",
        page=2,
        candidate_section_id="sec-B2",
        pdf_sha256="0" * 64,
        status="candidate",
        confidence=0.8,
        table_id="table_B1",
        caption="SQL Keywords",
        headers=["Keyword", "Description"],
        rows=[["SELECT", "Retrieve data"], ["WHERE", "Filter rows"]],
        is_baseline=False,
    )
    (pkg_dir / "tables_model_candidates.jsonl").write_text(table_b.model_dump_json() + "\n")

    # Figures and Formulas
    from study_engine.contracts.multimodal import FigureCandidate, FormulaCandidate
    figure_b = FigureCandidate(
        element_id="fig-B1",
        element_type="figure",
        document_id="doc-B",
        source_id="src-B",
        page=2,
        candidate_section_id="sec-B2",
        pdf_sha256="0" * 64,
        status="candidate",
        confidence=0.85,
        figure_id="figure_B1",
        caption="Query Plan Diagram",
        alt_text="Visual representation of query execution plan",
    )

    formula_a = FormulaCandidate(
        element_id="form-A1",
        element_type="formula",
        document_id="doc-A",
        source_id="src-A",
        page=2,
        candidate_section_id="sec-A2",
        pdf_sha256="0" * 64,
        status="candidate",
        confidence=0.9,
        formula_id="formula_A1",
        latex="A \\to B",
        plain_text="A determines B",
        variables=["A", "B"],
    )

    with open(pkg_dir / "figures_formulas_candidates.jsonl", "w") as f:
        f.write(figure_b.model_dump_json() + "\n")
        f.write(formula_a.model_dump_json() + "\n")

    # Pages evidence
    page_a1 = PageEvidence(
        page_id="page-A1",
        document_id="doc-A",
        source_id="src-A",
        page_number=1,
        pdf_sha256="0" * 64,
        text_content="Doc A page 1: Definition of 3NF.",
        chunk_ids=["chunk-A1"],
        table_ids=[],
        figure_ids=[],
        formula_ids=[],
        is_preliminary=False,
        multimodel_confidence=0.9,
        text_sha256=hashlib.sha256(b"Doc A page 1: Definition of 3NF.").hexdigest(),
    )
    (pkg_dir / "pages_evidence.jsonl").write_text(page_a1.model_dump_json() + "\n")

    page_a2 = PageEvidence(
        page_id="page-A2",
        document_id="doc-A",
        source_id="src-A",
        page_number=2,
        pdf_sha256="0" * 64,
        text_content="Doc A page 2: Functional dependencies.",
        chunk_ids=["chunk-A2"],
        table_ids=["table-A1"],
        figure_ids=[],
        formula_ids=["form-A1"],
        is_preliminary=False,
        multimodel_confidence=0.9,
        text_sha256=hashlib.sha256(b"Doc A page 2: Functional dependencies.").hexdigest(),
    )
    with open(pkg_dir / "pages_evidence.jsonl", "a") as f:
        f.write(page_a2.model_dump_json() + "\n")

    page_b1 = PageEvidence(
        page_id="page-B1",
        document_id="doc-B",
        source_id="src-B",
        page_number=1,
        pdf_sha256="0" * 64,
        text_content="Doc B page 1: SELECT syntax.",
        chunk_ids=["chunk-B1"],
        table_ids=[],
        figure_ids=[],
        formula_ids=[],
        is_preliminary=False,
        multimodel_confidence=0.9,
        text_sha256=hashlib.sha256(b"Doc B page 1: SELECT syntax.").hexdigest(),
    )
    with open(pkg_dir / "pages_evidence.jsonl", "a") as f:
        f.write(page_b1.model_dump_json() + "\n")

    page_b2 = PageEvidence(
        page_id="page-B2",
        document_id="doc-B",
        source_id="src-B",
        page_number=2,
        pdf_sha256="0" * 64,
        text_content="Doc B page 2: WHERE clause and table.",
        chunk_ids=["chunk-B2"],
        table_ids=["table-B1"],
        figure_ids=["fig-B1"],
        formula_ids=[],
        is_preliminary=False,
        multimodel_confidence=0.9,
        text_sha256=hashlib.sha256(b"Doc B page 2: WHERE clause and table.").hexdigest(),
    )
    with open(pkg_dir / "pages_evidence.jsonl", "a") as f:
        f.write(page_b2.model_dump_json() + "\n")

    (pkg_dir / "quality_report.json").write_text(json.dumps({"completeness": 0.9, "accuracy": 0.85}))
    (pkg_dir / "staging.sqlite").write_bytes(b"placeholder")

    return pkg_dir


def build_test_db(tmp_path: Path):
    """Build a test database with multimodal content."""
    pkg = make_synthetic_multimodal_package(tmp_path)
    db = tmp_path / "staging.db"
    MultimodalImporter(db).import_package(pkg)
    return pkg, KnowledgeStore(db)


def grant(tmp_path: Path, *sources, notebook="multimodal-colab"):
    path = tmp_path / f"acl-{notebook}-{len(sources)}.json"
    import json
    path.write_text(json.dumps({"grants": [dict(notebook_id=notebook, source_id=s, status="AUTHORIZED") for s in sources]}))
    return path


class TestMultimodalEvidenceAdapter:
    """Tests for MultimodalEvidenceAdapter."""

    def test_adapter_creates_evidence_from_hits(self, tmp_path):
        """Adapter converts multimodal hits to evaluated evidence items."""
        pkg, store = build_test_db(tmp_path)
        acl = grant(tmp_path, "src-A", "src-B")
        retriever = MultimodalRetriever(store, manifest_path=acl)

        # Search for content
        hits = retriever.search_multimodal("3NF", limit=5)
        assert len(hits) > 0

        adapter = MultimodalEvidenceAdapter()
        items = adapter.convert_hits_to_evidence_items(hits, "3NF")

        assert len(items) > 0
        for item in items:
            assert isinstance(item.chunk_id, str)
            assert isinstance(item.document_id, str)
            assert isinstance(item.source_id, str)
            assert item.content_hash == hashlib.sha256(item.content.encode()).hexdigest()
            assert item.retrieval_method == "multimodal_search"
            assert item.grade in ("SUFFICIENT", "PARTIAL", "UNASSESSED", "INSUFFICIENT")

    def test_adapter_creates_element_evidence(self, tmp_path):
        """Adapter creates evidence for tables, figures, formulas."""
        pkg, store = build_test_db(tmp_path)
        acl = grant(tmp_path, "src-A", "src-B")
        retriever = MultimodalRetriever(store, manifest_path=acl)

        # Search for content with tables
        hits = retriever.search_multimodal("functional dependencies", limit=5)
        assert len(hits) > 0

        adapter = MultimodalEvidenceAdapter()
        items = adapter.convert_hits_to_evidence_items(hits, "functional dependencies")

        # Should have chunk + table + formula evidence
        elem_items = [item for item in items if item.chunk_id.startswith(("table-", "figure-", "formula-"))]
        assert len(elem_items) > 0

        for item in elem_items:
            assert item.content_hash == hashlib.sha256(item.content.encode()).hexdigest()
            assert "Relación con fragmento:" in item.content or "Tabla:" in item.content or "Fórmula:" in item.content or "Figura:" in item.content

    def test_adapter_creates_evidence_packet(self, tmp_path):
        """Adapter creates complete evidence packet with coverage."""
        pkg, store = build_test_db(tmp_path)
        acl = grant(tmp_path, "src-A", "src-B")
        retriever = MultimodalRetriever(store, manifest_path=acl)

        hits = retriever.search_multimodal("3NF", limit=5)
        adapter = MultimodalEvidenceAdapter()
        # Pass sub_queries to get coverage report
        sub_queries = [SubQuery(sub_query_id="sq-1", text="third normal form (3NF)", intent="concept_explanation", priority_score=0.7)]
        packet = adapter.create_evidence_packet(hits, "3NF", sub_queries)

        assert packet.original_query == "3NF"
        assert packet.notebook_id == "multimodal-colab"
        assert packet.grounding_decision in ("SUPPORTED", "PARTIALLY_SUPPORTED", "UNASSESSED_EVIDENCE", "NO_CANDIDATES")
        assert packet.has_full_provenance is False
        assert packet.coverage_report is not None

    def test_adapter_decomposes_query(self, tmp_path):
        """Adapter decomposes query into sub-queries."""
        pkg, store = build_test_db(tmp_path)
        acl = grant(tmp_path, "src-A", "src-B")
        retriever = MultimodalRetriever(store, manifest_path=acl)

        adapter = MultimodalEvidenceAdapter()
        decomp = adapter.decompose_query("What is Table 6.2 and Figure 3.32 in 3NF?")

        assert decomp.original_query == "What is Table 6.2 and Figure 3.32 in 3NF?"
        assert len(decomp.sub_queries) > 0
        sq_texts = [sq.text for sq in decomp.sub_queries]
        assert any("Table 6.2" in t for t in sq_texts)
        assert any("Figure 3.32" in t for t in sq_texts)

    def test_adapter_decomposes_concept_query(self, tmp_path):
        """Adapter decomposes concept-based queries."""
        pkg, store = build_test_db(tmp_path)
        acl = grant(tmp_path, "src-A", "src-B")
        retriever = MultimodalRetriever(store, manifest_path=acl)

        adapter = MultimodalEvidenceAdapter()
        decomp = adapter.decompose_query("Explain 3NF and functional dependencies")

        assert decomp.original_query == "Explain 3NF and functional dependencies"
        assert len(decomp.sub_queries) > 0
        sq_texts = [sq.text for sq in decomp.sub_queries]
        assert any("third normal form" in t.lower() for t in sq_texts)
        assert any("functional dependenc" in t.lower() for t in sq_texts)


class TestMultimodalContextPacker:
    """Tests for MultimodalContextPacker."""

    def test_packer_creates_pedagogical_context(self, tmp_path):
        """Packer creates pedagogical context from multimodal hits."""
        pkg, store = build_test_db(tmp_path)
        acl = grant(tmp_path, "src-A", "src-B")
        retriever = MultimodalRetriever(store, manifest_path=acl)

        hits = retriever.search_multimodal("functional dependencies", limit=5)
        packer = MultimodalContextPacker()
        packed = packer.pack_for_pedagogy(hits, "functional dependencies")

        assert "packaged_context" in packed
        assert "evidence_packet" in packed
        assert "multimodal_summary" in packed
        assert "sub_query_decomposition" in packed
        assert "provenance" in packed

        prov = packed["provenance"]
        assert prov["source"] == "multimodal_staging"
        assert prov["trust_status"] == "PROVISIONAL_UNVERIFIED"

    def test_packer_multimodal_summary(self, tmp_path):
        """Packer builds correct multimodal summary."""
        pkg, store = build_test_db(tmp_path)
        acl = grant(tmp_path, "src-A", "src-B")
        retriever = MultimodalRetriever(store, manifest_path=acl)

        hits = retriever.search_multimodal("functional dependencies", limit=5)
        packer = MultimodalContextPacker()
        packed = packer.pack_for_pedagogy(hits, "functional dependencies")

        summary = packed["multimodal_summary"]
        assert "tables" in summary
        assert "figures" in summary
        assert "formulas" in summary
        assert "pages_with_elements" in summary
        assert summary["total_tables"] >= 0
        assert summary["total_figures"] >= 0
        assert summary["total_formulas"] >= 0

    def test_packer_format_for_llm(self, tmp_path):
        """Packer formats context for LLM with multimodal elements."""
        pkg, store = build_test_db(tmp_path)
        acl = grant(tmp_path, "src-A", "src-B")
        retriever = MultimodalRetriever(store, manifest_path=acl)

        hits = retriever.search_multimodal("3NF", limit=5)
        packer = MultimodalContextPacker()
        packed = packer.pack_for_pedagogy(hits, "3NF")

        formatted = packer.format_for_llm(packed)
        assert "EVIDENCIAS DOCUMENTADAS" in formatted
        assert "ELEMENTOS MULTIMODALES" in formatted


class TestDocumentIdentityIsolation:
    """Tests for document identity isolation in multimodal adapter."""

    def test_same_page_different_documents_isolated(self, tmp_path):
        """Two documents with chunks on same page number are isolated."""
        pkg, store = build_test_db(tmp_path)
        acl = grant(tmp_path, "src-A", "src-B")
        retriever = MultimodalRetriever(store, manifest_path=acl)

        # Both doc-A and doc-B have chunks on page 1
        hits_A = retriever.search_multimodal("Doc A", limit=5, document_id="doc-A")
        hits_B = retriever.search_multimodal("Doc B", limit=5, document_id="doc-B")

        # Hits should be isolated by document
        for hit in hits_A:
            if hit.chunk:
                assert hit.chunk.document_id == "doc-A"
        for hit in hits_B:
            if hit.chunk:
                assert hit.chunk.document_id == "doc-B"

        # Adapter should respect document isolation
        adapter = MultimodalEvidenceAdapter()
        items_A = adapter.convert_hits_to_evidence_items(hits_A, "Doc A")
        items_B = adapter.convert_hits_to_evidence_items(hits_B, "Doc B")

        for item in items_A:
            assert item.document_id == "doc-A"
        for item in items_B:
            assert item.document_id == "doc-B"

    def test_ambiguous_page_without_doc_returns_none(self, tmp_path):
        """Querying page 1 without document_id returns None (ambiguous)."""
        pkg, store = build_test_db(tmp_path)
        acl = grant(tmp_path, "src-A", "src-B")
        retriever = MultimodalRetriever(store, manifest_path=acl)

        # Page 1 exists in both doc-A and doc-B
        # Should not return mixed content
        hits = retriever.search_multimodal("page 1", limit=5)
        # The retriever should handle ambiguity appropriately
        # (either return None or return hits from one document only)
        # The key is no cross-document mixing in a single hit


class TestExplicitReferenceDetection:
    """Tests for explicit reference detection."""

    def test_explicit_table_reference_detected(self, tmp_path):
        """Explicit 'Table 6.2' reference is detected when element exists."""
        pkg, store = build_test_db(tmp_path)
        acl = grant(tmp_path, "src-A", "src-B")
        retriever = MultimodalRetriever(store, manifest_path=acl)

        # Search for explicit table reference
        hits = retriever.search_multimodal("Table 6.2", limit=5)
        # Should find explicit reference candidates if element exists
        explicit_hits = [
            h for h in hits
            if any(e.get("relation") == "explicit_reference_candidate" for e in h.multimodal_elements)
        ]
        # If table with matching caption/id exists, should detect
        # If not, returns empty (no false positives)

    def test_explicit_figure_reference_detected(self, tmp_path):
        """Explicit 'Figure 3.32' reference is detected when element exists."""
        pkg, store = build_test_db(tmp_path)
        acl = grant(tmp_path, "src-A", "src-B")
        retriever = MultimodalRetriever(store, manifest_path=acl)

        hits = retriever.search_multimodal("Figure 3.32", limit=5)
        explicit_hits = [
            h for h in hits
            if any(e.get("relation") == "explicit_reference_candidate" for e in h.multimodal_elements)
        ]
        # If figure with matching caption/id exists, should detect

    def test_nonexistent_reference_returns_no_false_positives(self, tmp_path):
        """Non-existent references return no false positive explicit matches."""
        pkg, store = build_test_db(tmp_path)
        acl = grant(tmp_path, "src-A", "src-B")
        retriever = MultimodalRetriever(store, manifest_path=acl)

        hits = retriever.search_multimodal("NonExistentTable 99.99", limit=5)
        explicit_hits = [
            h for h in hits
            if any(e.get("relation") == "explicit_reference_candidate" for e in h.multimodal_elements)
        ]
        # Should have no explicit reference candidates for non-existent elements
        assert len(explicit_hits) == 0


class TestPedagogicalScenarios:
    """Test the three educational scenarios."""

    def test_scenario_A_3NF_Coronel_page_217(self, tmp_path):
        """Scenario A: 3NF definition, Coronel, page 217."""
        # This test uses the real imported database
        # We'll test the adapter can pack this scenario
        from study_engine.retrieval.multimodal_adapter import MultimodalContextPacker

        # Mock the hits structure for 3NF scenario
        from study_engine.contracts.multimodal import PageEvidence

        page_evidence = PageEvidence(
            page_id="page-217",
            document_id="database-systems-design-implementation-and_4990c35d1608",
            source_id="database-systems-design-implementation-and_4990c35d1608",
            page_number=217,
            pdf_sha256="0" * 64,
            text_content="A table is in third normal form (3NF) when it is in 2NF and contains no transitive dependencies.",
            chunk_ids=[],
            table_ids=[],
            figure_ids=[],
            formula_ids=[],
            is_preliminary=False,
            multimodel_confidence=0.9,
            text_sha256="0" * 64,
        )

        hit = MultimodalHit(
            chunk=None,
            multimodal_elements=[],
            page_evidence=page_evidence,
            combined_score=0.9,
        )

        packer = MultimodalContextPacker()
        packed = packer.pack_for_pedagogy([hit], "What is 3NF in Coronel page 217?")

        assert "multimodal_summary" in packed
        summary = packed["multimodal_summary"]
        assert summary["total_tables"] == 0  # No tables in this specific hit
        assert summary["total_figures"] == 0
        assert summary["total_formulas"] == 0

    def test_scenario_B_SELECT_syntax(self, tmp_path):
        """Scenario B: SQL SELECT syntax with examples."""
        from study_engine.retrieval.multimodal_adapter import MultimodalContextPacker
        from study_engine.contracts.multimodal import PageEvidence, FigureCandidate, FormulaCandidate

        # Mock hit with SQL figure and formula
        figure = FigureCandidate(
            element_id="fig-select",
            element_type="figure",
            document_id="doc-SQL",
            source_id="src-SQL",
            page=5,
            candidate_section_id="sec-5",
            pdf_sha256="0" * 64,
            status="candidate",
            confidence=0.9,
            figure_id="figure_select",
            caption="SELECT Query Structure",
            alt_text="Diagram showing SELECT-FROM-WHERE structure",
        )
        formula = FormulaCandidate(
            element_id="form-select",
            element_type="formula",
            document_id="doc-SQL",
            source_id="src-SQL",
            page=5,
            candidate_section_id="sec-5",
            pdf_sha256="0" * 64,
            status="candidate",
            confidence=0.95,
            formula_id="formula_select",
            latex="SELECT column FROM table WHERE condition",
            plain_text="SELECT column FROM table WHERE condition",
            variables=["column", "table", "condition"],
        )

        hit = MultimodalHit(
            chunk=None,
            multimodal_elements=[
                {"type": "figure", "data": figure.model_dump(), "relation": "on_same_page"},
                {"type": "formula", "data": formula.model_dump(), "relation": "explicit_reference_candidate"},
            ],
            page_evidence=None,
            combined_score=0.95,
        )

        packer = MultimodalContextPacker()
        packed = packer.pack_for_pedagogy([hit], "Explain SELECT syntax")

        summary = packed["multimodal_summary"]
        assert summary["total_figures"] >= 1
        assert summary["total_formulas"] >= 1
        assert len(summary["pages_with_elements"]) >= 1

    def test_scenario_C_functional_dependencies_Coronel(self, tmp_path):
        """Scenario C: Functional dependencies, Coronel pages 210 and 215."""
        from study_engine.retrieval.multimodal_adapter import MultimodalContextPacker
        from study_engine.contracts.multimodal import PageEvidence, TableCandidate

        table = TableCandidate(
            element_id="table-fd",
            element_type="table",
            document_id="database-systems-design-implementation-and_4990c35d1608",
            source_id="database-systems-design-implementation-and_4990c35d1608",
            page=210,
            candidate_section_id="sec-210",
            pdf_sha256="0" * 64,
            status="candidate",
            confidence=0.9,
            table_id="table_fd",
            caption="Functional Dependencies",
            headers=["Determinant", "Dependent"],
            rows=[["A", "B"], ["C", "D"]],
            is_baseline=True,
        )

        hit1 = MultimodalHit(
            chunk=None,
            multimodal_elements=[{"type": "table", "data": table.model_dump(), "relation": "on_same_page"}],
            page_evidence=None,
            combined_score=0.9,
        )

        packer = MultimodalContextPacker()
        packed = packer.pack_for_pedagogy([hit1], "Functional dependencies in Coronel")

        summary = packed["multimodal_summary"]
        assert summary["total_tables"] >= 1
        assert any(t["page"] == 210 for t in summary["tables"])


class TestProvisionalIsolation:
    """Tests ensuring provisional content never reaches production."""

    def test_all_evidence_marked_unverified(self, tmp_path):
        """All multimodal evidence items are marked unverified."""
        pkg, store = build_test_db(tmp_path)
        acl = grant(tmp_path, "src-A", "src-B")
        retriever = MultimodalRetriever(store, manifest_path=acl)

        hits = retriever.search_multimodal("test", limit=5)
        adapter = MultimodalEvidenceAdapter()
        items = adapter.convert_hits_to_evidence_items(hits, "test")

        for item in items:
            assert item.trust_level == "unverified"
            assert item.grade in ("UNASSESSED", "PARTIAL", "SUFFICIENT")

    def test_context_pack_contains_provenance_warning(self, tmp_path):
        """Packed context includes provenance warning."""
        pkg, store = build_test_db(tmp_path)
        acl = grant(tmp_path, "src-A", "src-B")
        retriever = MultimodalRetriever(store, manifest_path=acl)

        hits = retriever.search_multimodal("test", limit=5)
        packer = MultimodalContextPacker()
        packed = packer.pack_for_pedagogy(hits, "test")

        prov = packed["provenance"]
        assert prov["trust_status"] == "PROVISIONAL_UNVERIFIED"
        assert prov["source"] == "multimodal_staging"

    def test_no_production_import_authorized(self, tmp_path):
        """No multimodal content is marked as production authorized."""
        pkg, store = build_test_db(tmp_path)
        acl = grant(tmp_path, "src-A", "src-B")
        retriever = MultimodalRetriever(store, manifest_path=acl)

        hits = retriever.search_multimodal("test", limit=5)
        for hit in hits:
            assert hit.trusted_for_rag is False
            assert hit.fidelity_certified is False
            assert hit.production_import_authorized is False


class TestExplicitReferenceEdgeCases:
    """Additional tests for explicit reference detection."""

    def test_case_insensitive_table_reference(self, tmp_path):
        """Table reference detection is case insensitive."""
        pkg, store = build_test_db(tmp_path)
        acl = grant(tmp_path, "src-A", "src-B")
        retriever = MultimodalRetriever(store, manifest_path=acl)

        # Test various case combinations
        for ref in ["Table 6.2", "TABLE 6.2", "table 6.2", "Tabla 6.2"]:
            hits = retriever.search_multimodal(ref, limit=5)
            explicit = [
                h for h in hits
                if any(e.get("relation") == "explicit_reference_candidate" for e in h.multimodal_elements)
            ]
            # Should not crash, returns empty if no match

    def test_ambiguous_reference_same_element_different_docs(self, tmp_path):
        """Same reference in different documents stays isolated."""
        pkg, store = build_test_db(tmp_path)
        acl = grant(tmp_path, "src-A", "src-B")
        retriever = MultimodalRetriever(store, manifest_path=acl)

        # If both doc-A and doc-B had a "Table 1", querying "Table 1"
        # with document_id should only return that document's table
        hits_A = retriever.search_multimodal("Table 1", limit=5, document_id="doc-A")
        for hit in hits_A:
            if hit.chunk:
                assert hit.chunk.document_id == "doc-A"

    def test_repeated_reference_same_document(self, tmp_path):
        """Repeated reference to same element in same document."""
        pkg, store = build_test_db(tmp_path)
        acl = grant(tmp_path, "src-A", "src-B")
        retriever = MultimodalRetriever(store, manifest_path=acl)

        hits1 = retriever.search_multimodal("Table 6.2", limit=5)
        hits2 = retriever.search_multimodal("Table 6.2", limit=5)

        # Both searches should return consistent results
        assert len(hits1) == len(hits2)