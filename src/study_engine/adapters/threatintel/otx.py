"""AlienVault OTX Threat Intelligence Adapter (Phase E4, Namespace [TF#]).

Provides deterministic lookup interface for pulses and IOC indicators with 24h TTL.
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


class OTXAdapter(ThreatIntelAdapter):
    """Adapter for AlienVault OTX feeds."""

    def __init__(
        self,
        cache: Optional[ThreatIntelCache] = None,
        mock_data: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(feed_type=ThreatFeedType.OTX, cache=cache, ttl_hours=24)
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
                confidence_score=data.get("confidence_score", 0.75),
                raw_tags=data.get("tags", ["otx", "alienvault"]),
                fetched_at=now,
                expires_at=expires,
                details=data.get("details", {}),
            )

        return ThreatIntelResult(
            feed_name=self.feed_type.value,
            ioc_value=indicator.ioc_value,
            verdict="unknown",
            confidence_score=0.1,
            raw_tags=["otx", "no_pulse"],
            fetched_at=now,
            expires_at=expires,
            details={"pulse_count": 0},
        )
