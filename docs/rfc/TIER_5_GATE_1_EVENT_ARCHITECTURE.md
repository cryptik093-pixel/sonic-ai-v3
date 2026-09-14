# Tier 5 Gate 1 — Event Architecture

## Objective

Create the canonical event backbone for Sonic AI V3 so downstream intelligence can observe business behavior without coupling the intelligence layer directly to Shopify, the web app, workers, or future integrations.

## Architecture

Source systems -> canonical BusinessEvent -> validation -> idempotency -> event bus -> future persistence, diagnostics, memory, analytics, and experiments.

## Required invariant

A business event is an immutable fact about something that happened. Recommendations, diagnoses, decisions, and actions are not business events and must not be mixed into this contract.

## Acceptance criteria

- [x] Canonical BusinessEvent type exists.
- [x] Schema version is explicit.
- [x] Source and entity identity are explicit.
- [x] Revenue impact is supported without forcing every event to be financial.
- [x] Runtime validation rejects malformed events.
- [x] Event bus supports subscription by event type.
- [x] Duplicate event_id deliveries are suppressed.
- [x] Unit tests cover validation and idempotency.
- [ ] Durable event persistence.
- [ ] Shopify webhook ingestion.
- [ ] Diagnostic engine.
- [ ] Decision engine.
- [ ] Autonomous execution.

Gate 2 should add durable persistence behind the same contract and expose a versioned ingestion endpoint from apps/api. Shopify can then become the first external producer without changing the canonical event model.
