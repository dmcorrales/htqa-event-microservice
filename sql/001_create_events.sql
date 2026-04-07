-- ============================================================
-- HTQA Event Monitoring Service - Events Table
-- ============================================================

CREATE TABLE IF NOT EXISTS events (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    source          VARCHAR(50)     NOT NULL,
    customer_id     VARCHAR(50)     NOT NULL,
    device_id       VARCHAR(50)     NOT NULL,
    event_type      VARCHAR(100)    NOT NULL,
    occurred_at     TIMESTAMPTZ     NOT NULL,
    metric_value    FLOAT           DEFAULT 0,
    metadata        JSONB,
    severity        VARCHAR(20)     NOT NULL,
    status          VARCHAR(20)     NOT NULL DEFAULT 'received',
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

-- Composite index for the critical-events-last-24h query
CREATE INDEX IF NOT EXISTS idx_events_severity_occurred
    ON events (severity, occurred_at DESC);

-- Unique constraint enforcing idempotency at the DB level (defense in depth)
CREATE UNIQUE INDEX IF NOT EXISTS idx_events_idempotency
    ON events (source, device_id, event_type, occurred_at);

-- Index for per-customer queries
CREATE INDEX IF NOT EXISTS idx_events_customer_occurred
    ON events (customer_id, occurred_at DESC);

-- ============================================================
-- Example query: critical events in the last 24 hours
-- ============================================================
-- SELECT e.id, e.source, e.customer_id, e.device_id,
--        e.event_type, e.severity, e.occurred_at,
--        e.metric_value, e.metadata
-- FROM events e
-- WHERE e.severity = 'critical'
--   AND e.occurred_at >= NOW() - INTERVAL '24 hours'
-- ORDER BY e.occurred_at DESC;

-- ============================================================
-- Audit log table (optional, for request auditing)
-- ============================================================

CREATE TABLE IF NOT EXISTS audit_log (
    id              UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    correlation_id  VARCHAR(64)     NOT NULL,
    method          VARCHAR(10)     NOT NULL,
    path            VARCHAR(500)    NOT NULL,
    status_code     INT             NOT NULL,
    client_ip       VARCHAR(45),
    user_agent      VARCHAR(500),
    user_id         VARCHAR(100),
    elapsed_ms      FLOAT,
    created_at      TIMESTAMPTZ     NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_audit_log_created
    ON audit_log (created_at DESC);
