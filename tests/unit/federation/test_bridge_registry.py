"""Unit tests for BridgeRegistry and TTL Governance (Phase E4, Amendment E4-2)."""

from datetime import datetime, timezone, timedelta
import pytest
from study_engine.federation.bridge_registry import BridgeRegistry, CrossNotebookBridge


def test_allowlist_loading_from_file() -> None:
    registry = BridgeRegistry(allowlist_path="config/bridges.allowlist.json")
    bridge = registry.find_bridge("fadena-prog", "fadena-so")
    assert bridge is not None
    assert bridge.bridge_id == "B-PROG-SO-MEM"
    assert "punteros" in bridge.topic_allowlist
    assert bridge.direction == "bidirectional"


def test_bridge_authorization_permitted_topic() -> None:
    registry = BridgeRegistry(allowlist_path="config/bridges.allowlist.json")
    ok, reason, b = registry.is_bridge_authorized("fadena-prog", "fadena-so", "punteros")
    assert ok is True
    assert b is not None
    assert b.bridge_id == "B-PROG-SO-MEM"


def test_bridge_authorization_rejected_unlisted_topic() -> None:
    registry = BridgeRegistry(allowlist_path="config/bridges.allowlist.json")
    ok, reason, b = registry.is_bridge_authorized("fadena-prog", "fadena-so", "unauthorized_topic")
    assert ok is False
    assert "not in bridge allow-list" in reason


def test_bridge_fail_closed_on_ttl_expiration() -> None:
    """Amendment E4-2: Expired bridge emits BRIDGE_EXPIRED and rejects authorization."""
    registry = BridgeRegistry(allowlist_path="config/bridges.allowlist.json")
    # Simulate time 120 days after bridge creation (ttl is 90 days)
    simulated_future = datetime(2027, 1, 1, tzinfo=timezone.utc)

    ok, reason, b = registry.is_bridge_authorized(
        "fadena-prog",
        "fadena-so",
        "punteros",
        now=simulated_future,
    )
    assert ok is False
    assert "expired" in reason.lower()

    # Check audit events for BRIDGE_EXPIRED
    events = [e for e in registry.get_audit_events() if e["event_type"] == "BRIDGE_EXPIRED"]
    assert len(events) >= 1


def test_filter_stale_in_flight_results() -> None:
    """Amendment E4-2: Stale in-flight results are marked and excluded."""
    registry = BridgeRegistry(allowlist_path="config/bridges.allowlist.json")
    bridge = registry.find_bridge("fadena-prog", "fadena-so")
    assert bridge is not None

    results = [{"chunk_id": "c1", "content": "test"}]
    # Test during valid period
    valid_res, is_stale = registry.filter_stale_in_flight_results(results, bridge, now=datetime(2026, 9, 20, tzinfo=timezone.utc))
    assert len(valid_res) == 1
    assert is_stale is False

    # Test when bridge has expired
    expired_time = datetime(2027, 2, 1, tzinfo=timezone.utc)
    filtered_res, is_stale = registry.filter_stale_in_flight_results(results, bridge, now=expired_time)
    assert len(filtered_res) == 0
    assert is_stale is True
    assert results[0].get("stale_bridge_result") is True
