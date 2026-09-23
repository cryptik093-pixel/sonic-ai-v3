# Sonic Producer Brief Intelligence 0.6 — Delivery Record

**Document ID:** `SAV3-STATUS-PRODUCER-BRIEF-20260923`
**Observed:** 2026-09-23
**Scope:** `codex/producer-brief-intelligence` based on canonical `main`
**Lifecycle:** implementation complete; repository CI review pending
**Claim state:** `SUPPORTED` pending the branch's Linux, Chromium and Windows GitHub Actions run
**Current-state reference:** [Sonic AI V3 Current-State Audit](../architecture/current-state-audit.md)

## Delivered

The existing workbench's structured MIDI form now accepts a free-text producer brief. Sonic provides a read-only interpretation preview, generates the resolved MIDI locally, and presents the mapped signals and assumptions beside the playable/downloadable output.

### Flagship output

- Prompt control mapping for key/scale, style, mood, tempo, bar count, density and a quoted optional title.
- Typed control resolution with explicit-control precedence, prompt excerpts, field sources, documented defaults, warnings and simple negation handling.
- A deterministic local MIDI composer whose supported mood changes affect the progression and motif. Seed and musical controls remain reproducible.
- Separate melody/chord/bass/drum MIDI parts, a multitrack arrangement, synthesized WAV audition, `Composition.json` and DAW import notes.
- A no-write preview that tests verify creates no run or output file.

### Scoped intelligence memory and lineage

- `Keep this direction` / `Not for me` feedback is persisted as a versioned `workbench.feedback_recorded` event on a completed MIDI run.
- Stable feedback request IDs make retry behavior idempotent; reusing an ID with different data is rejected.
- A kept-output reference uses only the latest run with a current `keep` decision. A variation request without kept wording uses the latest successful MIDI output. Ordinary prompts read no saved composition context. The preview names the selected run and reused fields.
- `Composition.json` records the request ID, compiler/composer identifiers, prompt evidence, resolved controls, lineage edges, per-output byte count/SHA-256, and rights status `not_assessed` under `OH_METADATA_PACKAGING_LINEAGE_V1`.
- The application, HTTP API and MCP use the same workbench service. MCP now has 15 tested tools; the interpretation preview is read-only, and generation/feedback are explicit writes. OAuth read-only contexts cannot execute those writes.
- Status and UI use the live API address for MCP discovery, including an alternate loopback port. API root and workbench status share version `0.6.0`.

### Documentation repair

- Replaced the obsolete root overview with current features, runtime path, ownership and commercial boundaries.
- Replaced the scaffold-era current audit and audit report that incorrectly said the app, MIDI generator, API, persistence, UI and tests did not exist.
- Replaced Postgres/Redis/S3/Supabase placeholders in `.env.example` with configuration the local workbench actually reads.
- Corrected the docs authority/index and marked the 2026-09-22 workbench epic report as a historical 0.5 baseline.
- Updated the desktop quick start and Chromium workflow for the prompt, feedback and continuity journey.

## Validation evidence

| Check | Observed result |
| --- | --- |
| `python -m pytest apps/api/tests -q` | **88 passed** in 9.47 s; 15 deprecation warnings remain in the installed Starlette/test and legacy datetime paths |
| `python apps/desktop/launcher.py --smoke-test ...` | **Passed**: local HTTP boot, bundled UI assets, parsed MIDI, archive download and authorization boundary; proof recorded `passed: true` with 8 output artifacts |
| `node --check apps/api/workbench/static/app.js` | Passed |
| Python bytecode compilation of API and browser verifier | Passed |
| `python -m pip check` | No broken requirements; this scratch environment prints warnings for an invalid leftover NumPy distribution metadata directory |
| `git diff --check` | Passed |
| Chromium UI run | Not yet executed locally because Playwright is absent from this scratch runtime. The modified Chromium flow is included in the pull request's GitHub Actions gate. |
| Windows packaged/native UI checks | Pending the same GitHub Actions gate; no new Windows package is claimed before that run. |

The local environment's NumPy 2.5.3 wheel crashed while importing the audio stack. The API requirement is now bounded to the tested 2.0–2.3 series; the complete API suite and desktop smoke passed with NumPy 2.3.5. The remote clean Linux/Windows install will verify this bound.

## Explicit limits

- Prompt mapping is a deterministic supported vocabulary, not general semantic understanding. Unmapped language is stored as creative context and does not silently change musical controls.
- This produces algorithmic MIDI, not model-generated audio. The WAV audition uses simple synthesized sounds and is not a mix/master.
- Audio analysis measures its documented fields and does not assert musical tempo/key, LUFS or true peak.
- The workbench uses a fixed local producer/workspace; it is not a hosted, multi-tenant SaaS service.
- The asset rights field remains `not_assessed`. Lineage and hashes prove provenance relationships and byte identity, not legal ownership, licensing or publication readiness.
- Release preparation writes a draft CSV; the workbench does not publish to Shopify or claim sales results.

The adjacent `OMEGA-HOUSE-OS` repository was reviewed for the Tier 6 asset-lineage, source-preservation and commercial-rights boundaries. Those constraints informed this implementation; the separate repository was not modified.
