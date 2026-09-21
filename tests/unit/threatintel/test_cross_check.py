"""Unit tests for Threat Intelligence Cross-Check Engine (Phase E4, Namespace [TF#])."""

from datetime import datetime, timezone, timedelta
import pytest
from study_engine.adapters.threatintel.base import (
    IOCIndicator,
    IOCType,
    ThreatFeedType,
    ThreatIntelResult,
)
from study_engine.adapters.threatintel.virustotal import VirusTotalAdapter
from study_engine.adapters.threatintel.otx import OTXAdapter
from study_engine.adapters.threatintel.abusech import AbuseCHAdapter
from study_engine.adapters.threatintel.cross_check import CrossCheckEngine


def test_cross_check_corroborated_malicious() -> None:
    ioc = "203.0.113.195"
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=12)

    r_vt = ThreatIntelResult(
        feed_name="virustotal",
        ioc_value=ioc,
        verdict="malicious",
        confidence_score=0.9,
        fetched_at=now,
        expires_at=expires,
    )
    r_otx = ThreatIntelResult(
        feed_name="otx",
        ioc_value=ioc,
        verdict="malicious",
        confidence_score=0.85,
        fetched_at=now,
        expires_at=expires,
    )

    engine = CrossCheckEngine()
    verdict = engine.evaluate_results(ioc, [r_vt, r_otx], now=now)

    assert verdict.corroborated is True
    assert verdict.status_code == "CORROBORATED"
    assert verdict.verdict == "malicious"
    assert verdict.feed_count == 2
    assert verdict.has_conflicts is False


def test_cross_check_single_feed_fails_closed() -> None:
    """Requirement: Single feed receives UNSUPPORTED_SINGLE_FEED and corroborated=False."""
    ioc = "203.0.113.50"
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=12)

    r_vt = ThreatIntelResult(
        feed_name="virustotal",
        ioc_value=ioc,
        verdict="malicious",
        confidence_score=0.9,
        fetched_at=now,
        expires_at=expires,
    )

    engine = CrossCheckEngine()
    verdict = engine.evaluate_results(ioc, [r_vt], now=now)

    assert verdict.corroborated is False
    assert verdict.status_code == "UNSUPPORTED_SINGLE_FEED"
    assert verdict.feed_count == 1


def test_cross_check_conflict_exposed_without_smoothing() -> None:
    """Requirement: Divergent verdicts exposed directly as CONFLICT_EXPOSED, never smoothed."""
    ioc = "198.51.100.77"
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=12)

    r_vt = ThreatIntelResult(
        feed_name="virustotal",
        ioc_value=ioc,
        verdict="malicious",
        confidence_score=0.95,
        fetched_at=now,
        expires_at=expires,
    )
    r_otx = ThreatIntelResult(
        feed_name="otx",
        ioc_value=ioc,
        verdict="clean",
        confidence_score=0.80,
        fetched_at=now,
        expires_at=expires,
    )

    engine = CrossCheckEngine()
    verdict = engine.evaluate_results(ioc, [r_vt, r_otx], now=now)

    assert verdict.corroborated is False
    assert verdict.status_code == "CONFLICT_EXPOSED"
    assert verdict.verdict == "divergent"
    assert verdict.has_conflicts is True
    assert len(verdict.conflicts) == 2


def test_cross_check_stale_feed_excluded() -> None:
    """Stale feed is not counted towards corroboration quorum."""
    ioc = "203.0.113.1"
    now = datetime.now(timezone.utc)

    # One fresh feed, one stale feed
    r_fresh = ThreatIntelResult(
        feed_name="virustotal",
        ioc_value=ioc,
        verdict="malicious",
        confidence_score=0.9,
        fetched_at=now,
        expires_at=now + timedelta(hours=12),
        is_stale=False,
    )
    r_stale = ThreatIntelResult(
        feed_name="otx",
        ioc_value=ioc,
        verdict="UNSUPPORTED_STALE",
        confidence_score=0.8,
        fetched_at=now - timedelta(hours=30),
        expires_at=now - timedelta(hours=6),
        is_stale=True,
    )

    engine = CrossCheckEngine()
    verdict = engine.evaluate_results(ioc, [r_fresh, r_stale], now=now)

    # Because r_stale is ignored, remaining feed_count is 1 -> fails with UNSUPPORTED_SINGLE_FEED
    assert verdict.corroborated is False
    assert verdict.status_code == "UNSUPPORTED_SINGLE_FEED"
    assert verdict.feed_count == 1
