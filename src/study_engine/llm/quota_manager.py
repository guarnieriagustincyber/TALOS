"""QuotaManager - Proactive Daily Token & Request Quota Management (Fase 5.9 / Pilar 4 / Ajuste 2).

Maintains persistent usage counters in SQLite with WAL mode (PRAGMA journal_mode=WAL).
Enforces proactive failover at 90% daily threshold to prevent HTTP 429 rate limit errors.
"""

from datetime import datetime, timezone
import logging
from pathlib import Path
import sqlite3
import threading
from typing import Any, Dict, Optional, Tuple, Union

logger = logging.getLogger(__name__)

DEFAULT_PROVIDER_QUOTAS: Dict[str, Optional[int]] = {
    "nvidia": 1_000_000,
    "cerebras": 1_000_000,
    "sambanova": 1_000_000,
    "cloudflare": 100_000,
    "ollama": None,  # Unlimited
    "mock": 10_000_000,
}


class QuotaManager:
    """Manages daily quotas and pro-active conmutation before 429s."""

    def __init__(
        self,
        db_path: Union[str, Path] = ":memory:",
        daily_quotas: Optional[Dict[str, Optional[int]]] = None,
        proactive_threshold_ratio: float = 0.90,
    ) -> None:
        self.db_path = str(db_path)
        self.daily_quotas: Dict[str, Optional[int]] = (
            dict(daily_quotas) if daily_quotas is not None else dict(DEFAULT_PROVIDER_QUOTAS)
        )
        self.proactive_threshold_ratio = proactive_threshold_ratio
        self._is_memory = self.db_path == ":memory:"
        self._lock = threading.Lock()

        if not self._is_memory:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        if not self._is_memory:
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA synchronous=NORMAL")
            self._conn.execute("PRAGMA busy_timeout = 5000")

        self._init_db()

    def _init_db(self) -> None:
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS daily_provider_quotas (
                    provider_name TEXT NOT NULL,
                    utc_date TEXT NOT NULL,
                    tokens_used INTEGER NOT NULL DEFAULT 0,
                    requests_count INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (provider_name, utc_date)
                )
                """
            )
            self._conn.commit()

    @staticmethod
    def _current_utc_date() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def record_usage(
        self,
        provider_name: str,
        tokens: int,
        utc_date: Optional[str] = None,
    ) -> None:
        """Record completed request token consumption."""
        date_str = utc_date or self._current_utc_date()
        with self._lock:
            self._conn.execute(
                """
                INSERT INTO daily_provider_quotas (provider_name, utc_date, tokens_used, requests_count)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(provider_name, utc_date) DO UPDATE SET
                    tokens_used = tokens_used + excluded.tokens_used,
                    requests_count = requests_count + 1
                """,
                (provider_name, date_str, tokens),
            )
            self._conn.commit()

    def get_usage(
        self,
        provider_name: str,
        utc_date: Optional[str] = None,
    ) -> Tuple[int, int]:
        """Return (tokens_used, requests_count) for the specified date."""
        date_str = utc_date or self._current_utc_date()
        with self._lock:
            cursor = self._conn.execute(
                """
                SELECT tokens_used, requests_count
                FROM daily_provider_quotas
                WHERE provider_name = ? AND utc_date = ?
                """,
                (provider_name, date_str),
            )
            row = cursor.fetchone()
            if row:
                return int(row["tokens_used"]), int(row["requests_count"])
            return 0, 0

    def check_quota(
        self,
        provider_name: str,
        estimated_tokens: int = 0,
        utc_date: Optional[str] = None,
    ) -> bool:
        """Check if provider can accept request within proactive 90% threshold.

        Returns True if request can proceed, False if quota is saturated.
        """
        limit = self.daily_quotas.get(provider_name)
        if limit is None or limit <= 0:
            return True  # Unlimited

        used_tokens, _ = self.get_usage(provider_name, utc_date=utc_date)
        max_allowed = int(limit * self.proactive_threshold_ratio)

        if used_tokens + estimated_tokens >= max_allowed:
            logger.warning(
                f"[QUOTA MANAGER] Provider {provider_name} exceeded proactive threshold "
                f"({used_tokens + estimated_tokens} >= {max_allowed} of {limit})."
            )
            return False

        return True

    def get_status(
        self,
        provider_name: Optional[str] = None,
        utc_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return status dictionary for one or all providers."""
        date_str = utc_date or self._current_utc_date()
        if provider_name:
            used_tokens, reqs = self.get_usage(provider_name, utc_date=date_str)
            limit = self.daily_quotas.get(provider_name)
            rem = max(0, limit - used_tokens) if limit is not None else None
            is_saturated = not self.check_quota(provider_name, utc_date=date_str)
            return {
                "provider": provider_name,
                "date": date_str,
                "tokens_used": used_tokens,
                "requests_count": reqs,
                "daily_limit": limit,
                "remaining_quota": rem,
                "saturated": is_saturated,
            }

        result: Dict[str, Any] = {}
        for p in self.daily_quotas:
            result[p] = self.get_status(p, utc_date=date_str)
        return result

    def close(self) -> None:
        """Close SQLite connection."""
        with self._lock:
            try:
                self._conn.close()
            except Exception:
                pass


