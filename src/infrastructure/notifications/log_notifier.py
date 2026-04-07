import logging

from src.domain.entities.event import Event
from src.domain.interfaces.notifier import Notifier

logger = logging.getLogger(__name__)


class LogNotifier(Notifier):
    """Logs notifications instead of sending emails. Suitable for dev/testing."""

    async def notify(self, event: Event) -> None:
        logger.info(
            "NOTIFICATION: New %s event [%s] on device %s for customer %s",
            event.severity.value,
            event.event_type,
            event.device_id,
            event.customer_id,
            extra={"event_id": event.id},
        )
