# ADLIB-93 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Execution context:** The owner selected a separate Codex session for implementation. This session prepares documents only. In Codex, use sequential native execution with `superpowers:executing-plans` if available; do not dispatch subagents merely because the generic header recommends them. This plan and its prompt are for owner review before execution.

**Goal:** Build a Windows x64 VST3 vocal multi-effect with 24 editable ad-lib presets, the approved pedal interface, and evidence for every release claim.

**Architecture:** A parameter registry drives pure DSP modules, a bounded two-engine transition system, versioned state and native JUCE controls. A production-DSP test executable verifies algorithms independently of the VST3 host; Windows validators and FL Studio verify the actual binary. DSP memory is allocated during preparation and owned by the audio thread.

**Tech Stack:** C++17, CMake >=3.22, JUCE 9.0.4 baseline tag, Windows x64/MSVC, CTest, external Steinberg VST3 validator and external pluginval. This tag is a proposed build baseline, not a tested dependency combination. Resolve its full commit and SDK revision during Task 1; never use a moving branch. If the actual repository has a working pinned framework, document compatibility before changing it. No dependency purchases.

**Spec:** `docs/superpowers/specs/2026-10-15-adlib93-design.md` (approved by Daniel Sutton on 2026-10-15). Preserve its content; the older review-pending wording inside that historical document is superseded by this dated approval record.

## Global Constraints

- Primary platform: Windows x64, FL Studio.
- Support mono→mono, mono→stereo and stereo→stereo main buses; reject unsupported layouts explicitly.
- No MIDI input/output, external sidechain, instrument hosting, cloud inference, account system or paid service dependency in V1.
- No allocation/deallocation, blocking mutexes, disk/network calls, logging, resizing buffers, exceptions or GUI work in the audio callback.
- Target zero added algorithmic through-path latency: no lookahead, oversampling or block FFT.
- Frequency controls are logarithmic.
- Limiter is enabled in Init and all factory presets.
- Factory presets never save vocal buffers; Throw/Freeze/Listen/internal bypass resume off after recall.
- All 24 exact names/recipes, control ranges, limits and UI requirements come from the spec. No silent feature substitution.
- Preserve existing plugin identities, source sessions, routing and approved renders. No automatic installation into an active DAW or overwriting another plugin.
- PASS means a recorded completed check; missing Windows/FL Studio/audio auditions means PENDING.

## Review Focus

1. Host state arriving while processing: no half-applied snapshot, deadlock or UI-thread assumption (Tasks 3, 10, 12).
2. Huge/zero/odd host blocks and missing tempo/time signature: finite output, bounded chunking, visible deterministic fallback (Tasks 2, 7, 12).
3. Frozen/throwing audio during preset selection, bypass, lost focus and project reopen: no stuck hold or unexpected new dry signal (Tasks 9–12).
4. Extreme/non-finite values, very low sample rates and hostile preset names/files: no invalid coefficients, traversal or oversized allocation (Tasks 3–8, 10).
5. Send routing and mono input with stereo effects: no doubled direct vocal, ineffective ping-pong or unexplained mono output (Tasks 2, 6, 7, 12).

## File map and execution conventions

Paths below are relative to a new isolated ADLIB-93 project root. If adapting an existing repository, record a one-to-one path mapping in `docs/ENVIRONMENT.md` before editing; follow its established layout without unrelated refactoring.

