"""Synthetic staging boundary tests; no providers, production DBs or student state.

Oracle: exported UTF-8 bytes/hashes, exact document+PDF page, L3 intersection,
and unchanged destination after errors. Does not certify academic fidelity.
"""
import hashlib
import json
import sqlite3

import pytest

from study_engine.contracts.multimodal import TRUST, TableCandidate
from study_engine.contracts.notebook import Notebook
from study_engine.ingestion.multimodal_importer import MultimodalImporter, MultimodalValidationError
from study_engine.retrieval.multimodal_retrieval import MultimodalRetriever
from study_engine.storage.knowledge_store import KnowledgeStore
from tests.unit.ingestion.test_multimodal_importer import make_synthetic_package


def rewrite(path, change):
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    change(rows)
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n")


def grant(tmp_path, *sources, notebook="multimodal-colab"):
    path = tmp_path / f"acl-{notebook}-{len(sources)}.json"
    path.write_text(json.dumps({"grants": [dict(notebook_id=notebook, source_id=s, status="AUTHORIZED") for s in sources]}))
    return path


def build(tmp_path):
    pkg = make_synthetic_package(tmp_path)
    db = tmp_path / "staging.db"
    MultimodalImporter(db).import_package(pkg)
    return pkg, KnowledgeStore(db)


def test_original_bytes_hashes_and_separate_candidate_index(tmp_path):
    pkg = make_synthetic_package(tmp_path)
    text = "SQL\r\nSELECT café, 'α';  \n"
    digest = hashlib.sha256(text.encode()).hexdigest()
    def edit(rows):
        rows[0]["content"] = text
        rows[0]["text_sha256"] = digest
    rewrite(pkg / "chunks.jsonl", edit)
    db = tmp_path / "staging.db"
    MultimodalImporter(db).import_package(pkg)
    store = KnowledgeStore(db)
    chunk = store.get_chunk("chunk-1")
    assert chunk.content.encode() == text.encode()
    assert chunk.metadata["text_sha256"] == digest
    assert hashlib.sha256(chunk.content.encode()).hexdigest() == digest
    with store.engine.transaction() as conn:
        assert conn.execute("SELECT count(*) FROM chunks").fetchone()[0] == 2
        assert conn.execute("SELECT count(*) FROM mm_elements").fetchone()[0] == 4
    assert store.fts_search("table_1", notebook_id="multimodal-colab") == []
    retriever = MultimodalRetriever(store, manifest_path=grant(tmp_path, "src-1"))
    assert retriever.search_multimodal("table_1")[0].multimodal_elements[0]["type"] == "table"


@pytest.mark.parametrize("field", list(TRUST))
@pytest.mark.parametrize("file", ["manifest.json", "chunks.jsonl", "figures_formulas_candidates.jsonl"])
def test_reject_export_trust_escalation_without_partial_state(tmp_path, field, file):
    pkg = make_synthetic_package(tmp_path)
    rewrite(pkg / file, lambda rows: rows[0].update({field: True}))
    target = tmp_path / "blocked.db"
    with pytest.raises(ValueError, match=field):
        MultimodalImporter(target).import_package(pkg)
    assert not target.exists()


@pytest.mark.parametrize("change", [
    {"doc_id": "another-book"}, {"pdf_page": 2},
    {"metadata": {"source_id": "another-source"}},
    {"metadata": {"trusted_for_rag": True}}, {"surprise_security_override": True},
])
def test_conflicting_aliases_metadata_and_unknown_fields_rejected(tmp_path, change):
    pkg = make_synthetic_package(tmp_path)
    rewrite(pkg / "baseline_tables_candidates.jsonl", lambda rows: rows[0].update(change))
    target = tmp_path / "blocked.db"
    with pytest.raises(ValueError):
        MultimodalImporter(target).import_package(pkg)
    assert not target.exists()


def test_contract_does_not_accept_extra_security_or_missing_identity():
    with pytest.raises(ValueError):
        TableCandidate(element_id="x", table_id="x", doc_id="a", trusted_for_rag=True)


def test_direct_page_acl_document_scope_and_missing_manifest(tmp_path):
    _, store = build(tmp_path)
    allowed = grant(tmp_path, "src-1")
    retriever = MultimodalRetriever(store, manifest_path=allowed)
    assert retriever.get_page_context(1, document_id="doc-1")["page_evidence"].document_id == "doc-1"
    for other in (
        MultimodalRetriever(store),
        MultimodalRetriever(store, manifest_path=tmp_path / "absent.json"),
        MultimodalRetriever(store, manifest_path=allowed, source_ids=[]),
        MultimodalRetriever(store, manifest_path=allowed, source_ids=["denied"]),
        MultimodalRetriever(store, manifest_path=allowed, document_id="other-doc"),
        MultimodalRetriever(store, notebook_id="other-notebook", manifest_path=allowed),
    ):
        assert other.search_multimodal("table") == []
        assert other.get_page_context(1) is None
        assert other._find_elements_on_page(1) == []
    # Relational membership alone is insufficient, as is an L3 grant alone.
    store.create_notebook(Notebook(id="linked", name="linked"))
    with store.engine.transaction() as conn:
        conn.execute("INSERT INTO notebook_sources VALUES ('linked', 'src-1')")
    assert MultimodalRetriever(store, "linked", manifest_path=allowed).get_page_context(1) is None
    assert MultimodalRetriever(store, "unlinked", manifest_path=grant(tmp_path, "src-1", notebook="unlinked")).get_page_context(1) is None


