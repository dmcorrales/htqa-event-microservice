from abc import ABC, abstractmethod
from datetime import datetime

from src.domain.entities.event import Event


class EventRepository(ABC):
    @abstractmethod
    async def save(self, event: Event) -> Event:
        ...

    @abstractmethod
    async def find_by_id(self, event_id: str) -> Event | None:
        ...

    @abstractmethod
    async def find_duplicate(
        self,
        source: str,
        device_id: str,
        event_type: str,
        occurred_at_start: datetime,
        occurred_at_end: datetime,
    ) -> Event | None:
        ...
