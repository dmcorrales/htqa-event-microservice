import logging
import smtplib
from email.message import EmailMessage

from src.config.settings import settings
from src.domain.entities.event import Event
from src.domain.interfaces.notifier import Notifier

logger = logging.getLogger(__name__)


class EmailNotifier(Notifier):
    """Sends email notifications. In production, replace with an async email
    provider (SendGrid, SES) or a Celery task for true non-blocking behavior."""

    async def notify(self, event: Event) -> None:
        msg = EmailMessage()
        msg["Subject"] = (
            f"[{event.severity.value.upper()}] {event.event_type} on {event.device_id}"
        )
        msg["From"] = "alerts@htqa.co"
        msg["To"] = settings.notification_email
        msg.set_content(
            f"Event ID: {event.id}\n"
            f"Source: {event.source}\n"
            f"Customer: {event.customer_id}\n"
            f"Device: {event.device_id}\n"
            f"Type: {event.event_type}\n"
            f"Severity: {event.severity.value}\n"
            f"Occurred at: {event.occurred_at.isoformat()}\n"
        )
        logger.info(
            "Email notification prepared for event %s to %s",
            event.id,
            settings.notification_email,
        )
