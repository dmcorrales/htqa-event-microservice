from __future__ import annotations

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.services.event_service import EventService
from src.config.database import get_session
from src.domain.rules.severity_classifier import SeverityClassifier
from src.infrastructure.cache.memory_idempotency_store import MemoryIdempotencyStore
from src.infrastructure.notifications.log_notifier import LogNotifier
from src.infrastructure.persistence.event_repository_impl import (
    SqlAlchemyEventRepository,
)

_idempotency_store = MemoryIdempotencyStore()
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
