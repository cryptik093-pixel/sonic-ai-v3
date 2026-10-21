# Omega House Pack Forge — integration and Codex handoff

**Status:** HANDOFF PREPARED — *not installed on the user's Windows desktop; no new ChatGPT plugin or Shopify endpoint has been deployed.*

**Source distribution:** `omega-house-pack-forge-v1.0.zip` (supplied in the ChatGPT conversation; it is **not** yet in this GitHub repository). SHA-256: `b8ad41841c7540cf6cbf008293d35b37902d8910dbe350d8699a522ae6e60b30`. Never fetch a similarly named archive from an untrusted URL. Confirm its hash before using it, or obtain explicit approval of a different hash.

## System ownership and reuse

This repository already has a production-workbench asset-packaging path, a measured-audio path and an MCP gateway. Inspect before integrating:

| Existing subsystem | Location | Reuse target |
| --- | --- | --- |
| Workbench upload / pack / release | `apps/api/workbench/router.py`, `apps/api/workbench/service.py` | Do not create a second divergent workflow |
| Audio evidence | `packages/audio-analysis/python` | Prefer existing measurement fields and defect taxonomy where equivalent |
| Producer/Sonic Intelligence | `apps/api/workbench/intelligence.py` and associated schemas | Decision record, evidence and review status |
| MCP transport and auth | `apps/api/integrations/gateway.py`, `apps/api/integrations/auth.py` | Explicit tools, scoped permission enforcement |
| Product/OS doctrine | `docs/operating-system/FOUNDER_ONBOARDING.md` | Approval owners and cross-system boundaries |

The ZIP's `integrations/AGENT_HANDOFFS.json` is a **contract proposal**, not evidence of remote agent dispatch. Its standalone HTTP service must not be blindly mounted into Sonic AI with its independent bearer-token model. Reuse project/operator authorization and durable event/audit storage first.

## Installer and immediate test

Run from the canonical repository root in an isolated environment, supplying the **actual** ZIP file to Codex:

```powershell
python scripts/install_pack_forge.py --zip "C:\path\to\omega-house-pack-forge-v1.0.zip"
python -m pip install -r tools/omega-house-pack-forge/requirements.txt
ffmpeg -version
ffprobe -version
python -m unittest discover -s tools/omega-house-pack-forge/tests -v
python tools/omega-house-pack-forge/scripts/pack_forge.py --help
```

Installer checks the GitHub checkout shape, archive traversal/symlinks, required files and size bounds; refuses an existing destination; never rewrites source sessions. Install success only means staged files, **not** service or MCP connectivity. Use the dedicated CLI documentation in `tools/omega-house-pack-forge/README.md` to run a real pack.

## Release state machine

```text
UPLOADED
  → VALIDATED_ARCHIVE
  → ANALYZED
  → {REVIEW_PENDING | READY_FOR_RIGHTS_CHECK}
  → RIGHTS_CONFIRMED_AND_LICENSE_APPROVED
  → RELEASE_READY
  → RELEASED_LOCAL_NOT_PUBLISHED
  → SHOPIFY_DRAFT_PREPARED
  → PUBLISHED (separate explicit approval + verified platform response)
```

Each saved job requires operator/project ownership; immutable archive SHA-256; analyzer/version/config hash; per-file original path/sha, proposed normalized category/path, measured metadata and confidence; review decisions with reviewer and timestamps; license version and approved scope; release ZIP SHA-256 and provenance; and downstream draft/publish identifiers only when genuinely returned.

Key/tempo are estimates with confidence and ambiguous half/double BPM guardrails. One-shots, percussion and non-tonal FX must not acquire fabricated musical keys. Near-duplicates are *review candidates*; exact duplicates are excluded from release but retained in the preserved source. Reject or quarantine corrupt archives, impossible metadata, symlinks and unsafe paths; bound decompressed size and audio decoding.

## Rights and commercial packaging

- Never infer ownership or clearance from filenames. Artist samples, stems and third-party presets need a recorded clearance decision.
- Separate `sample` / `preset` packages from `beat` packages. Beat **Basic** tier excludes stems and requires a legitimate approved stereo mix; **Premium** may include separately approved stems. No implicit exclusivity, resale rights, or trackout promise.
- Product record draft must carry genre/instrument/type, BPM range when supported, key when supported, descriptions, rights scope, technical formats, demo preview candidates and accurate counts. Sale listings should represent actual included audio files, not all source material.
- Publishing, theme edits, prices and platform delivery connections are independently gated by approval and verified API responses.
- Do not create new paid services or deploy a public processing endpoint to satisfy this milestone.

## Evidence and acceptance

**Local distribution baseline (Oct 21, 2026):** seven standard-library unit tests passed for deduplication, review/release gate, source preservation, damaged audio review, malicious ZIP paths, symlinks, MIDI review and Basic stem exclusion. This is **not** end-to-end validation inside Sonic AI.

**Required before integration completion:** verified distribution SHA; local installer success; baseline tests; actual application auth on the upload/manifest/review/release routes; persisted ownership and event history; confirmed developer MCP scope; one complete actual pack analysis; successful non-destructive release; actual Shopify draft only if separately approved and reachable; zero automatic publish; documented rollback.

**Avoid semantic conflict:** The standalone Pack Forge API is an auxiliary runner until its operations are reconciled with Sonic AI's native workbench. Where no integration adapter exists, report it as pending rather than routing around permissions.

## Codex deliverable

Create tested focused code on the feature branch; do not force-merge. Close with changed files, test outputs and coverage, runtime/auth evidence and remaining blockers, specifically distinguishing `STAGED`, `INTEGRATED_LOCAL`, `MCP_CONNECTED`, `DRAFT_READY` and `PUBLISHED`. Do not infer any later state from an earlier one.
