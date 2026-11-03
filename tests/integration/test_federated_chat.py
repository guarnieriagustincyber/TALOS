"""E4 chat contract: real planner, SQLite/FTS, C5, route, pipeline and S4.4.

Only generation and atomic NLI are synthetic (verbatim fixture claims only).
All persistence is temporary; no AppContainer startup, student state, providers,
corpus, protected snapshots or gates. Run inside the read-only offline sandbox.
These tests demonstrate local wiring, not external NLI semantics or release.
"""

from datetime import datetime, timedelta, timezone
import hashlib
import json
import re
from types import SimpleNamespace
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from study_engine.audit.auditor import ForensicAuditor
from study_engine.audit.contracts import AuditVerdict, ClaimSupportVerdict
from study_engine.audit.nli import NLIInferenceResult
from study_engine.contracts.chunk import Chunk
from study_engine.contracts.notebook import Notebook
from study_engine.federation.bridge_registry import BridgeRegistry, CrossNotebookBridge
from study_engine.federation.federated_query_planner import FederatedQueryPlanner
from study_engine.federation.notebook_registry import Notebook as FederatedNotebook, NotebookRegistry
from study_engine.pedagogy.contract import PedagogicalContract
from study_engine.pedagogy.response_phase import ResponsePhase
from study_engine.storage.knowledge_store import KnowledgeStore
from study_engine.web.dependencies import get_container
from study_engine.web.routes import chat


FACTS = {
    "a": "Los punteros almacenan direcciones de memoria.",
    "b": "Los semaforos coordinan el acceso a recursos compartidos.",
    "c": "Los sockets transportan mensajes entre procesos.",
}


class VerbatimGenerator:
    """Synthetic generation: echo only literal evidence received in the prompt."""

    def __init__(self):
        self.calls = []
        self.bad_citation = False

    async def stream(self, **kwargs):
        self.calls.append(kwargs)
        text = "\n".join(
            f"[{tag}] {content}" for tag, content in re.findall(
                r'\[(E\d+)\] Fuente: [^\n]+\n"([^"]+)"', kwargs["user_prompt"],
            )
        )
        yield text.replace("[E1]", "[E999]") if self.bad_citation else text


class VerbatimJudge:
    """Synthetic NLI oracle: exact fixture substrings, never unconditional approval."""

    judge_id = "synthetic-verbatim-e4"

    def __init__(self):
        self.calls = []

    def evaluate_claim(self, premise, hypothesis):
        self.calls.append((premise, hypothesis))
        supported = hypothesis.strip().rstrip(".").casefold() in premise.casefold()
        return NLIInferenceResult(
            verdict=ClaimSupportVerdict.ENTAILED if supported else ClaimSupportVerdict.NOT_ENTAILED,
            rationale="Synthetic verbatim oracle; no external semantic inference.",
        )


class RecordingAuditor(ForensicAuditor):
    def __init__(self, judge):
        super().__init__(nli_judge=judge, nli_max_concurrency=1, nli_reuse_cache=False)
        self.reports = []

    def audit(self, audit_input):
        report = super().audit(audit_input)
        self.reports.append(report)
        return report


