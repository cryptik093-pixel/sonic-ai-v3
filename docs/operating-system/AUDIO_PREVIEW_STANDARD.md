---
document_id: OH-OS-AUDIO-PREVIEW-STANDARD-001
knowledge_class: operating-protocol
status: ACTIVE
observed_at: 2026-09-17T18:07:00-05:00
lifecycle: current
claim_state: SUPPORTED
---

# Omega House Audio Preview Standard

## Purpose

Audio preview is a conversion proof surface, not decorative media.

Every active music product should expose one canonical preview asset through structured product data and one canonical player architecture.

## Source of truth

Primary preview source:

`product.metafields.custom.audio_preview`

Allowed fallback:

1. explicit section/page override when a controlled experiment requires it;
2. product `custom.audio_preview`;
3. no player when neither source exists.

Do not duplicate the same preview URL across templates when the product metafield can supply it.

## Canonical storefront architecture

- Trigger: `snippets/sf-audio.liquid` or equivalent `data-sf-audio` trigger.
- Player: global `sections/sf-player.liquid`.
- Entry product: `sections/oh-entry-funnel.liquid` resolves the same product metafield and launches the same global player.
- Only one media source may play at a time.
- No autoplay.
- Player state may persist inside a tab, but playback requires a user gesture.

## Required player UX

- immediate play/pause;
- visible seek/progress;
- current time and total duration;
- title and useful product metadata;
- previous/next only when multiple playlist tracks exist;
- clear product/release CTA;
- visible loading/error state;
- mobile-safe controls;
- keyboard/focus accessibility;
- persistent sticky/miniplayer behavior after a preview is invoked;
- no browser-native audio UI as the primary branded control surface.

## Analytics contract

Minimum events:

- `preview_start`
- `preview_25`
- `preview_50`
- `preview_75`
- `preview_complete`
- `preview_error`
- `preview_to_product`

Commercial linkage should later connect preview engagement to cart, checkout, order and revenue.

## Audio asset quality

Preview masters must:

- avoid clipping and obvious distortion;
- avoid accidental hard cuts;
- use intentional fades when truncated;
- maintain consistent perceived loudness across adjacent previews;
- preserve enough fidelity to demonstrate production quality;
- protect full-length/source assets when a short commercial preview is sufficient;
- use documented export/transcode settings.

Target duration for commercial product previews should normally be approximately 30 seconds unless the product requires a different listening proof.

## Anti-fragmentation rule

Do not create another audio player implementation when the canonical player can be extended.

Legacy/hardcoded players should be deprecated only after active template dependencies are proven absent.

## Validation

A preview implementation is not LOCKED until:

1. source resolution is verified;
2. desktop playback is verified;
3. mobile playback is verified;
4. seek/pause/close behavior is verified;
5. one-track-at-a-time behavior is verified;
6. analytics events are observable;
7. product/CTA destination is correct;
8. rollback path is documented.

## Rollback

Theme changes must be staged on an unpublished theme first. Rollback is restoration of the previous staged file versions or continued use of the unchanged MAIN theme.
