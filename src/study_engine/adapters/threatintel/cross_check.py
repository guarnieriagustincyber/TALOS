"""Threat Intelligence Cross-Check Engine (Phase E4, Ontological Namespace [TF#]).

Enforces:
1. Multi-feed corroboration (minimum 2 feeds required).
2. Single-feed rejection: items with only 1 feed receive UNSUPPORTED_SINGLE_FEED.
3. Conflict exposure without smoothing: Divergent verdicts (e.g. malicious vs clean)
   are explicitly surfaced as conflicts, never averaged or smoothed.
4. Stale feed exclusion: Stale feeds are not counted towards minimum feed threshold.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, ConfigDict, Field

from study_engine.adapters.threatintel.base import (
    IOCIndicator,
    ThreatIntelAdapter,
    ThreatIntelResult,
)


class CrossCheckVerdict(BaseModel):
    """Corroborated verdict across multiple threat intelligence feeds."""

    model_config = ConfigDict(frozen=True)

    ioc_value: str
    corroborated: bool
    status_code: str  # "CORROBORATED", "UNSUPPORTED_SINGLE_FEED", "CONFLICT_EXPOSED", "ALL_STALE"
    verdict: str  # "malicious", "clean", "suspicious", "divergent", "unsupported"
    contributing_feeds: List[str]
    feed_count: int
    has_conflicts: bool
    conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    results: List[ThreatIntelResult] = Field(default_factory=list)


class CrossCheckEngine:
    """Orchestrates multi-feed queries and verifies corroboration invariant."""

    def __init__(self, adapters: Optional[List[ThreatIntelAdapter]] = None) -> None:
        self.adapters = adapters or []

    def add_adapter(self, adapter: ThreatIntelAdapter) -> None:
        self.adapters.append(adapter)

    def cross_check(
        self,
        indicator: IOCIndicator,
        now: Optional[datetime] = None,
    ) -> CrossCheckVerdict:
        """Query all registered adapters and synthesize multi-feed consensus."""
        current_time = now or datetime.now(timezone.utc)
        results: List[ThreatIntelResult] = []

        for adapter in self.adapters:
            res = adapter.query_ioc(indicator, now=current_time)
            results.append(res)

        return self.evaluate_results(indicator.ioc_value, results, now=current_time)

    def evaluate_results(
        self,
        ioc_value: str,
        results: List[ThreatIntelResult],
        now: Optional[datetime] = None,
    ) -> CrossCheckVerdict:
        """Evaluate corroboration and detect conflicts across results without smoothing."""
        # 1. Filter out stale feeds or unknown unrecorded responses
        fresh_results = [r for r in results if not r.is_stale and r.verdict != "UNSUPPORTED_STALE"]
        if not fresh_results:
            return CrossCheckVerdict(
                ioc_value=ioc_value,
                corroborated=False,
                status_code="ALL_STALE",
                verdict="unsupported",
                contributing_feeds=[],
                feed_count=0,
                has_conflicts=False,
                conflicts=[],
                results=results,
            )

        # Non-empty meaningful verdicts (excluding neutral unknown)
        substantive = [r for r in fresh_results if r.verdict in ("malicious", "suspicious", "clean")]
        contributing_names = [r.feed_name for r in substantive]
        feed_count = len(substantive)

        # 2. Single-feed rule: feed_count < 2 must fail-closed
        if feed_count < 2:
            return CrossCheckVerdict(
                ioc_value=ioc_value,
                corroborated=False,
                status_code="UNSUPPORTED_SINGLE_FEED",
                verdict="unsupported",
                contributing_feeds=contributing_names,
                feed_count=feed_count,
                has_conflicts=False,
                conflicts=[],
                results=results,
            )

        # 3. Detect conflicts between verdicts (e.g. malicious vs clean)
        verdicts_set: Set[str] = {r.verdict for r in substantive}
        has_conflict = ("malicious" in verdicts_set and "clean" in verdicts_set)

        if has_conflict:
            conflicts_list = [
                {
                    "feed_name": r.feed_name,
                    "verdict": r.verdict,
                    "confidence": r.confidence_score,
                }
                for r in substantive
            ]
            return CrossCheckVerdict(
                ioc_value=ioc_value,
                corroborated=False,
                status_code="CONFLICT_EXPOSED",
                verdict="divergent",
                contributing_feeds=contributing_names,
                feed_count=feed_count,
                has_conflicts=True,
                conflicts=conflicts_list,
                results=results,
            )

        # 4. Consensus reached
        consensus_verdict = substantive[0].verdict
        return CrossCheckVerdict(
            ioc_value=ioc_value,
            corroborated=True,
            status_code="CORROBORATED",
            verdict=consensus_verdict,
            contributing_feeds=contributing_names,
            feed_count=feed_count,
            has_conflicts=False,
            conflicts=[],
            results=results,
        )