@pytest.fixture
def federation(tmp_path, monkeypatch):
    store = KnowledgeStore(tmp_path / "synthetic.db")
    store.initialize()
    registry = NotebookRegistry(initial_notebooks=[])
    for name, topic in (("a", "punteros"), ("b", "semaforos"), ("c", "sockets")):
        store.create_notebook(Notebook(id=f"synthetic-{name}", name=f"Synthetic {name}"))
        registry.register_notebook(FederatedNotebook(
            notebook_id=f"synthetic-{name}", name=f"Synthetic {name}", subject="Synthetic",
            sources=[f"src-{name}"], authority_matrix_ref={topic: 1.5},
        ))
        with store.engine.transaction() as conn:
            conn.execute(
                "INSERT INTO sources (source_id, title, role, sha256, manifest_json) VALUES (?, ?, ?, ?, ?)",
                (f"src-{name}", f"Synthetic {name}", "PRIMARY", hashlib.sha256(FACTS[name].encode()).hexdigest(),
                 json.dumps({"metadata": {"trust_level": "canonical", "origin": "TEST_FIXTURE"}})),
            )
            conn.execute("INSERT INTO documents (id, source_id, title) VALUES (?, ?, ?)",
                         (f"doc-{name}", f"src-{name}", f"Synthetic {name}"))
            conn.execute("INSERT INTO notebook_sources (notebook_id, source_id) VALUES (?, ?)",
                         (f"synthetic-{name}", f"src-{name}"))
        store.chunks.save_chunks([Chunk(
            id=f"chunk-{name}", document_id=f"doc-{name}", source_id=f"src-{name}",
            content=FACTS[name], page_start=1, page_end=1,
        )])
    manifest = tmp_path / "synthetic-l3.json"
    manifest.write_text(json.dumps({"grants": [
        {"notebook_id": f"synthetic-{name}", "source_id": f"src-{name}", "status": "AUTHORIZED"}
        for name in FACTS
    ]}))
    store.l3_manifest_path = manifest
    bridges = BridgeRegistry(allowlist_path=None)
    for name, topic in (("b", "semaforos"), ("c", "sockets")):
        bridges._bridges[f"bridge-{name}"] = CrossNotebookBridge(
            bridge_id=f"bridge-{name}", source_notebook="synthetic-a", target_notebook=f"synthetic-{name}",
            topic_allowlist=[topic], direction="unidirectional", ttl_days=1,
            created_at=datetime.now(timezone.utc), reviewer="synthetic-reviewer",
            provenance_tag=f"synthetic-authorization-{name}",
        )
    planner = FederatedQueryPlanner(registry, bridges)
    generator = VerbatimGenerator()
    judge = VerbatimJudge()
    auditor = RecordingAuditor(judge)
    container = SimpleNamespace(
        knowledge_store=store, federated_query_planner=planner,
        pedagogical_orchestrator=SimpleNamespace(_kc_catalog={}), controller=SimpleNamespace(),
        auditor=auditor, llm_backend=generator, student_storage=None, bkt_tracker=None,
    )
    store.save_pedagogical_contract(PedagogicalContract(
        notebook_id="synthetic-a", base_system_prompt="Tutor sintético: citar solamente la evidencia.",
        response_phases=[ResponsePhase(phase_id="conceptual", max_tokens=250, phase_prompt_template="{concept}")],
    ))
    calls = []
    search = store.search_hybrid

    def recording_search(**kwargs):
        calls.append(kwargs)
        return search(**kwargs)

    monkeypatch.setattr(store, "search_hybrid", recording_search)
    app = FastAPI()
    app.include_router(chat.router)
    app.dependency_overrides[get_container] = lambda: container
    with TestClient(app, base_url="http://127.0.0.1:8000", client=("127.0.0.1", 50000)) as client:
        yield SimpleNamespace(
            store=store, planner=planner, bridges=bridges, container=container,
            client=client, generator=generator, judge=judge, auditor=auditor, calls=calls,
        )
    store.close()


def assemble(env, query="punteros semaforos", **kwargs):
    return chat._assemble_epistemic_context(
        store=env.store, container=env.container, prompt_text=query,
        target_notebook_id="synthetic-a", **kwargs,
    )


def query_chat(env, query="punteros semaforos", **kwargs):
    response = env.client.post("/api/chat/query", json={
        "prompt": query, "scope_type": "notebook", "scope_id": "synthetic-a",
        "requested_phase": "conceptual", "session_id": f"synthetic-{uuid4().hex}", **kwargs,
    })
    assert response.status_code == 200
    return [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]


