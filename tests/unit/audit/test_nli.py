"""Unit tests for NLI judge and aggregator in Subsystem S4.4."""

import pytest

from study_engine.audit.contracts import (
    AuditVerdict,
    ClaimSupportVerdict,
    ClaimType,
    ClaimVerification,
    LexicalAnomalyStatus,
    LexicalDiagnostics,
)
from study_engine.audit.nli import (
    GeminiNLIJudge, MockNLIJudge, NLIAggregator, UnavailableNLIJudge,
)
from study_engine.llm.backends import ProviderCompletion


def _make_dummy_claim_verification(
    verdict: ClaimSupportVerdict,
) -> ClaimVerification:
    diag = LexicalDiagnostics(
        status=LexicalAnomalyStatus.NO_ANOMALY,
        token_overlap_ratio=0.8,
    )
    return ClaimVerification(
        claim_index=0,
        claim_text="Afirmación evaluada.",
        claim_type=ClaimType.FACTUAL,
        cited_tags=("E1",),
        lexical_diagnostics=diag,
        nli_verdict=verdict,
    )


def test_mock_nli_default_behavior():
    """Verify default mock judge returns configured default verdict."""
    judge = MockNLIJudge(default_verdict=ClaimSupportVerdict.ENTAILED)
    res = judge.evaluate_claim(premise="P", hypothesis="H")
    assert res.verdict == ClaimSupportVerdict.ENTAILED
    assert res.confidence == 0.90


def test_mock_nli_canned_verdict():
    """Verify mock judge dispatches canned verdicts based on match."""
    canned = {
        "contradictorio": ClaimSupportVerdict.CONTRADICTED,
        "sin_sustento": ClaimSupportVerdict.NOT_ENTAILED,
    }
    judge = MockNLIJudge(canned_verdicts=canned)

    res1 = judge.evaluate_claim(
        premise="P", hypothesis="Esto es contradictorio."
    )
    assert res1.verdict == ClaimSupportVerdict.CONTRADICTED

    res2 = judge.evaluate_claim(premise="P", hypothesis="Dato sin_sustento.")
    assert res2.verdict == ClaimSupportVerdict.NOT_ENTAILED


def test_mock_nli_inject_error():
    """Verify error injection causes evaluate_claim to raise."""
    judge = MockNLIJudge(inject_error=RuntimeError("Judge offline"))
    with pytest.raises(RuntimeError) as exc_info:
        judge.evaluate_claim(premise="P", hypothesis="H")
    assert "Judge offline" in str(exc_info.value)


def test_nli_aggregator_rules():
    """Verify formal aggregation policy: CONTRADICTION > NOT_ENTAILED."""
    agg = NLIAggregator()

    # 1. Empty verifications -> APPROVED
    assert agg.aggregate([]) == AuditVerdict.APPROVED

    # 2. All entailed -> APPROVED
    c_ent = _make_dummy_claim_verification(ClaimSupportVerdict.ENTAILED)
    assert agg.aggregate([c_ent, c_ent]) == AuditVerdict.APPROVED

    # 3. Any contradicted -> REJECTED_CONTRADICTION
    c_con = _make_dummy_claim_verification(ClaimSupportVerdict.CONTRADICTED)
    c_not = _make_dummy_claim_verification(ClaimSupportVerdict.NOT_ENTAILED)
    c_partial = _make_dummy_claim_verification(ClaimSupportVerdict.PARTIALLY_SUPPORTED)
    c_generalized = _make_dummy_claim_verification(ClaimSupportVerdict.UNSUPPORTED_GENERALIZATION)
    c_una = _make_dummy_claim_verification(ClaimSupportVerdict.UNASSESSED)
    assert (
        agg.aggregate([c_ent, c_con, c_not])
        == AuditVerdict.REJECTED_CONTRADICTION
    )

    # 4. Any not entailed without contradiction -> REJECTED_UNSUPPORTED
    assert (
        agg.aggregate([c_ent, c_not, c_una])
        == AuditVerdict.REJECTED_UNSUPPORTED
    )
    assert agg.aggregate([c_ent, c_partial]) == AuditVerdict.REJECTED_UNSUPPORTED
    assert agg.aggregate([c_ent, c_generalized]) == AuditVerdict.REJECTED_UNSUPPORTED

    assert agg.aggregate([c_ent, c_una]) == AuditVerdict.FLAGGED_UNASSESSED


