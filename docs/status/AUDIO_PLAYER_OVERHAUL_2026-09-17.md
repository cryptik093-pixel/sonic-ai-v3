---
document_id: SAV3-STATUS-AUDIO-PLAYER-2026-09-17
knowledge_class: audit
observed_at: 2026-09-17T18:07:00-05:00
lifecycle: current
claim_state: SUPPORTED
---

# Omega House Audio Player Overhaul — 2026-09-17

## STATE

**VERIFIED:** the MAIN theme remains unchanged.

**VERIFIED:** staging theme `Copy of Omega House — Sound First — Draft 01` remains UNPUBLISHED.

**VERIFIED:** the Flagship Producer Starter has a READY Shopify `custom.audio_preview` file reference.

**VERIFIED:** the live `omega-entry` template previously bypassed that metafield and depended only on a manual section URL.

**COMPLETED IN STAGING:** the Entry template now resolves:

`section.settings.audio_url | default: product.metafields.custom.audio_preview.value.url`

and feeds the resolved source into the existing global `sf-player`.

## STAGING THEME

- Theme GID: `gid://shopify/OnlineStoreTheme/165581947116`
- Name: `Copy of Omega House — Sound First — Draft 01`
- Role: `UNPUBLISHED`

## PHASE 1 — SOURCE WIRING

Completed:

- synced the live audio-critical layout/player/Entry template into staging;
- added product-metafield fallback to `oh-entry-funnel.liquid`;
- retained manual URL override precedence;
- reused `data-sf-audio`;
- no new player implementation introduced.

## PHASE 2 — PLAYER UX

Completed in staging:

- removed browser-native audio controls from the branded player surface;
- added custom play/pause;
- added seek/progress;
- added elapsed and duration display;
- preserved previous/next;
- preserved one-media-at-a-time behavior;
- preserved no-autoplay behavior;
- added product-type subtitle metadata to triggers;
- added preview milestone events for 25%, 50%, 75%, completion and errors;
- added preview-to-product CTA event.

## SOURCE-LEVEL VALIDATION

Passed:

- staging role is UNPUBLISHED;
- custom play/pause control exists;
- progress control exists;
- elapsed/duration fields exist;
- preview milestone event logic exists;
- native `<audio controls>` removed from canonical player;
- `preload="metadata"` retained;
- no autoplay token introduced;
- one-track-at-a-time enforcement remains;
- Starter fallback still resolves `custom.audio_preview`;
- homepage/product triggers now include product-type subtitle metadata.

## MAIN THEME PROTECTION

Confirmed unchanged after staging writes:

- `sections/oh-entry-funnel.liquid`
- `sections/sf-player.liquid`
- `snippets/sf-audio.liquid`
- `templates/product.omega-entry.json`

## REMAINING VALIDATION

**BLOCKED BY RENDERED-PREVIEW ACCESS IN CURRENT EXECUTION SURFACE:**

- visual desktop QA;
- visual mobile QA;
- real playback interaction;
- audible source correctness;
- preview loudness / clipping / truncation analysis.

These must pass before publishing staging.

## ROLLBACK

No live rollback is required because production was not modified.

Staging rollback is restoration of the prior staging files or abandonment of the unpublished theme.

## NEXT EXECUTION COMMAND

Open the unpublished theme preview on the Flagship Producer Starter page and validate play/pause, seek, sticky dock behavior, correct audio source and mobile layout before any publish action.
