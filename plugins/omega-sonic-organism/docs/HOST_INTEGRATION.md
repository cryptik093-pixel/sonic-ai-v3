> Historical stage specification retained from the engineering foundation. Current candidate behavior and gate decisions are in ARCHITECTURE.md and RELEASE_STATUS.md. Status statements below describe their original stage, not the current DLL.

# VST3 Integration Contract

## Binary identity (freeze on first publicly persisted release)
- Product name: `OMEGA SONIC ORGANISM`
- Vendor: `Omega House Studio LLC`
- VST3 subcategory: `Instrument|Synth`
- Processor FUID: `B7FE82DB-13A6-4A8D-AF3A-2CAA5CCC4CB1`
- Controller FUID: `B8BD8AEC-F05F-4A27-B0F6-EE2B15346516`
- Each should be encoded using the Steinberg SDK's documented `FUID` type / `INLINE_UID` mechanism; do not invent incompatible byte ordering.
- Product package identifier: `com.omegahouse.sonicorganism` (internal label, **not** a Steinberg registration claim).

## API obligations
- Processor: `AudioEffect` / `IComponent` + `IAudioProcessor`; controller: `EditControllerEx1` / `IEditController`; class factory registers both FUIDs; link a shared stable parameter definition.
- 1 event input; stereo `kMain` audio output bus. Optional mono layout after acceptance testing, no audio input at V1.
- Process data: 32-bit `channelBuffers32` initial implementation. Validate `numOutputs`, `numChannels`, and null buffers; never assume 64-bit bus pointers. `process` supports zero-event empty blocks, sample offset 0 through N-1, and nonconstant buffer sizes up to declared max.
- All VST3 parameters use normalized 0..1 host values, **immutable IDs** from `contracts/parameters.json`. Correct `stepCount`, named units, text display/conversion and parameter flags. Nonautomatable config options must not masquerade as automatable.
- Read parameter input changes with sample offsets; merge with event list and process subsegments. Offset collision: parameter update then note input event. Smoothing occurs in DSP, not by ignoring timing.
- Host automation gestures from GUI use beginEdit/performEdit/endEdit, on UI thread; do not mutate processor settings directly from GUI. GUI could be destroyed without muting sound.
- `getState`/`setState` processor and controller state sync must survive project save and reopen. Binary schema version `1`, input validation, rollback/default of missing items; reject or safely skip invalid blobs.
- `setupProcessing` allocates/prepares per-sample-rate tables and fixed-delay buffers; `process` and `setProcessing` perform no heap allocations.
- Runtime instrument plays completely offline; product cannot require web or Omega OS connection.
- Preserve integration test outputs: plugin build log, Steinberg validator result, FL Studio session notes and recorded render hashes/measurements.

## SDK/bootstrap
- Official source: https://github.com/steinbergmedia/vst3sdk
- SDK is MIT; inspect actual local version and use a fixed, recorded git commit with recursive submodules. VSTGUI is optional and can be linked through `vstgui_support`.
- Choose CMake's `smtg_add_vst3plugin` or the current documented helper validated against installed SDK; never assume an unverified helper signature. Follow current SDK samples, and prefer a skeleton generated from an official plugin example.
- Windows build: Visual Studio 2022/2026 Build Tools (actual installed compiler), CMake 3.25+, Win SDK; specify x64 and Release. Do not require admin rights for tests; copied bundles must target user-scoped plugin directories where possible.
- Do not distribute Steinberg SDK files inside the Omega House package beyond applicable MIT obligations or required plugin runtime resources.

## Audio/data boundary
```
VST3 Host Events/Automation -> Processor Adapter -> Event Scheduler
                                                   -> Parameter Registry/Smoothers
                                                   -> Portable Instrument Core
                                                   -> Stereo Output
VST3 UI -> Edit Controller -> Host Parameter Gestures -> Processor
Processor -> lock-free/atomic snapshot -> UI display (rate-limited)
```

## Automation and state pitfalls
- Mutating a non-automated preset selection during automated sweeps must not race with active automation.
- No change to `ParamID` values or their physical meaning after release. New options consume fresh IDs.
- Tail / silence flags must be honestly reported; Space effect has an audible tail.
- Offline render and playback use the same deterministic DSP by default, even if HQ quality becomes optional.
- Ensure note-off, voice steal, stop/play reset and panic produce finite bounded output.

## Stage evidence format
```
Component: processor / controller / VSTGUI / standalone core
Build: toolchain, command, outcome, artifact exact path
Unit tests: suite name, pass/fail counts
Validator: actual executable, command, output summary
FL Studio: version, scan result, note play, automation, saved-project reload, offline WAV render
Caveats: anything not tested and exact reason
```
