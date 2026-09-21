"""Deterministic citation and input identity verification for S4.4.

Enforces:
- HG-S4.4-02: Input Identity (request, response, context alignment).
- HG-S4.4-03: Manifest and Hash Integrity (no phantom citations, valid hashes).
"""

import hashlib
from typing import List
from study_engine.audit.contracts import (
    CheckSeverity,
    CheckStatus,
    DeterministicAuditCheck,
    ForensicAuditInput,
)


class CitationVerifier:
    """Deterministic verifier for input identity and manifest integrity."""

    def verify(
        self, audit_input: ForensicAuditInput
    ) -> List[DeterministicAuditCheck]:
        """Run deterministic checks on identity, manifest, and hashes."""
        checks: List[DeterministicAuditCheck] = []

        # 1. HG-S4.4-02: Input Identity Check
        req = audit_input.request
        resp = audit_input.response
        ctx = req.packaged_context

        identity_errors: List[str] = []
        if resp.request_id != req.request_id:
            identity_errors.append(
                f"request_id mismatch: {resp.request_id} != {req.request_id}"
            )
        if resp.notebook_id != req.notebook_id:
            identity_errors.append(
                f"notebook mismatch: {resp.notebook_id} != {req.notebook_id}"
            )
        if resp.mode != req.mode:
            identity_errors.append(
                f"mode mismatch: '{resp.mode}' != '{req.mode}'"
            )
        if resp.grounding_decision != ctx.packet.grounding_decision:
            identity_errors.append(
                f"decision mismatch: '{resp.grounding_decision}' "
                f"!= '{ctx.packet.grounding_decision}'"
            )

        if identity_errors:

            checks.append(
                DeterministicAuditCheck(
                    check_id="CHECK_INPUT_IDENTITY",
                    status=CheckStatus.FAIL,
                    severity=CheckSeverity.CRITICAL,
                    reason="; ".join(identity_errors),
                )
            )
        else:
            checks.append(
                DeterministicAuditCheck(
                    check_id="CHECK_INPUT_IDENTITY",
                    status=CheckStatus.PASS,
                    severity=CheckSeverity.CRITICAL,
                    reason=(
                        "Input identity strictly aligned across request, "
                        "response, and context."
                    ),
                )
            )

        # 2. HG-S4.4-03: Manifest & Evidence Hash Integrity
        manifest = ctx.citation_manifest
        unit_map = {u.citation.citation_id: u for u in ctx.packaged_units}
        phantom_tags: List[str] = []

        corrupted_hashes: List[str] = []

        for cite in resp.citations:
            tag = cite.citation_id
            if tag not in manifest.records:
                phantom_tags.append(tag)
            else:
                rec = manifest.records[tag]
                if len(rec.content_hash) != 64:
                    corrupted_hashes.append(
                        f"{tag}: invalid hash length ({len(rec.content_hash)})"
                    )
                unit = unit_map.get(tag)
                if unit is not None:
                    calc = hashlib.sha256(
                        unit.content.encode("utf-8")
                    ).hexdigest()
                    if calc != rec.content_hash:
                        corrupted_hashes.append(
                            f"{tag}: hash mismatch "
                            f"({calc} != {rec.content_hash})"
                        )

        if phantom_tags or corrupted_hashes:

            reasons = []
            if phantom_tags:
                reasons.append(
                    f"Phantom citations (not in manifest): {phantom_tags}"
                )
            if corrupted_hashes:
                reasons.append(
                    f"Corrupted evidence hashes: {corrupted_hashes}"
                )
            checks.append(
                DeterministicAuditCheck(
                    check_id="CHECK_MANIFEST_INTEGRITY",
                    status=CheckStatus.FAIL,
                    severity=CheckSeverity.CRITICAL,
                    reason="; ".join(reasons),
                )
            )
        else:
            checks.append(
                DeterministicAuditCheck(
                    check_id="CHECK_MANIFEST_INTEGRITY",
                    status=CheckStatus.PASS,
                    severity=CheckSeverity.CRITICAL,
                    reason=(
                        "All citations resolve to authoritative manifest "
                        "records with valid hashes."
                    ),
                )
            )

        # 3. Source Provenance & Trust Level Verification
        unverified_sources: List[str] = []
        for cite in resp.citations:
            tag = cite.citation_id
            rec = manifest.records.get(tag)
            if rec is not None:
                trust = getattr(rec, "trust_level", "canonical")
                if trust == "unverified":
                    unverified_sources.append(f"{tag} ({rec.source_id})")

        if unverified_sources:
            checks.append(
                DeterministicAuditCheck(
                    check_id="CHECK_SOURCE_PROVENANCE",
                    status=CheckStatus.FAIL,
                    severity=CheckSeverity.CRITICAL,
                    reason=f"Unverified or untrusted sources cited: {unverified_sources}",
                )
            )
        else:
            checks.append(
                DeterministicAuditCheck(
                    check_id="CHECK_SOURCE_PROVENANCE",
                    status=CheckStatus.PASS,
                    severity=CheckSeverity.CRITICAL,
                    reason="All cited sources satisfy provenance and trust level requirements.",
                )
            )

        return checks
