> Historical stage specification retained from the engineering foundation. Current candidate behavior and gate decisions are in ARCHITECTURE.md and RELEASE_STATUS.md. Status statements below describe their original stage, not the current DLL.

# Codex Implementation Backlog and Exit Criteria

**One vertical slice at a time. Priority is a playable, stable instrument, not extra UI or AI.**

## Milestone M0 — Baseline and DSP spike
- Audit canonical repo and preserve dirty state. Compile the included `core` prototype and tests.
- Record reference waveforms at five anchors, with notes C2/C3/C4 and 25% transition samples. Assess that the current prototype is provisional: upgrade oscillator quality and modal persistence rather than releasing toy sine mixes.
- Deliver exact test logs, code organization and integration plan.
- Exit: core compiles and tests pass or a precise blocking failure is documented.

## M1 — First *real* Windows x64 VST3 host build
- Implement class factory, processor/controller, stereo event instrument, normalized parameter plumbing, MIDI events, state, sample-offset event queue. Use standard host editor until DSP is reliable.
- Integrate portable core without SDK references in DSP.
- Deliver `.vst3`, validator report and FL load test if runtime available.
- Exit: playable in at least one actual VST3 host; clean project reload.

## M2 — Product-quality engine
- Replace prototypical harmonic core with band-limited oscillator/wavetable, robust modal bank (>=4 partials), calibrated resonant filter, smooth envelopes, pitch/bend/glide, stable deterministic voice manager.
- Implement macros according to profile-specific tables and make every family artistically distinguishable.
- Add Space tail, safety limiting, CPU/quality modes and oscillator alias tests.
- Exit: controlled five-anchor audio review, interpolation artifacts below defined thresholds and no major QA failures.

## M3 — Visual performance interface
- Implement VSTGUI with five-anchor Morph rail, 4 macros, advanced controls, preset display, visible meters. Match controller/host model; no direct UI thread cross-access to DSP.
- Add fine adjustments, tooltips, accessibility, DPI support.
- Exit: every control actually changes DSP and can reflect automation, no audio-thread allocations.

## M4 — Factory sound bank and production hardening
- Design/gain-match 30 factory presets; deterministic state migration, host preset serialization, JSON export; offline render comparison.
- Test 44.1/48/96 kHz, 1–1024 frame blocks and variable buffer sizes, all note lifecycle conditions, repeated reloads.
- Exit: all G1–G4 gates and reviewed preset bank.

## M5 — Candidate release
- Windows installation/portability test, versioned changelog, attribution/compliance, reproducible build and hashes, FL Studio project load on clean workstation.
- Exit: all G0–G5 gates green; signed release only if signing is available and approved. No unapproved purchases.

## Not in V1 (intentionally)
- Cloud AI, training on customer samples, automatic track recording/inspection.
- Sound-to-DNA import and reverse engineering of commercial presets.
- Multi-instance cross-channel listening in FL Studio instruments.
- Standalone Sonic AI server connection, network licensing, DAW-wide service agents.
- Mac/Linux releases, standalone executable, AAX/AU.
