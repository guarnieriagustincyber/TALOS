"""Base Academic Adapter with persistent SQLite caching, timeouts, and offline fallback.

Constraints:
- Decoupled from critical path: strictly an auxiliary metadata tool.
- Zero external dependencies: uses Python standard library (urllib, sqlite3, json).
- Offline fallback: network failures return None or cached results; never crash caller.
- Rate limiting and retry bounds: bounded to max_retries with timeout.
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import sqlite3
import time
from typing import Any, Dict, List, Optional
import urllib.error
import urllib.parse
import urllib.request

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AcademicMetadata(BaseModel):
    """Standardized academic metadata container."""
    title: Optional[str] = None
    authors: List[str] = Field(default_factory=list)
    year: Optional[int] = None
    doi: Optional[str] = None
    venue: Optional[str] = None
    citation_count: Optional[int] = None
    source_adapter: str
    raw_metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseAcademicAdapter:
    """Base class for decoupled academic metadata adapters."""

    def __init__(
        self,
        cache_db_path: Optional[Path] = None,
        timeout_seconds: float = 5.0,
        max_retries: int = 2,
    ) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self.cache_db_path = cache_db_path or Path("data/cache/academic_api_cache.sqlite3")
        self._init_cache()

    def _init_cache(self) -> None:
        """Initialize SQLite caching schema."""
        self.cache_db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.cache_db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS api_cache (
                    cache_key TEXT PRIMARY KEY,
                    response_json TEXT NOT NULL,
                    cached_at TIMESTAMP NOT NULL
                )
                """
            )
            conn.commit()

    def _get_cached(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached JSON payload if available."""
        try:
            with sqlite3.connect(self.cache_db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT response_json FROM api_cache WHERE cache_key = ?",
                    (cache_key,),
                )
                row = cursor.fetchone()
                if row:
                    return json.loads(row[0])
        except Exception as e:
            logger.warning(f"Cache read error: {e}")
        return None

    def _set_cached(self, cache_key: str, data: Dict[str, Any]) -> None:
        """Store JSON response in SQLite cache."""
        try:
            with sqlite3.connect(self.cache_db_path) as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO api_cache (cache_key, response_json, cached_at)
                    VALUES (?, ?, ?)
                    """,
                    (cache_key, json.dumps(data), datetime.now(timezone.utc).isoformat()),
                )
                conn.commit()
        except Exception as e:
            logger.warning(f"Cache write error: {e}")

    def fetch_json(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Fetch JSON from endpoint with caching, timeout, and offline fallback."""
        if params:
            query_str = urllib.parse.urlencode(params)
            sep = "&" if "?" in url else "?"
            full_url = f"{url}{sep}{query_str}"
        else:
            full_url = url

        cache_key = full_url
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        req_headers = {
            "User-Agent": "TALOS-Research-Bot/2.0 (Academic Metadata Ingestion)",
            "Accept": "application/json",
        }
        if headers:
            req_headers.update(headers)

        req = urllib.request.Request(full_url, headers=req_headers)

        for attempt in range(self.max_retries):
            try:
                with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                    if resp.status == 200:
                        raw_data = resp.read().decode("utf-8")
                        parsed = json.loads(raw_data)
                        self._set_cached(cache_key, parsed)
                        return parsed
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as e:
                logger.debug(f"Network fetch failed (attempt {attempt+1}/{self.max_retries}) for {full_url}: {e}")
                time.sleep(0.1 * (attempt + 1))
            except Exception as e:
                logger.warning(f"Unexpected adapter fetch error: {e}")
                break

        return None