| Paths | Responsibility |
|---|---|
| `CMakeLists.txt`, `CMakePresets.json`, `cmake/Dependencies.cmake`, `dependencies.lock.json` | Reproducible library/test/VST3 targets and pinned revisions |
| `src/core/Types.h`, `Parameters.h/.cpp` | Physical-unit snapshot, layout, host timing and parameter schema |
| `src/core/SnapshotMailbox.h`, `StateCodec.h/.cpp` | Bounded cross-thread transfer and validated persistent state |
| `src/dsp/Primitives.h/.cpp`, `OutputStage.h/.cpp` | Envelopes, smoothing, filter utilities, sample protection and limiter |
| `src/dsp/Cleanup.h/.cpp`, `Character.h/.cpp` | Gate, dynamic high band, filters and saturation |
| `src/dsp/Movement.h/.cpp`, `Echo.h/.cpp`, `Space.h/.cpp` | Delayed modulation, echo/diffusion, reverb/ducking |
| `src/dsp/Freeze.h/.cpp`, `Transitions.h/.cpp`, `AdlibEngine.h/.cpp` | Bounded performance states, engine transitions and routing |
| `src/presets/FactoryBank.h/.cpp`, `PresetStore.h/.cpp` | Full factory definitions and user preset persistence |
| `src/plugin/PluginProcessor.h/.cpp`, `PluginEditor.h/.cpp` | Host adapter and editor composition |
| `src/ui/PedalLookAndFeel.h/.cpp`, `MainControls.h/.cpp`, `DetailPanel.h/.cpp`, `PresetBrowser.h/.cpp`, `MeterBridge.h`, `UiState.h/.cpp` | Native pedal appearance, controls, navigation and metering |
| `tests/TestMain.cpp`, `TestSupport.h/.cpp`, `*Tests.cpp` | Exact production-DSP test runner/fixtures |
| `tools/RenderFixtures.cpp`, `Benchmark.cpp`, `scripts/package.ps1` | Reproducible renders, timing and Release bundle assembly |
| `docs/ENVIRONMENT.md`, `PARAMETERS.md`, `DSP.md`, `FL_STUDIO_CHECKLIST.md`, `AUDITION.md`, `VERIFICATION.md`, `THIRD_PARTY_NOTICES.md` | Evidence and operating instructions |

Shared types in `Types.h`: `enum class ChannelLayout { monoMono, monoStereo, stereoStereo }; struct PrepareSpec { double sampleRate; uint32_t maxBlockSize; ChannelLayout layout; }; struct StereoFrame { float left, right; }; struct HostTiming { double bpm; int numerator, denominator; bool bpmValid, signatureValid; }; struct ProcessContext { HostTiming timing; uint64_t absoluteSample; };`. Store snapshot parameters in explicit physical units: Hz, ms, dB, seconds, BPM and [0,1] fractions. Thus the spec default `deess.frequency=6 kHz` is **6000 Hz**, `delay.lp=8 kHz` is **8000 Hz**, not 6 or 8 Hz. `ParameterSnapshot` is fixed-size/trivially copyable with no strings or vectors. Percent controls convert at the UI/host boundary.

Module convention: `prepare(const PrepareSpec&)` may allocate; `reset()` is an offline lifecycle reset, allowed only outside `processBlock`; `setParameters(const ParameterSnapshot&) noexcept` does not allocate; `process(StereoFrame) noexcept -> StereoFrame` is per-sample unless a task defines a specialized signature. Audio-thread clear/prepare is incremental and must never call a bulk `reset()` on large buffers. Engine uses persistent scratch arrays and per-sample ordering independent of callback size.

Build targets: `adlib93_dsp` (library), `adlib93_tests` (runner), `ADLIB93_VST3`, `adlib93_render`, `adlib93_benchmark`. Register each named test case with CTest; runner syntax `adlib93_tests --case <name>` returns 0 on pass and nonzero on failed assertions. Use JUCE core/audio/DSP where needed, but no extra unit-test package is necessary. `require(condition, message)` in TestSupport supplies real failure messages.

Standard test cycle for every code task: add the named assertions, run the named CTest filter and observe a meaningful failure, implement the declared interface, rerun until pass, then commit only that task's paths. A configuration/toolchain failure is not a meaningful DSP test failure. No product code is supplied by this plan.

## Task 1: Establish a reproducible build and evidence baseline

