# Verification-oriented build milestones

Use these as *gates*, not promises of calendar time. Estimates depend on repo/toolchain state and require measurement.

## Gate 0 — preserve and baseline
- Inventory sources: adlib93 v1/v2, current Git branch, licenses, presets/parameters, build scripts and audio demos.
- Record `git status`, compiler/tool version, build output, working FL Studio version and already functioning features. No destructive operations.
- Decide **reuse vs. new shell** from evidence; write a one-page decision record.

## Gate 1 — authentic working VST3 file
- Export a stable `.vst3` with unique company/product identifiers and an audio-effect category, stereo output, mono vocal input where supported.
- Input gain -> bypass -> output gain; audio genuinely passes and bypasses. Minimal GUI is fine.
- CMake build repeatable locally and in Windows CI; executable/test artefacts are recorded. Validator detects no structural failures.
- FL Studio can load, route audio and recall parameters after save/reload when Windows host is available.

## Gate 2 — vocal-ready rack / user-perceivable quality
- Add EQ, compressor, de-esser/gate, drive/character, doubler/chorus, musical delay, reverb, dry/wet and per-slot bypass, with presets backed by versioned state.
- At least four assignable FX slots represented; actual implemented effect set is explicit. Do not show cosmetic unimplemented controls.
- Offline reference corpus: spoken voice, sustained singing, sibilants, breath, transients, silence, impulse, sweeps, low/high input levels.
- Demonstrate no clicks in ordinary bypass/parameter changes, stable peak/RMS and CPU under realistic vocal routing.

## Gate 3 — signature vocal pitch engine
- Build/use one F0 analyzer shared by correction and 3 harmony voices, preserving unvoiced content and note changes.
- MIDI/key-guided voice generation first; measured latency and audible artifact review (vowels, sibilance, slides, vibrato, transitions).
- Add formant handling and crossfades. Mute/disable unreliable voice generation rather than outputting unstable pitch at low confidence.
- Prototype vocoder as a distinct lane, tested with an internal carrier first; guitar/carrier sidechain only after confirmed host routing.
- Guitar-derived harmony is not a commercial release gate until patent counsel review.

## Gate 4 — production quality, not merely compiling
- Run VST3 validator; target FL Studio install/scan, full GUI editing, project save/reopen, automation record/replay and MIDI input tests.
- Test 44.1, 48 and 96 kHz; blocks 1, 64, 128, 512 and at least one larger unusual block, plus 0-frame if supported; both variable and fixed buffer lengths.
- Test silence, denormals, random automation fuzz, extreme parameters, parameter serialization backwards-compatibility, project reload, plugin bypass and host transport synchronization.
- Verify against explicit audio corpus; report peak/RMS, gross aliasing artifacts, pitch error, wet/dry and CPU/latency. Establish performance thresholds after measuring target Windows/FL hardware, not from guesses.
- No allocations/locks/file I/O in render callback after preparation, and no NaN/Inf. Instrument memory allocations during rendering when possible.
- Automated tests green, no known crashing host cases, licence notices preserved, user approval before any distribution or production release.

## Required milestone report
**Completed:** file paths and commit hashes when applicable.
**Verified:** commands, host version, representative actual output metrics, reproducible evidence.
**Blocked:** only unresolved dependency/authorization.
**Next:** exactly one implementation unit.