def test_real_federation_reaches_chat_and_grounding_audit(federation):
    events = query_chat(federation)
    completions = [e["payload"] for e in events if e["event_type"] == "phase_complete"]
    assert completions, json.dumps(events, ensure_ascii=False)
    provenance = completions[-1]["evidence_provenance"]
    assert {c["source_id"] for c in provenance} == {"src-a", "src-b"}
    assert {c["bridge_id"] for c in provenance} == {None, "bridge-b"}
    assert all(c["chunk_id"] and c["document_id"] and c["content_hash"] and c["plan_id"] for c in provenance)
    assert federation.generator.calls and federation.judge.calls
    assert federation.auditor.reports[-1].overall_verdict == AuditVerdict.APPROVED
    assert federation.auditor.reports[-1].nli_executed
    text = "".join(e["payload"].get("token", "") for e in events if e["event_type"] == "phase_token")
    assert all(fact in text for fact in (FACTS["a"], FACTS["b"]))
    assert set(re.findall(r"\[(E\d+)\]", text)) == {c["citation_id"] for c in provenance}
    assert {c["notebook_id"] for c in provenance} == {"synthetic-a", "synthetic-b"}
    assert all(call["source_ids"] for call in federation.calls)


def test_non_federated_query_keeps_local_path(federation):
    events = query_chat(federation, "punteros")
    assert any(e["event_type"] == "phase_complete" for e in events), events
    assert {call["notebook_id"] for call in federation.calls} == {"synthetic-a"}
    assert federation.auditor.reports[-1].overall_verdict == AuditVerdict.APPROVED


def test_combines_multiple_federated_sources(federation):
    pack, chunks = assemble(federation, "punteros semaforos sockets")
    assert not pack.abstained and pack.is_sufficient, pack.abstention_reason
    assert {c["source_id"] for c in chunks} == {"src-a", "src-b", "src-c"}
    assert len({c["citation_id"] for c in chunks}) == 3


@pytest.mark.parametrize("query, expected", [
    ("semáforos", True), ("SEMAFOROS", True), ("semaforos_extra", True), ("nosemaforos", False),
])
def test_planner_detects_normalized_whole_topics(federation, query, expected):
    plan = federation.planner.plan_query("synthetic-a", query)
    assert plan.is_cross_curricular is expected


@pytest.mark.parametrize("failure", ["unavailable", "empty", "content", "identity", "page", "provenance"])
def test_bad_federated_results_fail_closed(federation, monkeypatch, failure):
    search = federation.store.search_hybrid
    if failure == "empty":
        # Empty means no stored evidence, not just an empty hybrid selection with viable lexical recall.
        with federation.store.engine.transaction() as conn:
            conn.execute("DELETE FROM chunks WHERE source_id = 'src-b'")

    def faulty_search(**kwargs):
        if kwargs["notebook_id"] != "synthetic-b":
            return search(**kwargs)
        if failure == "unavailable":
            raise TimeoutError("synthetic unavailable source")
        if failure == "empty":
            return []
        results = search(**kwargs)
        assert results
        if failure == "provenance":
            with federation.store.engine.transaction() as conn:
                conn.execute("UPDATE sources SET sha256 = ? WHERE source_id = 'src-b'", ("0" * 64,))
            return results
        update = {"content": "invented evidence"} if failure == "content" else (
            {"source_id": "src-c"} if failure == "identity" else {"page_start": 99}
        )
        return [results[0].model_copy(update=update)]

    monkeypatch.setattr(federation.store, "search_hybrid", faulty_search)
    events = query_chat(federation)
    assert not federation.generator.calls and not federation.judge.calls
    assert not any(e["event_type"] == "phase_complete" for e in events)
    assert any(e["event_type"] in {"abstention", "error"} for e in events), events


@pytest.mark.parametrize("denial", ["bridge", "expired", "direction", "l3", "active_sources", "inactive"])
def test_unauthorized_target_never_reaches_retrieval(federation, denial):
    bridge = federation.bridges._bridges["bridge-b"]
    kwargs = {}
    if denial == "bridge":
        federation.bridges._bridges.pop("bridge-b")
    elif denial == "expired":
        federation.bridges._bridges["bridge-b"] = bridge.model_copy(update={
            "created_at": datetime.now(timezone.utc) - timedelta(days=2),
        })
    elif denial == "direction":
        federation.bridges._bridges["bridge-b"] = bridge.model_copy(update={
            "source_notebook": "synthetic-b", "target_notebook": "synthetic-a",
        })
    elif denial == "l3":
        federation.store.l3_manifest_path.write_text('{"grants": []}')
    elif denial == "active_sources":
        kwargs["active_sources"] = ["src-a"]
    else:
        nb = federation.planner.notebook_registry.get_notebook("synthetic-b")
        federation.planner.notebook_registry.register_notebook(nb.model_copy(update={"is_active": False}))
    pack, chunks = assemble(federation, **kwargs)
    assert pack.abstained and not pack.is_sufficient and chunks == []
    assert not any(c["notebook_id"] == "synthetic-b" for c in federation.calls)


