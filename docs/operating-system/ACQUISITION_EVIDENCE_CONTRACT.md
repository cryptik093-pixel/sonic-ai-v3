---
document_id: OH-OS-ACQUISITION-EVIDENCE-001
knowledge_class: operating-protocol
status: ACTIVE
observed_at: 2026-09-13T19:23:00-05:00
lifecycle: current
claim_state: SUPPORTED
---

# Omega House Acquisition Evidence Contract

## Purpose

Define the minimum acquisition provenance required before Omega House treats a marketing event as useful commercial evidence.

The contract exists to connect a creative decision to an economic result:

```text
SOURCE
  -> CAMPAIGN
  -> CREATIVE
  -> LANDING
  -> PRODUCT / SKU
  -> CART
  -> CHECKOUT
  -> ORDER
  -> REVENUE
  -> FOLLOW-ON VALUE
```

Traffic without this chain may still be operationally useful, but it must not be treated as validated campaign performance.

## Required acquisition fields

| Field | Purpose |
|---|---|
| observed_at | event time |
| source | acquisition platform |
| medium | paid_social, social, email, direct, etc. |
| campaign_id | stable campaign identity |
| creative_id | stable creative identity |
| placement | traffic placement or promotion mode |
| landing_path | first controlled landing destination |
| landing_variant | page/control version |
| product_sku | canonical product being sold |
| funnel_state | view, cart, checkout, purchase, post_purchase |
| order_id | Shopify order identifier when available |
| revenue | realized revenue when available |
| evidence_source | ClickFunnels, Shopify, analytics, order data |
| confidence | VERIFIED, SUPPORTED, INFERRED, UNKNOWN |
| test_flag | distinguish internal QA from real customer behavior |

## Naming rules

Identifiers must be stable, lowercase, human-readable, and versionable.

Example:

```text
campaign_id = ohb_starter_validation_20260913
creative_id = control_v1
landing_variant = cf_flagship_direct_v1
product_sku = OHB-FPS-001
```

Do not silently reuse one creative ID for materially different creative.

## Required URL parameters

For controlled acquisition traffic use, at minimum:

```text
utm_source
utm_medium
utm_campaign
utm_content
campaign_id
ad_id
placement
```

## Current ClickFunnels implementation

Control funnel:

- Funnel: **OHB — Flagship $5 Direct Sale**
- Funnel public ID: `YRGmkr`
- Domain: `mvp.omega-house.online`
- Domain state: connected / secured
- User-facing step path: `/flagship-entry-offer`
- Product destination: Shopify cart for variant `47889740136684`
- Product SKU: `OHB-FPS-001`
- Offer price: `$5.00`

The funnel-level attribution script currently captures:

- `utm_source`
- `utm_medium`
- `utm_campaign`
- `utm_content`
- `utm_term`
- `fbclid`
- `ttclid`
- `gclid`
- `campaign_id`
- `adset_id`
- `ad_id`
- `placement`

It stores acquisition state in local storage, emits dataLayer events, and decorates outbound Omega House Shopify URLs with the observed attribution values and cart attributes.

This implementation is **SUPPORTED** by configuration inspection. Runtime customer-level persistence remains **NOT LOCKED** until a controlled test is observed through the available evidence surfaces.

## Evidence states

### VIEW VALIDATED
A tagged, non-test session is observed at the intended landing page.

### CART VALIDATED
A non-test cart event is observed with campaign/creative provenance.

### CHECKOUT VALIDATED
A non-test checkout reach is observed with campaign/creative provenance.

### PURCHASE VALIDATED
A genuine paid order is observed and reconciled to the campaign/creative.

### ECONOMICS VALIDATED
Enough purchases exist to estimate conversion, revenue per visitor, acquisition cost, and expected value without treating one isolated order as a stable rate.

## Anti-contamination rules

- Internal QA must be marked as test traffic.
- Historical free/$1 Beta orders cannot validate the current $5 offer.
- Direct or unknown-source behavior cannot be assigned to a campaign without evidence.
- A ClickFunnels view does not equal a Shopify cart.
- A cart does not equal a purchase.
- One purchase proves possibility, not stable economics.

## LOCK rule

No campaign may be called commercially validated until:

1. destination is verified;
2. acquisition identifiers are preserved;
3. at least one genuine paid order is attributable;
4. sufficient additional evidence exists before rate/economics claims are locked.
