from datetime import datetime, timezone

import pytest

from src.config.settings import settings


VALID_PAYLOAD = {
    "source": "meraki",
    "customer_id": "cli-001",
    "device_id": "sw-44",
    "event_type": "device_down",
    "occurred_at": "2026-04-05T10:12:00Z",
    "metric_value": 0,
    "metadata": {"site": "Bogotá", "ip": "10.0.2.15"},
}

AUTH_HEADERS = {"X-API-Key": settings.api_key}


@pytest.mark.asyncio
class TestCreateEventEndpoint:
    async def test_create_event_returns_201(self, client):
        response = await client.post(
            "/api/v1/events", json=VALID_PAYLOAD, headers=AUTH_HEADERS
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "created"
        assert data["severity"] == "critical"
        assert "event_id" in data

    async def test_duplicate_returns_200(self, client):
        await client.post(
            "/api/v1/events", json=VALID_PAYLOAD, headers=AUTH_HEADERS
        )
        response = await client.post(
            "/api/v1/events", json=VALID_PAYLOAD, headers=AUTH_HEADERS
        )
        assert response.status_code == 200
        assert response.json()["status"] == "duplicate"

    async def test_missing_auth_returns_401(self, client):
        response = await client.post("/api/v1/events", json=VALID_PAYLOAD)
        assert response.status_code == 401

    async def test_invalid_source_returns_422(self, client):
        payload = {**VALID_PAYLOAD, "source": "unknown_source"}
        response = await client.post(
            "/api/v1/events", json=payload, headers=AUTH_HEADERS
        )
        assert response.status_code == 422

    async def test_invalid_customer_id_returns_422(self, client):
        payload = {**VALID_PAYLOAD, "customer_id": "bad-format"}
        response = await client.post(
            "/api/v1/events", json=payload, headers=AUTH_HEADERS
        )
        assert response.status_code == 422

    async def test_negative_metric_value_returns_422(self, client):
        payload = {**VALID_PAYLOAD, "metric_value": -5}
        response = await client.post(
            "/api/v1/events", json=payload, headers=AUTH_HEADERS
        )
        assert response.status_code == 422

    async def test_extra_fields_rejected(self, client):
        payload = {**VALID_PAYLOAD, "extra_field": "not_allowed"}
        response = await client.post(
            "/api/v1/events", json=payload, headers=AUTH_HEADERS
        )
        assert response.status_code == 422


@pytest.mark.asyncio
class TestHealthEndpoint:
    async def test_health_check(self, client):
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
