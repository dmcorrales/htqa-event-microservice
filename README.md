# HTQA Event Monitoring Microservice

Backend microservice for HTQA S.A.S. infrastructure monitoring. Ingests events from multiple sources (Meraki, Zabbix, Datadog, etc.), classifies severity, deduplicates within a 5-minute window, and dispatches notifications asynchronously.

## Architecture

```
src/
  domain/           # Enterprise rules, entities, abstract interfaces (no framework deps)
  application/      # Use cases, DTOs, service orchestration
  infrastructure/   # Adapters: DB repository, cache, notifiers, security
  presentation/     # HTTP routes, middleware (audit, error handling)
  config/           # Settings, DI wiring, database, logging
```

**Principles applied**: Clean Architecture with SOLID (SRP, OCP, DIP). Domain and application layers have zero dependency on frameworks or infrastructure. All external concerns are injected through abstract interfaces.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # Edit values as needed
uvicorn main:app --reload
```

API docs available at `http://localhost:8000/docs`.

## API

### POST /api/v1/events

**Authentication**: JWT Bearer token or `X-API-Key` header.

**Request body**:
```json
{
  "source": "meraki",
  "customer_id": "cli-001",
  "device_id": "sw-44",
  "event_type": "device_down",
  "occurred_at": "2026-04-05T10:12:00Z",
  "metric_value": 0,
  "metadata": {
    "site": "Bogota",
    "ip": "10.0.2.15"
  }
}
```

**201 Created**:
```json
{
  "status": "created",
  "event_id": "uuid",
  "severity": "critical",
  "received_at": "2026-04-05T10:12:01Z"
}
```

**200 Duplicate**:
```json
{
  "status": "duplicate",
  "event_id": "uuid-of-existing",
  "message": "Event already processed"
}
```

### GET /health

Returns `{"status": "healthy"}`. No authentication required.

## Idempotency

Events are deduplicated using a SHA-256 hash of `source + device_id + event_type + occurred_at`. The hash is checked atomically via an idempotency store (Redis `SET NX EX 300` in production, in-memory dict for dev). A DB-level unique constraint on `(source, device_id, event_type, occurred_at)` provides defense in depth.

## Severity Classification

Uses a Strategy/Chain pattern. Rules are evaluated in priority order; first match wins:

| Rule | Condition | Severity |
|------|-----------|----------|
| DeviceDownRule | `event_type == "device_down"` | CRITICAL |
| HighLatencyRule | `event_type == "high_latency" and metric_value > 1000` | HIGH |
| PacketLossRule | `event_type == "packet_loss" and metric_value > 50` | HIGH |
| HighCpuRule | `event_type == "high_cpu" and metric_value > 90` | MEDIUM |
| DefaultRule | always | LOW |

Add new rules by subclassing `SeverityRule` and registering in the classifier -- no existing code modification needed.

## Security

- **Authentication**: JWT Bearer + API Key fallback
- **Input validation**: Pydantic strict models with `extra="forbid"`
- **Rate limiting**: slowapi, 100 req/min per client IP
- **Secrets**: Environment variables via pydantic-settings
- **Logging**: Structured JSON, IP addresses masked
- **Audit**: Middleware logs every request with correlation ID

## Tests

```bash
python -m pytest tests/ -v
```

29 tests covering: severity rules (unit), event service (integration), API endpoint (E2E with auth, validation, idempotency), and idempotency store (unit).

## SQL

Production schema in `sql/001_create_events.sql`. Includes the events table, idempotency unique index, severity + time index for critical-events queries, and an audit_log table.
