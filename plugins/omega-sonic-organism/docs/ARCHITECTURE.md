# Architecture and build

The shipped target is a Windows x64 VST3 instrument using the official Steinberg SDK and VSTGUI. No JUCE or paid synthesis dependencies are required. The DSP layer is independent C++17. It has no SDK types or runtime network dependency.

RC2 caches only invariant work: fixed anchor logarithms, unchanged Energy/output mappings, per-control voice harmonic fades and modal normalization, plus shared per-sample modulation. Bounded oscillator lookup reuses the fundamental and original table interpolation. Resonator rotation is skipped only after all four complex states are exactly zero; oscillator/RNG/envelope/filter progression continues so a held note can morph back into a sustaining identity. Voice count, table sizes, FIR oversampling and 15-sample latency are preserved. `omega_cpu_profile` is an offline function-level diagnostic; `omega_engine_metrics` supplies uninstrumented paced callback measurements. Numerical before/after checks and DAW/listening approval are separate.

## Signal path

One shared voice combines sine, polyBLEP saw/pulse, an eight-partial Nyquist-tapered harmonic bank, four damped complex modes and deterministic noise. Morph interpolates oscillator weights, resonator ratios/decays, envelope, filter, pitch drop, drive and modulation traits between five anchors. Positive time/frequency traits interpolate logarithmically; appropriate weights interpolate linearly. This changes one voice structure rather than selecting five finished audio streams.

Each voice passes through a trapezoidal state-variable low-pass, delayed envelope, drive, velocity and gain. HQ drive uses equivalent polyphase 31-tap half-band interpolation/decimation. Eco is delayed to match HQ: both report 15 samples latency. Stereo modulation and a four-delay damped Hadamard-feedback room feed DC removal and bounded output shaping. The output stage is part of the existing design; signal criteria and listening remain separate.

The shared periodic source is exposed as `dsp::Exciter` for direct production
oscillator measurements. A mirrored-history FIR and `/Ob3` compiler experiment
were rejected after interleaved measurements increased median thread cycles.
The original FIR history layout and Release optimization policy are retained.
Current performance evidence must be read separately from historical RC2 results.

## Runtime contracts

`contracts/parameters.json` freezes IDs 100-114 and defines additive V4 controls 115-117. Original processor/controller CIDs remain B7FE82DB13A64A8DAF3A2CAA5CCC4CB1 / B8BD8AECF05F4A27B0F6EE2B15346516. MIDI mapping IDs 1000-1003 cover bend, sustain, all-notes-off and all-sound-off. Read-only output telemetry 1010-1013 adds no sound-state fields.

The adapter consumes host queues in time order, rendering bounded segments between event boundaries. Parameter points precede notes at equal offsets. The core smooths continuous values, refreshes costly coefficients every 16 samples, and uses fixed voice/note storage. Voice count is 1/8/16/32. Release voices are preferred for stealing, then oldest voices; steal transitions take five milliseconds. Room memory allocates only in preparation. Tests instrument C++ new around documented process paths; they are not a proof about every possible OS allocation.

Default V4 values retain OSO1/schema 1 byte for byte; nonzero V4 controls use the explicit 18-value OSO2/schema 2 extension. Both are validated before publication. The retained OSO1 format uses explicit little-endian doubles and an FNV corruption checksum, validated atomically. Six-field early states default later parameters. Sound parameters persist; current oscillation/voice phase, patch display names and user descriptions do not persist in native project state. A restarted instance retriggers deterministic sound from restored parameters.

`plugin/StateBridge.h` separates host state publication from audio-owned DSP.
`setState` validates a complete state and serializes host producers outside the
callback. `process` consumes a coherent snapshot at its next boundary using
bounded lock-free atomic loads; it never takes the host producer mutex. Audio
parameter snapshots are published atomically for `getState`. Capture performs
up to eight read attempts and reports failure under sustained contention rather
than writing mixed values. Setup, activation and other lifecycle operations
still require the VST3 host's prescribed ordering. Concurrency tests cover both
the handoff primitive and the actual processor adapter; these are not sanitizer
or named-host acceptance claims.

