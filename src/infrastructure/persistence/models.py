import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    Float,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class EventModel(Base):
    __tablename__ = "events"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source = Column(String(50), nullable=False)
    customer_id = Column(String(50), nullable=False)
    device_id = Column(String(50), nullable=False)
    event_type = Column(String(100), nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=False)
    metric_value = Column(Float, default=0)
    metadata_ = Column("metadata", JSON, nullable=True)
    severity = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="received")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        UniqueConstraint(
            "source", "device_id", "event_type", "occurred_at",
            name="uq_events_idempotency",
        ),
        Index("idx_events_severity_occurred", "severity", "occurred_at"),
        Index("idx_events_customer_occurred", "customer_id", "occurred_at"),
    )
