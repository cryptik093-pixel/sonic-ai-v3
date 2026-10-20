# BFCM 2026 — Sonic AI V3 / Shopify Commerce Integration Contract

**Status:** Design and verification contract, not shipped integration. **Campaign:** `bfcm_2026`. This proposal derives from the [Omega BFCM Codex skill](../../.agents/skills/omega-bfcm-2026/SKILL.md) and [commercial playbook](../../.agents/skills/omega-bfcm-2026/references/campaign-playbook.md). Preserve Sonic AI V3's documented local/single-operator architecture and no-publish boundary.

## Current capability and strict boundary

The root README (Sonic AI V3 0.6.0) describes deterministic MIDI creation, audio checks, pack ZIP inventory/lineage, prepared release copy/demo plans and an **unpublished Shopify draft CSV**. Those facts do not prove live Shopify OAuth, product creation, coupon scheduling, actual fulfillment, attribution events, email sending or a hosted autonomous agent. Do not introduce runtime claims without live test evidence. Product rights in metadata remain `not_assessed` until appropriately reviewed.

## Proposed phased integration

### 0. Read-only discovery and event ownership

Read and verify enabled auth scopes and tenant/operator ownership before any network calls. Resolve the exact Omega House Beats store, campaign, product/variant IDs, prices, bundled assets, licensing and published availability. Normalize into a typed, timestamped, source-attributed `commerce_snapshot` with `observed_at`, `store_id`, `product_id`, `variant_id`, `source`, `currency`, `price`, `license_reference`, `rights_review_status` and `confidence/status`. Missing facts are `unknown`, never default approvals.

### 1. Offer and asset planner

Create **proposed** draft bundle manifests for $39 Session Kit and $79 Vault, drawing only from verified eligible current SKUs and asset inventories. Enforce unambiguous license compatibility and duplicate-file handling; recalculate $99/$242 component comparisons as of actual sale date. Validate formats, pack hashes, ZIP size, delivery, any genuine limited offers, service scope/capacity and the Founder 500 allocator. Generate reviewed draft CSV / typed manifest without altering Shopify state.

### 2. Landing / lifecycle handoff

Output content contracts consumable by the actual Online Store 2.0 theme or an approved app integration:
- Audio preview entries with explicit `asset_id`, proven URL, credited creator, measured/published BPM and key when available, waveform/artwork reference, rights/preview limit and playback metadata.
- Audience pathways (producer vs artist) with correct target URLs and verified available offer IDs.
- Bundle comparison, license mini-FAQ, product formats, support links, actual price/urgency windows in America/Chicago.
- Consent-aware campaign content and segments, with content approval before any email send, post or external message.
- No guessed SKU URLs, invented sound files, synthetic customer reviews or externally asserted performance improvements.

### 3. Measurement / decision intelligence

Prefer established Shopify/GA4 standard commerce events: `view_item`, `select_item`, `add_to_cart`, `begin_checkout`, `purchase`, `refund`. Add explicit interaction events for `bfcm_audio_play`, `bfcm_audience_selected`, `bfcm_license_open`, `bfcm_offer_compare`, `bfcm_download_access` where actual instrumentation is approved. Required dimensions: `campaign_id=bfcm_2026`, `event_id`, timestamp, channel UTM, session (pseudonymous), consent and source, product/variant/offer IDs, currency and money only where applicable. Keep PII and license/download secrets out of event payloads. Deduplicate purchase events and reconcile against Shopify real paid orders, refund status and attribution coverage. Do not double count the same order.

Sonic Intelligence should produce campaign scorecards by audience and channel: gross/net revenue, revenue/session, order rate, AOV, qualified visits, audio engagement, view-to-cart, checkout completion, offer attach, email capture (consented), refund/support rate, asset access success and mobile performance. Report sample sizes and unknown/missing instrumentation.

### 4. Approval-gated execution (future implementation)

Separate permissions: READ catalog; DRAFT assets/offer; PREVIEW/TEST theme; WRITE Shopify catalog; SEND campaign; PUBLISH live campaign. Every consequential mutation requires authorized identity, scoped credential, immutable action log, target IDs, explicit approval, idempotency key, rollback strategy and verified result. A green internal model response is not a successful sale, a published theme or a sent email.

## Acceptance tests to add only with real implementation

- Unit: component sum, percentage discounts, time boundary (Nov 30 23:59 Central), offer validation, rights/availability fail-closed, event schema/PII handling.
- Integration against approved store/test environment: auth scopes, existing draft CSV conversion, rollback, product/variant linkage, accelerated/guest checkout eligibility, real digital download access and webhook/event deduplication.
- UI: 320px+ mobile, audio keyboard controls, actual preview playback, sticky CTA not obstructing checkout, licensing clarity, no heavy autoplay videos.
- Evidence: baseline and post-change snapshots, fixture vs live labeling, log IDs, minimal event schema, monitoring and support path.

## No-regression

No broad restructure of Sonic V3 to add a storefront. Preserve desktop launch, composition compiler, audio/ZIP lineage, owner/workspace boundaries, source originals, existing reports and tests. Any implementation must be reversible and pass existing repository checks. Do not add a paid dependency without approval.