def test_page_identity_ambiguity_no_cross_book_expansion(tmp_path):
    pkg = make_synthetic_package(tmp_path)
    docs = json.loads((pkg / "documents.json").read_text())
    docs.append(dict(docs[0], id="doc-2", source_id="src-2"))
    (pkg / "documents.json").write_text(json.dumps(docs))
    rewrite(pkg / "chunks.jsonl", lambda rows: rows.append(dict(rows[0], id="denied-chunk", document_id="doc-2", source_id="src-2", content="deniedsecret", index=0)))
    rewrite(pkg / "baseline_tables_candidates.jsonl", lambda rows: rows.append(dict(rows[0], element_id="denied-table", table_id="denied-table", document_id="doc-2", source_id="src-2", caption="deniedsecret")))
    rewrite(pkg / "pages_evidence.jsonl", lambda rows: rows.append(dict(rows[0], page_id=None, document_id="doc-2", source_id="src-2", chunk_ids=[], table_ids=[], figure_ids=[])))
    rewrite(pkg / "manifest.json", lambda rows: rows[0].update(documents_count=2, pages_with_evidence=2, chunks_count=3, tables_baseline=2))
    db = tmp_path / "staging.db"
    MultimodalImporter(db).import_package(pkg)
    store = KnowledgeStore(db)
    r = MultimodalRetriever(store, manifest_path=grant(tmp_path, "src-1", "src-2"))
    assert r.get_page_context(1) is None
    assert r.get_page_context(1, document_id="doc-2")["tables"][0]["element_id"] == "denied-table"
    assert len(r.get_page_context(1, document_id="doc-1")["tables"]) == 1
    assert r.search_multimodal("deniedsecret")
    assert r._find_elements_on_page(1) == []
    denied = MultimodalRetriever(store, manifest_path=grant(tmp_path, "src-1"))
    assert denied.get_page_context(1, document_id="doc-2") is None
    assert denied._find_elements_on_page(1, document_id="doc-2") == []
    assert denied.search_multimodal("deniedsecret") == []
    assert all(e["document_id"] == "doc-1" for e in denied._find_elements_on_page(1))


def test_chunk_with_all_modalities_correct_page_and_missing_assets(tmp_path):
    pkg = make_synthetic_package(tmp_path)
    rewrite(pkg / "figures_formulas_candidates.jsonl", lambda rows: rows[1].update(page=1))
    rewrite(pkg / "pages_evidence.jsonl", lambda rows: rows[0].update(formula_ids=["form-1"]))
    rewrite(pkg / "baseline_tables_candidates.jsonl", lambda rows: rows[0]["metadata"].update(asset_path="assets/missing.png"))
    db = tmp_path / "staging.db"
    MultimodalImporter(db).import_package(pkg)
    r = MultimodalRetriever(KnowledgeStore(db), manifest_path=grant(tmp_path, "src-1"))
    hits = r.search_multimodal("test document")
    hit = next(h for h in hits if h.chunk and h.chunk.chunk_id == "chunk-1")
    assert {e["type"] for e in hit.multimodal_elements} == {"table", "figure", "formula"}
    assert all(e["relation"] == "on_same_page" for e in hit.multimodal_elements)
    assert hit.page_evidence.document_id == "doc-1" and hit.page_evidence.page_number == 1
    assert all(e["data"]["page"] == 1 for e in hit.multimodal_elements)
    assert all(e["data"]["metadata"]["asset_status"] == "MISSING" for e in hit.multimodal_elements)
    assert all(all(e["data"][k] is False for k in TRUST) for e in hit.multimodal_elements)


def test_bad_hash_and_wrong_page_reference_leave_no_database(tmp_path):
    pkg = make_synthetic_package(tmp_path)
    rewrite(pkg / "chunks.jsonl", lambda rows: rows[0].update(text_sha256="f" * 64))
    target = tmp_path / "blocked.db"
    with pytest.raises(ValueError, match="text_sha256"):
        MultimodalImporter(target).import_package(pkg)
    assert not target.exists()
    rewrite(pkg / "chunks.jsonl", lambda rows: rows[0].pop("text_sha256"))
    rewrite(pkg / "pages_evidence.jsonl", lambda rows: rows[0].update(table_ids=["table-m1"]))
    with pytest.raises(ValueError, match="Cross-page table reference"):
        MultimodalImporter(target).import_package(pkg)
    assert not target.exists()


def test_write_failure_is_atomic_and_existing_nonstaging_is_untouched(tmp_path, monkeypatch):
    pkg = make_synthetic_package(tmp_path)
    target = tmp_path / "blocked.db"
    original = MultimodalImporter._build
    def fail_after_writes(self, *args):
        original(self, *args)
        raise RuntimeError("injected disk failure")
    monkeypatch.setattr(MultimodalImporter, "_build", fail_after_writes)
    with pytest.raises(RuntimeError):
        MultimodalImporter(target).import_package(pkg)
    assert not target.exists()
    target.write_bytes(b"existing protected database sentinel")
    before = target.read_bytes()
    with pytest.raises((sqlite3.Error, MultimodalValidationError)):
        MultimodalImporter(target).import_package(pkg)
    assert target.read_bytes() == before


def test_nonstaging_store_is_rejected(tmp_path):
    store = KnowledgeStore(tmp_path / "ordinary.db")
    store.initialize()
    with pytest.raises((sqlite3.Error, ValueError)):
        MultimodalRetriever(store)
