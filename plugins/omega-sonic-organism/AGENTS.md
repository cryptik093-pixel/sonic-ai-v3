# AGENTS.md — Omega Sonic Organism Codex rules

You are implementing an original professional audio instrument for Omega House Studio LLC.

## Nonnegotiable
- Inspect the existing project tree, build scripts, git status, known test suites, and local SDK toolchain before editing. Preserve user changes; never reset, clean, force-push, overwrite another plugin, or delete source artifacts.
- Add work within `plugins/omega-sonic-organism` if in the canonical project; otherwise work inside this package and report precise paths.
- Keep DSP in independent C++17/20 components with zero VST includes. VST3 processor/controller and VSTGUI are adapters. Use Steinberg official SDK under MIT; do not depend on paid frameworks.
- NO memory allocation, file I/O, locks, network calls, logging, exceptions, or UI calls inside the realtime audio callback. Prepare memory in `setupProcessing`/preflight, never inside `process` or `setProcessing`.
- Host parameter IDs and component CIDs MUST remain unchanged after adoption. Normalize host values 0–1 and map once in an authoritative registry. Sample-offset parameter automation and note events must be processed in time order.
- A Morph setting interpolates **DSP traits** (oscillator spectrum, material inharmonicity, transients, envelopes, filter and modulation), not merely two finished audio streams.
- VST3 state needs versioned binary serialization with round-trip and compatibility tests. Preset JSON is for import/export, not a replacement for native host state.
- Match the reported state to actual observed evidence. No claim of a passing VST3, validator, or FL Studio test unless actually run.
- Work in small verifiable changes with tests and clear evidence. One implementation phase at a time; no speculative additional features.
- Never add paid services, telemetry, remote patch generation, or cloud dependencies without explicit approval.

## Must produce after every stage
Changed files, actual commands executed, pass/fail results, what is still unverified, and next unblocker. Tests must run on real target tooling when available. Preserve original audio and preset files.