class _StructuredBackend:
    model_name = "synthetic-semantic-model"

    def __init__(self, output: str):
        self.output = output
        self.calls = []

    def complete(self, prompt_bundle):
        self.calls.append(prompt_bundle)
        return ProviderCompletion(
            text=self.output, latency_ms=1.0, model=self.model_name,
        )


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("ENTAILED", ClaimSupportVerdict.ENTAILED),
        ("PARTIAL", ClaimSupportVerdict.PARTIALLY_SUPPORTED),
        ("PARTIALLY_SUPPORTED", ClaimSupportVerdict.PARTIALLY_SUPPORTED),
        ("UNSUPPORTED_GENERALIZATION", ClaimSupportVerdict.UNSUPPORTED_GENERALIZATION),
        ("NOT_ENTAILED", ClaimSupportVerdict.NOT_ENTAILED),
        ("CONTRADICTED", ClaimSupportVerdict.CONTRADICTED),
        ("UNASSESSED", ClaimSupportVerdict.UNASSESSED),
    ],
)
def test_structured_semantic_labels_are_fail_closed(label, expected):
    backend = _StructuredBackend(
        '{"verdict":"' + label + '","rationale":"Source comparison"}'
    )
    result = GeminiNLIJudge(backend).evaluate_claim(
        "Changing physical storage need not change the logical schema.",
        "The logical schema need not change with physical storage.",
    )
    assert result.verdict == expected
    assert len(backend.calls) == 1
    assert "logical schema" in backend.calls[0].messages[0].content
    assert "absolute words" in backend.calls[0].system_prompt
    # Short list labels must be assessable as enumeration items, not as
    # malformed full sentences.
    assert "short label" in backend.calls[0].system_prompt


@pytest.mark.parametrize("output", ["not json", "{}", '{"verdict":"ENTAILED"}',
                                        '{"verdict":"PASS","rationale":"yes"}'])
def test_malformed_semantic_answer_cannot_approve(output):
    with pytest.raises(ValueError, match="Invalid structured semantic assessment"):
        GeminiNLIJudge(_StructuredBackend(output)).evaluate_claim("P", "H")


def test_single_json_fence_from_provider_is_accepted_without_extra_prose():
    backend = _StructuredBackend(
        '```json\n{"verdict":"NOT_ENTAILED","rationale":"The source is narrower."}\n```'
    )
    result = GeminiNLIJudge(backend).evaluate_claim("Some changes are tolerated.", "All changes are tolerated.")
    assert result.verdict == ClaimSupportVerdict.NOT_ENTAILED


def test_semantic_judge_budget_and_empty_evidence_fail_closed():
    backend = _StructuredBackend('{"verdict":"ENTAILED","rationale":"ok"}')
    judge = GeminiNLIJudge(backend, max_calls=1)
    assert judge.evaluate_claim("", "claim").verdict == ClaimSupportVerdict.UNASSESSED
    assert judge.evaluate_claim("source", "claim").verdict == ClaimSupportVerdict.ENTAILED
    assert judge.evaluate_claim("source", "new claim").verdict == ClaimSupportVerdict.UNASSESSED
    assert len(backend.calls) == 1
    assert judge.call_count == 1
    assert UnavailableNLIJudge().evaluate_claim("P", "H").verdict == ClaimSupportVerdict.UNASSESSED


@pytest.mark.parametrize("claim", [
    "Las consultas funcionan exactamente igual tras cambiar el hardware.",
    "Los índices garantizan la misma ejecución después del cambio.",
    "The application always behaves identically after migration.",
    "El rendimiento nunca cambia después de reorganizar los archivos.",
])
def test_unsupported_absolute_scope_is_rejected_before_model_call(claim):
    backend = _StructuredBackend('{"verdict":"ENTAILED","rationale":"looks related"}')
    judge = GeminiNLIJudge(backend)
    source = (
        "La independencia de datos física libera a las aplicaciones de la necesidad "
        "de conocer los detalles de almacenamiento y mejora su resistencia a cambios."
    )
    result = judge.evaluate_claim(source, claim)
    assert result.verdict == ClaimSupportVerdict.UNSUPPORTED_GENERALIZATION
    assert not backend.calls


def test_q2_absolute_equivalence_is_not_inferred_from_physical_independence():
    source_excerpt = (
        "La abstracción liberó a las aplicaciones de la necesidad de conocer "
        "los detalles del almacenamiento físico. Esta desvinculación mejoró "
        "la flexibilidad y las hizo más resistentes a los cambios en la "
        "infraestructura de almacenamiento subyacente."
    )
    q2_claim = (
        "Si se reorganizan los archivos en el disco, se modifica un índice "
        "o se cambia de hardware, las tablas y las consultas lógicas siguen "
        "funcionando exactamente igual sin que las aplicaciones sufran modificaciones."
    )
    backend = _StructuredBackend('{"verdict":"ENTAILED","rationale":"Apparent support"}')
    result = GeminiNLIJudge(backend).evaluate_claim(source_excerpt, q2_claim)
    assert result.verdict == ClaimSupportVerdict.UNSUPPORTED_GENERALIZATION
    assert backend.calls == []
