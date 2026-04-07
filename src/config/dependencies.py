from __future__ import annotations

import logging

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.event_service import EventService
from src.config.database import get_session
from src.config.settings import settings
from src.domain.interfaces.idempotency_store import IdempotencyStore
from src.domain.rules.severity_classifier import SeverityClassifier
from src.infrastructure.cache.memory_idempotency_store import MemoryIdempotencyStore
from src.infrastructure.notifications.log_notifier import LogNotifier
from src.infrastructure.persistence.event_repository_impl import (
    SqlAlchemyEventRepository,
)

logger = logging.getLogger(__name__)


def _build_idempotency_store() -> IdempotencyStore:
    if settings.use_redis:
        import redis.asyncio as aioredis

        from src.infrastructure.cache.redis_idempotency_store import (
            RedisIdempotencyStore,
        )

        client = aioredis.from_url(settings.redis_url, decode_responses=True)
        logger.info("Using Redis idempotency store at %s", settings.redis_url)
        return RedisIdempotencyStore(client)

    logger.info("Using in-memory idempotency store (dev mode)")
    return MemoryIdempotencyStore()


_idempotency_store = _build_idempotency_store()
_notifier = LogNotifier()
_classifier = SeverityClassifier()


async def get_event_service(
    session: AsyncSession = Depends(get_session),
) -> EventService:
    repository = SqlAlchemyEventRepository(session)
    return EventService(
        repository=repository,
        idempotency_store=_idempotency_store,
        notifier=_notifier,
        classifier=_classifier,
    )
