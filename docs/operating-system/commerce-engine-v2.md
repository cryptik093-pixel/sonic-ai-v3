# Omega House Commerce Engine V2 — Sonic Intelligence adapter

**Date:** 2026-10-19 · **Status:** staged proposal + tested-in-repo source awaiting CI/runtime verification · **No live Shopify mutation**

## Governing reference
Omega House OS (private repository) is the source of commerce policy:
`cryptik093-pixel/OMEGA-HOUSE-OS/knowledge/commerce/OMEGA_HOUSE_BEATS_COMMERCE_ENGINE_V2.html`
and its adjacent `commerce-engine-v2.manifest.json`.

The original document distinguishes current observed state from proposed pricing, products and UI changes. This bridge must not treat those proposals as published offers.

## Contract in code
`packages/events/src/commerce.ts` exports:
- `parseCommerceIntakeV2(rawEvent, expectedShopDomain)`: validates an allowlisted, client-origin event envelope, expected domain, timestamp, product/variant identifiers, and declared consent status. Returns only safe allowlisted fields, without arbitrary customer or financial data. Expected domain must come from trusted server configuration, NOT the browser request.
- `toSonicBusinessEventV1(event)`: maps only `view_item → product_viewed`, `add_to_cart → add_to_cart`, and `begin_checkout → checkout_started` to the existing v1 canonical event bus. All are marked `untrusted_client` and carry **no** revenue impact. Purchase, refund and order-state attribution cannot originate from a browser callback.

Specialized audio/offer/free-claim events are intentionally validated but not misrepresented as supported events by the existing canonical bus. A separate durable commerce-telemetry store with its own event vocabulary and idempotency is needed before collecting those events live; this change **does not** install tracking.

## Source-of-truth and identity
- Verified connected Shopify merchant: `omega-house.online`; currency USD; Basic plan at time of review. This does not prove that historical ShopifyQL analytics originated from that exact account.
- The blueprint records a conflicting analytics context `myvig8-wn.myshopify.com`. Block baseline conversion calculations until Shopify shop ID/merchant identity for the query output is reconciled.
- Revenue: Shopify paid order/refund records, deduplicated by stable order/refund IDs. A Shopify `orders/create` event does not automatically prove a paid order; inspect payment/financial status.
- Audio previews, product navigation, search filters: consent-compliant storefront instrumentation, attributed only to non-financial funnel interactions.
- Plugin release eligibility: separately verified installer hash, host compatibility, test report. Historical FL Studio .fst preset crashes remain blockers.
- Marketing automation requires explicit consent and legal eligibility; browsing intent and `email_marketing_consent` client events alone do not authorize outbound marketing.
- A SHA-256, contract version, license ID or QA metadata is evidence metadata, not automatic proof of ownership, exclusive rights or artist testimonial.

## Integration gate to make this live
1. Verify merchant identity using a stable shop ID and server-side configured domain. Do not wire browser events into unscoped or historical analytics.
2. Implement a consent-aware browser dispatcher that sends only allowed event fields through an authenticated/rate-limited endpoint, with abuse controls and a durable idempotent store.
3. Wire the guarded adapter to that endpoint and emit no financial business events without authenticated Shopify evidence.
4. Verify event dedup, mobile playback stability, download receipts, canceled/refunded orders and environment isolation.
5. Run tests, operator approval, staging data QA and monitored rollout. No new paid analytics platform is required.

## QA
The existing `packages/events/src/index.test.ts` suite includes cross-shop rejection, financial-event rejection, PII drop, canonical mapping and cart-variant checks. The repository's configured `npm test`/Vitest validation determines whether the change is accepted; no passing CI or running production endpoint is asserted by this document.