**Files:** create build files, `dependencies.lock.json`, `docs/ENVIRONMENT.md`, `tests/TestMain.cpp`, `tests/TestSupport.h/.cpp`, `tests/BuildTests.cpp`.

**Interfaces:** produces CMake targets and `require(bool, const char*)`; test CLI defined above. Dependencies expose the exact pinned JUCE source tree to all targets.

- [ ] Inspect actual AGENTS.md files, git status, repository structure and advertised skills. If a VST-builder skill exists, read it; otherwise do not invent one. Record OS/architecture, compiler, SDK, CMake, framework and Windows/FL Studio availability. Do not request an unrelated Sonic/Shopify integration.
- [ ] Record the approved spec hash and git baseline. New project: resolve official JUCE tag `9.0.4` to its full commit, record bundled VST3 SDK revision and tool versions; pin that commit. Existing project: verify its pin and map paths before changing dependencies. Disable unneeded JUCE browser/curl/MIDI-services features. Record the selected JUCE license path without asserting eligibility on the owner's behalf.
- [ ] Add `Build.Configuration` assertions: `require(sizeof(void*) == 8, "x64 required"); require(__cplusplus >= 201703L, "C++17 required");` with MSVC's standards-compliant `__cplusplus` flag enabled. Runner rejects unknown `--case` with nonzero status.
- [ ] Configure/build/test in Windows Developer PowerShell: `cmake --preset windows-release`, `cmake --build --preset windows-release --target adlib93_tests`, `ctest --preset windows-release -R Build.Configuration --output-on-failure`. Define presets with binary directory `build/windows-release`, Visual Studio 17 2022 generator and x64 platform. If unavailable, create/run an explicitly labeled native test preset and leave Windows PENDING.
- [ ] Commit build/runner/environment files: `build: establish reproducible ADLIB-93 test targets`.

## Task 2: Prove neutral routing and layout handling

**Files:** create Types, AdlibEngine, PluginProcessor and `tests/RoutingTests.cpp`; extend CMake with VST3 target. Initial editor may be a plain diagnostic editor until Task 11; label this stage incomplete.

**Interfaces:** `AdlibEngine::prepare(PrepareSpec)`, `process(const float* const* input, float* const* output, uint32_t frames, const ParameterSnapshot&, const ProcessContext&) noexcept`; `PluginProcessor` implements JUCE lifecycle/bus validation. Input can alias output; frame count zero requires no sample dereference.

- [ ] Add `Routing.Identity`, `Routing.Layouts`, `Routing.Blocks`: on seeded samples ≤0.5 amplitude with limiter off and all modules off, `require(maxAbsError(input,output)<=1e-6f,"dry identity")`; Mix fractions {0,.25,.5,.75,1} remain unity; mono duplication/fold-down exactly specified. Reject 2→1 and 0-channel main layouts. Process 0,1,17,128,4097 frame callbacks without overrun using 128-frame prepared scratch capacity; add in-place tests.
- [ ] Run `ctest --preset windows-release -R Routing --output-on-failure` and capture failures.
- [ ] Implement gain/blend/layout adapter, one wet pan/width stage and bounded chunking. Inputs are copied into owned scratch before outputs overwrite them. No silent stereo summing gain. Set actual neutral latency to zero and no MIDI/instrument flags. Send mode overrides effective mix/direct without overwriting Insert values.
- [ ] Rebuild `adlib93_tests` and `ADLIB93_VST3`; rerun Routing. Scan the neutral VST3 in a real Windows host if present; record that outcome separately.
- [ ] Commit: `feat: add neutral engine and supported VST3 routing`.

## Task 3: Parameter schema and safe snapshots

**Files:** Parameters, SnapshotMailbox, StateCodec, `docs/PARAMETERS.md`, `tests/ParameterTests.cpp`, `tests/StateTests.cpp`.

