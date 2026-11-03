"""Offline invocation contract; no change to C5 or production entry points.

Canonical synthetic sources use the existing chat producer and EvidenceEngine.
Colab-shaped fixtures stay on the staging-only route. Generation and atomic
NLI are verbatim doubles; SQLite, L3, C5 and S4.4 execute their real code.
"""
import asyncio
import hashlib
import json
import re

import pytest

from study_engine.audit.contracts import AuditVerdict
from study_engine.context.c5_trust import evaluate_epistemic_trust
from study_engine.context.packer import ContextPacker
from study_engine.contracts.evidence_engine import EvidenceGrade, GroundingDecision
from study_engine.contracts.ingestion import SourceManifest
from study_engine.contracts.retrieval import ScoredCandidate
from study_engine.evidence.engine import EvidenceEngine
from study_engine.pedagogy.contract import PedagogicalContract
from study_engine.pedagogy.response_phase import ResponsePhase
from study_engine.pedagogy.structured_pipeline import StructuredResponsePipeline
from study_engine.web.routes import chat
from tests.integration.test_federated_chat import FACTS, federation


@pytest.fixture
def canonical_fixture(federation):
    # The chat fixture has metadata-only manifests; EvidenceEngine needs the
    # complete SourceManifest contract, with hashes of the actual fixture bytes.
    with federation.store.engine.transaction() as conn:
        for name, fact in FACTS.items():
            manifest = SourceManifest(
                source_id=f"src-{name}", filename=f"Synthetic {name}",
                byte_size=len(fact.encode()), sha256=hashlib.sha256(fact.encode()).hexdigest(),
                metadata={"trust_level": "canonical", "origin": "TEST_FIXTURE"},
            )
            conn.execute("UPDATE sources SET manifest_json=? WHERE source_id=?",
                         (manifest.model_dump_json(), f"src-{name}"))
    return federation


def prepare_context(env, query, **kwargs):
    # The real producer owns L3 scope and retrieval; never rebuild its allowlist.
    source_pack, raw = chat._assemble_epistemic_context(
        store=env.store, container=env.container, prompt_text=query,
        target_notebook_id="synthetic-a", **kwargs,
    )
    if source_pack.abstained:
        return source_pack, None

    candidates = []
    grades = {}
    for rank, result in enumerate(source_pack.citations, 1):
        # External assessment is restricted to the exact declared fixture fact.
        assert result.content == FACTS["a"]
        assert result.chunk_id == "chunk-a" and result.document_id == "doc-a"
        assert result.source_id == "src-a"
        candidates.append(ScoredCandidate(
            chunk_id=result.chunk_id, document_id=result.document_id,
            source_id=result.source_id, notebook_id="synthetic-a", rank=rank,
            score=result.score, content=result.content, page_start=result.page_start,
            page_end=result.page_end, retrieval_method="hybrid",
        ))
        grades[result.chunk_id] = EvidenceGrade.DIRECT
    packet = EvidenceEngine().evaluate_candidates(
        query, "synthetic-a", candidates, store=env.store, assessed_grades=grades,
    )
    assert packet.grounding_decision == GroundingDecision.SUPPORTED
    packaged = ContextPacker().pack(packet)
    retained = {u.citation.chunk_id for u in packaged.packaged_units}
    selected = [c for c in raw if c["chunk_id"] in retained]
    assert {c["citation_id"] for c in selected} == set(packaged.citation_manifest.records)
    evaluation = evaluate_epistemic_trust(query, selected)
    # Correct invocation: use the real C5 input type, not PackagedContext.
    context = chat.EpistemicContextPack(
        formatted_context=packaged.formatted_context_block,
        citations=list(packaged.citation_manifest.records.values()), chunks=selected,
        abstained=packet.abstention_required or evaluation.abstained,
        abstention_reason=evaluation.abstention_reason,
        is_sufficient=evaluation.is_sufficient,
        trust_status=evaluation.status, coverage_ratio=evaluation.coverage_ratio,
        missing_critical_terms=evaluation.missing_critical_terms,
        is_conflicting=evaluation.is_conflicting,
        conflict_details=evaluation.conflict_details, max_relevance=evaluation.max_relevance,
    )
    return context, packaged


