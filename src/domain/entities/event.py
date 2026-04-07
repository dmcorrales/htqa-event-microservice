from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.domain.enums.severity import SeverityLevel
from src.domain.enums.event_status import EventStatus


@dataclass
class Event:
    source: str
    customer_id: str
    device_id: str
    event_type: str
    occurred_at: datetime
    metric_value: float
    metadata: dict[str, Any]
    severity: SeverityLevel
    status: EventStatus = EventStatus.RECEIVED
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
