from types import SimpleNamespace

import pytest
import hashlib
import json

from study_engine.audit.auditor import ForensicAuditor
from study_engine.audit.nli import GeminiNLIJudge
from study_engine.audit.contracts import AuditVerdict
from study_engine.audit.citation_verifier import CitationVerifier
from study_engine.contracts.evidence_engine import GroundingDecision
from study_engine.contracts.generation import GenerationMode
from study_engine.audit.generation_adapter import audit_generation_payload


# Fixed semantic oracles for a future authorized real-provider run; local preflight does not adjudicate them.
NLI_SEMANTIC_PREFLIGHT_CASES = [
    ("supported", "[E1] La variable n tiene el valor 7.", ("ENTAILED",), 1),
    ("contradiction", "[E1] La variable n tiene el valor 9.", ("CONTRADICTED",), 1),
    ("absent", "[E1] El servicio Luma está implementado en Rust.", ("NOT_ENTAILED",), 1),
    ("wrong-citation", "[E99] La variable n tiene el valor 7.", (), 0),
    ("partial", "[E1] La variable n tiene el valor 7 y el servicio Luma cifra el tráfico.", ("PARTIALLY_SUPPORTED",), 1),
    ("independent", "[E1] La variable n tiene el valor 7.\n[E1] El servicio Luma usa el puerto 8080.",
     ("ENTAILED", "CONTRADICTED"), 2),
]


@pytest.mark.parametrize("case_id, text, semantic_oracle, expected_calls", NLI_SEMANTIC_PREFLIGHT_CASES,
                         ids=[case[0] for case in NLI_SEMANTIC_PREFLIGHT_CASES])
def test_semantic_preflight_real_adapter_without_external_inference(case_id, text, semantic_oracle, expected_calls):
    """Real ClaimExtractor/S4.4/NLI adapter; transport is synthetic and NEVER judges semantics."""
    source = "La variable n tiene el valor 7. El servicio Luma usa el puerto 4242."

    class RecordingUnassessedBackend:
        model_name = "synthetic-preflight-no-semantic-inference"

        def __init__(self):
            self.inputs = []

        def complete(self, bundle):
            self.inputs.append(json.loads(bundle.messages[0].content))
            return SimpleNamespace(text=json.dumps({
                "verdict": "UNASSESSED", "rationale": "Local transport preflight; no semantic inference performed.",
            }))

    backend = RecordingUnassessedBackend()
    judge = GeminiNLIJudge(backend, max_calls=2)
    auditor = ForensicAuditor(nli_judge=judge, nli_max_concurrency=1, nli_reuse_cache=False)
    report = audit_generation_payload(
        auditor, generated_text=text,
        context_chunks=[_chunk(chunk_text=source, content_hash=hashlib.sha256(source.encode()).hexdigest(),
                               page_start=1, page_end=1)],
        query="Synthetic semantic acceptance preflight", notebook_id="synthetic-notebook",
    )
    assert judge.call_count == len(backend.inputs) == expected_calls
    assert len(semantic_oracle) == expected_calls  # Oracle cardinality, not semantic correctness.
    if case_id == "wrong-citation":
        assert report.overall_verdict == AuditVerdict.REJECTED_UNSUPPORTED
        assert any(check.check_id == "CHECK_MANIFEST_INTEGRITY" and check.status.value == "FAIL"
                   for check in report.deterministic_checks)
    else:
        assert report.overall_verdict == AuditVerdict.FLAGGED_UNASSESSED
        assert all(value["source_text"] == source for value in backend.inputs)
        assert all(set(value) == {"source_text", "claim"} for value in backend.inputs)
        assert all("[E" not in value["claim"] for value in backend.inputs)
        assert all(verification.nli_verdict.value == "UNASSESSED" for verification in report.claim_verifications)


