# @sonic-ai/events

Tier 5 Gate 1 establishes the canonical Sonic AI business-event contract.

Every persistent business event has event_id, event_type, schema_version, occurred_at, source, entity, optional actor/context, properties, optional outcome, optional revenue_impact, and optional currency.

The contract is source-neutral. Shopify is one producer of events, not the owner of the event model.

Gate 1 implements canonical event types, runtime validation, an in-process event bus, idempotency by event_id, and unit coverage.

Durable persistence, Shopify webhook ingestion, diagnostics, decisions, autonomous actions, and learning loops are intentionally deferred to later gates.
