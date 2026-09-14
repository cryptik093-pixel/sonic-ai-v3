---
document_id: SAV3-EXP-COMMERCE-STARTER-2026-09-13
knowledge_class: audit
observed_at: 2026-09-13T19:23:00-05:00
lifecycle: current
claim_state: SUPPORTED
campaign_id: ohb_starter_validation_20260913
creative_id: control_v1
landing_variant: cf_flagship_direct_v1
product_sku: OHB-FPS-001
---

# Flagship Producer Starter — Controlled Acquisition Experiment

## Objective

Validate whether a focused $5 direct-response landing experience can produce attributable commercial progression from TikTok traffic.

## Control funnel

- Platform: ClickFunnels
- Funnel: **OHB — Flagship $5 Direct Sale**
- Funnel public ID: `YRGmkr`
- Domain: `mvp.omega-house.online`
- Domain status: `secured`
- Step: **Flagship Entry — Direct Sale**
- User-facing path: `/flagship-entry-offer`
- Offer: Flagship Producer Starter — Omega House Entry Pack
- Shopify SKU: `OHB-FPS-001`
- Shopify variant: `47889740136684`
- Price: `$5.00`

## Canonical control URL

```text
https://mvp.omega-house.online/flagship-entry-offer?utm_source=tiktok&utm_medium=paid_social&utm_campaign=ohb_starter_validation_20260913&utm_content=control_v1&campaign_id=ohb_starter_validation_20260913&ad_id=control_v1&placement=tiktok_promote
```

This exact URL is the control link for the first TikTok paid/promoted validation run. A materially different creative receives a new `utm_content` / `ad_id`.

## Funnel proposition

The control page currently presents:

- $5 entry offer;
- direct Shopify cart CTA;
- original producer assets;
- Basic License;
- one-time purchase / no subscription;
- MVP Founder cohort positioning;
- direct-to-cart CTAs;
- no requirement to browse the broader storefront before purchase.

## Attribution configuration

The ClickFunnels funnel footer currently captures standard UTM/click identifiers and decorates outbound Omega House Shopify URLs with attribution and cart attributes.

Configuration inspection: **SUPPORTED**.

Observed real-customer end-to-end attribution: **NOT YET LOCKED**.

## Baseline before controlled traffic

### Shopify rolling 7 days at experiment start

- Sessions: 158
- Cart-add sessions: 2
- Checkout-reach sessions: 1
- Completed checkout sessions: 0
- Conversion rate: 0%
- Starter product landings: 4
- Starter product cart-add sessions: 1
- Homepage landings: 100
- Homepage cart-add sessions: 0
- Referrer mix: 151 direct, 5 search, 2 social

### ClickFunnels control funnel at experiment start

Window inspected: 2026-09-11 through 2026-09-13 19:23 CDT.

- Views: 0
- Unique views: 0
- Opt-ins: 0
- Sales: 0
- Sales value: $0

This zero-view baseline is useful because post-launch ClickFunnels traffic should be clearly distinguishable from pre-launch behavior.

## Hypothesis

If Producer Starter acquisition traffic is sent to a focused, direct-response page rather than the broad homepage, the campaign will produce attributable cart intent at a higher useful rate than the previous broad-homepage path.

## Primary sequence

```text
tagged ClickFunnels view
  -> outbound Shopify cart click
  -> Shopify cart state
  -> checkout
  -> paid $5 order
```

## Success gates

### Gate 1 — Route
At least one non-test tagged visitor reaches the ClickFunnels control page.

### Gate 2 — Intent
At least one non-test visitor reaches Shopify cart with preserved campaign/creative evidence.

### Gate 3 — Checkout
At least one attributed customer reaches checkout.

### Gate 4 — Purchase
At least one genuine $5 paid order is attributed to the control campaign.

### Gate 5 — Repeatability
Additional traffic/purchases are sufficient to judge whether the control is worth scaling.

## Failure handling

- Views but no outbound/cart intent: revise message, proof, CTA, or creative-message fit.
- Cart intent but no checkout: inspect cart/transition friction.
- Checkout but no purchase: inspect trust, payment, digital-delivery, or offer objections.
- Purchase but no repeatability: do not extrapolate economics from one order.

## Current state

**READY FOR CONTROLLED TRAFFIC.**

The funnel is live, its custom domain is secured, the $5 product is correct, and the attribution configuration is present.

The experiment is not yet commercially validated because ClickFunnels shows zero views and zero sales at baseline.

## Next evidence event

The next meaningful evidence is the **first non-test view on this control URL** followed by preservation of its campaign and creative identifiers into Shopify behavior.
