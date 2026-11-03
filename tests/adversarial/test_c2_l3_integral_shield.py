"""Adversarial regression test suite for C2 Gate B: L3 Authorization Model and Integral Shield.

Validates:
- Fixture A: Multi-source document isolation in SectionExpander (both retrieval and context implementations).
- Fixture B: Cross-notebook source isolation under L3 manifest.
- Fixture C: D2-A Policy-Not-Granted: 17 SOC -> FADENA relations strictly excluded from retrieval, expansion, assembler.
- Fixture D: D1-G4 Pending: src_fadena_prog_punteros excluded from L3 authorization for fase0-soc.
- Fixture E: Empty effective sources fail-closed: 0 retrieval, 0 expansion, 0 assembler evidence, 0 prompt, strictly NO fallback.
"""

import json
from pathlib import Path
from types import SimpleNamespace
import pytest

from study_engine.contracts.catalog import SourceRecord
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.document import Document
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.l3_manifest import (
    DEFAULT_MANIFEST_PATH,
    get_effective_sources,
    get_l3_authorized_sources,
    load_l3_manifest,
)
from study_engine.contracts.notebook import Notebook
from study_engine.contracts.search import SearchResult
from study_engine.contracts.source import Source, SourceRole
from study_engine.context.section_expander import SectionExpander as ContextSectionExpander
from study_engine.pedagogy.evidence_assembler import MultiSourceEvidenceAssembler
from study_engine.retrieval.expansion import SectionExpander as RetrievalSectionExpander
from study_engine.storage.knowledge_store import KnowledgeStore
from study_engine.web.routes.chat import (
    GLOBAL_SCOPE_ID,
    _authorized_sources_for_scope,
    _source_ids_for_notebook,
    _assemble_epistemic_context,
)


def _register_source(store: KnowledgeStore, source_id: str, title: str = "Test Source") -> None:
    """Helper to register source in catalog so save_document / link_source succeeds."""
    rec = SourceRecord(
        source_id=source_id,
        manifest=SourceManifest(
            source_id=source_id,
            filename=f"{source_id}.pdf",
            byte_size=100,
            sha256="a" * 64,
        ),
        source=Source(source_id=source_id, title=title, role=SourceRole.PRIMARY),
    )
    store.save_source(rec)


# ==============================================================================
# FIXTURE A: Multi-Source Document Isolation in SectionExpander
# ==============================================================================

