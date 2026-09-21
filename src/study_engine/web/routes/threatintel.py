"""Threat Intelligence Feed & Multi-Feed Quorum Endpoints (Fase 4.3)."""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, Query, Response
from pydantic import BaseModel, ConfigDict, Field

from study_engine.web.dependencies import AppContainer, get_container

router = APIRouter(prefix="/api/threatintel", tags=["ThreatIntel"])


class QuorumSummaryDto(BaseModel):
    """Corroboration agreement telemetry across independent threat feeds."""

    model_config = ConfigDict(frozen=True)

    feeds_agree: int = Field(..., ge=0, description="Number of feeds matching the consensus verdict")
    total_feeds: int = Field(..., ge=1, description="Total active feeds queried")


class ThreatIntelIOCDto(BaseModel):
    """Normalized Indicator of Compromise with multi-feed quorum consensus and trust tier."""

    model_config = ConfigDict(frozen=True)

    ioc_id: str = Field(..., description="Unique IOC record identifier")
    type: str = Field(..., description="'ip' | 'domain' | 'sha256' | 'url'")
    value: str = Field(..., description="Observed indicator value (IP, domain, hash or URL)")
    verdict: str = Field(..., description="'malicious' | 'clean' | 'suspicious' | 'unknown'")
    trust_level: str = Field(default="unverified", description="'unverified' | 'verified_human'")
    quorum: QuorumSummaryDto = Field(..., description="Multi-feed corroboration quorum")
    conflicts: List[str] = Field(default_factory=list, description="Explicit conflicts between divergent feeds")
    promoted_at: Optional[str] = Field(default=None, description="ISO timestamp if promoted to verified")
    promoter: Optional[str] = Field(default=None, description="Authority identity who verified/promoted")
    last_updated: str = Field(..., description="ISO 8601 UTC timestamp of last verification")


@router.get("/feed", response_model=List[ThreatIntelIOCDto])
def get_threat_intel_feed(
    response: Response,
    notebook_id: Optional[str] = Query(default=None, description="Filter IOCs relevant to active notebook scope"),
    container: AppContainer = Depends(get_container),
) -> List[ThreatIntelIOCDto]:
    """Retrieve normalized threat intelligence feed with multi-feed corroboration quorums.
    
    INVARIANT ADR-008:
    Entries with trust_level 'unverified' represent external threat data ([TF#])
    and CANNOT be promoted to curricular ground truth.
    """
    response.headers["X-Warning"] = "DEMO-DATA"
    now_iso = datetime.now(timezone.utc).isoformat()

    # Deterministic telemetry seed for demonstration and live consumption
    iocs: List[ThreatIntelIOCDto] = [
        ThreatIntelIOCDto(
            ioc_id="ioc_c2_ip_01",
            type="ip",
            value="198.51.100.24",
            verdict="malicious",
            trust_level="verified_human",
            quorum=QuorumSummaryDto(feeds_agree=3, total_feeds=3),
            conflicts=[],
            promoted_at="2026-09-12T14:30:00Z",
            promoter="SOC Cátedra Ciberdefensa",
            last_updated=now_iso,
        ),
        ThreatIntelIOCDto(
            ioc_id="ioc_ransom_hash_02",
            type="sha256",
            value="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            verdict="malicious",
            trust_level="unverified",
            quorum=QuorumSummaryDto(feeds_agree=2, total_feeds=3),
            conflicts=["VirusTotal reporta malware tipo Loader; OTX clasifica como heurístico dudoso"],
            promoted_at=None,
            promoter=None,
            last_updated=now_iso,
        ),
        ThreatIntelIOCDto(
            ioc_id="ioc_phish_domain_03",
            type="domain",
            value="auth-verify-portal.net",
            verdict="malicious",
            trust_level="unverified",
            quorum=QuorumSummaryDto(feeds_agree=2, total_feeds=2),
            conflicts=[],
            promoted_at=None,
            promoter=None,
            last_updated=now_iso,
        ),
        ThreatIntelIOCDto(
            ioc_id="ioc_cdn_clean_04",
            type="ip",
            value="203.0.113.88",
            verdict="clean",
            trust_level="verified_human",
            quorum=QuorumSummaryDto(feeds_agree=3, total_feeds=3),
            conflicts=[],
            promoted_at="2026-09-10T09:15:00Z",
            promoter="Auditor Epistémico TALOS",
            last_updated=now_iso,
        ),
        ThreatIntelIOCDto(
            ioc_id="ioc_exploit_url_05",
            type="url",
            value="http://198.51.100.240/payload.bin",
            verdict="suspicious",
            trust_level="unverified",
            quorum=QuorumSummaryDto(feeds_agree=1, total_feeds=3),
            conflicts=["URLHaus confirma hosting activo; VirusTotal no posee muestras recientes (quórum insuficiente)"],
            promoted_at=None,
            promoter=None,
            last_updated=now_iso,
        ),
    ]

    return iocs