def test_planner_exception_does_not_fall_back_to_local_answer(federation, monkeypatch):
    def broken_plan(*args, **kwargs):
        raise RuntimeError("synthetic planner failure")

    monkeypatch.setattr(federation.planner, "plan_query", broken_plan)
    events = query_chat(federation)
    assert not federation.calls and not federation.generator.calls
    assert any(e["event_type"] == "error" for e in events), events


def test_bridge_expiring_in_flight_is_not_evidence(federation, monkeypatch):
    search = federation.store.search_hybrid

    def expire_after_search(**kwargs):
        results = search(**kwargs)
        if kwargs["notebook_id"] == "synthetic-b":
            bridge = federation.bridges._bridges["bridge-b"]
            federation.bridges._bridges["bridge-b"] = bridge.model_copy(update={
                "created_at": datetime.now(timezone.utc) - timedelta(days=2),
            })
        return results

    monkeypatch.setattr(federation.store, "search_hybrid", expire_after_search)
    pack, chunks = assemble(federation)
    assert pack.abstained and chunks == []


def test_invalid_final_citation_is_rejected_by_real_auditor(federation):
    federation.generator.bad_citation = True
    events = query_chat(federation)
    assert federation.generator.calls
    assert federation.auditor.reports[-1].overall_verdict == AuditVerdict.REJECTED_UNSUPPORTED
    assert not any(e["event_type"] == "phase_token" for e in events), events


def test_l3_excludes_linked_poison_source_before_ranking(federation):
    with federation.store.engine.transaction() as conn:
        conn.execute(
            "INSERT INTO sources (source_id, title, role) VALUES ('poison', 'Synthetic forbidden', 'PRIMARY')",
        )
        conn.execute("INSERT INTO documents (id, source_id, title) VALUES ('poison-doc', 'poison', 'Forbidden')")
        conn.execute("INSERT INTO notebook_sources (notebook_id, source_id) VALUES ('synthetic-b', 'poison')")
    federation.store.chunks.save_chunks([Chunk(
        id="poison-chunk", source_id="poison", document_id="poison-doc",
        content="punteros semaforos punteros semaforos FORBIDDEN_SYNTHETIC", page_start=1, page_end=1,
    )])
    statements = []
    with federation.store.engine.transaction() as conn:
        conn.set_trace_callback(statements.append)
    pack, chunks = assemble(federation)
    assert not pack.abstained
    assert "FORBIDDEN_SYNTHETIC" not in pack.formatted_context
    assert all(c["source_id"] != "poison" for c in chunks)
    scoped_queries = [s for s in statements if "FROM chunks_fts" in s and "ns.notebook_id = 'synthetic-b'" in s]
    assert scoped_queries
    assert all("c.source_id IN ('src-b')" in s for s in scoped_queries)


@pytest.mark.parametrize("weight, winner", [(1.5, "chunk-a"), (2.0, "chunk-b")])
def test_real_candidates_use_original_deterministic_deduplication(federation, weight, winner):
    content = "Los punteros y semaforos son conceptos del ejercicio sintético."
    with federation.store.engine.transaction() as conn:
        conn.execute("UPDATE chunks SET content = ? WHERE source_id IN ('src-a', 'src-b')", (content,))
        conn.execute("UPDATE sources SET sha256 = ? WHERE source_id IN ('src-a', 'src-b')",
                     (hashlib.sha256(content.encode()).hexdigest(),))
    nb = federation.planner.notebook_registry.get_notebook("synthetic-b")
    federation.planner.notebook_registry.register_notebook(nb.model_copy(update={"authority_matrix_ref": {"semaforos": weight}}))
    pack, chunks = assemble(federation)
    assert not pack.abstained
    assert [c["chunk_id"] for c in chunks] == [winner]
    assert any(c["notebook_id"] == "synthetic-b" for c in federation.calls)


