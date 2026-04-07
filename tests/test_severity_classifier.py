from datetime import datetime, timezone

import pytest

from src.application.dtos.event_dto import EventCreateRequest, EventMetadata
from src.domain.enums.severity import SeverityLevel
from src.domain.rules.severity_classifier import (
    DefaultRule,
    DeviceDownRule,
    HighCpuRule,
    HighLatencyRule,
    PacketLossRule,
    SeverityClassifier,
)


def _make_event(**overrides) -> EventCreateRequest:
    defaults = {
        "source": "meraki",
        "customer_id": "cli-001",
        "device_id": "sw-44",
        "event_type": "device_up",
        "occurred_at": datetime(2026, 4, 5, 10, 0, 0, tzinfo=timezone.utc),
        "metric_value": 0,
        "metadata": EventMetadata(),
    }
    defaults.update(overrides)
    return EventCreateRequest(**defaults)


class TestDeviceDownRule:
    def test_matches_device_down(self):
        event = _make_event(event_type="device_down")
        assert DeviceDownRule().evaluate(event) == SeverityLevel.CRITICAL

    def test_ignores_other_types(self):
        event = _make_event(event_type="device_up")
        assert DeviceDownRule().evaluate(event) is None


class TestHighLatencyRule:
    def test_matches_high_latency_above_threshold(self):
        event = _make_event(event_type="high_latency", metric_value=1500)
        assert HighLatencyRule().evaluate(event) == SeverityLevel.HIGH

    def test_ignores_low_latency(self):
        event = _make_event(event_type="high_latency", metric_value=500)
        assert HighLatencyRule().evaluate(event) is None


class TestPacketLossRule:
    def test_matches_high_packet_loss(self):
        event = _make_event(event_type="packet_loss", metric_value=80)
        assert PacketLossRule().evaluate(event) == SeverityLevel.HIGH

    def test_ignores_low_packet_loss(self):
        event = _make_event(event_type="packet_loss", metric_value=10)
        assert PacketLossRule().evaluate(event) is None


class TestHighCpuRule:
    def test_matches_high_cpu(self):
        event = _make_event(event_type="high_cpu", metric_value=95)
        assert HighCpuRule().evaluate(event) == SeverityLevel.MEDIUM

    def test_ignores_normal_cpu(self):
        event = _make_event(event_type="high_cpu", metric_value=50)
        assert HighCpuRule().evaluate(event) is None


class TestDefaultRule:
    def test_always_returns_low(self):
        event = _make_event(event_type="device_up")
        assert DefaultRule().evaluate(event) == SeverityLevel.LOW


class TestSeverityClassifier:
    def test_device_down_is_critical(self):
        classifier = SeverityClassifier()
        event = _make_event(event_type="device_down")
        assert classifier.classify(event) == SeverityLevel.CRITICAL

    def test_unknown_type_defaults_to_low(self):
        classifier = SeverityClassifier()
        event = _make_event(event_type="device_up")
        assert classifier.classify(event) == SeverityLevel.LOW

    def test_first_matching_rule_wins(self):
        classifier = SeverityClassifier()
        event = _make_event(event_type="high_latency", metric_value=2000)
        assert classifier.classify(event) == SeverityLevel.HIGH

    def test_custom_rules_injection(self):
        classifier = SeverityClassifier(rules=[DefaultRule()])
        event = _make_event(event_type="device_down")
        assert classifier.classify(event) == SeverityLevel.LOW
