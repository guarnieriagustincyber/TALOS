"""Adversarial and Contractual Test Suite for C5 Abstention / Trust Gate (Gate B).

Normative Reference: CP110 Audit, CP111 Implementation & Addendum Vinculante.
Contracts Verified:
  - D_C5_1: Perímetro de abstención pre-LLM (0 chunks / uncalibrated theta)
  - D_C5_2: Sufficiency Gate pre-LLM (RELATED ≠ SUFFICIENT)
  - D_C5_3: Representación explícita de evidencia conflictiva
  - D_C5_4: Fail-closed absoluto ante fallos de retrieval (RETRIEVAL_FAILURE -> 0 LLM)
  - D_C5_5: Universal Trust Gate (eliminación de bypass en OfflinePedagogicalBackend y fallbacks)
  - D_C5_6: Rescate conversacional condicionado a compatibilidad temática verificable
  - Invariantes Contractuales I1 - I8
  - Suite de Sobreconfianza OC-1 - OC-5
  - Fixtures C5-A - C5-J
"""

import asyncio
import json
import sqlite3
from typing import Any, AsyncGenerator, Dict, List, Optional
import pytest

from study_engine.context.c5_trust import (
    EpistemicTrustStatus,
    EpistemicTrustEvaluation,
    evaluate_epistemic_trust,
    evaluate_conversational_rescue_compatibility,
    detect_evidence_conflicts,
    extract_critical_query_terms,
    evaluate_term_coverage,
    RELEVANCE_THRESHOLD_STATUS,
)
from study_engine.contracts.generation import GenerationParameters
from study_engine.generation.prompts import PromptBundle, PromptMessage, PromptRole
from study_engine.pedagogy.contract import PedagogicalContract, ResponsePhase
from study_engine.pedagogy.structured_pipeline import (
    StructuredResponsePipeline,
    StreamEvent,
)
from study_engine.web.routes.chat import EpistemicContextPack
from study_engine.llm.offline_oracle import OfflinePedagogicalBackend
from study_engine.llm.multi_fallback import MultiFallbackBackend
from study_engine.storage.knowledge_store import KnowledgeStore


