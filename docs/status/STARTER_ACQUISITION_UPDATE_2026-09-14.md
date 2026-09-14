---
document_id: SAV3-EXP-COMMERCE-STARTER-UPDATE-2026-09-14
knowledge_class: audit
observed_at: 2026-09-14
lifecycle: current
claim_state: SUPPORTED
campaign_id: ohb_starter_validation_20260913
creative_id: control_v1
landing_variant: cf_flagship_direct_v1
product_sku: OHB-FPS-001
---

# Flagship Producer Starter — Controlled Acquisition Update

## State change

The ClickFunnels control is no longer at a zero-traffic baseline.

### ClickFunnels control

For the post-baseline window beginning 2026-09-13 19:23 CDT:

- pageviews: 1
- reported unique views: 2
- opt-ins: 0
- sales: 0
- sales value: $0

The ClickFunnels response contains an internal inconsistency (`pageviews = 1`, `views_unique = 2`), so the only safe claim is that **control traffic has begun**. Do not infer an exact unique-visitor count from this response.

### Shopify rolling 7-day state

- sessions: 162
- cart-add sessions: 3
- checkout-reach sessions: 2
- completed checkout sessions: 0
- conversion rate: 0%
- orders: 0
- total sales: $0

Compared with the experiment-start baseline, Shopify moved from 158 sessions / 2 cart-add sessions / 1 checkout-reach session to 162 / 3 / 2.

The Starter product landing remains at 4 sessions and 1 cart-add session. The broad homepage now shows 108 landings and still 0 cart additions.

A new checkout landing path appears with 1 cart-add and 1 checkout-reach event, but the available ShopifyQL evidence does **not** preserve the campaign/creative identifiers needed to prove that event originated from the ClickFunnels control.

Recent Shopify referrer mix is dominated by direct traffic. Social traffic in the latest two-day window is 1 session from Facebook, not TikTok.

## Validation gates

### Gate 1 — Route

**SUPPORTED / PARTIAL PASS.** ClickFunnels now records traffic on the control funnel after the zero-view baseline.

The current evidence does not expose the visitor's query parameters, so the exact `campaign_id` / `creative_id` used by that visit is not independently visible in the stats response.

### Gate 2 — Intent

**NOT LOCKED.** Shopify cart activity increased, but current evidence cannot deterministically tie the new cart event to the ClickFunnels control.

### Gate 3 — Checkout

**NOT LOCKED.** Shopify checkout-reach activity increased, but provenance is unresolved.

### Gate 4 — Purchase

**FAILED / NOT YET ACHIEVED.** No completed checkout, order, or revenue exists in the current rolling seven-day window.

### Gate 5 — Repeatability

**NOT STARTED.** No paid conversion evidence exists.

## Current diagnosis

The experiment has advanced from `READY FOR CONTROLLED TRAFFIC` to `CONTROL TRAFFIC OBSERVED / ATTRIBUTION UNPROVEN`.

Do not redesign the control page yet. The sample remains too small, and the first priority is proving provenance across the ClickFunnels-to-Shopify transition.

## Highest-leverage next action

Run one deliberately identifiable QA acquisition pass through the control URL using a clearly marked test creative identifier, then verify whether that identifier survives into the Shopify-facing URL/cart attributes. The QA pass must remain distinguishable from genuine customer traffic and must not be counted as commercial conversion evidence.

After runtime propagation is proven, resume genuine controlled traffic and evaluate the first attributable cart, checkout, and paid order.
