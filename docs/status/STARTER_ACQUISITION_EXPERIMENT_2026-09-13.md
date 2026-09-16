---
document_id: SAV3-EXP-COMMERCE-STARTER-2026-09-13
knowledge_class: audit
observed_at: 2026-09-16T08:51:59-05:00
lifecycle: current
claim_state: SUPPORTED
campaign_id: ohb_starter_validation_20260913
creative_id: control_v1
landing_variant: cf_flagship_direct_v1
product_sku: OHB-FPS-001
---

# Flagship Producer Starter — Controlled Acquisition Experiment

## Objective

Validate whether a focused $5 direct-response landing experience can produce attributable commercial progression from controlled traffic.

## Control funnel

- Platform: ClickFunnels
- Funnel: **OHB — Flagship $5 Direct Sale**
- Funnel public ID: `YRGmkr`
- Domain: `mvp.omega-house.online`
- Domain status: secured
- Step: **Flagship Beats Production Suite — $5 Founder Offer**
- User-facing path: `/flagship-entry-offer`
- Shopify SKU: `OHB-FPS-001`
- Shopify variant: `47889740136684`
- Price: `$5.00`

## Canonical control URL

```text
https://mvp.omega-house.online/flagship-entry-offer?utm_source=tiktok&utm_medium=paid_social&utm_campaign=ohb_starter_validation_20260913&utm_content=control_v1&campaign_id=ohb_starter_validation_20260913&ad_id=control_v1&placement=tiktok_promote
```

## Baseline at experiment start — 2026-09-13

### Shopify rolling 7 days
- Sessions: 158
- Cart-add sessions: 2
- Checkout-reach sessions: 1
- Completed checkout sessions: 0
- Starter product landings: 4
- Starter product cart-add sessions: 1
- Homepage landings: 100
- Homepage cart-add sessions: 0

### ClickFunnels control
- Views: 0
- Unique views: 0
- Sales: 0
- Sales value: $0

## Observed state — 2026-09-16

### ClickFunnels control, 2026-09-13 through 2026-09-16 08:51 CDT
- Pageviews: 16
- Unique views: 13
- Entry-step sales: 0
- Checkout-step views: 0
- Confirmation-step views: 0
- Sales value: $0

**VERIFIED:** Gate 1 / route traffic has occurred at the ClickFunnels control surface.

**UNKNOWN:** the 13 unique views cannot yet be proven to be exclusively non-test TikTok traffic from the canonical control URL.

**VERIFIED:** no ClickFunnels-native progression into its checkout or confirmation steps occurred in this observation window.

### Shopify rolling 7 days ending 2026-09-16
- Sessions: 180
- Cart-add sessions: 4
- Checkout-reach sessions: 3
- Completed checkout sessions: 0
- Orders: 0
- Total sales: $0
- Homepage landings: 123; cart-adds: 0
- Starter product landings: 5; cart-adds: 1
- Shop Pay checkout landings: 2; cart-adds: 2; checkout reaches: 2
- Separate checkout landing: 1; cart-add: 1; checkout reach: 1

**VERIFIED:** Shopify has additional cart/checkout activity compared with the experiment-start baseline.

**UNKNOWN:** available analytics do not prove those Shopify cart/checkout events originated from the ClickFunnels control campaign.

**VERIFIED:** the current $5 acquisition experiment has produced no paid order and no attributable revenue.

## Current diagnostic

The earliest proven failure is now:

```text
CONTROL VIEW -> ATTRIBUTABLE OUTBOUND / CART TRANSITION
```

The landing surface can receive traffic. The next requirement is runtime evidence that campaign and creative identifiers survive the ClickFunnels-to-Shopify transition.

## Next validation action

Run exactly one marked QA attribution traversal using:

```text
utm_campaign=ohb_starter_validation_20260913
utm_content=qa_attribution_01
campaign_id=ohb_starter_validation_20260913
ad_id=qa_attribution_01
placement=qa_test
```

This traversal is test traffic and must never be counted as customer conversion evidence.

Validation sequence:
1. Observe the QA view on ClickFunnels.
2. Follow the primary Shopify CTA.
3. Confirm campaign/creative identifiers are present on the outbound Shopify destination or persisted cart attribution state.
4. If propagation passes, mark the bridge VERIFIED and resume non-test control traffic.
5. If propagation fails, repair attribution before paid scaling.

## Success gates

### Gate 1 — Route
**VERIFIED:** control surface has received traffic.

### Gate 2 — Intent
**NOT LOCKED:** no non-test cart event is yet deterministically reconciled to the control campaign.

### Gate 3 — Checkout
**NOT LOCKED:** Shopify checkout activity exists but is not deterministically reconciled to the control campaign.

### Gate 4 — Purchase
**NOT ACHIEVED:** zero paid orders in the current rolling 7-day window.

### Gate 5 — Repeatability
**NOT ACHIEVED.**

## LOCK status

**LOCKED:** the ClickFunnels control exists, is live, and has received traffic.

**LOCKED:** the broad Shopify homepage remains non-productive for cart progression in the current rolling window.

**NOT LOCKED:** ClickFunnels-to-Shopify attribution persistence.

**NOT LOCKED:** current offer conversion rate, CAC, revenue per visitor, and campaign economics.

## Next execution command

**Run one marked `qa_attribution_01` traversal through the ClickFunnels control and verify campaign/creative persistence into Shopify before increasing paid traffic.**
