"""Minimal derived view of a validated S4.4 report, never a second evaluation.

No prompts, rationales, generated claim text or evidence excerpts are publicized:
rejected generation must not leak through its own audit metadata.
"""
from study_engine.audit.contracts import ForensicAuditReport


def project_validated_audit(report: ForensicAuditReport, *, phase: str, content_sha256: str, content_binding_id: str) -> dict:
    return {
        "audit_id": report.audit_id,
        "request_id": report.request_id,
        "notebook_id": report.notebook_id,
        "phase": phase,
        "auditor_verdict": report.overall_verdict.value,
        "content_sha256": content_sha256,
        "content_binding_id": content_binding_id,
        "nli_executed": report.nli_executed,
        "claims": [
            {
                "claim_index": claim.claim_index,
                "claim_type": claim.claim_type.value,
                "cited_tags": list(claim.cited_tags),
                "nli_verdict": claim.nli_verdict.value,
            }
            for claim in report.claim_verifications
        ],
    }