class BudgetCeilingExceededError(Exception):
    """Raised when spending surpasses hard session or daily USD budget ceiling."""
    pass


class BudgetCeilingManager:
    """Hard financial circuit breaker enforcing session (< $1.00 USD) and daily (< $5.00 USD) ceilings.

    Prevents runaway expenditure during infinite retry storms, automated testing loops, or misconfigured agents.
    """

    def __init__(
        self,
        max_session_usd: float = 1.00,
        max_daily_usd: float = 5.00,
        pricing_table: Optional[Any] = None,
    ) -> None:
        self.max_session_usd = float(max_session_usd)
        self.max_daily_usd = float(max_daily_usd)
        self._pricing_table = pricing_table
        self._session_spend: Dict[str, float] = {}
        self._daily_spend: Dict[str, float] = {}
        self._session_tripped: Dict[str, bool] = {}
        self._daily_tripped: Dict[str, bool] = {}
        self._lock = threading.Lock()

    def _get_pricing_table(self) -> Any:
        if self._pricing_table is None:
            from study_engine.llm.factory import LLMPricingTable
            self._pricing_table = LLMPricingTable()
        return self._pricing_table

    @staticmethod
    def _current_utc_date() -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    def calculate_cost(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
    ) -> float:
        """Calculate exact USD cost using authoritative LLMPricingTable."""
        pt = self._get_pricing_table()
        return pt.calculate_cost(provider, model, prompt_tokens, completion_tokens)

    def can_proceed(
        self,
        session_id: str,
        estimated_cost_usd: float = 0.0,
        utc_date: Optional[str] = None,
    ) -> bool:
        """Check if request can proceed without violating session or daily budget ceiling."""
        date_str = utc_date or self._current_utc_date()
        with self._lock:
            if self._session_tripped.get(session_id, False):
                return False
            if self._daily_tripped.get(date_str, False):
                return False

            current_session = self._session_spend.get(session_id, 0.0)
            if (current_session + estimated_cost_usd) > self.max_session_usd:
                return False

            current_daily = self._daily_spend.get(date_str, 0.0)
            if (current_daily + estimated_cost_usd) > self.max_daily_usd:
                return False

            return True

    def record_spend(
        self,
        session_id: str,
        cost_usd: float,
        utc_date: Optional[str] = None,
    ) -> float:
        """Record monetary spend for session and day, triggering automatic cut-off if ceiling reached."""
        date_str = utc_date or self._current_utc_date()
        with self._lock:
            # Update session
            new_session = self._session_spend.get(session_id, 0.0) + cost_usd
            self._session_spend[session_id] = round(new_session, 6)
            if new_session >= self.max_session_usd:
                self._session_tripped[session_id] = True
                logger.warning(
                    f"[BUDGET CEILING] Session {session_id} exceeded budget ceiling: "
                    f"${new_session:.4f} >= ${self.max_session_usd:.2f} USD. Automatic cut-off tripped."
                )

            # Update daily
            new_daily = self._daily_spend.get(date_str, 0.0) + cost_usd
            self._daily_spend[date_str] = round(new_daily, 6)
            if new_daily >= self.max_daily_usd:
                self._daily_tripped[date_str] = True
                logger.warning(
                    f"[BUDGET CEILING] Daily spend exceeded limit on {date_str}: "
                    f"${new_daily:.4f} >= ${self.max_daily_usd:.2f} USD. Global automatic cut-off tripped."
                )

            if self._session_tripped.get(session_id, False):
                raise BudgetCeilingExceededError(
                    f"Session budget ceiling exceeded: ${new_session:.4f} >= ${self.max_session_usd:.2f}"
                )
            if self._daily_tripped.get(date_str, False):
                raise BudgetCeilingExceededError(
                    f"Daily budget ceiling exceeded: ${new_daily:.4f} >= ${self.max_daily_usd:.2f}"
                )

            return new_session

    def get_session_spend(self, session_id: str) -> float:
        with self._lock:
            return self._session_spend.get(session_id, 0.0)

    def get_daily_spend(self, utc_date: Optional[str] = None) -> float:
        date_str = utc_date or self._current_utc_date()
        with self._lock:
            return self._daily_spend.get(date_str, 0.0)

    def is_session_tripped(self, session_id: str) -> bool:
        with self._lock:
            return self._session_tripped.get(session_id, False)

    def is_daily_tripped(self, utc_date: Optional[str] = None) -> bool:
        date_str = utc_date or self._current_utc_date()
        with self._lock:
            return self._daily_tripped.get(date_str, False)

