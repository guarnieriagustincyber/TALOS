"""Focal F1 tests: end-to-end S4.4 grounding for markdown answers.

A grounded answer with headings, lists and citations can be APPROVED.  Any
uncited factual assertion -- including one hidden in a heading, a bullet or a
code block -- is still REJECTED_UNSUPPORTED.  Structural formatting never
consumes the bounded semantic budget, and an over-budget answer is FLAGGED,
never approved.
"""

import hashlib

from study_engine.contracts.evidence_engine import (
    CitationManifest,
    CitationRecord,
    EvidencePacket,
    GroundingDecision,
    PackagedContext,
    PackagedEvidenceUnit,
)
from study_engine.contracts.generation import (
    GenerationMode,
    GenerationRequest,
    GenerationResponse,
    ParsedCitation,
    ResponseValidationStatus,
)
from study_engine.audit.contracts import (
    AuditVerdict,
    ClaimSupportVerdict,
    ForensicAuditInput,
)
from study_engine.audit.auditor import ForensicAuditor
from study_engine.audit.nli import MockNLIJudge


def _make_input(text: str, manifest_tags=("E1",), declared_tags=None):
    declared_tags = tuple(manifest_tags) if declared_tags is None else tuple(declared_tags)

    records = {}
    units = []
    for tag in manifest_tags:
        content = f"Contenido autorizado y verificable para {tag}."
        content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        rec = CitationRecord(
            citation_id=tag,
            chunk_id=f"chk-{tag}",
            document_id=f"doc-{tag}",
            source_id=f"src-{tag}",
            source_title=f"Fuente {tag}",
            content_hash=content_hash,
        )
        records[tag] = rec
        units.append(
            PackagedEvidenceUnit(
                citation=rec,
                content=content,
                retrieval_score=0.9,
                retrieval_rank=1,
                retrieval_method="hybrid",
            )
        )

    manifest = CitationManifest(records=records)
    packet = EvidencePacket(
        original_query="query",
        normalized_query="query",
        notebook_id="fadena-so",
        grounding_decision=GroundingDecision.SUPPORTED,
    )
    ctx = PackagedContext(
        packet=packet,
        citation_manifest=manifest,
        packaged_units=units,
        formatted_context_block="contexto",
        total_characters=len("contexto"),
        epistemic_policy="Estricta",
    )
    req = GenerationRequest(
        request_id="req-1",
        notebook_id="fadena-so",
        query="query",
        packaged_context=ctx,
        mode=GenerationMode.EXPLANATION,
    )
    parsed = tuple(
        ParsedCitation(citation_id=tag, in_manifest=tag in manifest.records)
        for tag in declared_tags
    )
    resp = GenerationResponse(
        response_id="resp-1",
        request_id="req-1",
        notebook_id="fadena-so",
        mode=GenerationMode.EXPLANATION,
        text=text,
        raw_content=text,
        citations=parsed,
        validation_status=ResponseValidationStatus.VALID,
        is_abstention=False,
        grounding_decision=packet.grounding_decision,
    )
    return ForensicAuditInput(request=req, response=resp, prompt_hash="1" * 64)


def _audit(text, manifest_tags=("E1",), declared_tags=None):
    return ForensicAuditor().audit(
        _make_input(text, manifest_tags=manifest_tags, declared_tags=declared_tags)
    )


def test_grounded_headings_lists_and_citations_are_approved():
    text = (
        "## Introducción\n"
        "El scheduler desaloja el proceso cuando expira el quantum [E1].\n"
        "## Uso de memoria\n"
        "- Se solicita memoria dinámica en tiempo de ejecución [E1]\n"
        "- El kernel libera la página después del uso [E1]\n"
    )
    report = _audit(text)
    assert report.overall_verdict == AuditVerdict.APPROVED
    # Structural headings are not claims and do not appear as verifications.
    assert all(v.claim_type.value != "STRUCTURAL" for v in report.claim_verifications)


def test_uncited_heading_assertion_is_rejected():
    report = _audit("## El planificador siempre garantiza equidad")
    assert report.overall_verdict == AuditVerdict.REJECTED_UNSUPPORTED


def test_partial_abstention_meta_statement_does_not_require_citation():
    text = (
        "La evidencia proporcionada no menciona el quantum.\n"
        "El scheduler desaloja el proceso cuando expira el quantum [E1].\n"
    )
    report = _audit(text)
    assert report.overall_verdict == AuditVerdict.APPROVED


def test_contrastive_disclaimer_cannot_smuggle_an_uncited_claim():
    text = (
        "La evidencia no menciona el quantum, pero el quantum siempre es 10 ms.\n"
    )
    report = _audit(text)
    assert report.overall_verdict == AuditVerdict.REJECTED_UNSUPPORTED