**Interfaces:** `makeInitSnapshot() -> ParameterSnapshot`; `parameterDefinitions() -> fixed read-only span-equivalent view`; `sanitizeSnapshot(ParameterSnapshot,double sampleRate) noexcept -> ParameterSnapshot`; `SnapshotMailbox::tryPublish(const ParameterSnapshot&) noexcept -> bool`, `tryConsume(ParameterSnapshot&) noexcept -> bool`; `decodeState(const void*,size_t) -> DecodeResult`, `encodeState(const PersistedState&) -> juce::MemoryBlock` off audio thread. `PersistedState` contains schema=1, full snapshot, A/B, calibration locks and UiState.

- [ ] Add `Parameters.Schema`: unique stable IDs, each spec min/max/default, Hz conversions (6000/8000/6000), exact mute and logarithmic round trips; `require(effectiveCutoff(20000,32000)==14400,"Nyquist clamp")`. Validate NaN/Inf inputs, all enums, zero/negative sample rates before prepare.
- [ ] Add `State.RoundTrip`, `State.Malformed`, `State.Concurrent`: exact stable values/A–B/locks restored; transient performance booleans false; reject oversize (>256 KiB), invalid types and incompatible major schema. Missing fields use Init; unknown fields tolerated. Concurrent snapshot publishing never yields a mixture of generation markers.
- [ ] Run Parameter/State filters to meaningful failures. Implement fixed-size registry and a bounded mailbox with explicit buffer ownership; no data-racing seqlock around non-atomic object data, no heap snapshot retirement on audio thread. If all slots busy, producer retains only its newest pending request outside the callback.
- [ ] Rerun tests; run thread sanitization on a supported native target or record unavailability. Connect host parameters using JUCE attachments/atomics; decoding/serialization is outside DSP. Host callbacks received on unusual threads must not require UI availability.
- [ ] Commit: `feat: define stable parameters and validated state transfer`.

## Task 4: Output protection and reusable DSP primitives

**Files:** Primitives, OutputStage, `tests/OutputTests.cpp`.

**Interfaces:** `OutputStage::process(StereoFrame) noexcept -> StereoFrame`, `meters() noexcept -> OutputMeasurements`; helpers `dbToGain(float) noexcept`, `effectiveCutoff(float,double) noexcept`, `timeConstantCoefficient(float ms,double) noexcept`. One-pole convention α=exp(−1/(timeSeconds×sampleRate)); five time constants means within 1% of target. General gain smoothing=20 ms, Throw=5 ms, topology transition=20 ms unless spec overrides.

- [ ] Add `Output.Ceiling`, `Output.Linked`, `Output.Exceptional`: amplitudes up to 10^(24/20) and unequal channel peaks satisfy `abs(sample)<=dbToGain(-1)+1e-6`; stereo gain is identical; enabled limiter is after output gain; NaN/Inf input becomes zero; disabled limiter does not secretly clip. Silence remains finite and silent.
- [ ] Run Output filter to fail; implement the approved instant-attack/release limiter, denormal suppression and off-thread diagnostic counters. Use double intermediates or bounded conversions so finite extreme floats cannot overflow a saturator/limiter intermediate.
- [ ] Rerun Output and Routing; verify bypass still uses the agreed output stage.
- [ ] Commit: `feat: add linked sample-peak output protection`.

## Task 5: Gate and dynamic high-band de-esser

**Files:** Cleanup, `tests/CleanupTests.cpp`, `docs/DSP.md`.

**Interfaces:** `Cleanup::process(StereoFrame) noexcept -> StereoFrame`; `measurements() -> CleanupMeasurements`. Detector source is linked max absolute stereo. Choose a complementary one-pole split for the de-esser (not an unspecified mixture of crossover types), low state l, high=x−l; zero reduction reconstructs x.

