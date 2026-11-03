"""Authoritative ForensicAuditor facade coordinating Layers 1 & 2 for S4.4.

Enforces:
- HG-S4.4-01: Fail-Closed Deterministic Evaluation.
- HG-S4.4-07: Atomic Isolation of NLI.
- HG-S4.4-08: NLI Failure Is Not Approval.
- HG-S4.4-09: No Corpus Re-Retrieval.
- HG-S4.4-10: Immutable Forensic Traceability.
"""

import logging
import time
import uuid
import hashlib
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple

from study_engine.audit.contracts import (
    AuditVerdict,
    CheckStatus,
    ClaimSupportVerdict,
    ClaimType,
    ClaimVerification,
    ForensicAuditInput,
    ForensicAuditReport,
    LexicalAnomalyStatus,
    LexicalDiagnostics,
)
from study_engine.audit.engine import DeterministicAuditEngine
from study_engine.audit.nli import (
    BaseNLIJudge,
    MockNLIJudge,
    NLIAggregator,
    NLIInferenceResult,
)
from study_engine.llm.exceptions import (
    LLMBackendError,
    LLMConnectionError,
    LLMTimeoutError,
)
from study_engine.utils.cache import TTLCache

logger = logging.getLogger(__name__)

# Citation markers are metadata, not part of the proposition.  Sending them to
# the semantic judge distracts it (e.g. "En ejecución [E5]." is read as a claim
# about a reference) and produces false NOT_ENTAILED verdicts for valid lists.
_CITATION_TAG_RE = re.compile(r"\[[^\]]*\bE[0-9]+\b[^\]]*\]")

# M1-02 (enmienda de rendimiento): reutilización idempotente de veredictos NLI
# válidos dentro del mismo auditor (mismo contenedor).  La clave es el texto
# EXACTO premise+hipótesis bajo el judge_id actual: un hit reutiliza la
# sentencia de una evaluación byte-idéntica; jamás amplía el soporte ni
# transforma UNASSESSED en otra cosa.  El modelo es temp=0.0 (determinista a
# nivel de servicio); la reutilización es equivalente a re-ejecutar la misma
# llamada sin quema de cuota.  TALOS_NLI_REUSE_CACHE=0 la deshabilita.
_NLI_RESULT_CACHE_MAXSIZE = 4096
_NLI_RESULT_CACHE_TTL_S = 3600.0
# Reintento técnico acotado ante fallo transitorio del proveedor (HTTP 503 /
# timeout / conexión).  NUNCA se reintenta 429 (cuota agotada: reintentar
# empeora la ventana).  Un reintento consume presupuesto de wall-clock; el
# deadline del audit manda.
_NLI_MAX_TECHNICAL_RETRIES = 1
_NLI_RETRY_BACKOFF_S = 2.0