def run_pipeline(env, query, context):
    class VerbatimModel:
        name = "synthetic-verbatim-meta2"

        def __init__(self):
            self.calls = []

        async def stream(self, **kwargs):
            self.calls.append(kwargs)
            assert FACTS["a"] in kwargs["user_prompt"]
            yield f"[E1] {FACTS['a']}"

    model = VerbatimModel()
    contract = PedagogicalContract(
        notebook_id="synthetic-a", base_system_prompt="Citar solamente evidencia sintética.",
        response_phases=[ResponsePhase(
            phase_id="conceptual", max_tokens=250, phase_prompt_template="{concept}",
        )],
    )
    pipeline = StructuredResponsePipeline(contract, model, auditor=env.auditor)

    async def collect():
        return [e async for e in pipeline.generate_phased_response(
            user_query=query, context_pack=context, requested_phase="conceptual",
        )]

    return model, asyncio.run(collect())


def test_evaluated_canonical_fixture_reaches_c5_generation_and_s44(canonical_fixture):
    env = canonical_fixture
    context, packaged = prepare_context(env, "punteros")
    assert context.is_sufficient and not context.abstained
    assert context.coverage_ratio == 1.0 and not context.missing_critical_terms
    assert context.trust_status.value == "SUFFICIENT_EVIDENCE"
    assert packaged.packet.has_full_provenance
    citation = packaged.citation_manifest.records["E1"]
    assert citation.trust_level == "canonical"
    assert citation.content_hash == hashlib.sha256(FACTS["a"].encode()).hexdigest()
    model, events = run_pipeline(env, "punteros", context)
    assert len(model.calls) == 1
    assert len(env.auditor.reports) == 1
    report = env.auditor.reports[0]
    assert report.overall_verdict == AuditVerdict.APPROVED, report.model_dump(mode="json")
    assert report.nli_executed and report.claim_verifications and env.judge.calls
    types = [e.event_type for e in events]
    assert types.index("audit_verdict") < types.index("phase_token")
    complete = next(e.payload for e in events if e.event_type == "phase_complete")
    text = "".join(e.payload["token"] for e in events if e.event_type == "phase_token")
    assert FACTS["a"] in text
    assert set(re.findall(r"\[(E\d+)\]", text)) == set(packaged.citation_manifest.records)
    assert complete["completed_phase"] == "conceptual"
    print(json.dumps(dict(
        trace=["L3 Retrieval", "EvidenceEngine:DIRECT", "EvidencePacket:SUPPORTED",
               "ContextPacker:E1", "C5:SUFFICIENT_EVIDENCE", "model:1", "S4.4:APPROVED"],
        text=text, phase=complete["completed_phase"], citation=citation.model_dump(mode="json"),
        coverage=context.coverage_ratio,
    ), ensure_ascii=False))


@pytest.mark.parametrize("case", ["insufficient", "no_authorization", "foreign_document"])
def test_rejected_context_never_calls_model(canonical_fixture, case):
    env = canonical_fixture
    query, kwargs = "punteros", {}
    if case == "insufficient":
        query = "punteros criptografia asimetrica"
    elif case == "no_authorization":
        env.store.l3_manifest_path.write_text(json.dumps({"grants": []}))
    else:
        # doc-b belongs to src-b, which is not allowed for this local query.
        kwargs["active_sources"] = ["src-b"]
    context, packaged = prepare_context(env, query, **kwargs)
    assert context.abstained and not context.is_sufficient
    model, events = run_pipeline(env, query, context)
    assert not model.calls and not env.auditor.reports and not env.judge.calls
    assert [e.event_type for e in events] == ["abstention"]
    print(json.dumps(dict(case=case, model_calls=0, result=events[0].payload)))
