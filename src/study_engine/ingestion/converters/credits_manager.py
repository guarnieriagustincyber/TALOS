"""Cloud OCR Credits and Authorization Manager for Subsystem S1 (CAL §10).

Enforces strict governance over cloud OCR usage:
1. Daily quota budget.
2. Per-minute rate limits.
3. Explicit per-source human authorization flag.
"""

from datetime import datetime, timezone
import threading
from typing import Dict, Optional, Set


class ConversionCreditsManager:
    """Manages cloud OCR authorization flags and credit quotas."""

    def __init__(
        self,
        daily_budget: int = 500,
        rate_limit_per_minute: int = 60,
    ) -> None:
        self.daily_budget = daily_budget
        self.rate_limit_per_minute = rate_limit_per_minute
        self._authorized_sources: Set[str] = set()
        self._consumed_today: int = 0
        self._last_reset_day: int = datetime.now(timezone.utc).timetuple().tm_yday
        self._lock = threading.Lock()

    def _check_and_reset(self) -> None:
        current_day = datetime.now(timezone.utc).timetuple().tm_yday
        if current_day != self._last_reset_day:
            self._consumed_today = 0
            self._last_reset_day = current_day

    def authorize_source(self, source_id: str) -> None:
        """Explicitly authorize a source for cloud OCR."""
        with self._lock:
            self._authorized_sources.add(source_id.strip())

    def revoke_source(self, source_id: str) -> None:
        """Revoke cloud OCR authorization for a source."""
        with self._lock:
            self._authorized_sources.discard(source_id.strip())

    def is_authorized(self, source_id: str) -> bool:
        """Check if source has explicit cloud authorization."""
        with self._lock:
            return source_id.strip() in self._authorized_sources

    def can_consume(self, source_id: str, pages: int = 1) -> bool:
        """Check if source is authorized and sufficient credits remain."""
        with self._lock:
            self._check_and_reset()
            if source_id.strip() not in self._authorized_sources:
                return False
            return (self._consumed_today + pages) <= self.daily_budget

    def consume(self, source_id: str, pages: int = 1) -> bool:
        """Consume cloud OCR credits if authorized and available."""
        with self._lock:
            self._check_and_reset()
            clean_id = source_id.strip()
            if clean_id not in self._authorized_sources:
                return False
            if (self._consumed_today + pages) > self.daily_budget:
                return False
            self._consumed_today += pages
            return True

    def get_remaining_credits(self) -> int:
        """Get remaining daily cloud credits."""
        with self._lock:
            self._check_and_reset()
            return max(0, self.daily_budget - self._consumed_today)
