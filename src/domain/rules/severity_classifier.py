from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from src.domain.enums.severity import SeverityLevel

if TYPE_CHECKING:
    from src.application.dtos.event_dto import EventCreateRequest


class SeverityRule(ABC):
    """Base class for all severity classification rules."""

    @abstractmethod
    def evaluate(self, event: EventCreateRequest) -> SeverityLevel | None:
        """Return a severity level if the rule matches, or None to delegate."""
        ...


class DeviceDownRule(SeverityRule):
    def evaluate(self, event: EventCreateRequest) -> SeverityLevel | None:
        if event.event_type == "device_down":
            return SeverityLevel.CRITICAL
        return None


class HighLatencyRule(SeverityRule):
    def evaluate(self, event: EventCreateRequest) -> SeverityLevel | None:
        if event.event_type == "high_latency" and event.metric_value > 1000:
            return SeverityLevel.HIGH
        return None


class PacketLossRule(SeverityRule):
    def evaluate(self, event: EventCreateRequest) -> SeverityLevel | None:
        if event.event_type == "packet_loss" and event.metric_value > 50:
            return SeverityLevel.HIGH
        return None


class HighCpuRule(SeverityRule):
    def evaluate(self, event: EventCreateRequest) -> SeverityLevel | None:
        if event.event_type == "high_cpu" and event.metric_value > 90:
            return SeverityLevel.MEDIUM
        return None


class DefaultRule(SeverityRule):
    """Fallback rule -- always matches with LOW severity."""

    def evaluate(self, event: EventCreateRequest) -> SeverityLevel | None:
        return SeverityLevel.LOW


class SeverityClassifier:
    """Evaluates an ordered chain of rules. First match wins."""

    def __init__(self, rules: list[SeverityRule] | None = None):
        self._rules = rules or self._default_rules()

    @staticmethod
    def _default_rules() -> list[SeverityRule]:
        return [
            DeviceDownRule(),
            HighLatencyRule(),
            PacketLossRule(),
            HighCpuRule(),
            DefaultRule(),
        ]

    def classify(self, event: EventCreateRequest) -> SeverityLevel:
        for rule in self._rules:
            result = rule.evaluate(event)
            if result is not None:
                return result
        return SeverityLevel.LOW
