# Architecture and build

The shipped target is a Windows x64 VST3 instrument using the official Steinberg SDK and VSTGUI. No JUCE or paid synthesis dependencies are required. The DSP layer is independent C++17. It has no SDK types or runtime network dependency.

## Signal path

One shared voice combines sine, polyBLEP saw/pulse, an eight-partial Nyquist-tapered harmonic bank, four damped complex modes and deterministic noise. Morph interpolates oscillator weights, resonator ratios/decays, envelope, filter, pitch drop, drive and modulation traits between five anchors. Positive time/frequency traits interpolate logarithmically; appropriate weights interpolate linearly. This changes one voice structure rather than selecting five finished audio streams.

Each voice passes through a trapezoidal state-variable low-pass, delayed envelope, drive, velocity and gain. HQ drive uses equivalent polyphase 31-tap half-band interpolation/decimation. Eco is delayed to match HQ: both report 15 samples latency. Stereo modulation and a four-delay damped Hadamard-feedback room feed DC removal and bounded output shaping. The output stage is part of the existing design; signal criteria and listening remain separate.

## Runtime contracts

`contracts/parameters.json` freezes IDs 100-114. Original processor/controller CIDs remain B7FE82DB13A64A8DAF3A2CAA5CCC4CB1 / B8BD8AECF05F4A27B0F6EE2B15346516. MIDI mapping IDs 1000-1003 cover bend, sustain, all-notes-off and all-sound-off. Read-only output telemetry 1010-1013 adds no sound-state fields.

The adapter consumes host queues in time order, rendering bounded segments between event boundaries. Parameter points precede notes at equal offsets. The core smooths continuous values, refreshes costly coefficients every 16 samples, and uses fixed voice/note storage. Voice count is 1/8/16/32. Release voices are preferred for stealing, then oldest voices; steal transitions take five milliseconds. Room memory allocates only in preparation. Tests instrument C++ new around documented process paths; they are not a proof about every possible OS allocation.

State format OSO1/schema 1 is unchanged: explicit little-endian doubles and an FNV corruption checksum, validated atomically. Six-field early states default later parameters. Sound parameters persist; current oscillation/voice phase, patch display names and user descriptions do not persist in native project state. A restarted instance retriggers deterministic sound from restored parameters. State callbacks rely on the VST3 host lifecycle; concurrent arbitrary state mutation while processing is unsupported.

## Editor and preset boundary

The native 1040x620 editor uses standard VSTGUI controls and host begin/set/perform/end gestures. It polls controller values on the GUI thread for automation synchronization. Factory definitions are embedded JSON, also shipped as editable exchange files. Strict parsing/export and file dialogs stay on the UI/tool thread. No file access enters the callback. Meter updates depend on host forwarding output parameters. The trait drawing is a parameter visualization, not an FFT.

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

The probes load the DLL with InitDll/GetPluginFactory; they are not named-DAW acceptance. Validator paths can be passed to `tools/validate-windows.ps1`. GUI interaction, host automation behavior and project recall must also be exercised in FL Studio.
