from abc import ABC, abstractmethod


class IdempotencyStore(ABC):
    @abstractmethod
    async def check_and_set(self, key: str, ttl_seconds: int = 300) -> bool:
        """Return True if the key was newly set (not a duplicate).
        Return False if the key already existed (duplicate detected)."""
        ...
