export const EVENT_SCHEMA_VERSION = "1.0";

export type EventSource = "shopify" | "sonic" | "web" | "worker" | "system" | "manual";
export type EventOutcome = "success" | "failure" | "partial" | "unknown";

export interface EventEntity { type: string; id: string; }
export interface EventActor { user_id?: string; customer_id?: string; session_id?: string; }

export interface BusinessEvent<TProperties extends Record<string, unknown> = Record<string, unknown>> {
  event_id: string;
  event_type: string;
  schema_version: string;
  occurred_at: string;
  source: EventSource;
  entity: EventEntity;
  actor?: EventActor;
  context?: Record<string, unknown>;
  properties: TProperties;
  outcome?: EventOutcome;
  revenue_impact?: number;
  currency?: string;
}

export const CANONICAL_EVENT_TYPES = [
  "product_viewed", "add_to_cart", "checkout_started", "purchase_completed",
  "purchase_failed", "customer_returned", "product_created", "product_updated",
  "automation_triggered", "automation_completed", "conversion_changed",
  "asset_uploaded", "asset_metadata_generated", "project_created",
] as const;

export type CanonicalEventType = (typeof CANONICAL_EVENT_TYPES)[number];
