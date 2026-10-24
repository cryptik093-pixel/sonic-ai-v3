---
name: omega-vocal-vst3-forge
description: Build, extend, debug, and validate Omega House Studio vocal multi-effects plugins for Windows VST3, including adlib93 work. Use for real-time C++ DSP, JUCE/iPlug2, FL Studio compatibility, MIDI harmony, pitch shifting, preset recall, and audio regression. Do not use for unrelated audio marketing or general web development.
---

# Omega House Vocal VST3 Forge

Produce **working, measurable increments** toward a proprietary Omega House Studio vocal multi-effects VST3. Prioritize reusing an existing adlib93 implementation if its source is available. Never claim a VST3 builds or works in FL Studio without executing the relevant test.

## Execution order

1. **Inspect before editing.** Identify repo root, branch, dirty files, existing adlib93 DSP/UI/source/binaries, build framework, test facilities, installed Windows compiler, VST3 SDK, host, and licenses. Run `python scripts/preflight.py --repo <project-root>` as a read-only aid. Inspect relevant code, build outputs and prior decisions. Preserve user work and use a feature branch for substantial changes.
2. **Choose the shortest legal build route** using `references/licensing-and-ip.md`. If an existing compiling project is reusable, keep its framework and port its DSP into a modular engine. Otherwise: consider JUCE 9 Starter only after confirming company eligibility and user acceptance of the licence; use iPlug2OOS/CMake when avoiding future revenue-tier framework obligations is decisive. Never create a new paid commitment. Pin dependency revisions and preserve notices.
3. **Lock one thin vertical slice at a time** using `references/milestones-and-gates.md`: working VST3 shell, audible vocal channel, flexible pedal rack, high-quality pitch/harmony, then polishing. For each slice create a minimal plan, implement, compile, run offline DSP checks and plug-in validation, and report evidence. Do not build the full GUI or 20 FX before a working VST3 exists.
4. **Keep DSP independent from the GUI and plug-in wrapper.** Use a stable, versioned parameter catalogue (IDs never reused), a processing graph, one shared vocal F0 analysis path, preallocated buffers, smoothed updates, and explicit latency/state handling. See `references/architecture.md`.
5. **Protect the real-time callback.** No heap allocations, locks, disk/network access, blocking logs, dynamic FFT plan creation or dynamic topology construction on the audio thread. Handle denormals, silence, sample-rate changes, unusual channel arrangements and variable block sizes.
6. **Verify observed operation.** Configure/build the exact target; run relevant tests; run a Steinberg test host/validator where available; open in FL Studio on the authorized Windows desktop when accessible; save/reopen a project; test bypass, automation, MIDI, and realistic singing takes. Audio quality is a measured acceptance criterion, not a compilation claim.
7. **Report per slice:** Completed (files/commits), Verified (commands/results/audio evidence), Blocked (facts), Next (one highest priority task). No production release, destructive overwrite, signing commitment, store upload or paid dependency without approval.

## Product boundary

Use the uploaded VE-500 technical conversion study under `references/VE500_reference_study.pdf` as a **functional reference only**, not as source code, diagrams to copy, official presets or product identity. Maintain an original Omega House interface and product name. Commercial release of hardware-style guitar-chord-driven harmony is gated on claim-level patent review; refer to `references/licensing-and-ip.md`.

## Quality shortcut

Use small, deterministic tests and known permissively licensed DSP building blocks instead of asking the coding agent to invent and tune every signal-processing algorithm at once. `Signalsmith Stretch` may be evaluated for pitch/harmony; independently implement the YIN-style F0 analysis; share its results across correction/harmony. Measure audio artifacts and latency. Defer uncertain features instead of marketing them as accurate emulation.

## Boundary against scope creep

Do not alter Sonic AI V3, Omega House OS, Shopify or Tribal Network unless explicitly needed by the current integration task. No cloud service is required to run real-time audio DSP inside the VST3. Preserve source audio/stems, prior DAW projects, routing and approved renders.