class MockRecordingBackend:
    """Mock backend that counts invocations and records prompts."""

    def __init__(self, response_text: str = "Respuesta simulada autorizada"):
        self.called = False
        self.call_count = 0
        self.last_bundle: Optional[PromptBundle] = None
        self.last_system_prompt: str = ""
        self.last_user_prompt: str = ""
        self.response_text = response_text

    async def stream(
        self,
        system_prompt: str = "",
        user_prompt: str = "",
        *args,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        self.called = True
        self.call_count += 1
        self.last_system_prompt = system_prompt
        self.last_user_prompt = user_prompt
        for word in self.response_text.split():
            yield word + " "

    def complete(self, prompt_bundle: PromptBundle) -> Any:
        self.called = True
        self.call_count += 1
        self.last_bundle = prompt_bundle
        if prompt_bundle.system_instruction:
            self.last_system_prompt = prompt_bundle.system_instruction
        if prompt_bundle.messages:
            self.last_user_prompt = prompt_bundle.messages[0].content
        from study_engine.llm.backends import ProviderCompletion
        from study_engine.contracts.generation import TokenUsage
        return ProviderCompletion(
            text=self.response_text,
            latency_ms=10.0,
            tokens_used=TokenUsage(prompt_tokens=50, completion_tokens=50, total_tokens=100),
            model="mock-recording-backend",
        )


@pytest.fixture
def mock_backend():
    return MockRecordingBackend()


@pytest.fixture
def test_contract():
    return PedagogicalContract(
        contract_id="c5-test-contract",
        notebook_id="fase0-soc",
        response_phases=[
            ResponsePhase(
                phase_id="conceptual",
                phase_prompt_template="Fase conceptual para: {user_query}",
                max_tokens=1200,
            )
        ],
        base_system_prompt="Sistema tutor socrático formal de Sistemas Operativos.",
    )


@pytest.fixture
def pipeline(test_contract, mock_backend):
    return StructuredResponsePipeline(
        contract=test_contract,
        llm_backend=mock_backend,
    )


@pytest.fixture
def store():
    return KnowledgeStore("data/web_state/knowledge_store.db")


# ==============================================================================
# 1. FIXTURES ADVERSARIALES OBLIGATORIAS (C5-A a C5-J)
# ==============================================================================

@pytest.mark.anyio
async def test_fixture_c5_a_ood_detection(store, pipeline, mock_backend):
    """C5-A: Detección OOD (regex, semántico, vocabulario compartido y multi-turn) -> 0 LLM."""
    # 1. Regex OOD
    q_regex = "¿Quién ganó el mundial de fútbol de 1986?"
    res_regex = store.search(q_regex, notebook_id="fase0-soc", limit=3)
    eval_regex = evaluate_epistemic_trust(q_regex, res_regex)
    assert eval_regex.abstained is True
    assert eval_regex.is_sufficient is False
    assert eval_regex.status in (EpistemicTrustStatus.NO_EVIDENCE, EpistemicTrustStatus.NO_AUTHORIZED_EVIDENCE)

    # 2. OOD Semántico
    q_sem = "Fotosíntesis oxigénica en plantas y ciclo de Calvin"
    res_sem = store.search(q_sem, notebook_id="fase0-soc", limit=3)
    eval_sem = evaluate_epistemic_trust(q_sem, res_sem)
    assert eval_sem.abstained is True
    assert eval_sem.is_sufficient is False

    # 3. OOD con vocabulario compartido (Napoleón y memoria)
    q_shared = "La memoria histórica de las batallas de Napoleón Bonaparte"
    res_shared = store.search(q_shared, notebook_id="fase0-soc", limit=3)
    eval_shared = evaluate_epistemic_trust(q_shared, res_shared)
    assert eval_shared.abstained is True
    assert eval_shared.is_sufficient is False
    assert "napoleon" in eval_shared.missing_critical_terms or "bonaparte" in eval_shared.missing_critical_terms

    # Demostración explícita de 0 llamadas al LLM en pipeline para cada caso OOD
    for q, eval_obj in [(q_regex, eval_regex), (q_sem, eval_sem), (q_shared, eval_shared)]:
        pack = EpistemicContextPack(
            formatted_context="",
            citations=[],
            chunks=[],
            abstained=True,
            abstention_reason=eval_obj.abstention_reason or "QUERY_OUT_OF_SCOPE",
            trust_status=eval_obj.status,
            is_sufficient=False,
        )
        events = [e async for e in pipeline.generate_phased_response(q, context_pack=pack)]
        assert any(e.event_type == "abstention" for e in events)
        assert mock_backend.called is False
        assert mock_backend.call_count == 0


@pytest.mark.anyio
async def test_fixture_c5_b_zero_evidence_fail_closed(pipeline, mock_backend):
    """C5-B: Cero evidencia -> abstención inmediata -> 0 llamadas al LLM."""
    pack = EpistemicContextPack(
        formatted_context="",
        citations=[],
        chunks=[],
        abstained=True,
        abstention_reason="QUERY_OUT_OF_SCOPE",
        trust_status=EpistemicTrustStatus.NO_EVIDENCE,
        is_sufficient=False,
    )
    events = []
    async for ev in pipeline.generate_phased_response(
        user_query="Consulta sin ningún chunk en corpus",
        context_pack=pack,
    ):
        events.append(ev)

    assert any(e.event_type == "abstention" for e in events)
    assert not any(e.event_type == "phase_token" for e in events)
    assert mock_backend.called is False
    assert mock_backend.call_count == 0


@pytest.mark.anyio
async def test_fixture_c5_c_low_relevance_abstention(pipeline, mock_backend):
    """C5-C: Low relevance / chunks irrelevantes -> abstención -> 0 llamadas al LLM."""
    # Chunk irrelevante con coincidencia accidental de palabra vacía o periférica
    weak_chunk = {"chunk_text": "El color azul del cielo en una tarde despejada.", "source_id": "src1", "score": 0.12}
    eval_res = evaluate_epistemic_trust("Algoritmo de planificación Round Robin", [weak_chunk])
    assert eval_res.abstained is True
    assert eval_res.is_sufficient is False
    assert eval_res.status == EpistemicTrustStatus.RELATED_INSUFFICIENT

    pack = EpistemicContextPack(
        formatted_context="",
        citations=[],
        chunks=[weak_chunk],
        abstained=True,
        abstention_reason="QUERY_OUT_OF_SCOPE",
        trust_status=eval_res.status,
        is_sufficient=False,
    )
    events = []
    async for ev in pipeline.generate_phased_response(
        user_query="Algoritmo de planificación Round Robin",
        context_pack=pack,
    ):
        events.append(ev)

    assert any(e.event_type == "abstention" for e in events)
    assert mock_backend.called is False


@pytest.mark.anyio
async def test_fixture_c5_d_unauthorized_evidence_rejected(pipeline, mock_backend):
    """C5-D: Evidencia foránea/no autorizada -> rechazada -> C2/C4 preservados -> 0 LLM."""
    eval_res = evaluate_epistemic_trust(
        query="Explicá modulación QAM",
        raw_chunks=[],
        scope_authorized=False,
        scope_error_reason="SCOPE_UNAUTHORIZED",
    )
    assert eval_res.abstained is True
    assert eval_res.is_sufficient is False
    assert eval_res.status == EpistemicTrustStatus.NO_AUTHORIZED_EVIDENCE

    pack = EpistemicContextPack(
        formatted_context="",
        citations=[],
        chunks=[],
        abstained=True,
        abstention_reason="SCOPE_UNAUTHORIZED",
        trust_status=EpistemicTrustStatus.NO_AUTHORIZED_EVIDENCE,
        is_sufficient=False,
    )
    events = []
    async for ev in pipeline.generate_phased_response(
        user_query="Explicá modulación QAM",
        context_pack=pack,
    ):
        events.append(ev)

    assert any(e.event_type == "abstention" for e in events)
    assert mock_backend.called is False


@pytest.mark.anyio
async def test_fixture_c5_e_conflicting_evidence_representation(pipeline, mock_backend):
    """C5-E: Evidencia contradictoria entre fuentes autorizadas -> explícitamente representada."""
    conflicting_chunks = [
        {
            "chunk_text": "En la arquitectura Mach, el núcleo es microkernel puro y no es posible la ejecución monolítica.",
            "source_id": "src_tanenbaum_os",
            "score": 0.90,
        },
        {
            "chunk_text": "En sistemas contemporáneos derivados, es posible la ejecución en modo híbrido monolítico.",
            "source_id": "src_stallings_os",
            "score": 0.88,
        },
    ]
    eval_res = evaluate_epistemic_trust("¿La arquitectura Mach es microkernel puro?", conflicting_chunks)
    assert eval_res.is_conflicting is True
    assert eval_res.status == EpistemicTrustStatus.CONFLICTING_EVIDENCE
    assert eval_res.is_sufficient is True  # Puede generarse pero con contraste explícito

    banner = f"=== EVIDENCIA CONFLICTIVA ENTRE FUENTES AUTORIZADAS ===\n{eval_res.conflict_details}\n"
    pack = EpistemicContextPack(
        formatted_context=banner + "Detalles de fuentes...",
        citations=["src_tanenbaum_os", "src_stallings_os"],
        chunks=conflicting_chunks,
        abstained=False,
        trust_status=eval_res.status,
        is_sufficient=True,
        is_conflicting=True,
        conflict_details=eval_res.conflict_details,
    )
    events = []
    async for ev in pipeline.generate_phased_response(
        user_query="¿La arquitectura Mach es microkernel puro?",
        context_pack=pack,
    ):
        events.append(ev)

    assert any(e.event_type == "phase_start" for e in events)
    assert mock_backend.called is True
    assert "EVIDENCIA CONFLICTIVA" in mock_backend.last_user_prompt


@pytest.mark.anyio
async def test_fixture_c5_f_citation_mismatch_prevents_grounding():
    """C5-F: Cita [E99] no puede inventar grounding ni sustituir al pre-LLM trust gate."""
    from study_engine.pedagogy.citation_validator import CitationValidator, StreamCitationBuffer

    validator = CitationValidator()
    raw_chunks = [{"id": "E1"}, {"id": "E2"}]
    buffer = StreamCitationBuffer(validator=validator, raw_chunks=raw_chunks, strip_invalid=True)

    # Inyección de afirmación no fundamentada con cita inventada
    tokens = ["La", " paginación", " se", " inventó", " en", " 1492", " [E99]."]
    emitted = []
    for tok in tokens:
        emitted.extend(buffer.process_token(tok))

    result_text = "".join(emitted)
    # [E99] is stripped / rewritten, but stripping DOES NOT make the historical claim grounded
    assert "[E99]" not in result_text


@pytest.mark.anyio
async def test_fixture_c5_g_retrieval_failure_fails_closed(pipeline, mock_backend):
    """C5-G: Excepción en retrieval -> RETRIEVAL_FAILURE -> fail-closed -> 0 LLM."""
    pack = EpistemicContextPack(
        formatted_context="",
        citations=[],
        chunks=[],
        abstained=True,
        abstention_reason="RETRIEVAL_FAILURE",
        trust_status=EpistemicTrustStatus.RETRIEVAL_FAILURE,
        is_sufficient=False,
    )
    events = []
    async for ev in pipeline.generate_phased_response(
        user_query="Explicá llamadas al sistema",
        context_pack=pack,
    ):
        events.append(ev)

    error_events = [e for e in events if e.event_type == "error"]
    assert len(error_events) >= 1
    assert error_events[0].payload.get("error_code") == "RETRIEVAL_FAILURE"
    assert mock_backend.called is False
    assert mock_backend.call_count == 0


@pytest.mark.anyio
async def test_fixture_c5_h_provider_failure_maintains_trust_gate(pipeline, mock_backend):
    """C5-H: Fallback provider no permite eludir el Trust Gate de C5 -> 0 LLM."""
    fallback_backend = MultiFallbackBackend(providers=[("mock", mock_backend)])
    pipe_with_fallback = StructuredResponsePipeline(
        contract=pipeline.contract,
        llm_backend=fallback_backend,
    )
    pack = EpistemicContextPack(
        formatted_context="",
        citations=[],
        chunks=[],
        abstained=True,
        abstention_reason="QUERY_OUT_OF_SCOPE",
        trust_status=EpistemicTrustStatus.NO_EVIDENCE,
        is_sufficient=False,
    )
    events = [e async for e in pipe_with_fallback.generate_phased_response("Q", context_pack=pack)]
    assert any(e.event_type == "abstention" for e in events)
    assert mock_backend.called is False
    assert mock_backend.call_count == 0


@pytest.mark.anyio
async def test_fixture_c5_i_offline_oracle_universal_trust_gate(pipeline):
    """C5-I: OfflinePedagogicalBackend bloqueado ante pack abstención (0 bypass)."""
    offline_backend = OfflinePedagogicalBackend()
    pipe_with_offline = StructuredResponsePipeline(
        contract=pipeline.contract,
        llm_backend=offline_backend,
    )

    pack = EpistemicContextPack(
        formatted_context="",
        citations=[],
        chunks=[],
        abstained=True,
        abstention_reason="QUERY_OUT_OF_SCOPE",
        trust_status=EpistemicTrustStatus.NO_EVIDENCE,
        is_sufficient=False,
    )

    events = []
    async for ev in pipe_with_offline.generate_phased_response(
        user_query="Pregunta sobre astronomía",
        context_pack=pack,
    ):
        events.append(ev)

    assert any(e.event_type == "abstention" for e in events)
    assert not any(e.event_type == "phase_token" for e in events)


@pytest.mark.anyio
async def test_fixture_c5_j_zero_chunks_fallback_citations_fail_closed(pipeline, mock_backend):
    """C5-J: 0 chunks reales -> 0 citas inventadas -> abstención total -> 0 LLM."""
    pack = EpistemicContextPack(
        formatted_context="",
        citations=[],
        chunks=[],
        abstained=True,
        abstention_reason="QUERY_OUT_OF_SCOPE",
        trust_status=EpistemicTrustStatus.NO_EVIDENCE,
        is_sufficient=False,
    )
    events = []
    async for ev in pipeline.generate_phased_response(
        user_query="Consulta sin chunks",
        context_pack=pack,
    ):
        events.append(ev)

    assert any(e.event_type == "abstention" for e in events)
    assert mock_backend.called is False


# ==============================================================================
# 2. OVERCONFIDENCE SUITE (OC-1 a OC-5: RELATED ≠ SUFFICIENT)
# ==============================================================================

@pytest.mark.anyio
async def test_oc_1_rowhammer_sufficiency(store, pipeline, mock_backend):
    """OC-1: Rowhammer en DRAM -> evidencia parcial sobre DRAM/memoria != suficiente -> 0 LLM."""
    q = "ataque Rowhammer en memoria DRAM y mitigaciones"
    chunks = store.search(q, notebook_id="fase0-soc", limit=3)
    eval_res = evaluate_epistemic_trust(q, chunks)
    assert eval_res.abstained is True
    assert eval_res.is_sufficient is False
    assert eval_res.status == EpistemicTrustStatus.RELATED_INSUFFICIENT
    assert "rowhammer" in eval_res.missing_critical_terms

    pack = EpistemicContextPack(
        formatted_context="",
        citations=[],
        chunks=chunks,
        abstained=True,
        abstention_reason=eval_res.abstention_reason or "RELATED_INSUFFICIENT",
        trust_status=eval_res.status,
        is_sufficient=False,
    )
    events = [e async for e in pipeline.generate_phased_response(q, context_pack=pack)]
    assert any(e.event_type == "abstention" for e in events)
    assert mock_backend.called is False
    assert mock_backend.call_count == 0


@pytest.mark.anyio
async def test_oc_2_halting_problem_banquier_sufficiency(store, pipeline, mock_backend):
    """OC-2: Problema de la parada en Algoritmo del Banquero -> insuficiente -> 0 LLM."""
    q = "problema de la parada en el algoritmo del banquero"
    chunks = store.search(q, notebook_id="fase0-soc", limit=3)
    eval_res = evaluate_epistemic_trust(q, chunks)
    assert eval_res.abstained is True
    assert eval_res.is_sufficient is False
    assert "banquero" in eval_res.missing_critical_terms or "parada" in eval_res.missing_critical_terms

    pack = EpistemicContextPack(
        formatted_context="",
        citations=[],
        chunks=chunks,
        abstained=True,
        abstention_reason=eval_res.abstention_reason or "RELATED_INSUFFICIENT",
        trust_status=eval_res.status,
        is_sufficient=False,
    )
    events = [e async for e in pipeline.generate_phased_response(q, context_pack=pack)]
    assert any(e.event_type == "abstention" for e in events)
    assert mock_backend.called is False
    assert mock_backend.call_count == 0


@pytest.mark.anyio
async def test_oc_3_nagle_paging_sufficiency(store, pipeline, mock_backend):
    """OC-3: Algoritmo de Nagle en paginación -> insuficiente -> 0 LLM."""
    q = "algoritmo de Nagle en la paginación por demanda"
    chunks = store.search(q, notebook_id="fase0-soc", limit=3)
    eval_res = evaluate_epistemic_trust(q, chunks)
    assert eval_res.abstained is True
    assert eval_res.is_sufficient is False
    assert "nagle" in eval_res.missing_critical_terms

    pack = EpistemicContextPack(
        formatted_context="",
        citations=[],
        chunks=chunks,
        abstained=True,
        abstention_reason=eval_res.abstention_reason or "RELATED_INSUFFICIENT",
        trust_status=eval_res.status,
        is_sufficient=False,
    )
    events = [e async for e in pipeline.generate_phased_response(q, context_pack=pack)]
    assert any(e.event_type == "abstention" for e in events)
    assert mock_backend.called is False
    assert mock_backend.call_count == 0


@pytest.mark.anyio
async def test_oc_4_synthetic_statistic_sufficiency(store, pipeline, mock_backend):
    """OC-4: Fragmentación externa en Linux exactamente 42.5% -> no verificada -> 0 LLM."""
    q = "fragmentación externa en linux exactamente 42.5%"
    chunks = store.search(q, notebook_id="fase0-soc", limit=3)
    eval_res = evaluate_epistemic_trust(q, chunks)
    assert eval_res.abstained is True
    assert eval_res.is_sufficient is False
    assert any("42.5" in m or "%" in m for m in eval_res.missing_critical_terms)

    pack = EpistemicContextPack(
        formatted_context="",
        citations=[],
        chunks=chunks,
        abstained=True,
        abstention_reason=eval_res.abstention_reason or "RELATED_INSUFFICIENT",
        trust_status=eval_res.status,
        is_sufficient=False,
    )
    events = [e async for e in pipeline.generate_phased_response(q, context_pack=pack)]
    assert any(e.event_type == "abstention" for e in events)
    assert mock_backend.called is False
    assert mock_backend.call_count == 0


@pytest.mark.anyio
async def test_oc_5_cve_vulnerability_sufficiency(store, pipeline, mock_backend):
    """OC-5: Vulnerabilidad CVE-2024-1086 en nftables del kernel -> fuera de alcance -> 0 LLM."""
    q = "vulnerabilidad CVE-2024-1086 en nftables del kernel"
    chunks = store.search(q, notebook_id="fase0-soc", limit=3)
    eval_res = evaluate_epistemic_trust(q, chunks)
    assert eval_res.abstained is True
    assert eval_res.is_sufficient is False
    assert any("1086" in m or "nftabl" in m for m in eval_res.missing_critical_terms)

    pack = EpistemicContextPack(
        formatted_context="",
        citations=[],
        chunks=chunks,
        abstained=True,
        abstention_reason=eval_res.abstention_reason or "RELATED_INSUFFICIENT",
        trust_status=eval_res.status,
        is_sufficient=False,
    )
    events = [e async for e in pipeline.generate_phased_response(q, context_pack=pack)]
    assert any(e.event_type == "abstention" for e in events)
    assert mock_backend.called is False
    assert mock_backend.call_count == 0


# ==============================================================================
# 3. INVARIANTES CONTRACTUALES (I1 a I8)
# ==============================================================================

@pytest.mark.anyio
async def test_invariant_i1_no_evidence_no_llm(pipeline, mock_backend):
    """I1: NO_AUTHORIZED_SUFFICIENT_EVIDENCE -> NO_LLM_CALL."""
    pack = EpistemicContextPack(
        formatted_context="",
        citations=[],
        chunks=[],
        abstained=True,
        abstention_reason="QUERY_OUT_OF_SCOPE",
        trust_status=EpistemicTrustStatus.NO_EVIDENCE,
        is_sufficient=False,
    )
    async for _ in pipeline.generate_phased_response("Q", context_pack=pack):
        pass
    assert mock_backend.called is False
    assert mock_backend.call_count == 0


@pytest.mark.anyio
async def test_invariant_i2_retrieval_failure_no_llm(pipeline, mock_backend):
    """I2: RETRIEVAL_FAILURE -> NO_LLM_CALL."""
    pack = EpistemicContextPack(
        formatted_context="",
        citations=[],
        chunks=[],
        abstained=True,
        abstention_reason="RETRIEVAL_FAILURE",
        trust_status=EpistemicTrustStatus.RETRIEVAL_FAILURE,
        is_sufficient=False,
    )
    async for _ in pipeline.generate_phased_response("Q", context_pack=pack):
        pass
    assert mock_backend.called is False
    assert mock_backend.call_count == 0


@pytest.mark.anyio
async def test_invariant_incomplete_context_pack_fails_closed(pipeline, mock_backend):
    """Context pack incompleto o sin atributos -> fail-closed inmediato (Addendum 2) -> 0 llamadas al LLM."""
    class EmptyContextPack:
        pass

    events = [e async for e in pipeline.generate_phased_response("Q", context_pack=EmptyContextPack())]
    assert any(e.event_type == "abstention" for e in events)
    assert mock_backend.called is False
    assert mock_backend.call_count == 0


@pytest.mark.anyio
async def test_invariant_i3_abstained_pack_no_backend_bypass(pipeline):
    """I3: ABSTAINED_CONTEXT_PACK -> NO_BACKEND_BYPASS (Cloud, Fallback, Offline)."""
    offline = OfflinePedagogicalBackend()
    pipe = StructuredResponsePipeline(contract=pipeline.contract, llm_backend=offline)
    pack = EpistemicContextPack(
        formatted_context="",
        citations=[],
        chunks=[],
        abstained=True,
        trust_status=EpistemicTrustStatus.NO_EVIDENCE,
        is_sufficient=False,
    )
    events = [e async for e in pipe.generate_phased_response("Q", context_pack=pack)]
    assert any(e.event_type == "abstention" for e in events)


@pytest.mark.anyio
async def test_invariant_i4_c5_pass_c3_still_enforced(pipeline, mock_backend):
    """I4: C5_PASS -> C3_STILL_ENFORCED (Presupuesto efectivo <= 4761 tokens)."""
    huge_valid_evidence = "[Fuente: SOC] " + ("La memoria virtual divide el espacio. " * 800)
    pack = EpistemicContextPack(
        formatted_context=huge_valid_evidence,
        citations=["SOC"],
        chunks=[{"chunk_text": huge_valid_evidence, "source_id": "SOC", "score": 0.95}],
        abstained=False,
        trust_status=EpistemicTrustStatus.SUFFICIENT_EVIDENCE,
        is_sufficient=True,
    )
    async for _ in pipeline.generate_phased_response(
        user_query="Explicá memoria virtual",
        context_pack=pack,
    ):
        pass

    assert mock_backend.called is True
    from study_engine.context.c3_budget import (
        estimate_payload_tokens,
        EFFECTIVE_CONTEXT_CEILING_TOKENS,
    )
    tokens = estimate_payload_tokens(mock_backend.last_system_prompt, mock_backend.last_user_prompt)
    assert tokens <= EFFECTIVE_CONTEXT_CEILING_TOKENS


def test_invariant_i5_c2_rejected_source_cannot_enter_c5():
    """I5: C2_REJECTED_SOURCE -> C5_CANNOT_USE_IT."""
    eval_res = evaluate_epistemic_trust(
        query="Punteros en C",
        raw_chunks=[],
        scope_authorized=False,
        scope_error_reason="SOURCE_EXCLUDED_BY_ACL",
    )
    assert eval_res.abstained is True
    assert eval_res.status == EpistemicTrustStatus.NO_AUTHORIZED_EVIDENCE


def test_invariant_i6_c4_foreign_source_cannot_enter_c5():
    """I6: C4_FOREIGN_SOURCE -> C5_CANNOT_USE_IT."""
    eval_res = evaluate_epistemic_trust(
        query="Telecomunicaciones FADENA en cuaderno SOC",
        raw_chunks=[],
        scope_authorized=False,
        scope_error_reason="CROSS_CURRICULAR_ISOLATION_VIOLATION",
    )
    assert eval_res.abstained is True
    assert eval_res.status == EpistemicTrustStatus.NO_AUTHORIZED_EVIDENCE


def test_invariant_i7_invalid_citation_not_grounding():
    """I7: INVALID_CITATION != VALID_GROUNDING."""
    from study_engine.pedagogy.citation_validator import CitationValidator
    validator = CitationValidator()
    raw_chunks = [{"id": "E1"}]
    text = "Afirmación inventada sin sustento [E99]."
    corrected, invalid = validator.validate_and_rewrite(text, raw_chunks)
    assert "[E99]" in invalid
    assert "[ref. no verificada]" in corrected or "[E99]" not in corrected


def test_invariant_i8_post_stream_audit_not_pre_llm_trust_gate():
    """I8: POST_STREAM_AUDIT != PRE_LLM_TRUST_GATE."""
    # Pre-LLM decision is reached before generating any tokens
    eval_res = evaluate_epistemic_trust("fotosíntesis", [])
    assert eval_res.abstained is True
    assert eval_res.is_sufficient is False


# ==============================================================================
# 4. PRUEBAS DE RESCATE CONVERSACIONAL Y CONTINUIDAD (D_C5_6)
# ==============================================================================

def test_conversational_rescue_same_topic():
    """Rescate conversacional admitido en seguimiento deíctico dentro del mismo tema."""
    class MockPack:
        formatted_context = "Memoria virtual, páginas, marcos y tabla de páginas en x86."

    chunks = [{"content": "Paginación y MMU"}]
    is_compat, msg = evaluate_conversational_rescue_compatibility("¿y qué pasa con las páginas?", MockPack(), chunks)
    assert is_compat is True


def test_conversational_rescue_topic_switch_rejected():
    """Rescate conversacional rechazado ante cambio brusco de tema u OOD."""
    class MockPack:
        formatted_context = "Memoria virtual y paginación."

    chunks = [{"content": "Paginación y MMU"}]
    is_compat, msg = evaluate_conversational_rescue_compatibility("¿Qué es la fotosíntesis oxigénica?", MockPack(), chunks)
    assert is_compat is False
    assert "Incompatibilidad temática total" in msg


def test_conversational_rescue_pure_deictic():
    """Rescate conversacional admitido en consulta meramente deíctica."""
    class MockPack:
        formatted_context = "Memoria virtual y paginación."

    chunks = [{"content": "Paginación y MMU"}]
    is_compat, msg = evaluate_conversational_rescue_compatibility("¿y eso por qué ocurre ahí?", MockPack(), chunks)
    assert is_compat is True


def test_conversational_rescue_generic_followup_uses_resolved_context():
    class MockPack:
        formatted_context = "Punteros en C y operación swap."

    chunks = [{"content": "Punteros y swap"}]
    is_compat, _ = evaluate_conversational_rescue_compatibility(
        "podes detallarme mas?",
        MockPack(),
        chunks,
        contextual_query="¿Cómo se implementa el swap con punteros en C? podes detallarme mas?",
        topic_query="mas?",
    )

    assert is_compat is True


def test_conversational_rescue_rejects_new_topic_in_generic_followup():
    class MockPack:
        formatted_context = "Punteros en C y operación swap."

    chunks = [{"content": "Punteros y swap"}]
    is_compat, _ = evaluate_conversational_rescue_compatibility(
        "podes detallarme mas sobre fotosíntesis?",
        MockPack(),
        chunks,
        contextual_query="¿Cómo se implementa el swap con punteros en C? podes detallarme mas sobre fotosíntesis?",
        topic_query="mas sobre fotosíntesis?",
    )

    assert is_compat is False
