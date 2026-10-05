import { describe, expect, it, vi } from "vitest";
import { InProcessEventBus, validateBusinessEvent } from "./index";

const event = {
  event_id: "evt_001",
  event_type: "purchase_completed",
  schema_version: "1.0",
  occurred_at: "2026-08-24T13:20:00.000Z",
  source: "shopify" as const,
  entity: { type: "order", id: "order_123" },
  actor: { customer_id: "customer_456" },
  properties: { product_id: "omega-beats-demo-pack", value: 19 },
  outcome: "success" as const,
  revenue_impact: 19,
  currency: "USD",
};

describe("Tier 5 Gate 1 event contract", () => {
  it("accepts a canonical business event", () => {
    expect(() => validateBusinessEvent(event)).not.toThrow();
  });

  it("rejects unsupported schema versions", () => {
    expect(() => validateBusinessEvent({ ...event, schema_version: "2.0" })).toThrow(
      /Unsupported event schema version/,
    );
  });

  it("deduplicates event delivery by event_id", async () => {
    const bus = new InProcessEventBus();
    const handler = vi.fn();
    bus.subscribe("purchase_completed", handler);
    await bus.publish(event);
    await bus.publish(event);
    expect(handler).toHaveBeenCalledTimes(1);
  });
});
