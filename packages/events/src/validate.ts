import { BusinessEvent, CANONICAL_EVENT_TYPES, EventSource, EVENT_SCHEMA_VERSION } from "./types";

const SOURCES: EventSource[] = ["shopify", "sonic", "web", "worker", "system", "manual"];

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

export function validateBusinessEvent(value: unknown): asserts value is BusinessEvent {
  if (!isRecord(value)) throw new Error("BusinessEvent must be an object");
  for (const key of ["event_id", "event_type", "schema_version", "occurred_at"] as const) {
    if (typeof value[key] !== "string" || value[key].length === 0) {
      throw new Error("BusinessEvent." + key + " is required");
    }
  }
  if (value.schema_version !== EVENT_SCHEMA_VERSION) {
    throw new Error("Unsupported event schema version: " + String(value.schema_version));
  }
  if (!SOURCES.includes(value.source as EventSource)) {
    throw new Error("Unsupported event source: " + String(value.source));
  }
  if (!CANONICAL_EVENT_TYPES.includes(value.event_type as (typeof CANONICAL_EVENT_TYPES)[number])) {
    throw new Error("Unsupported canonical event type: " + String(value.event_type));
  }
  if (!isRecord(value.entity) || typeof value.entity.type !== "string" || typeof value.entity.id !== "string") {
    throw new Error("BusinessEvent.entity must contain type and id");
  }
  if (!isRecord(value.properties)) throw new Error("BusinessEvent.properties must be an object");
  if (value.revenue_impact !== undefined && typeof value.revenue_impact !== "number") {
    throw new Error("BusinessEvent.revenue_impact must be numeric");
  }
  if (value.currency !== undefined && typeof value.currency !== "string") {
    throw new Error("BusinessEvent.currency must be a string");
  }
  if (Number.isNaN(Date.parse(value.occurred_at))) {
    throw new Error("BusinessEvent.occurred_at must be an ISO-8601 timestamp");
  }
}
