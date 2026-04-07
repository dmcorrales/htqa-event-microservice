from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

ALLOWED_SOURCES = {"meraki", "zabbix", "datadog", "nagios", "prtg"}

ALLOWED_EVENT_TYPES = {
    "device_down",
    "device_up",
    "high_latency",
    "packet_loss",
    "high_cpu",
    "high_memory",
    "interface_down",
    "threshold_exceeded",
}


class EventMetadata(BaseModel):
    model_config = {"extra": "forbid"}

    site: str | None = None
    ip: str | None = None


class EventCreateRequest(BaseModel):
    model_config = {"extra": "forbid"}

    source: str = Field(..., min_length=1, max_length=50)
    customer_id: str = Field(..., pattern=r"^cli-\d{3,}$", max_length=50)
    device_id: str = Field(..., min_length=1, max_length=50)
    event_type: str = Field(..., min_length=1, max_length=100)
    occurred_at: datetime
    metric_value: float = Field(..., ge=0)
    metadata: EventMetadata = Field(default_factory=EventMetadata)

    @field_validator("source")
    @classmethod
    def validate_source(cls, v: str) -> str:
        v_lower = v.lower().strip()
        if v_lower not in ALLOWED_SOURCES:
            raise ValueError(
                f"Unknown source '{v}'. Allowed: {sorted(ALLOWED_SOURCES)}"
            )
        return v_lower

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v: str) -> str:
        v_lower = v.lower().strip()
        if v_lower not in ALLOWED_EVENT_TYPES:
            raise ValueError(
                f"Unknown event_type '{v}'. Allowed: {sorted(ALLOWED_EVENT_TYPES)}"
            )
        return v_lower

    @model_validator(mode="after")
    def occurred_at_not_in_future(self) -> EventCreateRequest:
        if self.occurred_at > datetime.now(timezone.utc):
            raise ValueError("occurred_at cannot be in the future")
        return self


class EventResponse(BaseModel):
    status: str
    event_id: str
    severity: str
    received_at: datetime


class DuplicateEventResponse(BaseModel):
    status: str = "duplicate"
    event_id: str
    message: str = "Event already processed"
