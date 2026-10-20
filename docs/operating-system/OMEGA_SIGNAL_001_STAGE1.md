# OMEGA SIGNAL-001 — Stage One: Reliable commerce evidence

**State:** IMPLEMENTED ON FEATURE BRANCH / NOT YET LIVE-VERIFIED

## Objective

Feed signed Shopify business events into the existing Sonic Intelligence evidence
ledger without treating traffic, provisional order totals, or inferred attribution
as confirmed revenue.

## Supported source

- `POST /api/v1/webhooks/shopify`: raw-body HMAC verified using
  `SONIC_SHOPIFY_WEBHOOK_SECRET` (legacy `SHOPIFY_WEBHOOK_SECRET` also supported).
- `SONIC_SHOPIFY_SHOP_DOMAIN` is required and compared against the webhook header.
- Sources: `orders/create`, `orders/updated`, `refunds/create`,
  `products/create`, `products/update`, and existing `customers/update`.
- No external publishing, outbound messages, product mutations, or paid advertising.

## Evidence workflow

```text
Authenticated Shopify webhook
  -> Validate HMAC / expected shop / topic / bounded raw payload
  -> Normalize safe event fields
  -> SQLite transaction: immutable event + verified receipt hash
  -> Sonic Intelligence immutable evidence record
  -> HTTP 202
```

If the intelligence projection fails after receipt persistence, return retryable
HTTP 503. This is a recoverable partial failure: an authorized operator can
replay verified receipts. An event can only be counted as signed commerce
evidence if it has the receipt row. Generic `/api/v1/events` events cannot
impersonate signed Shopify input.

## Operator endpoints

The local-token/loopback workbench security boundary protects:

- `GET /workbench/api/intelligence/commerce/status`
- `POST /workbench/api/intelligence/commerce/replay`

The report is a **diagnostic snapshot**, not Shopify's authoritative financial
statement. It deduplicates paid order snapshots and tracks product/refund event
counts, attribution identifier coverage, and unmatched refunds. Refund events
do **not** automatically change reported order totals. The
`settled_net_revenue` field intentionally stays null until independently
reconciled with Shopify Admin records.

## Explicit data policy

- Commerce evidence includes only source IDs, shop scope, event type, financial
  status, reported amount/currency, SKU quantities, and allowlisted campaign IDs.
- Customer IDs, raw landing URLs, and private details are not promoted into the
  intelligence evidence ledger.
- A webhook-valid event proves authenticity of a reported event, **not**
  settlement, sustained conversion, margin, customer consent, or true attribution.
- The current API has an older `/integrations/shopify/webhooks` product-event
  intake backed by a separate integration store. Stage One does not migrate or
  merge that historical stream. The new signed route is the canonical input for
  this stage's evidence projection; existing integration operations remain intact.

## Required environment for live intake

```text
SONIC_SHOPIFY_SHOP_DOMAIN=<your-shop>.myshopify.com
SONIC_SHOPIFY_WEBHOOK_SECRET=<server-side-webhook-secret>
SONIC_EVENT_DB=<persistent-events-sqlite-path>
SONIC_INTELLIGENCE_DB=<persistent-intelligence-sqlite-path>
SONIC_CONTROL_PLANE_TOKEN=<operator-secret>
```

**Never commit values for these variables.** The endpoint must be deployed on a
reachable, TLS-protected API host and registered for approved Shopify webhook
topics before live delivery is possible. The desktop loopback app alone cannot
receive public Shopify webhooks. Configure privacy and API access separately,
and monitor delivery failures.

## Acceptance and remaining gates

**Stage One acceptance (code):** HMAC/shop rejection, signature-proof
persisted atomically with events, identical retries idempotent, altered payload
conflict, status access controlled, replay recovery, order snapshot dedupe,
product/refund diagnostic counts, no fabricated settled revenue, CI tests pass.

**Not completed by source commits alone:** Shopify Admin reconciliation for
historical orders and refund settlement, Shopify API access/sync, registered
live webhook subscriptions, observed customer-level attribution continuity,
live endpoint deployment, and sustained event-delivery monitoring.
