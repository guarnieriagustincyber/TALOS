"""Unit tests for Threat Intelligence Adapters and SQLite Caching (Phase E4, Namespace [TF#])."""

from datetime import datetime, timezone, timedelta
import pytest
from study_engine.adapters.threatintel.base import (
    IOCIndicator,
    IOCType,
    ThreatFeedType,
    ThreatIntelCache,
    ThreatIntelResult,
)
from study_engine.adapters.threatintel.virustotal import VirusTotalAdapter
from study_engine.adapters.threatintel.otx import OTXAdapter
from study_engine.adapters.threatintel.abusech import AbuseCHAdapter


def test_sqlite_cache_set_and_get() -> None:
    cache = ThreatIntelCache(db_path=":memory:")
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=12)

    res = ThreatIntelResult(
        feed_name="virustotal",
        ioc_value="192.0.2.1",
        verdict="malicious",
        confidence_score=0.95,
        raw_tags=["botnet", "c2"],
        fetched_at=now,
        expires_at=expires,
        is_stale=False,
        details={"score": 85},
    )
    cache.set(res, ioc_type=IOCType.IP)

    fetched = cache.get("192.0.2.1", "virustotal", now=now)
    assert fetched is not None
    assert fetched.verdict == "malicious"
    assert fetched.confidence_score == 0.95
    assert fetched.is_stale is False


def test_sqlite_cache_ttl_expiration_fails_closed() -> None:
    """Expired cached entries must return UNSUPPORTED_STALE and is_stale=True."""
    cache = ThreatIntelCache(db_path=":memory:")
    now = datetime.now(timezone.utc)
    expires = now + timedelta(hours=6)

    res = ThreatIntelResult(
        feed_name="urlhaus",
        ioc_value="http://malicious-site.example/payload.bin",
        verdict="malicious",
        confidence_score=0.90,
        raw_tags=["malware"],
        fetched_at=now,
        expires_at=expires,
        is_stale=False,
    )
    cache.set(res, ioc_type=IOCType.URL)

    # Check after TTL expiration (7 hours later)
    future = now + timedelta(hours=7)
    fetched = cache.get("http://malicious-site.example/payload.bin", "urlhaus", now=future)
    assert fetched is not None
    assert fetched.verdict == "UNSUPPORTED_STALE"
    assert fetched.is_stale is True


def test_adapters_query_direct_with_mock() -> None:
    mock_vt = {"198.51.100.1": {"verdict": "malicious", "confidence_score": 0.92, "tags": ["apt"]}}
    vt_adapter = VirusTotalAdapter(mock_data=mock_vt)

    ind = IOCIndicator(ioc_value="198.51.100.1", ioc_type=IOCType.IP)
    res = vt_adapter.query_ioc(ind)
    assert res.verdict == "malicious"
    assert res.confidence_score == 0.92
    assert "apt" in res.raw_tags
    assert res.feed_name == "virustotal"

    # Query unmocked returns clean/unknown
    ind_unknown = IOCIndicator(ioc_value="8.8.8.8", ioc_type=IOCType.IP)
    res_unknown = vt_adapter.query_ioc(ind_unknown)
    assert res_unknown.verdict == "unknown"
