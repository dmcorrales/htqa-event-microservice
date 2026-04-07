from __future__ import annotations

import time
from threading import Lock

from src.domain.interfaces.idempotency_store import IdempotencyStore


class MemoryIdempotencyStore(IdempotencyStore):
    """In-memory idempotency store for development/testing.
    Uses a dict with TTL-based expiry. NOT suitable for multi-process deployments.
    """

    def __init__(self) -> None:
        self._store: dict[str, float] = {}
        self._lock = Lock()

    async def check_and_set(self, key: str, ttl_seconds: int = 300) -> bool:
        now = time.monotonic()
        with self._lock:
            self._purge_expired(now)
            if key in self._store:
                return False
            self._store[key] = now + ttl_seconds
            return True

    def _purge_expired(self, now: float) -> None:
        expired = [k for k, exp in self._store.items() if exp <= now]
        for k in expired:
            del self._store[k]