def test_cached_local_context_cannot_rescue_a_planner_failure(federation, monkeypatch):
    session = f"synthetic-{uuid4().hex}"
    first = query_chat(federation, "punteros", session_id=session)
    assert any(e["event_type"] == "phase_complete" for e in first)
    calls_before = len(federation.generator.calls)

    def broken_plan(*args, **kwargs):
        raise RuntimeError("synthetic planner failure with cached evidence")

    monkeypatch.setattr(federation.planner, "plan_query", broken_plan)
    events = query_chat(federation, "explicame más sobre punteros", session_id=session)
    assert any(e["event_type"] == "error" for e in events), events
    assert len(federation.generator.calls) == calls_before
    assert not any(e["event_type"] == "phase_token" for e in events)


def test_coverage_recovery_never_retries_without_source_authorization(federation, monkeypatch):
    search = federation.store.search
    hybrid = federation.store.search_hybrid
    lexical_calls = []

    def empty_hybrid(**kwargs):
        return [] if kwargs["notebook_id"] == "synthetic-b" else hybrid(**kwargs)

    def rejecting_search(**kwargs):
        if kwargs["notebook_id"] == "synthetic-b":
            lexical_calls.append(kwargs)
            if "source_ids" in kwargs:
                raise TypeError("Synthetic adapter rejects scoped search")
        return search(**kwargs)

    monkeypatch.setattr(federation.store, "search_hybrid", empty_hybrid)
    monkeypatch.setattr(federation.store, "search", rejecting_search)
    pack, chunks = assemble(federation)
    assert pack.abstained and chunks == []
    assert lexical_calls and all(c.get("source_ids") == ["src-b"] for c in lexical_calls)


def test_unregistered_notebook_keeps_its_existing_local_path(federation):
    federation.planner.notebook_registry._notebooks.pop("synthetic-a")
    pack, chunks = assemble(federation, "punteros")
    assert not pack.abstained and pack.is_sufficient
    assert {c["source_id"] for c in chunks} == {"src-a"}
    assert {c["notebook_id"] for c in federation.calls} == {"synthetic-a"}


def test_cached_bridge_evidence_requires_replanning_even_for_shared_sources(federation):
    with federation.store.engine.transaction() as conn:
        conn.execute("INSERT INTO notebook_sources (notebook_id, source_id) VALUES ('synthetic-a', 'src-b')")
    manifest = json.loads(federation.store.l3_manifest_path.read_text())
    manifest["grants"].append({"notebook_id": "synthetic-a", "source_id": "src-b", "status": "AUTHORIZED"})
    federation.store.l3_manifest_path.write_text(json.dumps(manifest))
    nb = federation.planner.notebook_registry.get_notebook("synthetic-b")
    federation.planner.notebook_registry.register_notebook(nb.model_copy(update={"authority_matrix_ref": {"semaforos": 2.0}}))
    pack, chunks = assemble(federation)
    assert not pack.abstained and any(c["bridge_id"] == "bridge-b" for c in chunks)
    assert not chat._is_authorized_reusable_pack(
        pack, chunks, store=federation.store, target_notebook_id="synthetic-a", global_folder_id=None,
    )


def test_missing_bridge_does_not_masquerade_as_expiry_and_block_local_retrieval(federation):
    federation.bridges._bridges.pop("bridge-b")
    nb = federation.planner.notebook_registry.get_notebook("synthetic-b")
    federation.planner.notebook_registry.register_notebook(nb.model_copy(update={"authority_matrix_ref": {"punteros": 1.5}}))
    pack, chunks = assemble(federation, "punteros")
    assert not pack.abstained and pack.is_sufficient
    assert {c["source_id"] for c in chunks} == {"src-a"}
    assert {c["notebook_id"] for c in federation.calls} == {"synthetic-a"}