def test_fixture_a_multi_source_document_retrieval_expansion_defense_in_depth() -> None:
    """Fixture A (retrieval.expansion): Chunks from unauthorized sources in the same document are strictly pruned."""
    store = KnowledgeStore(":memory:")
    store.initialize()

    doc_id = "doc-shared-multi"
    src_auth = "src-authorized"
    src_unauth = "src-unauthorized-leak"

    _register_source(store, src_auth, "Fuente Autorizada")
    _register_source(store, src_unauth, "Fuente No Autorizada")

    # Insert document and chunks directly to simulate multi-source document
    with store.engine.transaction() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO documents (id, source_id, title) VALUES (?, ?, ?);",
            (doc_id, src_auth, "Shared Doc"),
        )
        cursor.execute(
            """
            INSERT INTO chunks (id, document_id, source_id, content, page_start, pos_index, section, token_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            ("chk-0-auth", doc_id, src_auth, "Contenido legítimo de fuente autorizada.", 10, 0, "General", 20),
        )
        cursor.execute(
            """
            INSERT INTO chunks (id, document_id, source_id, content, page_start, pos_index, section, token_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            ("chk-1-unauth", doc_id, src_unauth, "LEAK_PAYLOAD: Contenido confidencial de fuente no autorizada.", 11, 1, "General", 25),
        )

    # Seed result only hits chk-0-auth
    seed_results = [
        SearchResult(
            chunk_id="chk-0-auth",
            document_id=doc_id,
            source_id=src_auth,
            score=0.95,
            snippet="Contenido legítimo",
            content="Contenido legítimo de fuente autorizada.",
            index=0,
            page_start=10,
        )
    ]

    expander = RetrievalSectionExpander(engine=store.engine, hard_ceiling_tokens=5000)
    meta_cache = {
        src_auth: {"title": "Fuente Autorizada"},
        src_unauth: {"title": "Fuente No Autorizada"},
    }

    # Expand WITH allowed_source_ids restricting to authorized source
    expanded_chunks, formatted_context = expander.expand_results(
        seed_results=seed_results,
        source_meta_cache=meta_cache,
        allowed_source_ids={src_auth},
    )

    # Assert strict containment
    expanded_ids = [c.chunk_id for c in expanded_chunks]
    assert expanded_ids == ["chk-0-auth"], f"Unauthorized chunk leaked: {expanded_ids}"
    assert all(c.source_id == src_auth for c in expanded_chunks)
    assert "LEAK_PAYLOAD" not in formatted_context
    assert "Fuente No Autorizada" not in formatted_context
    assert "chk-1-unauth" not in formatted_context


def test_fixture_a_multi_source_document_context_section_expander_defense_in_depth() -> None:
    """Fixture A (context.section_expander): Chunks from unauthorized sources in the same document are strictly pruned."""
    store = KnowledgeStore(":memory:")
    store.initialize()

    doc_id = "doc-shared-multi-ctx"
    src_auth = "src-auth-ctx"
    src_unauth = "src-unauth-ctx"

    _register_source(store, src_auth, "Fuente Autorizada Context")
    _register_source(store, src_unauth, "Fuente No Autorizada Context")

    with store.engine.transaction() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO documents (id, source_id, title) VALUES (?, ?, ?);",
            (doc_id, src_auth, "Shared Doc Context"),
        )
        cursor.execute(
            """
            INSERT INTO chunks (id, document_id, source_id, content, page_start, pos_index, section, token_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            ("chk-ctx-0-auth", doc_id, src_auth, "Context legítimo de fuente autorizada.", 20, 0, "General", 20),
        )
        cursor.execute(
            """
            INSERT INTO chunks (id, document_id, source_id, content, page_start, pos_index, section, token_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """,
            ("chk-ctx-1-unauth", doc_id, src_unauth, "UNAUTH_LEAK_IN_CONTEXT: Contenido prohibido.", 21, 1, "General", 25),
        )

    seed_results = [
        SearchResult(
            chunk_id="chk-ctx-0-auth",
            document_id=doc_id,
            source_id=src_auth,
            score=0.92,
            snippet="Context legítimo",
            content="Context legítimo de fuente autorizada.",
            index=0,
            page_start=20,
        )
    ]

    expander = ContextSectionExpander(engine=store.engine, hard_ceiling_tokens=5000)
    meta_cache = {
        src_auth: {"title": "Fuente Autorizada Context"},
        src_unauth: {"title": "Fuente No Autorizada Context"},
    }

    expanded_chunks, formatted_context = expander.expand_results(
        seed_results=seed_results,
        source_meta_cache=meta_cache,
        allowed_source_ids={src_auth},
    )

    expanded_ids = [c.chunk_id for c in expanded_chunks]
    assert expanded_ids == ["chk-ctx-0-auth"]
    assert all(c.source_id == src_auth for c in expanded_chunks)
    assert "UNAUTH_LEAK_IN_CONTEXT" not in formatted_context
    assert "Fuente No Autorizada Context" not in formatted_context


# ==============================================================================
# FIXTURE B: Cross-Notebook Source Isolation under L3 Manifest
# ==============================================================================

def test_fixture_b_cross_notebook_isolation(tmp_path: Path) -> None:
    """Fixture B: Cross-notebook isolation guarantees notebook A only retrieves sources authorized for notebook A."""
    manifest_file = tmp_path / "test_manifest.json"
    manifest_data = {
        "manifest_version": "1.0.0",
        "grants": [
            {"grant_id": "G1", "notebook_id": "nb-alpha", "source_id": "src-alpha-1", "status": "AUTHORIZED"},
            {"grant_id": "G2", "notebook_id": "nb-alpha", "source_id": "src-alpha-2", "status": "AUTHORIZED"},
            {"grant_id": "G3", "notebook_id": "nb-beta", "source_id": "src-beta-1", "status": "AUTHORIZED"},
        ],
    }
    manifest_file.write_text(json.dumps(manifest_data), encoding="utf-8")

    store = KnowledgeStore(":memory:")
    store.initialize()
    store.l3_manifest_path = manifest_file

    _register_source(store, "src-alpha-1")
    _register_source(store, "src-alpha-2")
    _register_source(store, "src-beta-1")

    # Technical links in SQLite: deliberately cross-link nb-alpha with src-beta-1
    store.create_notebook(Notebook(id="nb-alpha", name="Alpha"))
    store.create_notebook(Notebook(id="nb-beta", name="Beta"))

    store.link_source_to_notebook("nb-alpha", "src-alpha-1")
    store.link_source_to_notebook("nb-alpha", "src-beta-1")  # Cross-talk / unauthorized link!
    store.link_source_to_notebook("nb-beta", "src-beta-1")

    # Resolve sources for nb-alpha: must ONLY be src-alpha-1 (src-beta-1 filtered out by L3 manifest)
    alpha_effective = _source_ids_for_notebook(store, "nb-alpha")
    assert alpha_effective == {"src-alpha-1"}, f"Cross-notebook leak in alpha: {alpha_effective}"

    # Resolve sources for nb-beta: must ONLY be src-beta-1
    beta_effective = _source_ids_for_notebook(store, "nb-beta")
    assert beta_effective == {"src-beta-1"}, f"Cross-notebook leak in beta: {beta_effective}"


# ==============================================================================
# FIXTURE C: D2-A Policy-Not-Granted: 17 SOC -> FADENA Relations Excluded
# ==============================================================================

def test_fixture_c_soc_to_fadena_17_relations_strictly_excluded() -> None:
    """Fixture C: All 17 SOC -> FADENA relations are excluded by policy D2-A."""
    manifest = load_l3_manifest(DEFAULT_MANIFEST_PATH)
    all_grants = manifest.get("grants", [])

    # Exactly 81 AUTHORIZED, 1 PENDING, 17 EXCLUDED = 99 relations
    auth_grants = [g for g in all_grants if g["status"] == "AUTHORIZED"]
    pending_grants = [g for g in all_grants if g["status"] == "PENDING"]
    excl_grants = [g for g in all_grants if g["status"] == "EXCLUDED"]

    assert len(auth_grants) == 81, f"Expected 81 authorized grants, got {len(auth_grants)}"
    assert len(pending_grants) == 1, f"Expected 1 pending grant, got {len(pending_grants)}"
    assert len(excl_grants) == 17, f"Expected 17 excluded grants, got {len(excl_grants)}"
    assert len(all_grants) == 99, f"Expected exactly 99 total relations, got {len(all_grants)}"

    # In fadena-lenguajes, exactly 7 are excluded and 10 are authorized
    fl_auth = {g["source_id"] for g in auth_grants if g["notebook_id"] == "fadena-lenguajes"}
    fl_excl = {g["source_id"] for g in excl_grants if g["notebook_id"] == "fadena-lenguajes"}
    assert len(fl_auth) == 10
    assert len(fl_excl) == 7

    # Test known excluded sources in fadena-lenguajes
    known_excluded_lenguajes = [
        "src_joyanes_fundamentos",
        "src_spraul_think_like_a_programmer",
        "src_sweigart_automate_boring_stuff",
        "src_fadena_prog_arboles",
        "src_fadena_prog_archivos",
        "src_fadena_prog_lineales",
        "src_fadena_prog_punteros",
    ]
    for s in known_excluded_lenguajes:
        assert s in fl_excl, f"{s} must be EXCLUDED for fadena-lenguajes"
        assert s not in fl_auth, f"{s} must NOT be AUTHORIZED for fadena-lenguajes"

    # Test runtime enforcement in store
    store = KnowledgeStore(":memory:")
    store.initialize()
    store.l3_manifest_path = DEFAULT_MANIFEST_PATH

    _register_source(store, "src_fadena_leng_clase1")
    _register_source(store, "src_joyanes_fundamentos")

    store.create_notebook(Notebook(id="fadena-lenguajes", name="Lenguajes"))
    # Link a legitimate source and an excluded SOC source in SQLite
    store.link_source_to_notebook("fadena-lenguajes", "src_fadena_leng_clase1")
    store.link_source_to_notebook("fadena-lenguajes", "src_joyanes_fundamentos")

    effective = _source_ids_for_notebook(store, "fadena-lenguajes")
    assert "src_fadena_leng_clase1" in effective
    assert "src_joyanes_fundamentos" not in effective, "Policy-not-granted SOC source leaked into effective ACL!"

    # Test MultiSourceEvidenceAssembler excludes SOC sources
    assembler = MultiSourceEvidenceAssembler(
        knowledge_store=store,
        l3_manifest_path=DEFAULT_MANIFEST_PATH,
    )
    evidence_by_role, citations = assembler.assemble_evidence_for_kc(
        notebook_id="fadena-lenguajes",
        kc_id="kc-1",
        query="kernel",
    )
    for cit in citations:
        assert cit.source_id != "src_joyanes_fundamentos"


# ==============================================================================
# FIXTURE D: D1-G4 Pending: src_fadena_prog_punteros Excluded from L3
# ==============================================================================

def test_fixture_d_g4_pending_punteros_excluded() -> None:
    """Fixture D: src_fadena_prog_punteros is excluded from L3 authorization for fase0-soc under D1-G4."""
    manifest = load_l3_manifest(DEFAULT_MANIFEST_PATH)
    fase0_grants = {
        g["source_id"]: g["status"]
        for g in manifest.get("grants", [])
        if g.get("notebook_id") == "fase0-soc"
    }

    fase0_auth = {sid for sid, status in fase0_grants.items() if status == "AUTHORIZED"}
    fase0_pending = {sid for sid, status in fase0_grants.items() if status == "PENDING"}

    assert "src_fadena_prog_punteros" in fase0_pending, "src_fadena_prog_punteros must be marked PENDING"
    assert "src_fadena_prog_punteros" not in fase0_auth, "src_fadena_prog_punteros must NOT be AUTHORIZED under D1-G4"
    assert len(fase0_auth) == 25, f"Expected 25 authorized sources in fase0-soc, got {len(fase0_auth)}"

    # Test runtime enforcement in store
    store = KnowledgeStore(":memory:")
    store.initialize()
    store.l3_manifest_path = DEFAULT_MANIFEST_PATH

    _register_source(store, "src_fadena_prog_punteros")
    _register_source(store, "src_kurose_computer_networking")

    store.create_notebook(Notebook(id="fase0-soc", name="Fase 0 SOC"))
    # In SQLite, fase0-soc technically has src_fadena_prog_punteros (as observed in production DB)
    store.link_source_to_notebook("fase0-soc", "src_fadena_prog_punteros")
    store.link_source_to_notebook("fase0-soc", "src_kurose_computer_networking")

    effective = _source_ids_for_notebook(store, "fase0-soc")
    assert "src_kurose_computer_networking" in effective
    assert "src_fadena_prog_punteros" not in effective, "G4 pending source leaked into effective ACL!"

    # MultiSourceEvidenceAssembler check
    assembler = MultiSourceEvidenceAssembler(
        knowledge_store=store,
        l3_manifest_path=DEFAULT_MANIFEST_PATH,
    )
    _, citations = assembler.assemble_evidence_for_kc(
        notebook_id="fase0-soc",
        kc_id="kc-ptrs",
        query="puntero",
    )
    for cit in citations:
        assert cit.source_id != "src_fadena_prog_punteros"


# ==============================================================================
# FIXTURE E: Empty Effective ACL Fail-Closed (Zero Fallback)
# ==============================================================================

def test_fixture_e_empty_effective_acl_fail_closed_zero_fallback(tmp_path: Path) -> None:
    """Fixture E: When effective_sources = empty, system strictly fails closed with 0 retrieval, 0 expansion, and NO fallback."""
    # Create empty manifest (zero authorized sources)
    manifest_file = tmp_path / "empty_manifest.json"
    manifest_data = {
        "manifest_version": "1.0.0",
        "grants": [
            {"grant_id": "G-EXCL", "notebook_id": "nb-locked", "source_id": "src-tech-installed", "status": "EXCLUDED"}
        ],
    }
    manifest_file.write_text(json.dumps(manifest_data), encoding="utf-8")

    store = KnowledgeStore(":memory:")
    store.initialize()
    store.l3_manifest_path = manifest_file

    _register_source(store, "src-tech-installed")
    store.create_notebook(Notebook(id="nb-locked", name="Locked Notebook"))
    store.link_source_to_notebook("nb-locked", "src-tech-installed")

    # 1. Effective sources check: must be strictly empty
    effective = _source_ids_for_notebook(store, "nb-locked")
    assert effective == set(), f"Expected empty effective sources, got {effective}"

    scope_sources = _authorized_sources_for_scope(store, "nb-locked", None)
    assert scope_sources == set()

    # 2. SectionExpander fail-closed check: allowed_source_ids=set() must return ([], "")
    expander = RetrievalSectionExpander(engine=store.engine)
    dummy_seed = [
        SearchResult(
            chunk_id="c1",
            document_id="d1",
            source_id="src-tech-installed",
            score=0.9,
            snippet="leak",
            content="leak",
            index=0,
        )
    ]
    chunks, text = expander.expand_results(seed_results=dummy_seed, allowed_source_ids=set())
    assert chunks == [], "SectionExpander must return empty list when allowed_source_ids is empty"
    assert text == "", "SectionExpander must return empty string when allowed_source_ids is empty"

    # Context SectionExpander fail-closed check
    ctx_expander = ContextSectionExpander(engine=store.engine)
    ctx_chunks, ctx_text = ctx_expander.expand_results(seed_results=dummy_seed, allowed_source_ids=set())
    assert ctx_chunks == []
    assert ctx_text == ""

    # 3. MultiSourceEvidenceAssembler fail-closed check
    assembler = MultiSourceEvidenceAssembler(
        knowledge_store=store,
        l3_manifest_path=manifest_file,
    )
    evidence, citations = assembler.assemble_evidence_for_kc(
        notebook_id="nb-locked",
        kc_id="kc-1",
        query="test",
    )
    assert citations == []
    assert all(len(ev_list) == 0 for ev_list in evidence.values())

    # 4. _assemble_epistemic_context fail-closed check
    container = SimpleNamespace(
        pedagogical_orchestrator=SimpleNamespace(_kc_catalog={}),
        student_storage=None,
    )
    pack, raw_chunks = _assemble_epistemic_context(
        store=store,
        container=container,
        prompt_text="pregunta sobre punteros",
        target_notebook_id="nb-locked",
    )
    assert pack is not None
    assert pack.abstained is True
    assert pack.abstention_reason in ("NO_AUTHORIZED_SOURCES_IN_SCOPE", "NO_AUTHORIZED_ACTIVE_SOURCES")
    assert pack.formatted_context == ""
    assert pack.citations == []
    assert pack.chunks == []
    assert raw_chunks == []
