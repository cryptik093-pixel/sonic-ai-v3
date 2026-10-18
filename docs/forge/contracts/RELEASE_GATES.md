# Release Gates and Evidence Requirements

## Gate F0 — Foundation (this package)
PASS iff nested ZIP hash-lineage works, unsafe ZIP test matrix rejects adversarial cases, review approval is explicit, no approved filename collisions, rights-gated unpublished offline CSV is generated, and tests pass. Observed package-local result: **17/17 passed on 2026-10-18**. The example audio is synthetic and not commercially validated.

## Gate F1 — Canonical repository merge readiness
- Baseline SHA and repository branches written in PR, `AGENTS.md` honored.
- Overlay integrated without moving or deleting existing MIDI, pack, workbench, MCP and event code.
- Existing repository tests all pass, or regressions are reproduced, resolved and documented.
- Contract and API test paths validated from the canonical repo, not only standalone overlay.
- New fixtures never contain proprietary audio or customer identity in public Git.
- No external integration credentials committed.

## Gate F2 — Audio inference
- Actual WAV/FLAC decoding with bounded, streaming/segmented analysis; MP3/AIF support declared only after tested.
- BPM and key confidence thresholds calibrated against truth-labeled real/curated material with tempo half/double interpretation addressed.
- Silence, unsupported, nonrhythmic, ambiguous tonal and drum-only samples return unknown when appropriate.
- Any displayed BPM/key has method, confidence, algorithm version and human override indication.
- Reviewable UI available; operator decisions stored separately from model/DSP inferences.

## Gate F3 — Live Forge Workbench
- Authenticated actor, owner/workspace, verified resource-level rights and revision checks.
- ZIP import, analysis, batch review and export pass browser/API smoke with actual approved pack.
- Database writes and versioning are atomic; process crash or repeated request cannot double-export or corrupt manifests.
- Derived artifacts do not overwrite source/stem/master files or an existing export path.
- Authorized downloads, safe filenames, activity logs and tested rollback are in place.

## Gate A0 — Acquire/read-only Shopify
- Review stacked PRs in actual dependency order: OMEGA-HOUSE-OS #10 -> #11 -> #13; separate Tribe #16.
- Verify store-specific OAuth and real scoped Shopify reads, not only mocked responses; redact tokens and PII.
- Currency/refund-aware metrics and store isolation tested; no unsupported conversion or attribution claims.
- Human approval and auditable send mode; never assume a logged-in browser grants backend API permission.

## Gate S0 — Signal
- Rights/approval audit for all media, versioned content preview, correct channel asset dimensions, no autopublishing on defaults.
- Publishing evidence only after real authenticated integration; performance measurement only when verified provider data exists.

## Required PR evidence table

| Item | Required proof |
| --- | --- |
| Source truth | Repo + baseline and resulting commit SHA |
| Behavior | Screen/CLI walkthrough tied to code run |
| Verification | Exact test commands, results and counts |
| Security | Traversal/symlink/bomb/collision and owner/revision negative tests |
| Audio | Method, fixtures and known misdetections/unknowns |
| Data safety | Before/after source checksums and original immutability |
| External services | Connected / not connected / not tested, no guesses |
| Reversibility | Artifact rollback and migration rollback evidence |
| Release verdict | PASS / FAIL / NOT TESTED for each applicable gate |
