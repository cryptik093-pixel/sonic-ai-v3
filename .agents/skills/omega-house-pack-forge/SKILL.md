---
name: omega-house-pack-forge
description: Execute Omega House Studio's rights-aware ZIP sample-pack, beat-pack and preset-pack intake, BPM/key estimates, audio QA, duplicate screening, review queue, license approvals and release packaging. Use when the user asks to process a sound pack or integrate OMEGA FORGE with Sonic AI V3, Omega House OS, Tribal Network or Shopify.
---

# Omega House Pack Forge — Codex handoff

This is the **repository integration skill**, not proof that Pack Forge is installed. The V1.0 distribution must be supplied as `omega-house-pack-forge-v1.0.zip` (or located and hash-verified against the user-approved distribution). The pack-processing implementation is inside that ZIP. Never claim an installed or working integration until tests and runtime checks pass.

## Canonical system

- Repository: `cryptik093-pixel/sonic-ai-v3`, preserving `AGENTS.md`, current `main` baseline, and any local recovery branch. Never overwrite local project work.
- Existing points of integration: `apps/api/workbench/router.py` and `apps/api/workbench/service.py` for existing asset packaging, `apps/api/integrations/gateway.py` for MCP, `apps/api/main.py` for FastAPI routing, `packages/audio-analysis/python` for existing measurements, and `docs/operating-system/FOUNDER_ONBOARDING.md` for company contracts.
- Sonic AI computes evidence. Sonic Intelligence evaluates it. Omega House OS owns approvals/orchestration. Tribal Network provides creator handoff. Omega House Beats Shopify is **draft-only** until publication is explicitly approved.

## Real execution, not a plan

1. Read `docs/operating-system/PACK_FORGE_INTEGRATION_HANDOFF.md` and examine the current code and actual user-supplied distribution; preserve license terms and source files.
2. From the repository root, run `python scripts/install_pack_forge.py --zip "<path-to-omega-house-pack-forge-v1.0.zip>"`. The installer only stages the distribution at `tools/omega-house-pack-forge/`; it intentionally refuses overwrites.
3. Run `python -m pip install -r tools/omega-house-pack-forge/requirements.txt` in an isolated environment (no paid services); verify FFmpeg/FFprobe. Run `python -m unittest discover -s tools/omega-house-pack-forge/tests -v`. Do not use this as evidence for runtime APIs or commercial music quality.
4. Reconcile the existing native ZIP pack workflow and Pack Forge's job model. Create a single authenticated orchestration path rather than exposing an unauthenticated second API. Enforce operator/project ownership, source hash lineage, review status and rights/terms gates.
5. For a real pack ZIP, run `analyze`; capture manifest/index, BPM/key *confidence*, technical defect signals, duplicate decisions and review holds. Review cannot be auto-approved by an agent. Keep unpitched drums keyless and ambiguous tempo unknown.
6. Build or reuse safe UI/API for review and attestation. Release only after explicit actual rights-holder confirmation; sample/preset tier `standard`, beat tier `basic` (no stems) or `premium` (approved stems).
7. Create a Shopify **draft preparation** handoff, machine-readable product metadata and verified delivery file, without auto-publishing or silently changing any existing live product. Any connected Tribal Network handoff must be authorized and audited.
8. Expose ChatGPT-accessible MCP tools only through the repo's authenticated gateway and declared capabilities; a local stdio MCP tool is not proof of a ChatGPT plugin connection.
9. Run tests for hostile ZIPs, malicious symlinks, duplicate data, failed decode, workspace ownership, review gate, Basic stem exclusion, rights approval and replay/idempotency. Verify at least one real sample pack before claiming commercial readiness.
10. Report exact file changes, commands, tests, API/MCP connectivity checks, distribution hash and known blockers. Do not mark a pipeline live merely because configuration exists.

## Operational safety

Original uploads immutable. No source deletions, unauthorized publication, license invention, fake key/BPM certainty, or forced musical-quality verdicts. No paid dependencies without approval. Preserve existing FL Studio sessions, plugin builds, routes, and release assets. If ZIP source is unavailable, say **blocked: distribution not provided**, and do not pretend staging completed.