- [ ] Add `Cleanup.Gate`, `Cleanup.Deess`, `Cleanup.Listen`: opening threshold/3 dB closing hysteresis and exact hold sample count; gain convergence within 1% after five time constants; max reduction 0 gives ≤1e−6 reconstruction error; steady high tone never exceeds configured reduction+0.2 dB; Listen state is visible and excluded from recall.
- [ ] Run Cleanup filter to fail. Implement gate timing, de-ess 1/80 ms detector behavior and the spec reduction law; link channel reduction. Use the same documented detector convention as Output primitives. Listen routes high-band audio through output protection only.
- [ ] Rerun tests at all four release sample rates and asymmetric L/R input.
- [ ] Commit: `feat: add vocal gate and de-esser`.

## Task 6: Character, double, chorus and stereo movement

**Files:** Character, Movement, `tests/CharacterTests.cpp`, `tests/MovementTests.cpp`.

**Interfaces:** module convention; `Movement::processBranches(StereoFrame) noexcept -> MovementReturns { StereoFrame doubler, chorus; }`; engine owns direct/movement branch levels and the single final wet pan/width stage.

- [ ] Add `Character.Transfer`, `Character.Filters`, `Movement.Delays`, `Movement.Mono`: exact soft/hard/asymmetric curves after warmup with DC blocker accounted for; bypass gives identity; Clean ignores Drive. At depth=0, expected impulses at 14/22 ms within ±1 sample. Width=0 gives L=R; centered balance gives unity; mono output uses (L+R)/2. Reset LFOs once, and compare irregular blocks to one continuous run within 1e−5.
- [ ] Run these filters to fail; implement approved 12 dB/octave filters, transfer curves, 10 Hz DC blocker, preallocated fractional delays and phase-continuous LFOs. Clamp delay to ≥1 sample for base/depth combinations. Clamp very-low-rate coefficients; reject unsupported prepare rates before allocating.
- [ ] Rerun tests and render aliasing fixtures at 44.1 kHz into a local test-artifact directory. Record analysis; subjective acceptability remains PENDING until listened to.
- [ ] Commit: `feat: add character and stereo vocal movement`.

## Task 7: Rhythmic delay, diffusion and Throw

**Files:** Echo, `tests/EchoTests.cpp`, `tests/TimingTests.cpp`.

**Interfaces:** `resolveDelayTime(const ParameterSnapshot&,const HostTiming&) noexcept -> DelayTiming { double milliseconds; bool clamped, usingManual; }`; `Echo::process(StereoFrame input,float throwGate) noexcept -> StereoFrame` returns filtered/diffused echo before branch gain. Diffusion applies to audible return and feedback; a nonzero amount therefore remains audible at zero feedback.

- [ ] Add `Echo.Timing`, `Echo.PingPong`, `Echo.Throw`, `Echo.Stability`: first repeat ±1 sample; BPM {60,90,120,180}, signatures {3/4,4/4,6/8}; missing/NaN tempo uses 120 BPM fallback, invalid signature 4/4. 100% ping-pong mono impulses alternate dominant L/R, not identical channels. Throw-only gates new input; continuous Throw adds exactly +6 dB injection before nonlinear feedback, with 5 ms ramp; existing repeats continue after release. Confirm diffusion affects first return at feedback=0.
- [ ] Run Echo/Timing to fail. Implement four-second stereo memory, approved feedback matrix, mono-left injection interpolation, filters, fixed all-pass diffusion and 4×tanh(x/4) feedback safeguard. For each time retarget, finish the current 100 ms two-tap transition, then apply the most recent queued target; at most two active taps. Do not add unbounded taps on rapid automation.
- [ ] Rerun tests, limiter off, across feedback/ping-pong extremes. Measure internal state maxima and decay, not only protected output.
- [ ] Commit: `feat: implement synchronized ad-lib echo and throws`.

## Task 8: Reverb and internally detected ducking

**Files:** Space, `tests/SpaceTests.cpp`; extend DSP documentation.

**Interfaces:** `Space::process(StereoFrame clean, StereoFrame leveledDelay, StereoFrame detectorInput) noexcept -> SpaceReturns { StereoFrame reverb; float duckGain; }`; echo branch output is ducked separately by engine using the same returned gain. Reverb excitation is clean plus configured delay send before ducking.

