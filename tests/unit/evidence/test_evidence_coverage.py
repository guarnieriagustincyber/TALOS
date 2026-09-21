"""Unit tests for EvidenceCoverageEvaluator and ContextPacker Warning Injection (V1.1 Fase D)."""

import pytest

from study_engine.contracts.evidence_engine import (
    CoverageStatus,
    EvaluatedEvidenceItem,
    EvidenceGrade,
    EvidencePacket,
    GroundingDecision,
    SubQuery,
)
from study_engine.contracts.retrieval import ScoredCandidate
from study_engine.context.packer import ContextPacker
from study_engine.evidence.coverage import EvidenceCoverageEvaluator


def make_candidate(
    chunk_id: str,
    source_id: str,
    score: float,
    content: str,
    trust_level: str = "canonical",
    sub_query_id: str = None,
) -> ScoredCandidate:
    meta = {"trust_level": trust_level}
    if sub_query_id:
        meta["sub_query_id"] = sub_query_id
    return ScoredCandidate(
        chunk_id=chunk_id,
        document_id=f"doc_{source_id}",
        source_id=source_id,
        notebook_id="NB-TEST",
        rank=1,
        score=score,
        content=content,
        retrieval_method="hybrid",
        metadata=meta,
    )


def test_quality_score_shallow_chunk():
    """Verifica que chunks superficiales (< 150 tokens) obtienen score bajo y clasifican como MISSING (Refinamiento 2)."""
    evaluator = EvidenceCoverageEvaluator(min_depth_tokens=150)
    # Very short chunk (5 tokens), low score
    shallow_chunk = make_candidate(
        "c_shallow",
        "src_1",
        0.30,
        "TCP es un protocolo.",
    )
    score = evaluator.calculate_quality_score([shallow_chunk])
    # 0.4 * (5/150 = 0.033) + 0.3 * 0.3 + 0.2 * 1.0 + 0.1 * 0.0 = 0.013 + 0.09 + 0.20 = ~0.303 < 0.40
    assert score < 0.40

    sq = SubQuery(sub_query_id="sq-1", text="¿Qué es TCP?")
    report = evaluator.evaluate_coverage([sq], [shallow_chunk])
    assert report.coverage[0].status == CoverageStatus.MISSING


def test_quality_score_deep_canonical_chunk():
    """Verifica que chunks profundos con claridad pedagógica y fuente canónica superan 0.7 (SUFFICIENT)."""
    evaluator = EvidenceCoverageEvaluator(min_depth_tokens=150)
    # Long descriptive text with pedagogical keywords
    deep_content = (
        "En sistemas operativos, una condición de carrera se define formalmente como una situación "
        "en la cual dos o más procesos acceden a un recurso compartido y el resultado final "
        "depende del orden de ejecución. Por ejemplo, en el spooler de impresión, si dos procesos "
        "escriben simultáneamente en la misma ranura del búfer, se produce una inconsistencia severa. "
        "La función principal de los algoritmos de exclusión mutua es garantizar que solo un proceso "
        "entre a la sección crítica a la vez. Este proceso consiste en verificar cerrojos atómicos o "
        "semáforos antes de realizar cualquier operación de escritura concurrente. " * 3
    )
    deep_chunk = make_candidate(
        "c_deep",
        "src_concurrency",
        0.92,
        deep_content,
        trust_level="canonical",
    )
    score = evaluator.calculate_quality_score([deep_chunk])
    assert score >= 0.70

    sq = SubQuery(sub_query_id="sq-race", text="¿Qué es una condición de carrera?")
    report = evaluator.evaluate_coverage([sq], [deep_chunk])
    assert report.coverage[0].status == CoverageStatus.SUFFICIENT


def test_coverage_warnings_in_system_prompt():
    """Verifica que las advertencias de cobertura se inyectan en el prompt del sistema (Refinamiento 3)."""
    evaluator = EvidenceCoverageEvaluator()
    packer = ContextPacker()

    sq_covered = SubQuery(sub_query_id="sq-1", text="¿Cómo funciona el handshake TCP?")
    sq_missing = SubQuery(sub_query_id="sq-2", text="¿Cómo detecta anomalías Suricata en red?")

    # Only provide evidence for sq_covered
    deep_chunk = make_candidate(
        "c_tcp",
        "src_tcp",
        0.95,
        "El three-way handshake de TCP consiste en SYN, SYN-ACK y ACK. Por ejemplo, define la conexión. " * 10,
        sub_query_id="sq-1",
    )

    report = evaluator.evaluate_coverage([sq_covered, sq_missing], [deep_chunk])
    assert report.coverage[0].status == CoverageStatus.SUFFICIENT
    assert report.coverage[1].status == CoverageStatus.MISSING

    # Create packet
    item = EvaluatedEvidenceItem(
        chunk_id="c_tcp",
        document_id="doc_tcp",
        source_id="src_tcp",
        source_title="TCP/IP Guide",
        content="El three-way handshake de TCP consiste en SYN, SYN-ACK y ACK.",
        content_hash="a" * 64,
        retrieval_score=0.95,
        retrieval_rank=1,
        retrieval_method="hybrid",
        grade=EvidenceGrade.DIRECT,
    )
    packet = EvidencePacket(
        original_query="Pregunta mixta",
        normalized_query="pregunta mixta",
        notebook_id="NB-TEST",
        grounding_decision=GroundingDecision.SUPPORTED,
        evidence_items=[item],
        coverage_report=report,
    )

    packaged_ctx = packer.pack(packet)

    # Check that system prompt policy contains forced warnings
    assert "ADVERTENCIAS DE COBERTURA DE EVIDENCIA" in packaged_ctx.epistemic_policy
    assert "⚠️ TEMA FALTANTE: '¿Cómo detecta anomalías Suricata en red?'" in packaged_ctx.epistemic_policy
    assert "PROHIBIDO GENERAR EXPLICACIÓN O INVENTAR" in packaged_ctx.epistemic_policy
    assert "SIGUE ESTAS REGLAS ESTRICTAMENTE" in packaged_ctx.epistemic_policy
    assert packaged_ctx.coverage_report is not None
    assert packaged_ctx.coverage_report.has_missing
