"""L3 non-disclosure through real SQLite/FTS, chat assembly and HTTP/SSE.

Temporary synthetic stores only; generation/NLI are verbatim doubles. No
production resources, full startup, external inference or gate accreditation.
The forbidden marker must be retrievable without ACL, but never reach the
generator, assembled context, citations, provenance or SSE under L3.
"""

import hashlib
import json
import re
import subprocess
import sys

import pytest

from study_engine.contracts.chunk import Chunk
from study_engine.pedagogy.contract import PedagogicalContract
from study_engine.pedagogy.response_phase import ResponsePhase
from study_engine.web.routes import chat
from tests.integration.test_federated_chat import FACTS, federation


FORBIDDEN = "MARCADOR_DENEGADO Los punteros y semaforos revelan contenido prohibido."


@pytest.fixture
def acl_consumer(federation):
    env = federation
    with env.store.engine.transaction() as conn:
        conn.execute(
            "INSERT INTO sources (source_id, title, role, sha256, manifest_json) VALUES (?, ?, ?, ?, ?)",
            ("src-denied", "Denied", "PRIMARY", "d" * 64,
             json.dumps({"metadata": {"trust_level": "canonical"}})),
        )
        conn.execute("INSERT INTO documents (id, source_id, title) VALUES ('doc-denied', 'src-denied', 'Denied')")
        for nb in ("synthetic-a", "synthetic-b"):
            conn.execute("INSERT INTO notebook_sources (notebook_id, source_id) VALUES (?, 'src-denied')", (nb,))
    env.store.chunks.save_chunks([Chunk(
        id="chunk-denied", source_id="src-denied", document_id="doc-denied",
        content=FORBIDDEN, page_start=1, page_end=1,
    )])
    path = env.store.l3_manifest_path
    manifest = json.loads(path.read_text())
    manifest["grants"].extend([
        {"notebook_id": nb, "source_id": "src-denied", "status": "DENIED"}
        for nb in ("synthetic-a", "synthetic-b")
    ])
    path.write_text(json.dumps(manifest))
    env.store.save_pedagogical_contract(PedagogicalContract(
        notebook_id="synthetic-b", base_system_prompt="Citar solamente evidencia.",
        response_phases=[ResponsePhase(phase_id="conceptual", max_tokens=250, phase_prompt_template="{concept}")],
    ))
    # Positive adversarial control: the denied text is actually indexed in FTS.
    assert any(r.source_id == "src-denied" for r in env.store.search_hybrid(
        query="punteros semaforos", notebook_id="synthetic-a", limit=20, min_sources=1,
    ))
    env.calls.clear()
    return env


def request(env, notebook, query):
    response = env.client.post("/api/chat/query", json={
        "prompt": query, "scope_type": "notebook", "scope_id": notebook,
        "requested_phase": "conceptual",
    })
    assert "MARCADOR_DENEGADO" not in response.text
    assert "src-denied" not in response.text and "doc-denied" not in response.text
    return response, [json.loads(line[6:]) for line in response.text.splitlines() if line.startswith("data: ")]


@pytest.mark.parametrize("notebook,query,allowed", [
    ("synthetic-a", "punteros", {"src-a"}),
    ("synthetic-b", "semaforos", {"src-b"}),
    ("synthetic-a", "punteros semaforos", {"src-a", "src-b"}),
])
def test_authorized_context_and_sse_exclude_denied_and_cross_scope(acl_consumer, notebook, query, allowed):
    env = acl_consumer
    pack, chunks = chat._assemble_epistemic_context(
        store=env.store, container=env.container, prompt_text=query, target_notebook_id=notebook,
    )
    assert not pack.abstained and pack.is_sufficient
    assert {c["source_id"] for c in chunks} == allowed
    assert {c.source_id for c in pack.citations} == allowed
    assert "MARCADOR_DENEGADO" not in pack.formatted_context
    response, events = request(env, notebook, query)
    assert response.status_code == 200
    completed = [e["payload"] for e in events if e["event_type"] == "phase_complete"]
    assert completed, events
    provenance = completed[-1]["evidence_provenance"]
    assert {c["source_id"] for c in provenance} == allowed
    for citation in provenance:
        name = citation["source_id"].removeprefix("src-")
        assert citation["document_id"] == f"doc-{name}"
        assert citation["chunk_id"] == f"chunk-{name}"
        assert citation["citation_id"]
        if len(allowed) > 1:
            assert citation["content_hash"] == hashlib.sha256(FACTS[name].encode()).hexdigest()
        else:
            assert citation["doc_hash"] == hashlib.sha256(FACTS[name].encode()).hexdigest()
    assert env.generator.calls
    prompts = json.dumps(env.generator.calls, ensure_ascii=False)
    for name in FACTS:
        assert (FACTS[name] in prompts) == (f"src-{name}" in allowed)
    assert "MARCADOR_DENEGADO" not in prompts
    emitted = "".join(e["payload"].get("token", "") for e in events if e["event_type"] == "phase_token")
    for name in FACTS:
        assert (FACTS[name] in emitted) == (f"src-{name}" in allowed)
        if f"src-{name}" not in allowed:
            assert FACTS[name] not in response.text
    assert set(re.findall(r"\[(E\d+)\]", emitted)) == {c["citation_id"] for c in provenance}
    assert all("src-denied" not in c["source_ids"] for c in env.calls)


@pytest.mark.parametrize("failure", ["missing", "unconfigured", "identity", "incomplete", "federated_acl"])
def test_incomplete_authorization_never_calls_generator(acl_consumer, failure):
    env = acl_consumer
    notebook, query = "synthetic-a", "punteros"
    path = env.store.l3_manifest_path
    if failure == "missing":
        env.store.l3_manifest_path = path.with_name("missing.json")
    elif failure == "unconfigured":
        del env.store.l3_manifest_path
    elif failure == "identity":
        notebook = "unknown-notebook"
    else:
        manifest = json.loads(path.read_text())
        target = "synthetic-b" if failure == "federated_acl" else "synthetic-a"
        for grant in manifest["grants"]:
            if grant["notebook_id"] == target:
                grant.pop("status", None)
        path.write_text(json.dumps(manifest))
        if failure == "federated_acl":
            query = "punteros semaforos"
    response, events = request(env, notebook, query)
    assert response.status_code in {200, 404, 422}
    assert not env.generator.calls and not env.judge.calls
    assert not any(e["event_type"] in {"phase_token", "phase_complete"} for e in events)
    assert response.status_code != 200 or any(e["event_type"] in {"abstention", "error"} for e in events)


def test_effective_source_contract_does_not_import_web():
    result = subprocess.run([sys.executable, "-c", """
import sys
from types import SimpleNamespace
from study_engine.contracts.l3_manifest import get_effective_sources
assert get_effective_sources(SimpleNamespace(), '__global__') == set()
assert not any(name.startswith('study_engine.web') for name in sys.modules)
"""], capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
