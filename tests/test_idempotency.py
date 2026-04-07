import pytest

from src.infrastructure.cache.memory_idempotency_store import MemoryIdempotencyStore


@pytest.mark.asyncio
class TestMemoryIdempotencyStore:
    async def test_first_call_returns_true(self):
        store = MemoryIdempotencyStore()
        assert await store.check_and_set("key1") is True

    async def test_second_call_returns_false(self):
        store = MemoryIdempotencyStore()
        await store.check_and_set("key1")
        assert await store.check_and_set("key1") is False

    async def test_different_keys_are_independent(self):
        store = MemoryIdempotencyStore()
        assert await store.check_and_set("key1") is True
        assert await store.check_and_set("key2") is True

    async def test_expired_key_can_be_reset(self):
        store = MemoryIdempotencyStore()
        await store.check_and_set("key1", ttl_seconds=0)
        # TTL=0 means it expires immediately on next purge
        import time
        time.sleep(0.01)
        assert await store.check_and_set("key1", ttl_seconds=300) is True