@pytest.mark.parametrize("finish_reason, usage", [
    ("stop", {"prompt_tokens": 90, "completion_tokens": 18, "total_tokens": 108}),
    ("length", {"prompt_tokens": 90, "completion_tokens": 180, "total_tokens": 270}),
    (None, None),
])
def test_nli_transport_telemetry_preserves_provider_metadata(finish_reason, usage):
    """Synthetic HTTP response only: no credentials, remote service or semantic inference."""
    import httpx
    from study_engine.llm.gemini_backend import GeminiBackend
    requests = []
    completions = []

    def respond(request):
        requests.append(json.loads(request.content))
        return httpx.Response(200, json={
            "model": "gemini-3.5-flash-lite",
            "choices": [{"message": {"content": '{"verdict":"UNASSESSED","rationale":"Synthetic response"}'},
                         "finish_reason": finish_reason}],
            "usage": usage,
        })

    class RecordingBackend:
        model_name = "gemini-3.5-flash-lite"

        def __init__(self, backend):
            self.backend = backend

        def complete(self, bundle):
            completion = self.backend.complete(bundle)
            completions.append(completion)
            return completion

    with httpx.Client(transport=httpx.MockTransport(respond)) as client:
        backend = GeminiBackend(api_key="synthetic-not-a-credential", model_name="gemini-3.5-flash-lite", client=client)
        judge = GeminiNLIJudge(RecordingBackend(backend), max_calls=1)
        result = judge.evaluate_claim("Synthetic source text.", "Synthetic claim text.")
    assert result.verdict.value == "UNASSESSED"
    assert len(requests) == judge.call_count == 1
    assert requests[0]["model"] == "gemini-3.5-flash-lite"
    assert requests[0]["max_tokens"] == 180
    assert completions[0].finish_reason == finish_reason
    assert completions[0].model == "gemini-3.5-flash-lite"
    if usage is None:
        assert completions[0].tokens_used is None
    else:
        assert completions[0].tokens_used.model_dump() == usage


def test_nli_transport_telemetry_keeps_technical_error_distinct():
    import httpx
    from study_engine.llm.gemini_backend import GeminiBackend
    from study_engine.llm.exceptions import LLMBackendError
    requests = []

    def unavailable(request):
        requests.append(request.url.path)
        return httpx.Response(503, json={"error": "Synthetic unavailable service"})

    with httpx.Client(transport=httpx.MockTransport(unavailable)) as client:
        judge = GeminiNLIJudge(GeminiBackend(api_key="synthetic-not-a-credential", client=client), max_calls=1)
        with pytest.raises(LLMBackendError, match="503"):
            judge.evaluate_claim("Synthetic source text.", "Synthetic claim text.")
    assert judge.call_count == len(requests) == 1


def _chunk(**overrides):
    return {
        "citation_id": "E1",
        "chunk_id": "synthetic-chunk-1",
        "document_id": "synthetic-document-1",
        "source_id": "synthetic-source-1",
        "source_title": "Synthetic source",
        "chunk_text": "Contenido de evidencia sintético.",
        "trust_level": "canonical",
        **overrides,
    }


def test_retrieval_metadata_reflects_actual_chat_pipeline_not_hybrid():
    """A3-G4: adapter must not claim hybrid dense or any specific retrieval modality."""
    auditor = ForensicAuditor(nli_judge=None)

    class CaptureUnits:
        def __init__(self):
            self.units = None

        def audit(self, payload):
            self.units = payload.request.packaged_context.packaged_units
            from study_engine.audit.contracts import ForensicAuditReport
            return ForensicAuditReport(
                audit_id="audit-synthetic", request_id=payload.request.request_id,
                notebook_id=payload.request.notebook_id,
                overall_verdict=AuditVerdict.APPROVED,
                audit_latency_ms=0.0, auditor_backend="capture",
            )

    capture = CaptureUnits()
    audit_generation_payload(
        capture,
        generated_text="Respuesta sintética [E1]",
        context_chunks=[_chunk(relevance_score=0.85)],
        query="consulta sintética",
        notebook_id="synthetic-academic-notebook",
    )
    unit = capture.units[0]
    # Adapter cannot know the retrieval modality; it must not claim one
    assert unit.retrieval_method == "adapter_packaged"
    assert unit.retrieval_score == 0.85
    assert unit.retrieval_rank == 1
    for misleading in ("hybrid", "vector", "lexical", "dense", "fts"):
        assert misleading not in unit.retrieval_method

    # Chunks without relevance_score (dialogue ConceptPacket strings) default to 0.0
    capture2 = CaptureUnits()
    audit_generation_payload(
        capture2,
        generated_text="Respuesta [E1]",
        context_chunks=[_chunk()],  # no relevance_score override
        query="consulta",
        notebook_id="synthetic-notebook",
    )
    unit2 = capture2.units[0]
    assert unit2.retrieval_score == 0.0
    assert unit2.retrieval_method == "adapter_packaged"