- [ ] Add `Space.Decay`, `Space.Duck`, `Space.Stereo`: RT60 0.5/2/6/12 s within ±25% with damping opened; finite tails and nonidentical stereo response; detector steps never exceed max reduction+0.2 dB and do not change echo feedback decay. Input on one channel must still excite both reverb outputs.
- [ ] Run Space to fail. Implement eight-line FDN with H=I−(2/8)11ᵀ. Injection vectors L=(1,1,1,1,1,1,1,1)/sqrt(8), R=(1,−1,1,−1,1,−1,1,−1)/sqrt(8); inject (uL×L+uR×R)/sqrt(2). Output vectors L=(1,1,−1,−1,1,1,−1,−1)/sqrt(8), R=(1,−1,−1,1,1,−1,−1,1)/sqrt(8). Use the eight approved delays, per-line RT60 gains and damping, preallocated predelay. Record measured normalization/decay results.
- [ ] Rerun Space and Echo, including 12-second tails at 96 kHz. Engine ordering stays sample-based so branch routing is invariant to host block partition.
- [ ] Commit: `feat: add measured reverb decay and vocal ducking`.

## Task 9: Freeze, bounded clearing and preset transitions

**Files:** Freeze, Transitions, `tests/PerformanceTests.cpp`.

**Interfaces:** `Freeze::process(StereoFrame normalSpatial,bool active) noexcept -> StereoFrame`, `suppressesExcitation() noexcept -> bool`; `beginClear() noexcept`, `clearStep(uint32_t maxWrites) noexcept -> bool` on memory-owning modules; `Transitions::request(const ParameterSnapshot&) noexcept`, `process(...) noexcept` around two prepared engines.

- [ ] Add `Performance.Freeze`, `Performance.Clear`, `Performance.Switches`: silent hold remains silent; freeze gain does not grow over 60 s; release/crossfade durations match spec within one sample; repeated commands cannot recursively capture the held layer. 1,000 preset/A–B changes coalesce safely; before a prepared incoming engine is ready, active engine keeps playing. Clear never runs a bulk buffer fill in the callback.
- [ ] Run Performance to fail. Use two rolling 250 ms histories and a held-buffer ownership swap at Freeze edge; the captured ring is immutable until release, while the spare ring collects only normal spatial audio. Loop with 20 ms complementary overlap; keep the original rolling window chronological through read indices. Suppress excitation during hold while letting underlying networks decay. Crossfade 50 ms into hold and 250 ms out.
- [ ] Implement transition/clear budgets: at most 256 float writes per processed audio frame across all modules, plus ≤64 writes for a zero-frame callback. Do not begin engine crossfade until its clear completes; coalesce pending requests. Clear fade=20 ms, zeroing while muted, then 20 ms fade-in. This may take longer than the initial fade and must show Clearing status. CPU budget tests still apply.
- [ ] Rerun with allocation hooks and test transient release during preset/A–B changes, bypass and project restore. Add 180-second normal-tail expiry; Freeze deliberately remains held until released/cleared.
- [ ] Commit: `feat: add bounded freeze and engine transitions`.

## Task 10: Factory bank, user presets and project recall

**Files:** FactoryBank, PresetStore, `tests/PresetTests.cpp`; extend StateCodec and PluginProcessor.

**Interfaces:** `factoryPresets() -> const std::array<FactoryPreset,24>&`; `loadFactory(uint32_t index,const ParameterSnapshot& current,CalibrationLocks) -> ParameterSnapshot`; `PresetStore::save(const UserPreset&) -> SaveResult`, `load(const juce::File&) -> LoadResult` off audio thread. `FactoryPreset` contains immutable ID/name/family/full snapshot.

