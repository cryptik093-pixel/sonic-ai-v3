# OH-CONTENT-002 — Post, Sound, Proof, and Delivery Spec

## Audio direction

- Music: restrained, modern, cinematic hip-hop bed; leave the midrange open for speech. Use cleared Omega House source audio only.
- Sound design: sub hit, five diagnostic ticks, mono/narrowing transitions, subtle UI clicks. Avoid horror risers, meme effects, and over-compression.
- Voice mix: center, intelligible, lightly compressed, de-essed, music ducked 4–6 dB under speech. Keep proof transitions level-matched so the “before/after” is not a loudness trick.
- Delivery target: stereo AAC at 48 kHz; voice and proof must remain intelligible on phone playback. Confirm no clipping after encoding.

## Before/after audio proof plan

1. Select one real beat excerpt with permission to use; document file name, source, BPM/key if known, and the exact 5–10 second region.
2. Render a clean stereo reference and a mono fold-down from that same excerpt at matched integrated loudness.
3. Capture the exact same musical moment in both states; do not swap beats, change arrangement, or claim a score that was not measured.
4. Play stereo first, then mono, with a clear on-screen label. If a problem is not audible, do not dramatize it.
5. For the optional after example, document the actual stock-tool change and render again. Label it **BEFORE** / **AFTER** and state what changed, not “fixed” or “professional.”
6. Archive the source excerpt, renders, settings, and a short note describing the audible/visual evidence for reproducibility.

## Captions and graphics

- Burn-in captions for social master; provide a separate clean master without captions.
- Use high-contrast white text with restrained violet accent and Omega House red; avoid covering the muzzle, hands, proof UI, or CTA.
- Captions are sentence case, 2 lines maximum, timed to speech. Preserve the exact phrases **WILL YOUR BEAT SURVIVE?**, **THE SONIC INTEGRITY TEST**, and the CTA.
- Add a caption-safe end-card hold of at least 2.5 seconds.

## Required exports

- `OH-CONTENT-002_HERO_55S_CLEAN_1080x1920.mp4`
- `OH-CONTENT-002_HERO_55S_CAPTIONED_1080x1920.mp4`
- `OH-CONTENT-002_HOOK_18S_CAPTIONED_1080x1920.mp4`
- `OH-CONTENT-002_PROOF-OFFER_30S_CAPTIONED_1080x1920.mp4`
- `OH-CONTENT-002_THUMBNAIL_1080x1920.png` — approved avatar frame, no unverified score.
- `OH-CONTENT-002_ENDCARD_SCORECARD_1080x1920.png`
- `OH-CONTENT-002_ENDCARD_PLAYBOOK_ALT_1080x1920.png`

## Release QA gate

- Playback inspection: first frame, avatar identity/wardrobe, lip sync, every text card, caption timing, proof labels, and final CTA.
- Audio inspection: headphones, phone speaker, stereo-to-mono fold-down, audible proof contrast, no clipping or distracting music masking.
- Link inspection: replace `[SCORECARD_URL]`, click/test the exact destination from the final release asset, and record the result.
- Record export paths, codec, duration, dimensions, loudness notes, proof source, and inspector/date in the release log.

## Alternate end card

Render and retain separately: **“Get the Sonic Integrity Playbook™ — Foundational Mix Architecture.”** Do not append it to the first-release master unless the campaign owner explicitly changes the CTA strategy.