def test_q2_absolute_claim_is_blocked_by_real_s44_path_without_model_approval():
    class MisleadingBackend:
        model_name = "synthetic-judge"

        def __init__(self):
            self.calls = 0

        def complete(self, bundle):
            self.calls += 1
            raise AssertionError("The unsupported absolute must be rejected before NLI")

    backend = MisleadingBackend()
    auditor = ForensicAuditor(nli_judge=GeminiNLIJudge(backend))
    report = audit_generation_payload(
        auditor,
        generated_text=(
            "Si se reorganizan los archivos, las tablas y las consultas lógicas "
            "siguen funcionando exactamente igual [E1]."
        ),
        context_chunks=[_chunk(chunk_text=(
            "La independencia de datos física libera a las aplicaciones de "
            "conocer los detalles del almacenamiento y mejora su resistencia "
            "a cambios en la infraestructura."
        ))],
        query="¿Qué significa independencia física de datos?",
        notebook_id="synthetic-academic-notebook",
    )
    assert report.overall_verdict == AuditVerdict.REJECTED_UNSUPPORTED
    assert backend.calls == 0


def test_empty_evidence_is_rejected_before_audit():
    with pytest.raises(ValueError, match="At least one evidence chunk"):
        audit_generation_payload(
            ForensicAuditor(),
            generated_text="No hay evidencia.",
            context_chunks=[],
            query="synthetic query",
            notebook_id="synthetic-notebook",
        )


def test_identifier_only_chunk_is_not_converted_to_evidence():
    with pytest.raises(ValueError, match="missing provenance fields"):
        audit_generation_payload(
            ForensicAuditor(),
            generated_text="La afirmación se apoya en [E1].",
            context_chunks=["E1"],
            query="synthetic query",
            notebook_id="synthetic-notebook",
        )


def test_blank_content_is_not_replaced_with_a_placeholder():
    with pytest.raises(ValueError, match="no usable evidence content"):
        audit_generation_payload(
            ForensicAuditor(),
            generated_text="La afirmación se apoya en [E1].",
            context_chunks=[_chunk(chunk_text="  ")],
            query="synthetic query",
            notebook_id="synthetic-notebook",
        )


def test_zero_hash_placeholder_is_rejected_as_non_evidence():
    chunk = _chunk(content_hash="0" * 64)
    with pytest.raises(ValueError, match="content_hash"):
        audit_generation_payload(
            ForensicAuditor(),
            generated_text="La afirmación se apoya en [E1].",
            context_chunks=[chunk],
            query="synthetic query",
            notebook_id="synthetic-notebook",
        )


def test_missing_provenance_is_not_fabricated():
    chunk = _chunk()
    del chunk["source_id"]

    with pytest.raises(ValueError, match="source_id"):
        audit_generation_payload(
            ForensicAuditor(),
            generated_text="La afirmación se apoya en [E1].",
            context_chunks=[chunk],
            query="synthetic query",
            notebook_id="synthetic-notebook",
        )


def test_explicit_unverified_trust_is_preserved_by_the_audit():
    report = audit_generation_payload(
        ForensicAuditor(),
        generated_text="La afirmación sintética se apoya en el contexto [E1].",
        context_chunks=[_chunk(trust_level="unverified")],
        query="synthetic query",
        notebook_id="synthetic-notebook",
    )

    provenance_check = next(
        check
        for check in report.deterministic_checks
        if check.check_id == "CHECK_SOURCE_PROVENANCE"
    )
    assert provenance_check.status.value == "FAIL"
    assert report.overall_verdict.value == "UNVERIFIED_SOURCE"


def test_missing_trust_level_defaults_to_unverified():
    captured = {}
    chunk = _chunk()
    del chunk["trust_level"]

    class CapturingAuditor:
        def audit(self, audit_input):
            captured["input"] = audit_input
            return "captured"

    audit_generation_payload(
        CapturingAuditor(),
        generated_text="La afirmación sintética se apoya en el contexto [E1].",
        context_chunks=[chunk],
        query="synthetic query",
        notebook_id="synthetic-notebook",
    )

    citation = captured["input"].request.packaged_context.packaged_units[0].citation
    assert citation.trust_level == "unverified"

    report = audit_generation_payload(
        ForensicAuditor(),
        generated_text="La afirmación sintética se apoya en el contexto [E1].",
        context_chunks=[chunk],
        query="synthetic query",
        notebook_id="synthetic-notebook",
    )
    assert report.overall_verdict.value == "UNVERIFIED_SOURCE"


def test_missing_page_metadata_remains_missing_in_the_audit_manifest():
    captured = {}
    chunk = _chunk()
    chunk.pop("page_start", None)
    chunk.pop("page", None)
    chunk.pop("page_end", None)

    class CapturingAuditor:
        def audit(self, audit_input):
            captured["input"] = audit_input
            return "captured"

    audit_generation_payload(
        CapturingAuditor(),
        generated_text="Contenido sintético respaldado [E1].",
        context_chunks=[chunk],
        query="Consulta sintética",
        notebook_id="synthetic-notebook",
    )

    citation = captured["input"].request.packaged_context.packaged_units[0].citation
    assert citation.page_start is None
    assert citation.page_end is None


