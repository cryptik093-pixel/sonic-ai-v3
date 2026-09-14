---
document_id: SAV3-STATUS-COMMERCE-PULSE-2026-09-13
knowledge_class: audit
observed_at: 2026-09-13T08:19:26-05:00
commit_scope: main
lifecycle: current
claim_state: SUPPORTED
supersedes:
  - SAV3-STATUS-COMMERCE-PULSE-2026-09-12
evidence_refs:
  - ShopifyQL rolling 7-day funnel comparison 2026-09-13
  - ShopifyQL rolling 7-day landing-page funnel 2026-09-13
  - ShopifyQL rolling 7-day referrer-source sessions 2026-09-13
  - ShopifyQL rolling 7-day sales comparison 2026-09-13
  - ClickFunnels funnel structure/configuration inspection 2026-09-13
  - ClickFunnels funnel/page stats baseline 2026-09-13
  - ClickFunnels domain status inspection 2026-09-13
---

# Omega House Commerce Command Pulse — 2026-09-13

# OMEGA HOUSE COMMAND STATE

## STATE

**VERIFIED:** rolling 7-day store traffic is materially lower than the prior comparison period.

**VERIFIED:** the current rolling 7-day funnel contains 157 sessions, 2 sessions with cart additions, 1 session reaching checkout, 0 completed checkouts, and 0 orders / $0 sales.

**VERIFIED:** the Flagship Producer Starter product path `/products/flagship-producer-starter` received 4 landing sessions and generated 1 cart-add session.

**VERIFIED:** the homepage `/` received 99 landing sessions and generated 0 cart additions, 0 checkout reaches, and 0 completed checkouts.

**VERIFIED:** one separate Shop Pay checkout landing generated a cart-add + checkout-reach event but did not complete purchase; this does not validate the Starter landing path.

**VERIFIED:** current traffic source mix is primarily direct (150 sessions), with search (5) and social (2). The prior TikTok-heavy burst is no longer the dominant current window.

**UNKNOWN:** the identity/provenance of the Starter-page cart-add session is not deterministically attributable to a campaign or creative with the current analytics evidence.

## REVENUE BOTTLENECK

The current offer still has no validated paid conversion in the rolling 7-day window. The immediate problem is no longer lack of traffic volume alone; it is insufficient attributable commercial progression from landing to purchase.

## CONVERSION BOTTLENECK

The homepage remains non-productive for direct commercial progression in the current window. The dedicated Starter product page has produced the only clearly associated cart-add behavior from a product landing, but the sample is extremely small and cannot yet be treated as a stable conversion rate.

Current diagnostic order:

`Destination quality -> attributable cart intent -> checkout -> paid order`

## ENGINEERING BOTTLENECK

Sonic Intelligence still lacks deterministic acquisition provenance connecting:

`creative_id -> campaign_id -> source -> landing_variant -> sku -> cart -> checkout -> order -> revenue`

Without this contract, aggregate Shopify events cannot reliably identify which message or acquisition source caused a commercial state transition.

## PRODUCTION / IP OPPORTUNITY

Promote the Acquisition Evidence Contract into a reusable Sonic Intelligence commerce primitive.

Minimum event fields:

- observed_at
- session/acquisition identifier
- source
- medium
- campaign_id
- creative_id
- landing_path / landing_variant
- product_sku
- funnel_state
- order_id when present
- revenue when present
- evidence_source
- confidence

This converts campaign learning into durable operational intelligence instead of isolated marketing observations.

## 10-YEAR PERSPECTIVE

A mature Omega House would not optimize from raw session totals. It would rank acquisition paths by attributable downstream value. Today's data reinforces that principle: the broad homepage receives most landings but no cart behavior, while the focused Starter destination shows an early cart signal on very low volume.

## HIGHEST-LEVERAGE MOVE

Promote the verified ClickFunnels control funnel **OHB — Flagship $5 Direct Sale** to primary controlled acquisition destination.

Control route:

`https://mvp.omega-house.online/flagship-entry-offer`

The Shopify Starter product page remains the fallback/product source-of-truth, while Shopify cart/checkout remains the transaction source-of-truth.

The ClickFunnels control funnel is live on a secured custom domain, uses direct-to-Shopify-cart CTAs, and contains an attribution script that captures UTM/click identifiers and decorates outbound Shopify URLs. Configuration is SUPPORTED; real-customer end-to-end attribution remains NOT LOCKED until observed.

Do not infer success from the prior 1-of-4 Shopify Starter cart event. Treat it as a signal that justified this controlled experiment, not as a proven conversion rate.

# NOW

