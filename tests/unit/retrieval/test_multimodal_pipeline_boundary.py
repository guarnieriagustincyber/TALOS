"""Synthetic chain contract: direct PackagedContext consumption must fail closed.

Exercises real retrieval, adapter, packer and pipeline; only the model is a
deterministic spy. No StudentState or provider. Does not certify S4.4/generation.
"""
import asyncio
import json

from study_engine.pedagogy.fase0_seed import FASE0_CONTRACT
from study_engine.pedagogy.structured_pipeline import StructuredResponsePipeline
from study_engine.retrieval.multimodal_adapter import MultimodalContextPacker
from study_engine.retrieval.multimodal_retrieval import MultimodalRetriever
from tests.unit.retrieval.test_multimodal_adapter import build_test_db, grant


def test_synthetic_retrieval_to_pipeline_contract_boundary(tmp_path):
    _, store = build_test_db(tmp_path)
    try:
        acl = grant(tmp_path, "src-A")
        retriever = MultimodalRetriever(store, manifest_path=acl)
        query = "functional dependencies"
        hits = retriever.search_multimodal(query, document_id="doc-A")
        assert any(h.chunk for h in hits)
        assert any(h.multimodal_elements for h in hits)
        assert retriever.search_multimodal(query, document_id="doc-B") == []
        assert MultimodalRetriever(store).search_multimodal(query) == []

        packed = MultimodalContextPacker().pack_for_pedagogy(hits, query)
        packet = packed["evidence_packet"]
        context = packed["packaged_context"]
        assert packet.original_query == query
        assert packet.evidence_items and not packet.abstention_required
        assert context.packet == packet
        assert context.citation_manifest.records
        assert all(i.document_id == "doc-A" and i.source_id == "src-A"
                   for i in packet.evidence_items)
        assert all(i.trust_level == "unverified" for i in packet.evidence_items)
        assert all(not h.trusted_for_rag and not h.production_import_authorized
                   and not h.fidelity_certified for h in hits)
        assert not hasattr(context, "is_sufficient")
        assert not hasattr(context, "abstained")

        class DeterministicModel:
            calls = 0

            async def stream(self, **kwargs):
                self.calls += 1
                yield "Según el fixture, A determina B [E1]."

        model = DeterministicModel()
        pipeline = StructuredResponsePipeline(FASE0_CONTRACT, model)

        async def collect():
            return [e async for e in pipeline.generate_phased_response(
                user_query=query, context_pack=context,
                requested_phase="conceptual",
            )]

        events = asyncio.run(collect())
        assert model.calls == 0
        assert [e.event_type for e in events] == ["abstention"]
        assert events[0].payload["abstained"] is True
        assert events[0].payload["abstention_code"] == "NO_EVIDENCE"
        print(json.dumps({
            "trace": ["Retrieval", "MultimodalEvidenceAdapter", "EvidencePacket",
                      "MultimodalContextPacker", "StructuredResponsePipeline", "C5_BLOCK"],
            "evidence_items": len(packet.evidence_items),
            "citations": list(context.citation_manifest.records),
            "model_calls": model.calls,
            "events": [dict(event_type=e.event_type, payload=e.payload) for e in events],
            "s4_4": "NOT_REACHED",
        }, ensure_ascii=False))
    finally:
        store.close()
