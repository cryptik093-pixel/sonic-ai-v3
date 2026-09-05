# Phase 3 — Shopify Commerce Ingestion

Phase 3 connects Omega House storefront behavior to Sonic AI V3's durable event backbone without treating browser-side intent as authoritative commerce state.

## Architecture

```text
Omega House storefront
  ├─ omega:commerce browser signals
  │    ├─ product_preview_ready
  │    ├─ audio_preview_started
  │    ├─ audio_preview_completed
  │    ├─ variant_selected / license_selected
  │    └─ add_to_cart_submitted (intent only)
  │
  └─ Shopify authoritative commerce state
       ├─ orders/create
       ├─ refunds/create
       └─ customers/update
              ↓
POST /api/v1/webhooks/shopify
              ↓
HMAC verification + topic allowlist + canonicalization
              ↓
EventStore (SQLite, event_id idempotency)
              ↓
Sonic Intelligence™ decision / attribution layer
```

## Implemented

- `shopify_webhooks.py`
  - FastAPI router at `POST /api/v1/webhooks/shopify`
  - verifies `X-Shopify-Hmac-SHA256` against the raw request body
  - uses constant-time HMAC comparison
  - rejects missing/invalid signatures
  - rejects unsupported topics instead of silently accepting unknown schemas
  - preserves Shopify delivery metadata in `context`
  - canonicalizes supported events into Gate 2 `BusinessEvent` shape
  - persists directly through the existing `EventStore`
  - deduplicates retries through canonical `event_id`

- Supported authoritative mappings
  - `orders/create` → `order_created`
  - `refunds/create` → `refund`
  - `customers/update` → `customer_updated`

- `test_shopify_webhooks.py`
  - valid HMAC acceptance
  - invalid HMAC rejection
  - order mapping
  - refund negative revenue impact mapping
  - customer mapping

## Required environment

```text
SHOPIFY_WEBHOOK_SECRET=<Shopify app client secret used to sign webhook deliveries>
SONIC_EVENT_DB=data/sonic_events.sqlite3
```

Never commit the real Shopify secret.

## App mounting

The runtime entrypoint must mount both routers:

```python
from events_router import router as events_router
from shopify_webhooks import router as shopify_webhooks_router

app.include_router(events_router)
app.include_router(shopify_webhooks_router)
```

## Subscription activation gate

Do **not** create Shopify webhook subscriptions until all of the following are true:

1. Sonic API is deployed to a stable public HTTPS hostname.
2. `POST /api/v1/webhooks/shopify` is reachable from the public internet.
3. `SHOPIFY_WEBHOOK_SECRET` is configured in the deployment secret store.
4. Valid HMAC test delivery returns HTTP 202.
5. Invalid HMAC test delivery returns HTTP 401.
6. Duplicate delivery returns HTTP 202 with `duplicate: true`.
7. Persisted event can be retrieved through the Gate 2 event retrieval endpoint.

Once those checks pass, create Shopify subscriptions for the supported topics using the verified public endpoint.

## Evidence rules

- Browser event `add_to_cart_submitted` is purchase intent, not proof of cart creation, checkout, payment, or order creation.
- `order_created`, `refund`, and `customer_updated` are authoritative only when produced from validated Shopify webhook deliveries.
- Unsupported or ambiguous source data must remain unmapped until a schema and provenance rule are explicitly defined.
- Audio preview assets must only be attached to products when the mapping is evidence-backed; filename similarity alone is insufficient.

## Deferred after Phase 3 ingestion gate

- public deployment and runtime mounting
- live Shopify webhook subscription creation
- queue/outbox for asynchronous downstream processing
- webhook diagnostics dashboard
- attribution join between browser `omega:commerce` session signals and authoritative Shopify events
- decision engine
- autonomous actions
- learning loop
