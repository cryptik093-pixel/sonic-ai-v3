# Omega House Vocal Multi-FX — implementation target

The source is a 23-page user-provided VE-500 technical conversion study. Treat the hardware as a behavior reference; no reverse engineering of firmware or copying manufacturer presets/UI.

## Product packaging
- Working name: **Omega House Vocal Multi-FX**; avoid claiming it is a BOSS/VE-500 product.
- First host/platform: Windows 10/11 x64, VST3 audio effect, FL Studio Producer Edition.
- Brand direction: original Omega House vintage vocal pedal / rack visual language. This is a UI direction, not a reason to delay DSP validation.
- Existing adlib93 v1 may be valuable if source and rights can be verified; inspect before choosing a fresh project.

## Dependency boundary
```
VST3 host / automation / MIDI / sidechain
                  |
     Plugin adapter (JUCE or iPlug2)
                  |
    Stable parameter/state catalogue
                  |
   DSP engine: preallocated routing graph
                  |
  Input -> Enhance -> Pitch/Voice -> FX rack -> Time FX -> Output
                  ^             ^
                shared F0      MIDI/guide policy
```

## Build interfaces
- `AudioConfig`: sample rate, max block, bus channels, quality mode, preallocated buffers.
- `ParameterCatalog`: persistent IDs, types, display transforms, smoothing, host automation, deterministic versioned serialization.
- `VoiceAnalyzer`: shared F0/confidence/voiced-unvoiced metadata; operate at sensible control rate with no allocations during render.
- `VoiceProcessor`: correction, doubled voice and up to three harmony generators; compare implementation libraries against quality data. Harmony guidance based on MIDI/key first; guide-guitar path research-only until legal review.
- `FXGraph`: four logical slots with independent `FXType`, wet/dry and order; allow documented serial/parallel layouts without changing exported parameter IDs.
- `SpaceGraph`: two delays/reverbs with flexible routing and safe transitions.
- `AudioMetrics`: RMS/peak metering transported to UI without real-time locks.
- `State`: chunked versioned schema; exact round-trip with regression tests.

## VST3 and DAW guarantees
- Mono vocal input and stereo output first; optional stereo input and guide auxiliary input only after host-specific tests. Never assume FL Studio exposes every auxiliary bus identically to the VST3 reference host.
- Audio thread cannot wait on controller/UI events. No UI requirement for audio processing.
- Smooth continuous automation; discrete switches at correct host sample offsets where wrapper permits; for architecture changes prepare off-thread and crossfade.
- Report actual algorithmic latency to host. If latency changes with quality mode, notify host and revalidate project delay compensation.
- All output samples finite (not NaN/Inf); silence remains finite and decay bounded; bypass timing/latency matched.

## DSP choice
Evaluate `Signalsmith Stretch` (MIT) first for a pitch/harmony prototype; it is not a finished vocal-tuning engine. Pitch correction also requires voiced/unvoiced classification, note targeting, pitch continuity, retune behavior, formant handling and confidence-based fallback. Verify all library versions, transitive dependencies and licences before bundling. Build chorus, delay, tremolo, gates, EQ and compression from small known DSP components; initialize buffers outside callbacks. High gain saturation paths may require targeted 2x-4x oversampling.

## Optional scope
Looper, guitar chord recognition, full 20 FX types, specialty Freeze/Warp, stereo auxiliary stems and macOS universal builds follow a validated initial product. Do not mark omitted scope implemented.