- [ ] Add `Presets.Bank`, `Presets.Locks`, `Presets.Files`, `Presets.Recall`: names/order/values exactly match all 24 spec rows; load order cannot leak effects. Preset 12 enables delay/diffusion/send; preset 22 mutes direct at Mix=.45. Default locks retain input/gate/output calibration, full host restore ignores locks, transient booleans off. Reject traversal-like names, reserved Windows filenames, oversized/corrupt files, incompatible schema and non-finite data; escaped display names cannot change file location.
- [ ] Run Presets to fail; implement complete maps from one base definition and validated overrides, materialized into full immutable snapshots at startup off the callback. Save files atomically inside an OS-resolved per-user `Omega House Studio/ADLIB-93/Presets` directory, using safe internal IDs for filenames and display names inside JSON. Browser text/search runs off audio thread.
- [ ] Test host recall with editor closed and while audio processes; restore durable values/A–B/locks exactly, release transient states via fades, never serialize held audio. Add modified markers, Save As and lock-aware Reset, with explicit Full Reset.
- [ ] Rerun State/Presets/Performance and commit: `feat: add 24 factory presets and reliable recall`.

## Task 11: Build the approved pedal interface

**Files:** editor and all UI files; `tests/UiModelTests.cpp`; optional original vector assets under `assets/`.

**Interfaces:** `MeterBridge::publish(const MeterSnapshot&) noexcept`, `read() noexcept -> MeterSnapshot`; editor attachments target stable parameter IDs only. `UiState` holds scaling/page/selection, not DSP buffers. `PresetBrowser` emits a load request only on click/Enter, not search/highlight.

- [ ] Add `UI.Bindings`, `UI.RoutingOverrides`, `UI.Gestures`: each of ten knobs maps to precisely its specified ID; Send overrides Mix/direct visibly and restores Insert values; clean Drive disabled; labels open correct detail pages; momentary Throw releases on mouse-up/focus loss/editor destruction, latch remains explicit; preset search does not load. Diagnostic Listen and held Freeze are unmistakably indicated.
- [ ] Run UI model tests to fail. Implement native JUCE controls: 1040×680 logical pixels, 75–150% proportional scale, two rows of five, six detail pages, top preset/calibration strip and bottom performance switches/Clear. Charcoal/rubber/bone/cyan/amber treatment, no copied trademarks. Use deferred parameter gestures, not audio-thread UI callbacks.
- [ ] Implement ≤30 Hz meter snapshots and correlation with 300 ms window; below −80 dBFS or mono output show unavailable. All controls have accessible names, keyboard/numeric entry, visible focus, fine adjustment and unit readouts. Refreshing meters must not allocate in audio processing.
- [ ] Verify 75/100/150% plugin scale × Windows 100/150/200% DPI, keyboard-only operation, no clipped essential controls, editor open/close while processing. Archive screenshots as internal test evidence only unless requested as deliverables.
- [ ] Commit: `feat: add ADLIB-93 pedal controls and preset browser`.

## Task 12: Integrated real-time, automation and render verification

**Files:** `tests/IntegrationTests.cpp`, `tests/RealtimeTests.cpp`, RenderFixtures, Benchmark, verification docs and FL checklist.

**Interfaces:** renderer CLI `adlib93_render --preset <1..24> --input <wav> --output <wav> --sample-rate <hz> --block-size <n>`; benchmark CLI `adlib93_benchmark --sample-rate 48000 --block-size 128 --seconds 600 --report <json>`. Load/render/write files outside audio callback using production engine. Test fixtures use seeded signals and sample-indexed automation schedules.

