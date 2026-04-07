from abc import ABC, abstractmethod

from src.domain.entities.event import Event


class Notifier(ABC):
    @abstractmethod
    async def notify(self, event: Event) -> None:
        ...