## Editor and preset boundary

The native 1040x620 editor uses standard VSTGUI controls and host begin/set/perform/end gestures. It polls controller values on the GUI thread for automation synchronization. Factory definitions are embedded JSON, also shipped as editable exchange files. Strict parsing/export and file dialogs stay on the UI/tool thread. No file access enters the callback. Meter updates depend on host forwarding output parameters. The trait drawing is a parameter visualization, not an FFT.

Seven sector buttons navigate to the existing macro or advanced controls and
focus the relevant parameter. Navigation changes no sound values. Experimental
16-step motion, modulation contour and coupled modes remain outside the shipping
signal path and have no new host IDs or state fields.

## Build and probes

`tools/build-windows.ps1 -SdkRoot <official-sdk-path> -Jobs 1` configures Ninja Release with a static MSVC runtime. Optional `-BuildDirectory <new-absolute-path>` supports an independent build. C++ tools, MSVC/Windows SDK, CMake and Python are required. VSTGUI uses its official Windows amalgamation. `tools/reproduce-build.ps1` verifies and extracts the bundled SDK archive and builds/tests in a new directory. This avoids depending on another Sonic plugin's checkout.

`tools/finish-windows.ps1` builds the core, numerically calibrates the bank, builds the plugin, runs CTest, runs official and independent validators, renders 27 Eco + 27 HQ + 120 preset-note cases, produces 48 PCM24 auditions, probes editor lifecycle/scaling, and records CPU/alias/tuning/DC measurements. It preserves each evidence run. A pipeline success means execution succeeded; performance goals are evaluated separately and can fail.

Native probes:

```powershell
build/bin/omega_binary_probe.exe <binary.vst3> <output-folder> 0
build/bin/omega_binary_probe.exe <binary.vst3> <output-folder> 1
build/bin/omega_binary_probe.exe <binary.vst3> <output-folder> --bank
build/bin/omega_audition_probe.exe <binary.vst3> <output-folder>
build/bin/omega_editor_probe.exe <binary.vst3> <output-folder>
build/omega_engine_metrics.exe <output-folder> 30
python tools/analyze_engine_metrics.py <output-folder>
```

The probes load the DLL with InitDll/GetPluginFactory; they are not named-DAW acceptance. The editor-only probe supplies synthetic controller/meter values to test drawing and synchronization; its captures are not evidence of audio-meter relay in a DAW. Separate adapter tests exercise actual processor telemetry through preallocated host output queues. Validator paths can be passed to `tools/validate-windows.ps1`. GUI interaction, host automation behavior and project recall must also be exercised in FL Studio.

## Integrated V4 motion and body interaction

Motion16 prepares all four fixed patterns before processing. A single shared lane
advances in sixteenth notes and modulates cutoff by up to one octave through smoothed
Step Depth. The existing LFO continues independently. Valid VST3 musical context
synchronizes starts and timeline discontinuities to canonical four-beat step phase;
contiguous callbacks preserve phase and smoothing. Without musical context the lane
free-runs from processing reset at the supplied tempo. Tempo changes retain fractional
step phase. Seek handling only affects the new lane, preserving legacy LFO behavior.

Chamber Coupling performs bounded convex real-state exchange between two of the four
existing modes before normalized rotation and damping. It adds no resonator bank or
per-voice space. This models a controlled musical interaction inspired by the archived
research; it is not a calibrated physical chamber simulation.

A local MSVC force-inline on the existing voice processing function reduced measured
thread cycles in the paired benchmark, with zero sample error. Global Release flags,
original table oscillator and FIR remain unchanged. Two harmonic-recurrence candidates
were rejected because measured processing cost increased despite meeting audio limits.
