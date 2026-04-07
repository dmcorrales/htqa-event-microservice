from __future__ import annotations

import logging

import redis.asyncio as aioredis

from src.domain.interfaces.idempotency_store import IdempotencyStore

logger = logging.getLogger(__name__)


class RedisIdempotencyStore(IdempotencyStore):
    """Redis-backed idempotency store. Uses SET NX EX for atomic check-and-set."""

    def __init__(self, redis_client: aioredis.Redis):
        self._redis = redis_client

    async def check_and_set(self, key: str, ttl_seconds: int = 300) -> bool:
        prefixed_key = f"idemp:{key}"
        result = await self._redis.set(prefixed_key, "1", nx=True, ex=ttl_seconds)
        return result is not None
