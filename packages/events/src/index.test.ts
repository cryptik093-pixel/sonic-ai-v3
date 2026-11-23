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

import { parseCommerceIntakeV2, toSonicBusinessEventV1 } from "./commerce";

describe("Commerce Engine V2 intake", () => {
  const shop = "omega-house.online";
  const base = {
    event_id: "evt-client-1", event_name: "view_item",
    timestamp_utc: "2026-10-19T17:00:00Z", shop_domain: shop,
    anonymous_session_id: "anonymous-session-1", consent_status: "unknown",
    product_gid: "gid://shopify/Product/12345", email: "DO-NOT-COPY@example.com",
    revenue_impact: 999999,
  };

  it("accepts a verified domain expectation and removes unexpected PII/revenue", () => {
    const parsed = parseCommerceIntakeV2(base, shop);
    expect(parsed).not.toHaveProperty("email");
    expect(parsed).not.toHaveProperty("revenue_impact");
    const mapped = toSonicBusinessEventV1(parsed);
    expect(mapped?.event_type).toBe("product_viewed");
    expect(mapped?.revenue_impact).toBeUndefined();
    expect(mapped?.context?.evidence_level).toBe("untrusted_client");
    expect(() => validateBusinessEvent(mapped)).not.toThrow();
  });

  it("rejects cross-shop events and browser purchase assertions", () => {
    expect(() => parseCommerceIntakeV2({ ...base, shop_domain: "other-shop.example" }, shop)).toThrow(/identity mismatch/);
    expect(() => parseCommerceIntakeV2({ ...base, event_name: "purchase" }, shop)).toThrow(/Shopify evidence/);
    expect(() => parseCommerceIntakeV2({ ...base, event_name: "refund" }, shop)).toThrow(/Shopify evidence/);
  });

  it("requires a selected product variant for cart activity", () => {
    expect(() => parseCommerceIntakeV2({ ...base, event_name: "add_to_cart" }, shop)).toThrow(/variant/);
    const added = parseCommerceIntakeV2({
      ...base, event_name: "add_to_cart", variant_gid: "gid://shopify/ProductVariant/456",
    }, shop);
    expect(toSonicBusinessEventV1(added)?.event_type).toBe("add_to_cart");
  });

  it("keeps specialized audio events out of the canonical business bus", () => {
    const sound = parseCommerceIntakeV2({ ...base, event_name: "audio_play" }, shop);
    expect(toSonicBusinessEventV1(sound)).toBeNull();
    expect(() => parseCommerceIntakeV2({ ...base, consent_status: "yes" }, shop)).toThrow(/consent/);
  });
});