def test_unsupported_trust_vocabulary_is_not_accepted_as_canonical():
    class CapturingAuditor:
        def audit(self, audit_input):
            pytest.fail("auditor must not receive an unsupported trust level")

    with pytest.raises(ValueError, match="unsupported trust_level"):
        audit_generation_payload(
            CapturingAuditor(),
            generated_text="La afirmación sintética se apoya en el contexto [E1].",
            context_chunks=[_chunk(trust_level="verified")],
            query="synthetic query",
            notebook_id="synthetic-notebook",
        )


def test_auditor_rejects_trust_values_outside_its_contract():
    decision = GroundingDecision.SUPPORTED
    request = SimpleNamespace(
        request_id="request-1",
        notebook_id="synthetic-notebook",
        mode=GenerationMode.EXPLANATION,
        packaged_context=SimpleNamespace(
            packet=SimpleNamespace(grounding_decision=decision),
            citation_manifest=SimpleNamespace(
                records={
                    "E1": SimpleNamespace(
                        trust_level="verified",
                        source_id="synthetic-source-1",
                        content_hash="0" * 64,
                    )
                }
            ),
            packaged_units=[],
        ),
    )
    response = SimpleNamespace(
        request_id="request-1",
        notebook_id="synthetic-notebook",
        mode=GenerationMode.EXPLANATION,
        grounding_decision=decision,
        citations=[SimpleNamespace(citation_id="E1")],
    )

    checks = CitationVerifier().verify(
        SimpleNamespace(request=request, response=response)
    )

    provenance_check = next(
        check
        for check in checks
        if check.check_id == "CHECK_SOURCE_PROVENANCE"
    )
    assert provenance_check.status.value == "FAIL"


def test_complete_canonical_evidence_preserves_the_adapter_contract():
    captured = {}

    class CapturingAuditor:
        def audit(self, audit_input):
            captured["input"] = audit_input
            return "captured"

    result = audit_generation_payload(
        CapturingAuditor(),
        generated_text="La afirmación sintética se apoya en el contexto [E1].",
        context_chunks=[_chunk()],
        query="synthetic query",
        notebook_id="synthetic-notebook",
    )

    context = captured["input"].request.packaged_context
    unit = context.packaged_units[0]
    assert result == "captured"
    assert unit.content == "Contenido de evidencia sintético."
    assert unit.citation.source_id == "synthetic-source-1"
    assert unit.citation.trust_level == "canonical"


def test_complete_canonical_evidence_is_accepted_by_the_existing_auditor():
    report = audit_generation_payload(
        ForensicAuditor(),
        generated_text="La afirmación sintética se apoya en el contexto [E1].",
        context_chunks=[_chunk()],
        query="synthetic query",
        notebook_id="synthetic-notebook",
    )

    assert report.overall_verdict.value == "APPROVED"


def test_supplied_audit_request_identity_reaches_request_and_response():
    captured = {}

    class CapturingAuditor:
        def audit(self, audit_input):
            captured["input"] = audit_input
            return "captured"

    result = audit_generation_payload(
        CapturingAuditor(),
        generated_text="Contenido sintético [E1].",
        context_chunks=[_chunk()],
        query="synthetic query",
        notebook_id="synthetic-notebook",
        prompt_hash="a" * 64,
        request_id="req_current_execution",
    )

    assert result == "captured"
    assert captured["input"].request.request_id == "req_current_execution"
    assert captured["input"].response.request_id == "req_current_execution"
    assert captured["input"].response.text == "Contenido sintético [E1]."
    assert captured["input"].prompt_hash == "a" * 64


def test_real_audit_report_preserves_supplied_request_identity():
    report = audit_generation_payload(
        ForensicAuditor(),
        generated_text="La afirmación sintética se apoya en el contexto [E1].",
        context_chunks=[_chunk()],
        query="synthetic query",
        notebook_id="synthetic-notebook",
        prompt_hash="a" * 64,
        request_id="req_current_execution",
    )

    assert report.request_id == "req_current_execution"
    assert report.notebook_id == "synthetic-notebook"
    assert report.prompt_hash == "a" * 64
    assert report.audit_id


@pytest.mark.parametrize("request_id", ["", "   ", 42])
def test_invalid_supplied_request_identity_is_rejected(request_id):
    with pytest.raises(ValueError, match="request_id"):
        audit_generation_payload(
            ForensicAuditor(),
            generated_text="Contenido sintético [E1].",
            context_chunks=[_chunk()],
            query="synthetic query",
            notebook_id="synthetic-notebook",
            request_id=request_id,
        )
