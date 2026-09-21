"""Cross-Notebook Bridge Registry and TTL Governance (Phase E4, Amendment E4-2).

Enforces:
1. Pure allow-list containment for cross-notebook federation.
2. Directionality and topic constraints.
3. Strict fail-closed TTL expiration: expired bridge -> is_bridge_authorized() == False,
   emits BRIDGE_EXPIRED, and marks in-flight results as stale_bridge_result=True.
4. Dynamic allow-list reloads: hash change triggers atomic reload and emits ALLOWLIST_RELOADED.
"""

from datetime import datetime, timezone, timedelta
import hashlib
import json
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, ConfigDict, Field


class CrossNotebookBridge(BaseModel):
    """Typed contractual bridge permitting cross-notebook evidence crossing."""

    model_config = ConfigDict(frozen=True)

    bridge_id: str = Field(..., min_length=1)
    source_notebook: str = Field(..., min_length=1)
    target_notebook: str = Field(..., min_length=1)
    topic_allowlist: List[str] = Field(..., min_length=1)
    direction: str = Field(default="bidirectional", description="'unidirectional' | 'bidirectional'")
    ttl_days: int = Field(default=90, ge=0)
    created_at: datetime = Field(...)
    reviewer: str = Field(..., min_length=1)
    provenance_tag: str = Field(...)


class BridgeRegistry:
    """Manages bridge allow-list, monitors TTLs, and logs security audit events."""

    def __init__(self, allowlist_path: Optional[str] = "config/bridges.allowlist.json") -> None:
        self.allowlist_path = Path(allowlist_path) if allowlist_path else None
        self._bridges: Dict[str, CrossNotebookBridge] = {}
        self._current_hash: str = ""
        self._audit_events: List[Dict[str, Any]] = []
        self._lock = threading.Lock()

        if self.allowlist_path and self.allowlist_path.exists():
            self._load_allowlist()

    def _load_allowlist(self) -> None:
        """Load and parse allow-list JSON while tracking hash integrity."""
        raw_bytes = self.allowlist_path.read_bytes()
        new_hash = hashlib.sha256(raw_bytes).hexdigest()

        data = json.loads(raw_bytes.decode("utf-8"))
        bridges_raw = data.get("bridges", [])

        loaded: Dict[str, CrossNotebookBridge] = {}
        for b_dict in bridges_raw:
            created_at_dt = datetime.fromisoformat(b_dict["created_at"].replace("Z", "+00:00"))
            b_obj = CrossNotebookBridge(
                bridge_id=b_dict["bridge_id"],
                source_notebook=b_dict["source_notebook"],
                target_notebook=b_dict["target_notebook"],
                topic_allowlist=[t.lower().strip() for t in b_dict["topic_allowlist"]],
                direction=b_dict.get("direction", "bidirectional"),
                ttl_days=b_dict.get("ttl_days", 90),
                created_at=created_at_dt,
                reviewer=b_dict["reviewer"],
                provenance_tag=b_dict["provenance_tag"],
            )
            loaded[b_obj.bridge_id] = b_obj

        old_hash = self._current_hash
        self._bridges = loaded
        self._current_hash = new_hash

        if old_hash and old_hash != new_hash:
            self._record_event(
                event_type="ALLOWLIST_RELOADED",
                details={"old_hash": old_hash, "new_hash": new_hash, "count": len(loaded)},
            )

    def reload_if_modified(self) -> bool:
        """Check file hash and reload if modified on disk."""
        if not self.allowlist_path or not self.allowlist_path.exists():
            return False
        with self._lock:
            current_bytes = self.allowlist_path.read_bytes()
            new_hash = hashlib.sha256(current_bytes).hexdigest()
            if new_hash != self._current_hash:
                self._load_allowlist()
                return True
            return False

    def _record_event(self, event_type: str, details: Dict[str, Any]) -> None:
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "details": details,
        }
        self._audit_events.append(event)

    def is_bridge_expired(self, bridge: CrossNotebookBridge, now: Optional[datetime] = None) -> bool:
        """Evaluate if bridge has exceeded its authorized TTL."""
        current_time = now or datetime.now(timezone.utc)
        expiry = bridge.created_at + timedelta(days=bridge.ttl_days)
        return current_time > expiry

    def find_bridge(
        self,
        source_nb: str,
        target_nb: str,
        now: Optional[datetime] = None,
    ) -> Optional[CrossNotebookBridge]:
        """Lookup active bridge between two notebooks respecting directionality and TTL."""
        self.reload_if_modified()
        src = source_nb.strip()
        tgt = target_nb.strip()

        with self._lock:
            for b in self._bridges.values():
                if b.source_notebook == src and b.target_notebook == tgt:
                    if self.is_bridge_expired(b, now=now):
                        self._record_event(
                            event_type="BRIDGE_EXPIRED",
                            details={"bridge_id": b.bridge_id, "source": src, "target": tgt},
                        )
                        return None
                    return b
                elif b.direction == "bidirectional" and b.source_notebook == tgt and b.target_notebook == src:
                    if self.is_bridge_expired(b, now=now):
                        self._record_event(
                            event_type="BRIDGE_EXPIRED",
                            details={"bridge_id": b.bridge_id, "source": src, "target": tgt},
                        )
                        return None
                    return b
            return None

    def is_bridge_authorized(
        self,
        source_nb: str,
        target_nb: str,
        topic: str,
        now: Optional[datetime] = None,
    ) -> Tuple[bool, Optional[str], Optional[CrossNotebookBridge]]:
        """Authorize cross-notebook query for a given topic.

        Returns (is_authorized, reason, bridge_object).
        """
        bridge = self.find_bridge(source_nb, target_nb, now=now)
        if not bridge:
            self._record_event(
                event_type="UNAUTHORIZED_BRIDGE_ATTEMPT",
                details={"source": source_nb, "target": target_nb, "topic": topic},
            )
            return False, "Bridge not found or expired in allow-list", None

        clean_topic = topic.lower().strip()
        if clean_topic not in bridge.topic_allowlist:
            self._record_event(
                event_type="UNAUTHORIZED_TOPIC_ATTEMPT",
                details={"bridge_id": bridge.bridge_id, "topic": clean_topic, "allowed": bridge.topic_allowlist},
            )
            return False, f"Topic '{clean_topic}' not in bridge allow-list", bridge

        return True, "Authorized", bridge

    def filter_stale_in_flight_results(
        self,
        results: List[Dict[str, Any]],
        bridge: CrossNotebookBridge,
        now: Optional[datetime] = None,
    ) -> Tuple[List[Dict[str, Any]], bool]:
        """E4-2: Exclude in-flight results if the bridge expired during execution."""
        if self.is_bridge_expired(bridge, now=now):
            self._record_event(
                event_type="IN_FLIGHT_BRIDGE_EXPIRATION",
                details={"bridge_id": bridge.bridge_id, "omitted_count": len(results)},
            )
            # Mark results as stale and exclude from canonical union
            for r in results:
                r["stale_bridge_result"] = True
            return [], True
        return results, False

    def get_audit_events(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._audit_events)
