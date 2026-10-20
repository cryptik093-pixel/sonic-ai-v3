# Tier 5 Event Contract — Selective Recovery

Date: 2026-10-05
Canonical parent: `19ff3b7648c49f3f81b82dcc5e445028719edaba`
Historical sources:
- `tier5/gate-1-event-architecture`
- `tier5/gate-2-durable-ingestion`

## Recovered

- canonical TypeScript business-event envelope
- validator and event type vocabulary
- in-process event bus
- event package unit tests
- SQLite durable event store
- idempotency/persistence tests

## Deliberately excluded

- `events_router.py`
- Shopify webhook producer
- external event ingestion mount
- old Gate 1/Gate 2 integration instructions

Reason: the historical Gate 2 contract explicitly deferred event authentication and signature verification. External ingestion therefore remains **disabled/fail-closed** until a current authenticated boundary is designed and tested.

## Provenance

The event/runtime files embedded in `feat/studio-drop-002-packaging` were verified byte-for-byte identical to the dedicated Tier-5 branches, so Studio Drop is not treated as the authoritative source for event infrastructure.

## Validation

This recovery branch adds dedicated CI for:
- current-workspace TypeScript event contract tests
- durable SQLite store persistence/idempotency tests

Current main Runtime Baseline and PR security checks remain additional gates.
