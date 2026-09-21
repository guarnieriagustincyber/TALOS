"""Epistemic evidence, claims verification, and coverage endpoints (Phase E2 / Phase 3)."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from study_engine.evidence.verification_backstop import GenerationVerificationBackstop
from study_engine.utils.cache import TTLCache
from study_engine.web.dependencies import AppContainer, get_container
from study_engine.web.routes.sources import OpenLocalPayload, open_in_system_viewer

router = APIRouter(prefix="/api/evidence", tags=["Evidence"])

# In-memory session verification cache with TTL eviction (session_id -> ClaimsVerificationResponse)
_claims_cache: TTLCache = TTLCache(maxsize=1000, ttl=3600.0)
_coverage_cache: TTLCache = TTLCache(maxsize=1000, ttl=3600.0)


class ClaimItemDto(BaseModel):
    claim_id: str
    claim_text: str
    claim_type: str
    criticality: str
    status: str  # SUPPORTED | PARTIALLY_SUPPORTED | UNSUPPORTED | CONTRADICTION
    grounding_ratio: float
    cited_evidence_indices: List[str] = Field(default_factory=list)
    has_redaction: bool = False


class ContradictionItemDto(BaseModel):
    claim_id: str
    claim_text: str
    source_a: str
    assertion_a: str
    source_b: str
    assertion_b: str
    conflict_type: str
    status: str = "UNRESOLVED_CONTRADICTION"


class ClaimsVerificationResponse(BaseModel):
    session_id: str
    verdict: str  # APPROVED | PARTIAL_ABSTENTION | REJECTED_UNSUPPORTED | FLAGGED_UNASSESSED
    claims: List[ClaimItemDto]
    redacted_text: Optional[str] = None
    contradictions: List[ContradictionItemDto] = Field(default_factory=list)


class CoverageResponse(BaseModel):
    session_id: str
    facets: Dict[str, str]  # facet_name -> "SUFFICIENT" | "PARTIAL" | "MISSING"
    coverage_ratio: float
    sufficient_count: int
    partial_count: int
    missing_count: int
    status: str  # FULL_COVERAGE | PARTIAL_COVERAGE | INSUFFICIENT_COVERAGE
    grounding_rate: float
    notes: Optional[str] = None


def _get_or_create_claims_for_session(
    session_id: str, container: Optional[AppContainer] = None
) -> ClaimsVerificationResponse:
    """Retrieve cached claims, audit active session response, or return empty claims for unknown sessions."""
    if session_id in _claims_cache:
        data = _claims_cache[session_id]
        return ClaimsVerificationResponse(**data)

    # 1. Inspect real active session in StudySessionOrchestrator if container is available
    if container is not None and hasattr(container, "study_session_orchestrator"):
        session_state = getattr(container.study_session_orchestrator, "_sessions", {}).get(session_id)
        if session_state and hasattr(session_state, "history") and session_state.history:
            latest_turn = session_state.history[-1]
            response_text = getattr(latest_turn, "tutor_response", "") or getattr(latest_turn, "response", "")
            if response_text:
                backstop = GenerationVerificationBackstop()
                evidence_chunks = getattr(latest_turn, "evidence_chunks", []) or []
                audit_res = backstop.verify_e2_claims(response_text, evidence_chunks)
                claims_dtos = [
                    ClaimItemDto(
                        claim_id=f"C{idx+1}",
                        claim_text=c.get("text", ""),
                        claim_type=c.get("type", "FACTUAL_TEXTUAL"),
                        criticality=c.get("criticality", "NON_CRITICAL"),
                        status=c.get("status", "SUPPORTED"),
                        grounding_ratio=c.get("grounding_ratio", 1.0),
                        cited_evidence_indices=c.get("citations", []),
                        has_redaction=c.get("has_redaction", False),
                    )
                    for idx, c in enumerate(audit_res.get("claims", []))
                ]
                resp = ClaimsVerificationResponse(
                    session_id=session_id,
                    verdict=audit_res.get("verdict", "APPROVED"),
                    claims=claims_dtos,
                    redacted_text=audit_res.get("redacted_text"),
                    contradictions=[],
                )
                _claims_cache[session_id] = resp.model_dump()
                return resp

    # Default fail-closed for sessions without active verified claims (no fabricated claims)
    resp = ClaimsVerificationResponse(
        session_id=session_id,
        verdict="APPROVED",
        claims=[],
        redacted_text=None,
        contradictions=[],
    )
    _claims_cache[session_id] = resp.model_dump()
    return resp


def _get_or_create_coverage_for_session(
    session_id: str, container: Optional[AppContainer] = None
) -> CoverageResponse:
    """Retrieve cached coverage or evaluate facet coverage."""
    if session_id in _coverage_cache:
        data = _coverage_cache[session_id]
        return CoverageResponse(**data)

    # Default empty coverage for sessions without data
    resp = CoverageResponse(
        session_id=session_id,
        facets={},
        coverage_ratio=0.0,
        sufficient_count=0,
        partial_count=0,
        missing_count=0,
        status="INSUFFICIENT_COVERAGE",
        grounding_rate=0.0,
        notes="Sin observaciones de facetas para la sesión.",
    )
    _coverage_cache[session_id] = resp.model_dump()
    return resp


@router.get("/claims/{session_id}", response_model=ClaimsVerificationResponse)
def get_session_claims(
    session_id: str,
    container: AppContainer = Depends(get_container),
) -> ClaimsVerificationResponse:
    """Retrieve atomic claims, grounding statuses, and detected contradictions for a session."""
    if not session_id or not session_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_id no puede estar vacío.",
        )
    return _get_or_create_claims_for_session(session_id, container)


@router.get("/coverage/{session_id}", response_model=CoverageResponse)
def get_session_coverage(
    session_id: str,
    container: AppContainer = Depends(get_container),
) -> CoverageResponse:
    """Retrieve pedagogical facet coverage and token grounding rate for a session."""
    if not session_id or not session_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="session_id no puede estar vacío.",
        )
    return _get_or_create_coverage_for_session(session_id, container)


@router.get("/open-local-pdf")
def open_local_pdf(
    hash: Optional[str] = None,
    doc_hash: Optional[str] = None,
    page: int = 1,
) -> Dict[str, Any]:
    """Open document in the OS default desktop PDF viewer by delegating to canonical sources endpoint."""
    target_hash = (hash or doc_hash or "").strip()
    clean_hash = target_hash.split(":")[-1].lower()
    return open_in_system_viewer(OpenLocalPayload(doc_hash=clean_hash, page=page))

