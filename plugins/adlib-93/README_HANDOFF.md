# Omega House ADLIB-93 — Pre-Codex handoff

Prepared October 15, 2026 for Daniel Sutton / Omega House Studio LLC.

This archive is the design-and-build handoff for a real vocal multi-effects VST3. It contains no source implementation or installable plugin yet.

## Files

1. `docs/superpowers/specs/2026-10-15-adlib93-design.md` — approved engineering specification: scope, routing, all controls, DSP, 24 recipes, UI, state and acceptance tests.
2. `docs/superpowers/plans/2026-10-15-adlib93-implementation.md` — proposed 13-task implementation plan for review; concrete files, interfaces, tests, commands and delivery requirements.
3. `CODEX_START_HERE.md` — setup instructions and the ready-to-paste execution prompt, to use after reviewing the plan.
4. `README_HANDOFF.md` — this guide and approval record.

## Approval record

Daniel approved the written engineering specification on October 15, 2026 with “i approve.” This supersedes the historical review-pending text inside the unchanged specification. The implementation plan is newly prepared and has not yet been reviewed by the owner. Execution is intended for a separate Codex session, not this design session.

## Use

Extract this entire ZIP, review the plan, then open the actual development repository in Codex. Copy/attach the spec and plan preserving their relative paths. Paste the prompt in CODEX_START_HERE.md when ready to authorize the build. If using Windows Codex locally, the Windows compiler/FL Studio checks can run there where those tools are actually available. Cloud Codex may require a separate Windows build/host verification step; it must report that honestly.

Do not place this ZIP in FL Studio's VST folder. Only the later built `.vst3` bundle is installable.

## Evidence boundary

Completed here: collaborative design approval, written specification, implementation plan, prompt, document consistency/coverage checks and archive validation. Not completed here: DSP implementation, Windows compilation, plugin scan, audio audition, measured CPU/latency or commercial release validation. Dependency versions are build selections, not proof of compatibility. All 24 presets require listening and controlled tuning against real ad-lib tracks before commercial quality claims.

## Selected workflow guidance and checkpoint

Sonic Chat Orchestrator: keep the requested studio-tool goal, use the smallest sufficient workflow and distinguish prepared work from validated runtime outcomes. Codex Coordinator: one native Codex task by default; use an existing enabled claim board correctly if present, without inventing parallel tasks or background management. Temporal: reviewed, with no runtime service required for this local C++ audio effect. These skills informed the handoff; no Temporal cluster, Codex task window or background agent was started.

Current objective: build the approved ADLIB-93 product in a separate Codex workspace. Active version: engineering specification v1 plus implementation plan dated 2026-10-15. Authority: design approval and preparation of this complete handoff; no spending, publication or installed-plugin overwrite. Remaining dependency: actual development workspace/toolchain, followed by Windows/FL Studio and owner listening evidence. Next executable task: Task 1 environment inventory and reproducible neutral build. No customer outreach is part of this task.
