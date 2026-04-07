from datetime import datetime, timezone

import pytest

from src.application.dtos.event_dto import EventCreateRequest, EventMetadata
from src.application.services.event_service import DuplicateEventError
from src.domain.enums.severity import SeverityLevel


def _make_request(**overrides) -> EventCreateRequest:
    defaults = {
        "source": "meraki",
        "customer_id": "cli-001",
        "device_id": "sw-44",
        "event_type": "device_down",
        "occurred_at": datetime(2026, 4, 5, 10, 12, 0, tzinfo=timezone.utc),
        "metric_value": 0,
        "metadata": EventMetadata(site="Bogotá", ip="10.0.2.15"),
    }
    defaults.update(overrides)
    return EventCreateRequest(**defaults)


@pytest.mark.asyncio
class TestEventService:
    async def test_create_event_success(self, event_service):
        request = _make_request()
        event = await event_service.create_event(request)

        assert event.id is not None
        assert event.source == "meraki"
        assert event.severity == SeverityLevel.CRITICAL
        assert event.customer_id == "cli-001"

    async def test_duplicate_event_raises(self, event_service):
        request = _make_request()
        await event_service.create_event(request)

        with pytest.raises(DuplicateEventError):
            await event_service.create_event(request)

    async def test_different_events_not_duplicated(self, event_service):
        req1 = _make_request(device_id="sw-44")
        req2 = _make_request(device_id="sw-45")

        event1 = await event_service.create_event(req1)
        event2 = await event_service.create_event(req2)

        assert event1.id != event2.id

    async def test_severity_classification(self, event_service):
        req = _make_request(event_type="device_up", metric_value=5)
        event = await event_service.create_event(req)
        assert event.severity == SeverityLevel.LOW
