# Sonic Preset Forge — Engineering Execution Directive (Codex / VS Code)
Date: 2026-11-05 | STATUS: new work authorization guide; no code changes authorized by this document alone

## Operating mission
Extend the CURRENT Sonic AI V3 `tools/fst_generator` implementation, not a fresh demo application. Turn one novel, purposeful chain into a saved-and-reloaded, audible, independent FL Studio-native `.fst` with evidence and source integrity. Prioritize the first Crown Center v002 Patcher quality proof and then audio-player reliability. Follow `FORGE_VNEXT_PRODUCT_ARCHITECTURE.md` and `AUDIT_AND_PROGRESSION.md`.

## Preflight invariants
1. Inspect current working tree, branch, recent local edits, active ports, existing FL sessions, plugin versions and tests. Never reset/switch/delete/stash, kill unrelated apps, or bulk stage.
2. Read existing architecture in `tools/fst_generator/docs/`, the two historical milestone locks and `docs/production/preset-forge/IMPORT_INDEX_2026-11-02.md`. No duplicate engines.
3. Re-hash original Crown Center FST/FLP and all reference WAVs before work; store evidence under a NEW timestamped output directory. Do not alter source media or the app SQLite database without a transactional backup.
4. Re-run `python -m unittest discover -s tests -q` in the installed Forge, and preserve the real console result.
5. Check FL Studio can safely be used in a disposable QA project; do not seize or alter a live mixing session. Confirm actual installed stock effects and Omega-branded effect IDs before referencing them.
6. Preserve public repo safety: no private data, local paths containing secrets, customer info, licensing keys, binary presets or recorded audio pushed to public Git.

## First engineering increment: Crown Center v002
1. Compare saved v001 signal graph to intended v002: identify unity dry path, actual wet branch summing, oversaturation/noise, unnecessary harshness and variable mapping. Record hypotheses before editing.
2. Instantiate only host-proven Patcher/Control Surface/EQ2/Limiter/WaveShaper/Stereo FX. Keep the initial path simple, serial and audible; conditionally add wet parallel or M/S only after baseline proves it adds useful identity.
3. Prove CHARACTER, PRESSURE, AIR, WIDTH exact parameter names/IDs and physical-to-normalized behavior by readback. Store a versioned calibrated mapping; uncertain mappings are BLOCKED.
4. Use a known fixture and a real saved Patcher state. Export exactly ONE new native `.fst` through FL Studio; its hash must differ from original. Label export as host-saved, not autonomous.
5. On a CLEAN disposable QA project reload same saved state; render same source at fixed host settings. Measure level, noise, mono, silence, stereo, dynamics and artifact flags, and run operator matched-loudness listening.
6. Record plugin order/bypass/wet, host FL build, source/processed/reloaded file hashes, macro before-after response, QA fixture, render settings, subjective notes and unresolved failures.
7. If quality or host reload fails, retain failure as an inspectable attempt and improve ONE bounded parameter/graph hypothesis. No mass generation until this gate is approved.

## Required negative tests
Missing plugin, disk-only plugin, unverified license, unknown parameter, stale seed hash, unsupported topology, duplicate dry path, malformed AI JSON, dangerous control range, missing/invalid audio, silent preview, expired browser session, request replay, corrupt FST, failed reload, failed render, unauthorized output path, interrupted job, and output source-hash mismatch. Tests must prove failure is visible and cannot be labeled successful.

## Observable definition of done
- New unique native Patcher FST exists and loads in actual certified FL Studio version.
- Four macros audibly function and are backed by host readback.
- Before/after and reloaded same-source WAVs with hashes and gain-match offsets are present.
- Browser can play actual media on the selected output; absence of audio cannot render a misleading success state.
- Measured change is documented, but does not replace producer approval of the sonic identity.
- User's original FST/FLP and reference audio hashes remain unchanged.
- Focused tests and existing regression pass; failures and warnings reported.
- New manifest links exact evidence; label `DAW_VERIFIED` only on observed host proof and `RELEASE_CLEARED` only after rights, installation and product QA.

## Rollback
All new artifacts in separately named locations. Code edits require a scoped before/after snapshot and straightforward revert of ONLY those edits; never restore an old SQLite snapshot over a live DB. No production deployment, paid model use, licensing changes, pricing changes or public release without founder approval.
