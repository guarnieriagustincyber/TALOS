"""Base Threat Intelligence Adapter and SQLite Cache (Phase E4, Namespace [TF#]).

Maintains:
1. Standardized IOC representation (IP, Domain, Hash, URL).
2. Local SQLite cache with strict TTL enforcement.
3. Fail-closed expiration policy: Expired entries return status UNSUPPORTED_STALE.
4. Default TTLs:
   - urlhaus: 6 hours
   - threatfox: 6 hours
   - otx: 24 hours
   - virustotal: 12 hours
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from enum import Enum
import json
from pathlib import Path
import sqlite3
import threading
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ThreatFeedType(str, Enum):
    VIRUSTOTAL = "virustotal"
    OTX = "otx"
    URLHAUS = "urlhaus"
    THREATFOX = "threatfox"


DEFAULT_FEED_TTLS_HOURS = {
    ThreatFeedType.VIRUSTOTAL: 12,
    ThreatFeedType.OTX: 24,
    ThreatFeedType.URLHAUS: 6,
    ThreatFeedType.THREATFOX: 6,
}


class IOCType(str, Enum):
    IP = "ip"
    DOMAIN = "domain"
    HASH_SHA256 = "sha256"
    HASH_MD5 = "md5"
    URL = "url"


class IOCIndicator(BaseModel):
    """Normalized Indicator of Compromise."""

    model_config = ConfigDict(frozen=True)

    ioc_value: str = Field(..., min_length=1)
    ioc_type: IOCType
    description: Optional[str] = None


class ThreatIntelResult(BaseModel):
    """Standardized response from a Threat Intelligence feed."""

    model_config = ConfigDict(frozen=True)

    feed_name: str
    ioc_value: str
    verdict: str  # "malicious", "suspicious", "clean", "unknown", "UNSUPPORTED_STALE"
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    raw_tags: List[str] = Field(default_factory=list)
    fetched_at: datetime
    expires_at: datetime
    is_stale: bool = False
    details: Dict[str, Any] = Field(default_factory=dict)


class ThreatIntelCache:
    """Thread-safe SQLite persistent cache for Threat Intelligence IOC queries."""

    def __init__(self, db_path: str = ":memory:") -> None:
        self.db_path = db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self) -> None:
        with self._lock:
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS threat_ioc_cache (
                    ioc_value TEXT NOT NULL,
                    feed_name TEXT NOT NULL,
                    ioc_type TEXT NOT NULL,
                    verdict TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    raw_tags TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    fetched_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    PRIMARY KEY (ioc_value, feed_name)
                )
            """)
            self._conn.commit()

    def get(
        self,
        ioc_value: str,
        feed_name: str,
        now: Optional[datetime] = None,
    ) -> Optional[ThreatIntelResult]:
        """Fetch cached IOC result. If expired, returns ThreatIntelResult with is_stale=True and verdict=UNSUPPORTED_STALE."""
        current_time = now or datetime.now(timezone.utc)
        clean_ioc = ioc_value.strip()

        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM threat_ioc_cache WHERE ioc_value = ? AND feed_name = ?",
                (clean_ioc, feed_name),
            ).fetchone()

            if not row:
                return None

            fetched_at = datetime.fromisoformat(row["fetched_at"])
            expires_at = datetime.fromisoformat(row["expires_at"])
            tags = json.loads(row["raw_tags"])
            details = json.loads(row["details_json"])

            if current_time > expires_at:
                return ThreatIntelResult(
                    feed_name=row["feed_name"],
                    ioc_value=row["ioc_value"],
                    verdict="UNSUPPORTED_STALE",
                    confidence_score=row["confidence_score"],
                    raw_tags=tags,
                    fetched_at=fetched_at,
                    expires_at=expires_at,
                    is_stale=True,
                    details=details,
                )

            return ThreatIntelResult(
                feed_name=row["feed_name"],
                ioc_value=row["ioc_value"],
                verdict=row["verdict"],
                confidence_score=row["confidence_score"],
                raw_tags=tags,
                fetched_at=fetched_at,
                expires_at=expires_at,
                is_stale=False,
                details=details,
            )

    def set(self, result: ThreatIntelResult, ioc_type: IOCType = IOCType.IP) -> None:
        """Store or update threat feed result."""
        with self._lock:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO threat_ioc_cache
                (ioc_value, feed_name, ioc_type, verdict, confidence_score, raw_tags, details_json, fetched_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.ioc_value,
                    result.feed_name,
                    ioc_type.value,
                    result.verdict,
                    result.confidence_score,
                    json.dumps(result.raw_tags),
                    json.dumps(result.details),
                    result.fetched_at.isoformat(),
                    result.expires_at.isoformat(),
                ),
            )
            self._conn.commit()


class ThreatIntelAdapter(ABC):
    """Abstract interface for threat intelligence feeds."""

    def __init__(
        self,
        feed_type: ThreatFeedType,
        cache: Optional[ThreatIntelCache] = None,
        ttl_hours: Optional[int] = None,
    ) -> None:
        self.feed_type = feed_type
        self.cache = cache or ThreatIntelCache()
        self.ttl_hours = ttl_hours if ttl_hours is not None else DEFAULT_FEED_TTLS_HOURS.get(feed_type, 12)

    @abstractmethod
    def query_ioc_direct(self, indicator: IOCIndicator) -> ThreatIntelResult:
        """Query direct external or mocked feed source."""
        pass

    def query_ioc(
        self,
        indicator: IOCIndicator,
        now: Optional[datetime] = None,
        force_refresh: bool = False,
    ) -> ThreatIntelResult:
        """Query IOC with cache lookup and TTL fail-closed policy."""
        current_time = now or datetime.now(timezone.utc)

        if not force_refresh:
            cached = self.cache.get(indicator.ioc_value, self.feed_type.value, now=current_time)
            if cached:
                return cached

        # Execute direct query
        result = self.query_ioc_direct(indicator)
        self.cache.set(result, ioc_type=indicator.ioc_type)
        return result
