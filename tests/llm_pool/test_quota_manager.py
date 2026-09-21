"""Unit tests for QuotaManager persistent token tracking (Fase 5.9 / Pilar 4 / Ajuste 2)."""

from pathlib import Path
import sqlite3
import pytest

from study_engine.llm.quota_manager import QuotaManager


def test_quota_manager_wal_mode(tmp_path: Path):
    """Ajuste 2: QuotaManager should configure SQLite with WAL mode on persistent databases."""
    db_file = tmp_path / "quotas_wal_test.db"
    qm = QuotaManager(db_path=db_file)

    conn = sqlite3.connect(str(db_file))
    cursor = conn.execute("PRAGMA journal_mode")
    journal_mode = cursor.fetchone()[0]
    cursor.close()
    conn.close()

    assert journal_mode.upper() == "WAL"


def test_quota_manager_record_and_get_usage(tmp_path: Path):
    """QuotaManager should persist and accumulate tokens and request counts."""
    qm = QuotaManager(db_path=tmp_path / "quotas.db")
    tokens, reqs = qm.get_usage("cerebras", utc_date="2026-05-01")
    assert tokens == 0
    assert reqs == 0

    qm.record_usage("cerebras", tokens=500, utc_date="2026-05-01")
    qm.record_usage("cerebras", tokens=350, utc_date="2026-05-01")

    tokens, reqs = qm.get_usage("cerebras", utc_date="2026-05-01")
    assert tokens == 850
    assert reqs == 2


def test_quota_manager_proactive_90_percent_cutoff():
    """QuotaManager should report saturated when tokens exceed 90% of daily limit."""
    custom_limits = {
        "provider_a": 1000,
        "provider_b": None,  # Unlimited
    }
    qm = QuotaManager(
        db_path=":memory:",
        daily_quotas=custom_limits,
        proactive_threshold_ratio=0.90,
    )

    # Initially within quota
    assert qm.check_quota("provider_a", estimated_tokens=100) is True

    # Accumulate up to 890 tokens (89% < 90%)
    qm.record_usage("provider_a", tokens=890)
    assert qm.check_quota("provider_a", estimated_tokens=5) is True

    # 890 + 15 = 905 >= 900 (90%) -> Proactive failover triggered!
    assert qm.check_quota("provider_a", estimated_tokens=15) is False

    # Unlimited provider always proceeds
    qm.record_usage("provider_b", tokens=1_000_000)
    assert qm.check_quota("provider_b", estimated_tokens=500_000) is True


def test_quota_manager_daily_rollover(tmp_path: Path):
    """QuotaManager should partition counts by UTC date."""
    qm = QuotaManager(
        db_path=tmp_path / "rollover.db",
        daily_quotas={"cerebras": 1000},
    )

    qm.record_usage("cerebras", tokens=950, utc_date="2026-01-01")
    assert qm.check_quota("cerebras", utc_date="2026-01-01") is False

    # Next day: counts are fresh
    tokens_day2, reqs_day2 = qm.get_usage("cerebras", utc_date="2026-01-02")
    assert tokens_day2 == 0
    assert reqs_day2 == 0
    assert qm.check_quota("cerebras", utc_date="2026-01-02") is True


def test_quota_manager_get_status():
    """QuotaManager should provide diagnostic status dictionary."""
    qm = QuotaManager(
        db_path=":memory:",
        daily_quotas={"test_prov": 2000},
    )
    qm.record_usage("test_prov", tokens=500)

    status = qm.get_status("test_prov")
    assert status["provider"] == "test_prov"
    assert status["tokens_used"] == 500
    assert status["requests_count"] == 1
    assert status["daily_limit"] == 2000
    assert status["remaining_quota"] == 1500
    assert status["saturated"] is False
