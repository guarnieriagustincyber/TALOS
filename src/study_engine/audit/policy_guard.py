"""Deterministic policy and pedagogical mode guard for S4.4.

Enforces:
- HG-S4.4-04: Mandatory Abstention Enforcement.
- HG-S4.4-05: P7 Structural Non-Advancement (no student mastery claims).
- Socratic Structural Shape Verification.
"""

import re
from typing import List

from study_engine.audit.contracts import (
    CheckSeverity,
    CheckStatus,
    DeterministicAuditCheck,
    ForensicAuditInput,
)
from study_engine.contracts.generation import GenerationMode


_P7_PROHIBITED_PATTERNS = [
    re.compile(
        r"\b(has|quedas|quedó)\s+(aprobado|promovido|certificado)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(avanzas|pasas)\s+al\s+siguiente\s+(nivel|módulo|tema)\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(te\s+otorgo|adquieres|obtienes)\s+(la\s+)?maestría\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(tu\s+)?estado\s+curricular\s+(ha\s+sido\s+)?actualizado\b",
        re.IGNORECASE,
    ),
    re.compile(
        r"\b(dominio\s+completo|maestría\s+alcanzada)\b",
        re.IGNORECASE,
    ),
]


class PolicyGuard:
    """Deterministic policy guard for abstention, P7, and pedagogical modes."""

    def verify(
        self, audit_input: ForensicAuditInput
    ) -> List[DeterministicAuditCheck]:
        """Execute policy verification checks."""
        checks: List[DeterministicAuditCheck] = []
        resp = audit_input.response
        req = audit_input.request
        ctx = req.packaged_context

        # 1. HG-S4.4-04: Mandatory Abstention Check
        if ctx.packet.abstention_required:
            if resp.citations:
                checks.append(
                    DeterministicAuditCheck(
                        check_id="CHECK_MANDATORY_ABSTENTION",
                        status=CheckStatus.FAIL,
                        severity=CheckSeverity.CRITICAL,
                        reason=(
                            f"Response generated {len(resp.citations)} "
                            "citations despite mandatory abstention."
                        ),
                    )
                )
            elif not resp.is_abstention:
                checks.append(
                    DeterministicAuditCheck(
                        check_id="CHECK_MANDATORY_ABSTENTION",
                        status=CheckStatus.FAIL,
                        severity=CheckSeverity.CRITICAL,
                        reason=(
                            "Response text did not signal abstention when "
                            "required by context."
                        ),
                    )
                )
            else:
                checks.append(
                    DeterministicAuditCheck(
                        check_id="CHECK_MANDATORY_ABSTENTION",
                        status=CheckStatus.PASS,
                        severity=CheckSeverity.CRITICAL,
                        reason=(
                            "Mandatory abstention strictly respected "
                            "without citations."
                        ),
                    )
                )

        # 2. HG-S4.4-05: P7 Structural Mastery Mutation Check
        matched_p7 = []
        for pattern in _P7_PROHIBITED_PATTERNS:
            match = pattern.search(resp.text)
            if match:
                matched_p7.append(match.group(0))

        if matched_p7:
            checks.append(
                DeterministicAuditCheck(
                    check_id="CHECK_P7_MASTERY_MUTATION",
                    status=CheckStatus.FAIL,
                    severity=CheckSeverity.CRITICAL,
                    reason=(
                        f"Principio P7 violated: response claims student "
                        f"mastery advancement: {matched_p7}"
                    ),
                )
            )
        else:
            checks.append(
                DeterministicAuditCheck(
                    check_id="CHECK_P7_MASTERY_MUTATION",
                    status=CheckStatus.PASS,
                    severity=CheckSeverity.CRITICAL,
                    reason=(
                        "No student state or curricular advancement claims "
                        "detected."
                    ),
                )
            )

        # 3. Socratic Structural Shape Check
        if resp.mode == GenerationMode.SOCRATIC_TUTOR:
            has_question = "?" in resp.text or "¿" in resp.text
            if not has_question and len(resp.text) > 150:
                checks.append(
                    DeterministicAuditCheck(
                        check_id="CHECK_SOCRATIC_STRUCTURAL_SHAPE",
                        status=CheckStatus.FAIL,
                        severity=CheckSeverity.WARNING,
                        reason=(
                            "Socratic response contains no questions in "
                            "long text."
                        ),
                    )
                )
            elif has_question:
                checks.append(
                    DeterministicAuditCheck(
                        check_id="CHECK_SOCRATIC_STRUCTURAL_SHAPE",
                        status=CheckStatus.PASS,
                        severity=CheckSeverity.INFORMATIONAL,
                        reason=(
                            "Socratic response exhibits guided questioning "
                            "syntax."
                        ),
                    )
                )
            else:
                checks.append(
                    DeterministicAuditCheck(
                        check_id="CHECK_SOCRATIC_STRUCTURAL_SHAPE",
                        status=CheckStatus.INCONCLUSIVE,
                        severity=CheckSeverity.INFORMATIONAL,
                        reason=(
                            "Socratic response is concise; shape is "
                            "inconclusive."
                        ),
                    )
                )

        return checks
