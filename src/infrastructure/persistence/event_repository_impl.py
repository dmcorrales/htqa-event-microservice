from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.event import Event
from src.domain.enums.event_status import EventStatus
from src.domain.enums.severity import SeverityLevel
from src.domain.interfaces.event_repository import EventRepository
from src.infrastructure.persistence.models import EventModel

logger = logging.getLogger(__name__)


class SqlAlchemyEventRepository(EventRepository):
    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, event: Event) -> Event:
        model = EventModel(
            id=event.id,
            source=event.source,
            customer_id=event.customer_id,
            device_id=event.device_id,
            event_type=event.event_type,
            occurred_at=event.occurred_at,
            metric_value=event.metric_value,
            metadata_=event.metadata,
            severity=event.severity.value,
            status=event.status.value,
            created_at=event.created_at,
        )
        try:
            self._session.add(model)
            await self._session.commit()
            await self._session.refresh(model)
        except IntegrityError:
            await self._session.rollback()
            logger.warning(
                "DB-level duplicate detected (unique constraint)",
                extra={"event_id": event.id},
            )
            raise
        return self._to_entity(model)

    async def find_by_id(self, event_id: str) -> Event | None:
        result = await self._session.execute(
            select(EventModel).where(EventModel.id == event_id)
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def find_duplicate(
        self,
        source: str,
        device_id: str,
        event_type: str,
        occurred_at_start: datetime,
        occurred_at_end: datetime,
    ) -> Event | None:
        result = await self._session.execute(
            select(EventModel).where(
                EventModel.source == source,
                EventModel.device_id == device_id,
                EventModel.event_type == event_type,
                EventModel.occurred_at >= occurred_at_start,
                EventModel.occurred_at <= occurred_at_end,
            )
        )
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    @staticmethod
    def _to_entity(model: EventModel) -> Event:
        return Event(
            id=model.id,
            source=model.source,
            customer_id=model.customer_id,
            device_id=model.device_id,
            event_type=model.event_type,
            occurred_at=model.occurred_at,
            metric_value=model.metric_value,
            metadata=model.metadata_ or {},
            severity=SeverityLevel(model.severity),
            status=EventStatus(model.status),
            created_at=model.created_at,
        )