def test_consequential_disclaimer_cannot_smuggle_an_uncited_claim():
    text = (
        "La evidencia no menciona el quantum, por lo tanto el quantum es 10 ms.\n"
    )
    report = _audit(text)
    assert report.overall_verdict == AuditVerdict.REJECTED_UNSUPPORTED


def test_uncited_bullet_assertion_is_rejected():
    report = _audit("## Ventajas\n- El kernel libera la página después del uso\n")
    assert report.overall_verdict == AuditVerdict.REJECTED_UNSUPPORTED


def test_uncited_verbless_assertion_is_rejected():
    for text in (
        "## Ventajas\n- Mayor eficiencia\n",
        "## Resultados siempre correctos\n",
        "- Clave primaria obligatoriamente numérica\n",
    ):
        report = _audit(text)
        assert report.overall_verdict == AuditVerdict.REJECTED_UNSUPPORTED, text


def test_cited_verbless_assertion_is_approved():
    text = "## Ventajas\n- Mayor eficiencia [E1]\n"
    report = _audit(text)
    assert report.overall_verdict == AuditVerdict.APPROVED


def test_verbless_code_comment_cannot_evade_grounding():
    report = _audit("```c\n// Mayor eficiencia operativa\n```\n")
    assert report.overall_verdict == AuditVerdict.REJECTED_UNSUPPORTED


def test_code_block_assertion_cannot_evade_grounding():
    text = "```c\n// El kernel libera la página después del uso\nint x = 5;\n```"
    report = _audit(text)
    assert report.overall_verdict == AuditVerdict.REJECTED_UNSUPPORTED


def test_pure_code_and_labels_have_no_unsupported_claims():
    text = "## Listado\n```c\nint x = 5;\nreturn x;\n```\n"
    report = _audit(text)
    assert report.overall_verdict == AuditVerdict.APPROVED
    assert report.claim_verifications == ()


def test_phantom_citation_in_bullet_is_rejected():
    text = "- El kernel libera la página después del uso [E99]\n"
    report = _audit(text, manifest_tags=("E1",), declared_tags=("E99",))
    assert report.overall_verdict == AuditVerdict.REJECTED_UNSUPPORTED


def test_many_structural_elements_do_not_exhaust_semantic_budget():
    headings = "\n".join(f"## Sección {i}" for i in range(20))
    text = f"{headings}\nEl scheduler desaloja el proceso [E1].\n"
    report = _audit(text, manifest_tags=("E1",))
    assert report.overall_verdict == AuditVerdict.APPROVED
    assert report.nli_executed is True


def test_more_than_twelve_cited_claims_is_flagged_not_approved():
    tags = tuple(f"E{i}" for i in range(1, 14))
    text = "\n".join(
        f"- El recurso {tag} se libera de forma verificable [{tag}]" for tag in tags
    )
    report = _audit(text, manifest_tags=tags)
    assert report.overall_verdict == AuditVerdict.FLAGGED_UNASSESSED
    assert report.nli_executed is False


def test_uncited_factual_claim_still_rejected_by_mock():
    report = _audit("El scheduler desaloja el proceso sin cita alguna.")
    assert report.overall_verdict == AuditVerdict.REJECTED_UNSUPPORTED


def test_cited_but_not_entailed_claim_is_rejected():
    text = "El scheduler desaloja el proceso [E1].\n"
    report = ForensicAuditor(
        nli_judge=MockNLIJudge(default_verdict=ClaimSupportVerdict.NOT_ENTAILED)
    ).audit(_make_input(text))
    assert report.overall_verdict == AuditVerdict.REJECTED_UNSUPPORTED


def test_false_heading_with_citation_is_still_audited_and_rejected():
    text = "## El scheduler nunca desaloja un proceso [E1]\n"
    report = ForensicAuditor(
        nli_judge=MockNLIJudge(default_verdict=ClaimSupportVerdict.NOT_ENTAILED)
    ).audit(_make_input(text))
    assert report.overall_verdict == AuditVerdict.REJECTED_UNSUPPORTED


def test_false_code_comment_with_citation_is_still_audited_and_rejected():
    text = "```c\n// El kernel nunca libera la página [E1]\n```\n"
    report = ForensicAuditor(
        nli_judge=MockNLIJudge(default_verdict=ClaimSupportVerdict.NOT_ENTAILED)
    ).audit(_make_input(text))
    assert report.overall_verdict == AuditVerdict.REJECTED_UNSUPPORTED
