from __future__ import annotations

import hashlib
import logging
from datetime import timedelta, timezone

from src.application.dtos.event_dto import EventCreateRequest
from src.domain.entities.event import Event
from src.domain.enums.event_status import EventStatus
from src.domain.interfaces.event_repository import EventRepository
from src.domain.interfaces.idempotency_store import IdempotencyStore
from src.domain.interfaces.notifier import Notifier
from src.domain.rules.severity_classifier import SeverityClassifier

logger = logging.getLogger(__name__)

IDEMPOTENCY_WINDOW_SECONDS = 300  # 5 minutes


class DuplicateEventError(Exception):
    def __init__(self, event_id: str):
        self.event_id = event_id
        super().__init__(f"Duplicate event detected: {event_id}")


class EventService:
    def __init__(
        self,
        repository: EventRepository,
        idempotency_store: IdempotencyStore,
        notifier: Notifier,
        classifier: SeverityClassifier,
    ):
        self._repository = repository
        self._idempotency_store = idempotency_store
        self._notifier = notifier
        self._classifier = classifier

    async def create_event(self, request: EventCreateRequest) -> Event:
        idempotency_key = self._build_idempotency_key(request)
        logger.info(
            "Processing event",
            extra={
                "source": request.source,
                "device_id": request.device_id,
                "event_type": request.event_type,
            },
        )

        is_new = await self._idempotency_store.check_and_set(
            idempotency_key, ttl_seconds=IDEMPOTENCY_WINDOW_SECONDS
        )
        if not is_new:
            existing = await self._find_existing_event(request)
            event_id = existing.id if existing else "unknown"
            logger.warning("Duplicate event detected", extra={"event_id": event_id})
            raise DuplicateEventError(event_id=event_id)

        severity = self._classifier.classify(request)

        event = Event(
            source=request.source,
            customer_id=request.customer_id,
            device_id=request.device_id,
            event_type=request.event_type,
            occurred_at=request.occurred_at,
            metric_value=request.metric_value,
            metadata=request.metadata.model_dump(),
            severity=severity,
            status=EventStatus.RECEIVED,
        )

        saved_event = await self._repository.save(event)
        logger.info(
            "Event persisted",
            extra={"event_id": saved_event.id, "severity": severity.value},
        )

        return saved_event

    async def dispatch_notification(self, event: Event) -> None:
        """Fire-and-forget notification -- called as a background task."""
        try:
            await self._notifier.notify(event)
            logger.info("Notification sent", extra={"event_id": event.id})
        except Exception:
            logger.exception(
                "Notification failed (non-blocking)", extra={"event_id": event.id}
            )

    async def _find_existing_event(
        self, request: EventCreateRequest
    ) -> Event | None:
        window_start = request.occurred_at - timedelta(
            seconds=IDEMPOTENCY_WINDOW_SECONDS
        )
        window_end = request.occurred_at + timedelta(
            seconds=IDEMPOTENCY_WINDOW_SECONDS
        )
        return await self._repository.find_duplicate(
            source=request.source,
            device_id=request.device_id,
            event_type=request.event_type,
            occurred_at_start=window_start,
            occurred_at_end=window_end,
        )

    @staticmethod
    def _build_idempotency_key(request: EventCreateRequest) -> str:
        raw = f"{request.source}:{request.device_id}:{request.event_type}:{request.occurred_at.astimezone(timezone.utc).isoformat()}"
        return hashlib.sha256(raw.encode()).hexdigest()
