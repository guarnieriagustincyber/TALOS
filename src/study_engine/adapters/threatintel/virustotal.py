"""VirusTotal Threat Intelligence Adapter (Phase E4, Namespace [TF#]).

Provides deterministic lookup interface for file hashes, IPs, and domains with 12h TTL.
"""

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional
from study_engine.adapters.threatintel.base import (
    IOCIndicator,
    ThreatFeedType,
    ThreatIntelAdapter,
    ThreatIntelCache,
    ThreatIntelResult,
)


class VirusTotalAdapter(ThreatIntelAdapter):
    """Adapter for VirusTotal feeds."""

    def __init__(
        self,
        cache: Optional[ThreatIntelCache] = None,
        mock_data: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(feed_type=ThreatFeedType.VIRUSTOTAL, cache=cache, ttl_hours=12)
        self.mock_data = mock_data or {}

    def query_ioc_direct(self, indicator: IOCIndicator) -> ThreatIntelResult:
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=self.ttl_hours)

        data = self.mock_data.get(indicator.ioc_value)
        if data:
            return ThreatIntelResult(
                feed_name=self.feed_type.value,
                ioc_value=indicator.ioc_value,
                verdict=data.get("verdict", "unknown"),
                confidence_score=data.get("confidence_score", 0.8),
                raw_tags=data.get("tags", ["malware", "virustotal"]),
                fetched_at=now,
                expires_at=expires,
                details=data.get("details", {}),
            )

        # Default clean / unknown for unmocked offline indicators
        return ThreatIntelResult(
            feed_name=self.feed_type.value,
            ioc_value=indicator.ioc_value,
            verdict="unknown",
            confidence_score=0.1,
            raw_tags=["virustotal", "unrecorded"],
            fetched_at=now,
            expires_at=expires,
            details={"positives": 0, "total": 70},
        )
