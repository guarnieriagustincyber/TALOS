"""Thread-safe TTL and LRU Cache implementations for KASIU/TALOS Study Engine."""

from collections import OrderedDict
import threading
import time
from typing import Any, Iterator, MutableMapping, Optional, Tuple


class TTLCache(MutableMapping[Any, Any]):
    """Thread-safe in-memory cache with time-to-live (TTL) and maximum capacity eviction."""

    def __init__(self, maxsize: int = 1000, ttl: float = 3600.0) -> None:
        if maxsize <= 0:
            raise ValueError("maxsize must be greater than 0")
        if ttl <= 0:
            raise ValueError("ttl must be greater than 0")
        self.maxsize = maxsize
        self.ttl = float(ttl)
        self._data: OrderedDict[Any, Tuple[Any, float]] = OrderedDict()
        self._lock = threading.RLock()

    def _purge_expired(self, now: Optional[float] = None) -> None:
        if now is None:
            now = time.time()
        expired_keys = [k for k, (_, exp) in self._data.items() if exp <= now]
        for k in expired_keys:
            self._data.pop(k, None)

    def __getitem__(self, key: Any) -> Any:
        with self._lock:
            if key not in self._data:
                raise KeyError(key)
            val, exp = self._data[key]
            if exp <= time.time():
                del self._data[key]
                raise KeyError(key)
            self._data.move_to_end(key)
            return val

    def __setitem__(self, key: Any, value: Any) -> None:
        with self._lock:
            now = time.time()
            self._purge_expired(now)
            if key in self._data:
                del self._data[key]
            elif len(self._data) >= self.maxsize:
                self._data.popitem(last=False)
            self._data[key] = (value, now + self.ttl)

    def __delitem__(self, key: Any) -> None:
        with self._lock:
            del self._data[key]

    def __iter__(self) -> Iterator[Any]:
        with self._lock:
            self._purge_expired()
            return iter(list(self._data.keys()))

    def __len__(self) -> int:
        with self._lock:
            self._purge_expired()
            return len(self._data)

    def __contains__(self, key: Any) -> bool:
        with self._lock:
            if key not in self._data:
                return False
            _, exp = self._data[key]
            if exp <= time.time():
                del self._data[key]
                return False
            return True

    def get(self, key: Any, default: Any = None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def clear(self) -> None:
        with self._lock:
            self._data.clear()

    def __repr__(self) -> str:
        with self._lock:
            return f"TTLCache(maxsize={self.maxsize}, ttl={self.ttl}, currsize={len(self)})"