- [ ] Add `Integration.Matrix`, `Integration.OfflineParity`, `Integration.Fuzz`, `Realtime.NoAllocation`, `Realtime.Budget`: four sample rates and block matrix from spec; varying blocks and equivalent automation schedules differ ≤1e−5; 10,000 random finite/invalid parameter operations remain bounded. Instrument allocate/free and forbidden lock/I/O in production callback during preset/freeze transitions, not merely individual modules.
- [ ] Run test filters and capture failures. Implement missing lifecycle/automation/exception recovery behavior; no changes to accepted DSP requirements solely to make a test pass. Oversized blocks chunk without changing process context absolute sample timing. Keep per-sample envelopes/LFOs independent of callback boundaries.
- [ ] Run the 10-minute reference-machine benchmark, both steady and dual-engine transitions. Require steady p99<0.533 ms, transition p99<1.067 ms, observed max<2.667 ms at 48 kHz/128; DSP buffer usage≤64 MiB at 96 kHz. Report machine/toolchain, repeatable method and measurement overhead. Mark actual unavailable hardware checks PENDING. Verify stable memory over 1,000 switches.
- [ ] Build Windows Release VST3; run Steinberg validator and external pluginval strictness≥5, then 10. Discover/version their actual executable paths; do not invent PASS logs or assume embedded pluginval/JUCE integration compatibility. Fix failures with focused regression tests.
- [ ] Complete FL Studio scan/load/monitoring/automation/save-reopen/offline WAV/bypass/tails/multiple-instance checklist on actual Windows host. Measure/report device monitoring latency separately. If hardware/host access is missing, complete all independent checks and provide exact remaining user steps.
- [ ] Commit: `test: verify production DSP and Windows host behavior`.

## Task 13: Audition, tune and package a reviewable release candidate

**Files:** `docs/AUDITION.md`, `VERIFICATION.md`, `THIRD_PARTY_NOTICES.md`, `README.md`, `scripts/package.ps1`; only measured preset trim/level changes in FactoryBank.

**Interfaces:** package command `powershell -NoProfile -File scripts/package.ps1 -Configuration Release`; output `dist/ADLIB-93_<version>_Windows_x64.zip`, containing the actual `.vst3` directory bundle, installation/use guide, notices and verification report. Source archive separately includes pinned dependency instructions and excludes caches/credentials/user recordings.

- [ ] Define one audition row per preset × spoken/whispered/shouted/sibilant/sung source, stereo/mono, solo/in-mix. Use only owner-cleared recordings. Match active-phrase RMS within 0.5 dB for comparisons; preserve tails. Until heard, identity/usefulness and aliasing acceptability remain PENDING, even when files render.
- [ ] Obtain owner listening feedback on all 24; fix only demonstrated recipe problems and record before/after values/reasons. Gate/deess thresholds remain adjustable for source level. Rerun affected DSP tests and integration once after tuning, without pointless repeated broad testing.
- [ ] Record each acceptance row as PASS/FAIL/PENDING with evidence paths. A real built binary can be a Release Candidate with pending listening, but must not be advertised as commercially validated. Confirm applicable dependency licenses/notices before distribution; no purchasing or publication automatically authorized.
- [ ] Package the Release `.vst3` bundle with its internal structure intact. Document default install path `C:\Program Files\Common Files\VST3` and FL Studio rescan steps, but do not copy/install to system folders or overwrite installed versions without task authorization. Check archive integrity and SHA-256; retain source revision and dependency lock with report.
- [ ] Commit: `docs: package ADLIB-93 release candidate with evidence`.

## Coverage and self-review record

Spec §1/2 → Tasks 1/2/12; §3 → Tasks 3/11; §4 → Tasks 4–9/12; §5 → Tasks 10/13; §6 → Task 11; §7 → Tasks 1/3/9/10/12; §8 → Tasks 2/9/12; §9 → Tasks 4–13; §10–12 → handoff and evidence records. All five Review Focus conditions have owning tests. Interfaces use ParameterSnapshot, PrepareSpec, StereoFrame and ProcessContext consistently. No product implementation or audio acceptance test was executed while authoring this plan.

References checked 2026-10-15: official JUCE releases https://github.com/juce-framework/JUCE/releases (9.0.4 listed); official build requirements https://github.com/juce-framework/JUCE/blob/master/README.md (CMake >=3.22). Pinning at execution is still required. Other primary references are in the approved spec.