## 1. Run a controlled Starter destination test

- **OWNER / ROLE:** Growth / CRO
- **EXACT ACTION:** send the next intentional Producer Starter acquisition traffic to the live ClickFunnels control at `mvp.omega-house.online/flagship-entry-offer`, not the homepage.
- **WHY NOW:** the focused Starter path has produced a cart signal while the homepage has not.
- **DEPENDENCY:** tagged acquisition URL.
- **EXPECTED RESULT:** measurable landing-to-cart behavior from the intended path.
- **EVIDENCE REQUIRED:** attributed session plus cart-add event from the tagged destination.
- **DEFINITION OF DONE:** at least one non-test customer cart event with preserved acquisition provenance.

## 2. Enforce acquisition tagging

- **OWNER / ROLE:** Sonic Intelligence / Growth Engineering
- **EXACT ACTION:** require campaign/source/creative identifiers on intentional acquisition links.
- **WHY NOW:** current cart behavior cannot be confidently tied to a creative or campaign.
- **DEPENDENCY:** stable naming convention.
- **EXPECTED RESULT:** every future cart and order can be reconciled to acquisition intent.
- **EVIDENCE REQUIRED:** tagged landing session visible in analytics or captured event data.
- **DEFINITION OF DONE:** one end-to-end tagged session is observed and its identifiers are preserved through the available funnel evidence.

## 3. Hold traffic scaling

- **OWNER / ROLE:** Founder / Growth
- **EXACT ACTION:** avoid materially increasing paid/promoted traffic until the controlled route produces attributable cart behavior and begins to establish paid-order evidence.
- **WHY NOW:** current revenue remains $0 and attribution is not yet reliable.
- **DEPENDENCY:** controlled test results.
- **EXPECTED RESULT:** learning efficiency improves before acquisition spend scales.
- **EVIDENCE REQUIRED:** first attributable cart, then first attributable paid order.
- **DEFINITION OF DONE:** scaling decision is based on measured route economics rather than session volume.

# NEXT

- If attributed carts appear but checkout does not: audit cart transition and offer confidence.
- If checkout appears but purchase does not: audit payment/trust/delivery friction.
- If no attributed carts appear: revise creative-message-offer fit before downstream optimization.

# LATER

- automated campaign-to-revenue attribution ingestion into Sonic Intelligence;
- creative expected-value scoring;
- Starter-to-suite LTV cohorts;
- automated commerce-consistency scans.

# IMPLEMENTATION SPEC

Canonical control URL:

`https://mvp.omega-house.online/flagship-entry-offer?utm_source=tiktok&utm_medium=paid_social&utm_campaign=ohb_starter_validation_20260913&utm_content=control_v1&campaign_id=ohb_starter_validation_20260913&ad_id=control_v1&placement=tiktok_promote`

See `docs/operating-system/ACQUISITION_EVIDENCE_CONTRACT.md` and `docs/status/STARTER_ACQUISITION_EXPERIMENT_2026-09-13.md`.

Naming must be stable and human-readable. Creative IDs should map to a documented creative ledger rather than arbitrary changing labels.

# VALIDATION PLAN

1. Launch one intentionally tagged acquisition click.
2. Confirm the landing destination and query parameters are intact.
3. Separate internal/test activity from genuine customer behavior.
4. Observe the next genuine cart event.
5. Reconcile that cart to source/campaign/creative where supported.
6. Require a genuine paid $5 order before declaring offer conversion validated.

# WHAT DANIEL SHOULD LEARN FROM THIS

A promising event is not yet a result. Four Starter landings producing one cart is directionally interesting, but the sample is too small and provenance is incomplete. The disciplined move is to turn that observation into a controlled test rather than celebrate or redesign prematurely.

# RISKS / DEPENDENCIES

- current traffic volume is much smaller than the previous comparison period, so evidence will accumulate more slowly;
- direct traffic dominates the present window, limiting source-level interpretation;
- the Shop Pay checkout event is not evidence that the Starter page drove checkout;
- no paid order exists in the current 7-day window.

# LOCK STATUS

**LOCKED:** the broad homepage remains unvalidated as the primary Producer Starter acquisition destination.

**SUPPORTED / NOT LOCKED:** the dedicated Starter product page shows an early cart-intent signal.

**NOT LOCKED:** current $5 offer conversion and campaign economics; zero paid orders remain in the rolling 7-day window.

# NEXT EXECUTION COMMAND

**Route the next controlled Producer Starter traffic to the ClickFunnels control URL using campaign `ohb_starter_validation_20260913` and creative `control_v1`; require an attributable genuine cart event before increasing traffic spend.**
