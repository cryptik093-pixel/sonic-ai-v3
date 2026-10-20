/** Omega House Commerce Engine V2: untrusted storefront-event boundary.
 *
 * This is a read-only typed intake contract, not a webhook endpoint.
 * Browser events cannot establish completed purchases, refunds, legal rights,
 * actual revenue, or marketing consent by themselves.
 */
import type { BusinessEvent } from "./types";

export const STOREFRONT_EVENT_NAMES_V2 = [
  "view_item", "audio_play", "audio_engaged", "filter_apply",
  "license_select", "add_to_cart", "begin_checkout", "download_success",
  "free_claim", "email_marketing_consent",
  "related_offer_view", "related_offer_accept",
] as const;

export type StorefrontCommerceName = typeof STOREFRONT_EVENT_NAMES_V2[number];
export type ConsentState = "granted" | "denied" | "unknown";

export interface CommerceIntakeEventV2 {
  event_id: string;
  event_name: StorefrontCommerceName;
  timestamp_utc: string;
  shop_domain: string;
  anonymous_session_id: string;
  consent_status: ConsentState;
  product_gid?: string;
  variant_gid?: string;
  catalog_type?: "beat" | "beat_pack" | "sample_pack" | "plugin" | "service";
  audio_asset_id?: string;
  source?: string;
  medium?: string;
  campaign?: string;
  device?: string;
}

function object(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function optionalString(value: unknown, name: string): string | undefined {
  if (value === undefined || value === null) return undefined;
  if (typeof value !== "string" || value.length > 256) throw new Error("Invalid " + name);
  return value;
}

function requiredString(value: unknown, name: string): string {
  if (typeof value !== "string" || value.trim().length === 0 || value.length > 256) {
    throw new Error("Invalid " + name);
  }
  return value;
}

/** Rejects malformed, cross-shop and client-asserted financial events.
 * Returns only allowlisted metadata, dropping unexpected/PII fields.
 * Passing this validation does NOT imply the browser event is genuine.
 */
export function parseCommerceIntakeV2(value: unknown, expectedShopDomain: string): CommerceIntakeEventV2 {
  if (!object(value)) throw new Error("Commerce event must be an object");
  const expected = requiredString(expectedShopDomain, "expectedShopDomain").toLowerCase();
  const received = requiredString(value.shop_domain, "shop_domain").toLowerCase();
  if (expected !== received) throw new Error("Commerce shop identity mismatch");
  const event_name = requiredString(value.event_name, "event_name") as StorefrontCommerceName;
  if (!(STOREFRONT_EVENT_NAMES_V2 as readonly string[]).includes(event_name)) {
    throw new Error("Unsupported storefront event; purchase/refund require Shopify evidence");
  }
  const timestamp_utc = requiredString(value.timestamp_utc, "timestamp_utc");
  if (!/^\d{4}-\d{2}-\d{2}T.*Z$/.test(timestamp_utc) || Number.isNaN(Date.parse(timestamp_utc))) {
    throw new Error("timestamp_utc must be valid UTC ISO 8601");
  }
  const consent_status = value.consent_status;
  if (!["granted","denied","unknown"].includes(String(consent_status))) {
    throw new Error("Invalid consent status");
  }
  const catalog_type = optionalString(value.catalog_type, "catalog_type");
  if (catalog_type !== undefined && !["beat","beat_pack","sample_pack","plugin","service"].includes(catalog_type)) {
    throw new Error("Invalid catalog_type");
  }
  const product_gid = optionalString(value.product_gid, "product_gid");
  const variant_gid = optionalString(value.variant_gid, "variant_gid");
  if (product_gid && !/^gid:\/\/shopify\/Product\/\d+$/.test(product_gid)) throw new Error("Invalid product GID");
  if (variant_gid && !/^gid:\/\/shopify\/ProductVariant\/\d+$/.test(variant_gid)) throw new Error("Invalid variant GID");
  if (["view_item","add_to_cart","license_select"].includes(event_name) && !product_gid) {
    throw new Error("Product GID is required for product interaction");
  }
  if (event_name === "add_to_cart" && !variant_gid) throw new Error("Cart event requires a selected variant");
  return {
    event_id: requiredString(value.event_id, "event_id"),
    event_name,
    timestamp_utc,
    shop_domain: received,
    anonymous_session_id: requiredString(value.anonymous_session_id, "anonymous_session_id"),
    consent_status: consent_status as ConsentState,
    product_gid,
    variant_gid,
    catalog_type: catalog_type as CommerceIntakeEventV2["catalog_type"],
    audio_asset_id: optionalString(value.audio_asset_id, "audio_asset_id"),
    source: optionalString(value.source, "source"),
    medium: optionalString(value.medium, "medium"),
    campaign: optionalString(value.campaign, "campaign"),
    device: optionalString(value.device, "device"),
  };
}

/** Bridge ONLY compatible nonfinancial events into the existing canonical bus.
 * Other specialized funnel events must use a separately versioned analytics
 * store rather than pretending to be supported canonical event types.
 */
export function toSonicBusinessEventV1(event: CommerceIntakeEventV2): BusinessEvent | null {
  const map: Partial<Record<StorefrontCommerceName,string>> = {
    view_item: "product_viewed",
    add_to_cart: "add_to_cart",
    begin_checkout: "checkout_started",
  };
  const event_type = map[event.event_name];
  if (!event_type) return null;
  return {
    event_id: "commerce-v2:" + event.shop_domain + ":" + event.event_id,
    event_type,
    schema_version: "1.0",
    occurred_at: event.timestamp_utc,
    source: "web",
    entity: { type: event.product_gid ? "product" : "session", id: event.product_gid || event.anonymous_session_id },
    actor: { session_id: event.anonymous_session_id },
    context: { shop_domain: event.shop_domain, channel: "storefront", evidence_level: "untrusted_client" },
    properties: { commerce_event_name: event.event_name, catalog_type: event.catalog_type,
      variant_gid: event.variant_gid, consent_status: event.consent_status,
      source: event.source, medium: event.medium, campaign: event.campaign, device: event.device },
    outcome: "unknown",
  };
}