class ForensicAuditor:
    """Primary forensic auditor orchestrating deterministic & NLI checks."""

    def __init__(
        self,
        engine: Optional[DeterministicAuditEngine] = None,
        nli_judge: Optional[BaseNLIJudge] = None,
        nli_aggregator: Optional[NLIAggregator] = None,
        auditor_backend: str = "forensic-auditor-v1",
        nli_max_concurrency: int = 3,
        nli_budget_seconds: Optional[float] = 20.0,
        nli_reuse_cache: bool = True,
    ) -> None:
        if nli_max_concurrency < 1:
            raise ValueError("nli_max_concurrency must be positive")
        if nli_budget_seconds is not None and nli_budget_seconds <= 0:
            raise ValueError("nli_budget_seconds must be positive or None")
        self._engine = engine or DeterministicAuditEngine()
        self._nli_judge = nli_judge or MockNLIJudge()
        self._nli_aggregator = nli_aggregator or NLIAggregator()
        self._auditor_backend = auditor_backend
        self._nli_max_concurrency = nli_max_concurrency
        self._nli_budget_seconds = nli_budget_seconds
        # Idempotent cross-audit verdict reuse (see module comment).  Scoped to
        # this auditor instance so tests with injectable judges stay isolated.
        self._nli_result_cache: Optional[TTLCache] = (
            TTLCache(
                maxsize=_NLI_RESULT_CACHE_MAXSIZE,
                ttl=_NLI_RESULT_CACHE_TTL_S,
            )
            if nli_reuse_cache
            else None
        )
        self._nli_cache_lock = threading.Lock()

    def _nli_cache_lookup(
        self, premise: str, hypothesis: str
    ) -> Optional[NLIInferenceResult]:
        """Reuse a verdict for a byte-identical (premise, hypothesis) pair."""
        if self._nli_result_cache is None:
            return None
        try:
            cache_key = hashlib.sha256(
                f"{self._nli_judge.judge_id}\x00{premise}\x00{hypothesis}".encode(
                    "utf-8"
                )
            ).hexdigest()
        except Exception:  # pragma: no cover - sha256 cannot fail on str/bytes
            return None
        with self._nli_cache_lock:
            return self._nli_result_cache.get(cache_key)

    def _nli_cache_store(
        self, premise: str, hypothesis: str, result: NLIInferenceResult
    ) -> None:
        """Persist a *valid* verdict for byte-identical future reuse.

        UNASSESSED results (technical or genuine) are never stored: a technical
        failure later retried live is preferable to freezing an unknown.
        """
        if self._nli_result_cache is None or result is None:
            return
        if result.verdict == ClaimSupportVerdict.UNASSESSED:
            return
        try:
            cache_key = hashlib.sha256(
                f"{self._nli_judge.judge_id}\x00{premise}\x00{hypothesis}".encode(
                    "utf-8"
                )
            ).hexdigest()
            with self._nli_cache_lock:
                self._nli_result_cache[cache_key] = result
        except Exception:  # pragma: no cover - defensive
            logger.debug("[S4.4-NLI-CACHE] store failed (ignored)")

    # ------------------------------------------------------------------
    # M1-02: idempotent verdict reuse + provider failure classification
    # ------------------------------------------------------------------
    @staticmethod
    def _classify_provider_failure(exc: Exception) -> Optional[str]:
        """Classify a judge exception as reusable-verbatim failure classes.

        Returns None for non-provider errors (parsing/contract bugs), which are
        never retried.  Classification follows the observed Gemini transport:
        - "provider_rate_limit":    HTTP 503 (sobrecarga transitoria)
        - "provider_quota":         HTTP 429 (cuota agotada; NO reintentar)
        - "provider_timeout":       LLMTimeoutError
        - "provider_connectivity":  LLMConnectionError / ConnectError
        """
        message = str(exc)
        if "HTTP 429" in message:
            return "provider_quota"
        if "HTTP 503" in message:
            return "provider_rate_limit"
        if isinstance(exc, LLMTimeoutError):
            return "provider_timeout"
        if isinstance(exc, (LLMConnectionError, LLMBackendError)) and (
            "connect" in message.lower() or isinstance(exc, LLMConnectionError)
        ):
            return "provider_connectivity"
        if isinstance(exc, LLMBackendError):
            return "provider_error"
        return None

    def audit(self, audit_input: ForensicAuditInput) -> ForensicAuditReport:
        """Perform end-to-end forensic audit on a generation response."""
        start_time = time.perf_counter()
        req = audit_input.request
        ctx = req.packaged_context

        # Gather evidence hashes

        evidence_hashes = tuple(
            rec.content_hash for rec in ctx.citation_manifest.records.values()
        )

        # 1. Execute Layer 1 Deterministic Audit Engine
        det_res = self._engine.evaluate(audit_input)

        # 2. Check for Fail-Closed Critical Failure (HG-S4.4-01)
        if det_res.has_critical_failure:
            latency_ms = (time.perf_counter() - start_time) * 1000.0

            # Build unassessed claim records
            verifications: List[ClaimVerification] = []
            for c in det_res.claims:
                if c.claim_type == ClaimType.STRUCTURAL:
                    continue
                diag = det_res.lexical_diagnostics.get(
                    c.claim_index,
                    LexicalDiagnostics(
                        status=LexicalAnomalyStatus.INCONCLUSIVE,
                        token_overlap_ratio=0.0,
                    ),
                )
                verifications.append(
                    ClaimVerification(
                        claim_index=c.claim_index,
                        claim_text=c.claim_text,
                        claim_type=c.claim_type,
                        cited_tags=c.cited_tags,
                        lexical_diagnostics=diag,
                        nli_verdict=ClaimSupportVerdict.UNASSESSED,
                        nli_confidence=None,
                        nli_rationale=(
                            "Bypassed by Layer 1 fail-closed critical failure"
                        ),
                    )
                )

            verdict = (
                det_res.early_verdict
                or AuditVerdict.REJECTED_POLICY_VIOLATION
            )
            return ForensicAuditReport(
                audit_id=f"audit_{uuid.uuid4().hex[:12]}",
                request_id=req.request_id,
                notebook_id=req.notebook_id,
                overall_verdict=verdict,
                deterministic_checks=det_res.checks,
                claim_verifications=tuple(verifications),
                nli_executed=False,
                nli_judge_id=None,
                prompt_hash=audit_input.prompt_hash,
                evidence_hashes=evidence_hashes,
                audit_latency_ms=round(latency_ms, 2),
                auditor_backend=self._auditor_backend,
            )

        # 3. Layer 2: Bounded Atomic NLI Evaluation (HG-S4.4-07, HG-S4.4-08)
        # Do not silently assess an unbounded number of *assessable* claims.
        # The bound applies to claims that will actually be sent to the
        # semantic judge (those citing evidence).  Purely presentational
        # STRUCTURAL elements and uncited pedagogical/conversational framing
        # are not semantic calls, so formatting alone cannot exhaust the
        # budget and force a spurious FLAGGED_UNASSESSED.
        assessable_claims = [c for c in det_res.claims if c.cited_tags]
        if len(assessable_claims) > 12:
            return ForensicAuditReport(
                audit_id=f"audit_{uuid.uuid4().hex[:12]}",
                request_id=req.request_id,
                notebook_id=req.notebook_id,
                overall_verdict=AuditVerdict.FLAGGED_UNASSESSED,
                deterministic_checks=det_res.checks,
                claim_verifications=(),
                nli_executed=False,
                nli_judge_id=None,
                nli_budget_exhausted=True,
                prompt_hash=audit_input.prompt_hash,
                evidence_hashes=evidence_hashes,
                audit_latency_ms=round((time.perf_counter() - start_time) * 1000.0, 2),
                auditor_backend=self._auditor_backend,
            )
        unit_map = {u.citation.citation_id: u for u in ctx.packaged_units}
        claim_verifications: List[ClaimVerification] = []
        nli_calls = 0
        nli_cache_hits = 0
        nli_total_ms = 0.0
        nli_technical_failures = 0
        nli_budget_exhausted = False

        def _diagnostics(claim) -> LexicalDiagnostics:
            return det_res.lexical_diagnostics.get(
                claim.claim_index,
                LexicalDiagnostics(
                    status=LexicalAnomalyStatus.INCONCLUSIVE,
                    token_overlap_ratio=0.0,
                ),
            )

        # First pass: identify distinct (premise, hypothesis) pairs.  The exact
        # evidence text and the citation-stripped claim text form the cache key.
        # No semantic equivalence is inferred, so a cache hit only reuses the
        # verdict of a byte-identical evaluation; it never widens support.
        pending: Dict[str, Tuple[str, str, bool]] = {}
        claim_keys: Dict[int, str] = {}
        nli_results: Dict[str, NLIInferenceResult] = {}
        nli_reused_on_entry = 0
        for c in det_res.claims:
            if c.claim_type == ClaimType.STRUCTURAL or not c.cited_tags:
                continue
            evidence_units = [
                unit_map[t] for t in c.cited_tags if t in unit_map
            ]
            premise = "\n\n".join(u.content for u in evidence_units)
            hypothesis = _CITATION_TAG_RE.sub("", c.claim_text)
            hypothesis = re.sub(r"\s+([.,;:!?])", r"\1", hypothesis)
            hypothesis = re.sub(r"\s+", " ", hypothesis).strip()
            key = hashlib.sha256(
                f"{premise}\x00{hypothesis}".encode("utf-8")
            ).hexdigest()
            claim_keys[c.claim_index] = key
            resolvable = bool(evidence_units)
            cached_result = (
                self._nli_cache_lookup(premise, hypothesis) if resolvable else None
            )
            if cached_result is not None and key not in nli_results:
                # Byte-identical pair already judged: reuse the exact
                # verdict, do not schedule a new provider call.
                nli_results[key] = cached_result
                nli_reused_on_entry += 1
                continue
            pending.setdefault(
                key, (premise, hypothesis, resolvable)
            )

        # A citation that does not resolve to packaged evidence cannot be
        # assessed.  This is a defense-in-depth check: the manifest integrity
        # check normally catches phantom tags first.
        for key, (_, _, resolvable) in pending.items():
            if not resolvable:
                nli_results[key] = NLIInferenceResult(
                    verdict=ClaimSupportVerdict.UNASSESSED,
                    rationale="Cited evidence not present in packaged context",
                )

        evaluable = [
            (key, premise, hypothesis)
            for key, (premise, hypothesis, resolvable) in pending.items()
            if resolvable
        ]
        nli_cache_hits = sum(
            1
            for c in det_res.claims
            if c.claim_type != ClaimType.STRUCTURAL and c.cited_tags
        ) - len(pending)

        if evaluable:
            deadline = (
                start_time + self._nli_budget_seconds
                if self._nli_budget_seconds is not None
                else None
            )
            max_workers = max(1, min(self._nli_max_concurrency, len(evaluable)))

            def _invoke(
                premise: str, hypothesis: str
            ) -> Tuple[NLIInferenceResult, float, bool]:
                started = time.perf_counter()
                technical_failure = False
                attempts = 0
                while True:
                    attempts += 1
                    try:
                        result = self._nli_judge.evaluate_claim(
                            premise=premise, hypothesis=hypothesis
                        )
                        self._nli_cache_store(premise, hypothesis, result)
                        break
                    except Exception as exc:
                        failure_class = self._classify_provider_failure(exc)
                        retriable = (
                            failure_class is not None
                            and failure_class != "provider_quota"
                            and attempts <= _NLI_MAX_TECHNICAL_RETRIES
                            and (
                                deadline is None
                                or time.perf_counter() + _NLI_RETRY_BACKOFF_S
                                < deadline
                            )
                        )
                        if not retriable:
                            # HG-S4.4-08: Failure is NOT approval.  The flag lets the
                            # pipeline distinguish an operational provider failure
                            # (429/503/timeout) from a genuine semantic UNASSESSED.
                            logger.warning(
                                "[S4.4-NLI] %s tras %d intento(s) [clase=%s]: %s",
                                "fallo técnico final" if failure_class else "error del juez",
                                attempts,
                                failure_class or "non_provider",
                                exc,
                            )
                            result = NLIInferenceResult(
                                verdict=ClaimSupportVerdict.UNASSESSED,
                                rationale=f"Judge error: {exc}",
                            )
                            technical_failure = True
                            break
                        logger.warning(
                            "[S4.4-NLI] reintento técnico %d/%d [clase=%s] en %.1fs: %s",
                            attempts,
                            _NLI_MAX_TECHNICAL_RETRIES,
                            failure_class,
                            _NLI_RETRY_BACKOFF_S,
                            exc,
                        )
                        time.sleep(_NLI_RETRY_BACKOFF_S)
                return (
                    result,
                    (time.perf_counter() - started) * 1000.0,
                    technical_failure,
                )

            budget_exhausted = False
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                for offset in range(0, len(evaluable), max_workers):
                    chunk = evaluable[offset : offset + max_workers]
                    if budget_exhausted or (
                        deadline is not None and time.perf_counter() >= deadline
                    ):
                        budget_exhausted = True
                        nli_budget_exhausted = True
                        for key, _, _ in chunk:
                            nli_results[key] = NLIInferenceResult(
                                verdict=ClaimSupportVerdict.UNASSESSED,
                                rationale=(
                                    "Audit time budget exhausted before "
                                    "semantic evaluation"
                                ),
                            )
                        continue

                    # Bounded concurrency preserves the atomic contract: every
                    # provider call receives exactly one premise and one
                    # hypothesis.  It reduces wall-clock latency without
                    # merging evidence across claims.
                    futures = {
                        pool.submit(_invoke, premise, hypothesis): key
                        for key, premise, hypothesis in chunk
                    }
                    for future in as_completed(futures):
                        key = futures[future]
                        result, elapsed_ms, technical_failure = future.result()
                        nli_results[key] = result
                        nli_calls += 1
                        nli_total_ms += elapsed_ms
                        if technical_failure:
                            nli_technical_failures += 1

        for c in det_res.claims:
            # Structural presentation is not a claim: it is neither grounded
            # nor semantically assessed.
            if c.claim_type == ClaimType.STRUCTURAL:
                continue

            diag = _diagnostics(c)

            # Conversational/pedagogical sentences default to entailed
            if not c.cited_tags:
                claim_verifications.append(
                    ClaimVerification(
                        claim_index=c.claim_index,
                        claim_text=c.claim_text,
                        claim_type=c.claim_type,
                        cited_tags=(),
                        lexical_diagnostics=diag,
                        nli_verdict=ClaimSupportVerdict.ENTAILED,
                        nli_confidence=1.0,
                        nli_rationale=(
                            "Non-factual sentence; no evidence required"
                        ),
                    )
                )
                continue

            result = nli_results[claim_keys[c.claim_index]]
            claim_verifications.append(
                ClaimVerification(
                    claim_index=c.claim_index,
                    claim_text=c.claim_text,
                    claim_type=c.claim_type,
                    cited_tags=c.cited_tags,
                    lexical_diagnostics=diag,
                    nli_verdict=result.verdict,
                    nli_confidence=(
                        round(result.confidence, 2)
                        if result.confidence
                        else None
                    ),
                    nli_rationale=result.rationale,
                )
            )

        # 4. Aggregate claim verifications
        nli_verdict = self._nli_aggregator.aggregate(claim_verifications)

        # Invariant: ENTAILMENT from NLI is NOT automatic approval.
        # It proceeds to approval only if Layer 1 checks also passed.
        if nli_verdict == AuditVerdict.APPROVED:
            failing_checks = [
                ch for ch in det_res.checks if ch.status == CheckStatus.FAIL
            ]
            if failing_checks:
                overall_verdict = (
                    det_res.early_verdict
                    or AuditVerdict.REJECTED_POLICY_VIOLATION
                )
            else:
                overall_verdict = AuditVerdict.APPROVED
        else:
            overall_verdict = nli_verdict

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        logger.info(
            "[S4.4-NLI] claims_total=%d assessable=%d nli_calls=%d "
            "cache_hits=%d reused_on_entry=%d technical_failures=%d "
            "budget_exhausted=%s "
            "concurrency=%d nli_ms=%.1f audit_ms=%.1f verdict=%s judge=%s",
            len(det_res.claims),
            len(assessable_claims),
            nli_calls,
            nli_cache_hits,
            nli_reused_on_entry,
            nli_technical_failures,
            nli_budget_exhausted,
            self._nli_max_concurrency,
            nli_total_ms,
            latency_ms,
            overall_verdict.value,
            self._nli_judge.judge_id,
        )

        return ForensicAuditReport(
            audit_id=f"audit_{uuid.uuid4().hex[:12]}",
            request_id=req.request_id,
            notebook_id=req.notebook_id,
            overall_verdict=overall_verdict,
            deterministic_checks=det_res.checks,
            claim_verifications=tuple(claim_verifications),
            nli_executed=True,
            nli_judge_id=self._nli_judge.judge_id,
            nli_calls=nli_calls,
            nli_cache_hits=nli_cache_hits,
            nli_technical_failures=nli_technical_failures,
            nli_budget_exhausted=nli_budget_exhausted,
            prompt_hash=audit_input.prompt_hash,
            evidence_hashes=evidence_hashes,
            audit_latency_ms=round(latency_ms, 2),
            auditor_backend=self._auditor_backend,
        )
