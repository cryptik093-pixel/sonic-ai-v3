# Tier 5 Gate 2 — Durable Event Persistence + Ingestion

Gate 2 makes the Gate 1 event contract durable and externally ingestible.

## Components

- `event_store.py`: SQLite-backed durable event store using only the Python standard library.
- `events_router.py`: FastAPI router exposing versioned ingestion and retrieval.
- `test_event_store.py`: persistence and idempotency tests.

## Mount

The existing FastAPI application should include:

```python
from events_router import router as events_router
app.include_router(events_router)
```

This intentionally does not replace or modify the existing application entrypoint.

## API

### POST /api/v1/events

Accepts the canonical event envelope and returns:

```json
{
  "accepted": true,
  "duplicate": false,
  "event_id": "evt_123"
}
```

Repeated delivery of the same `event_id` is accepted as an idempotent duplicate and does not create another database row.

### GET /api/v1/events/{event_id}

Returns the persisted canonical event.

## Environment

Optional:

```text
SONIC_EVENT_DB=data/sonic_events.sqlite3
```

The default keeps the database under the API working directory.

## Gate 2 acceptance boundary

Implemented:
- durable SQLite persistence
- event_id uniqueness/idempotency
- versioned ingestion endpoint
- event retrieval endpoint
- persistence tests
- integration instructions that preserve the existing FastAPI entrypoint

Deferred:
- Shopify webhook producer
- event authentication/signature verification
- queue/outbox
- diagnostics
- decision engine
- autonomous actions
- learning loop
