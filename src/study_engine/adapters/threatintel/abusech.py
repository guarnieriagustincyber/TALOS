"""Abuse.ch (URLhaus / ThreatFox) Threat Intelligence Adapter (Phase E4, Namespace [TF#]).

Provides deterministic lookup interface for botnet/malware IOCs with 6h TTL.
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


class AbuseCHAdapter(ThreatIntelAdapter):
    """Adapter for Abuse.ch URLhaus / ThreatFox feeds."""

    def __init__(
        self,
        subfeed: ThreatFeedType = ThreatFeedType.URLHAUS,
        cache: Optional[ThreatIntelCache] = None,
        mock_data: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        super().__init__(feed_type=subfeed, cache=cache, ttl_hours=6)
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
                confidence_score=data.get("confidence_score", 0.9),
                raw_tags=data.get("tags", [self.feed_type.value, "abuse.ch"]),
                fetched_at=now,
                expires_at=expires,
                details=data.get("details", {}),
            )

        return ThreatIntelResult(
            feed_name=self.feed_type.value,
            ioc_value=indicator.ioc_value,
            verdict="unknown",
            confidence_score=0.1,
            raw_tags=[self.feed_type.value, "not_found"],
            fetched_at=now,
            expires_at=expires,
            details={"threat_entry": False},
        )
