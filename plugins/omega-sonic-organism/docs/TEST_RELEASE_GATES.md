> Historical stage specification retained from the engineering foundation. Current candidate behavior and gate decisions are in ARCHITECTURE.md and RELEASE_STATUS.md. Status statements below describe their original stage, not the current DLL.

# Quality Gates and Acceptance Matrix

**Rule:** A run not executed is `NOT VERIFIED`, never `PASS`. Save reports under `test-results/`, do not overwrite golden recordings without approved listening review.

## Gate G0 — Repository and toolchain
- [ ] Existing repo branch + dirty state recorded; no unrelated files changed.
- [ ] Actual available Windows MSVC/SDK/CMake versions recorded.
- [ ] External SDK commit recorded, licensing notices tracked; build does not require paid tools.

## Gate G1 — Standalone DSP (must pass before VST3 integration)
- [ ] Portable C++ library builds with CMake; all CTest assertions green (real results).
- [ ] Each anchor, each midpoint, and 0/1 morph extremes output finite nonzero sound after note-on.
- [ ] Distinct timbre metrics at five anchors; objective centroid or spectral-band measure supports non-identical character.
- [ ] Smooth morph ramp on a sustained note creates no abrupt amplitude discontinuity; no retrigger.
- [ ] Note-off decays; repeated notes / voice stealing do not leave stuck voices.
- [ ] Silence after long tail; stable at 44.1/48/96 kHz and multiple frame sizes.
- [ ] No heap allocations inside realtime path (allocation probe plus inspection).
- [ ] Deterministic repeat render under identical seed, input and sample rate.

## Gate G2 — Steinberg VST3
- [ ] Host scans `.vst3` as *instrument*, one event input and stereo audio output.
- [ ] Processor and controller instantiate, configure, activate, process and deactivate.
- [ ] All exported `ParamID` values, step counts, ranges, and state names match registry.
- [ ] Sample-offset note-on/off and parameter edits work at nonzero offsets and zero-offset collisions.
- [ ] Versioned `getState`/`setState` round-trip and truncated/invalid input safety tests pass.
- [ ] 32-bit sample path and 44.1/48/96 kHz pass; 64-bit process path either implemented/tested or explicitly declined if host can select 32-bit.
- [ ] Steinberg `validator` standard and extensive suite outcomes recorded; no blocking failures.
- [ ] Plug-in does not allocate/block/file I/O/log inside processor callbacks.

## Gate G3 — FL Studio manual/automated host QA
- [ ] Load in Channel Rack; notes via MIDI keyboard AND Piano Roll; velocity changes tone.
- [ ] Sweep Morph while notes sustain; play all five anchors; change all four macros.
- [ ] Automate Morph, Energy and at least one Advanced parameter; save, close FL Studio, reopen and verify settings/automation.
- [ ] Multi-instance compatibility; no shared accidental state; test mute, stop/start, panic and project reload.
- [ ] Offline WAV export: no stuck notes, unintended silences or divergence vs normal playback (expected tolerance documented).
- [ ] Plugin displays correctly at 100%, 125%, 150% Windows scaling; no crash with editor closed.
- [ ] Scan, install and uninstall behavior tested as non-admin user.

## Gate G4 — DSP fidelity
- [ ] Unwanted DC level < -60 dBFS on sustained test patches when measured over an appropriate window.
- [ ] Peak output safe during 16-voice stress and 6 dB output setting with protective level policy; never NaN or Inf.
- [ ] Oscillator alias components are assessed by swept sine/note renders against a documented bandlimit baseline.
- [ ] Excessive zipper/click transients not audible/measurable under scripted macro sweeps.
- [ ] Profile tuning tests at roots (MIDI 36, 48, 60, 72, 84) show playable musical pitch where expected; percussion can be intentionally noisy.
- [ ] Long decay does not cause denormal CPU spikes.
- [ ] 16-voice / 48kHz / 256-sample reference machine benchmark: record median, P95, P99 per-callback cost. Engineering goal P95 <= 1.0 ms and P99 <= 2.0 ms on documented midrange desktop; **machine-specific goals, not universal guarantees**. Playback never overrun on validated test machine.

## Gate G5 — Presets/commercial packaging
- [ ] At least 30 musically reviewed and level-matched patches: 5 each anchor + 5 transitions.
- [ ] Host state survives cross-session with unchanged processor/controller IDs and stable `ParamID`s.
- [ ] Preset import/export schema validates; invalid documents rejected without partial state mutation.
- [ ] Professional UI, offline operation, help/documentation, copyright/trademark notices, no missing assets.
- [ ] Fresh-install/uninstall test and reproducible Release artifact checksum.
- [ ] Version and release notes consistent; no `1.0` label without all mandatory gates.

## Required test report shape

| Gate | Command/Host | Evidence file | Result | Blocker/Notes |
|---|---|---|---|---|
| G0..G5 | exact commands | path | PASS/FAIL/NOT VERIFIED | verifiable explanation |
