# Drum Supply Headquarters — native synthesis milestone

Version 0.1.0. Local Windows x64 engineering candidate, not a commercial release.
No samples, optional libraries, network calls, Sonic service or DAW session edits
are required for synthesis. There is no sample selector or sample playback path.

The signature workflow is Department → BODY → CHARACTER → SPACE. MIDI 60 plays
the selected department. General MIDI drum notes play the corresponding kit
departments; other notes play percussion. Audition queues a single hit on the
audio thread. Note-off does not cut one-shot drums; All Notes Off clears voices
and ambience. Sixteen fixed voices use oldest-voice stealing with a 2 ms residual
fade. Mono/stereo output,
no input/sidechain, float processing, no lookahead, host latency 0 samples.

| Department | Engine | BODY | CHARACTER | SPACE |
|---|---|---|---|---|
| Kick | Sine body, pitch envelope, harmonic and noise transient | 38–80 Hz body; decay, pitch-envelope time | Pitch sweep, harmonic balance, attack noise | Short stereo taps, damping/feedback/wet |
| Snare | Inharmonic shell modes plus band-shaped noise | Shell tuning, tonal/noise decay | Shell/noise balance, pitch attack, spectral decay | Shell-room diffusion, damping/feedback/wet |
| Hi-Hat | Three metallic oscillator products and shaped noise | Oscillator tuning and envelope | Metallic/noise balance, spectral tilt | Tight stereo diffusion, damping/feedback/wet |
| Cymbal | Eight inharmonic modes with noise excitation | Partial tuning, long evolving decay | Modal/noise balance, per-partial decay | Longer stereo taps, damping/feedback/wet |
| Tom | Tuned shell modes, pitch envelope, noise attack | Root, decay; GM note changes tuning | Pitch drop, excitation, modal decay | Resonant-room taps, damping/feedback/wet |
| Percussion | Excited modal bank | Tuning and decay | Continuous wood/membrane/metal partial-ratio morph | Material-room taps, damping/feedback/wet |
| Clap | Three time-offset filtered noise bursts plus tail | Noise filter, burst width, tail | Burst spacing, transient, spectral shaping | Short reflected taps, damping/feedback/wet |

BODY, CHARACTER and SPACE are normalized 0–1, default .5/.5/.25. Continuous
targets smooth over 20 ms; bounded coefficient updates occur every 32 samples,
independent of host blocks. Every department has its own synthesis mapping.
Ambience is shared by the kit and follows the last-triggered department's fixed
tap family. Changing departments can change ambience tap positions. Extreme
polyphony has a final ±.98 safety clamp; this is not a transparent limiter.
Rapid voice stealing and ambience-family switching require listening review
before a release claim. No oversampling or alias-free claim is made.

## Reproduce

From the Sonic repository root in PowerShell:

```powershell
& ./plugins/drum-supply/scripts/build-windows.ps1 -CoreOnly
& ./plugins/drum-supply/scripts/build-windows.ps1
& ./plugins/drum-supply/build/DrumDspTests.exe ./plugins/drum-supply/evidence/renders
& ./plugins/drum-supply/build/DrumProcessorTests.exe ./plugins/drum-supply/evidence
```

The script reuses Sonic Pocket's existing MSVC/Windows SDK environment discovery
and verified JUCE archive cache. It does not change Sonic Pocket sources or copy
a binary into an installed VST3 directory. CMake also supports a separately
supplied `FETCHCONTENT_SOURCE_DIR_JUCE` with the pinned dependency.

Artifact: `build/OmegaDrumSupply_artefacts/Release/VST3/Omega Drum Supply.vst3`.
Editor bounds: 700×460, default 900×560, max 1200×780. Knobs have APVTS
attachments, host gestures, typed normalized values and double-click reset.
Editor reopening does not reset the engine. The peak display becomes inactive
after six missed 30 Hz UI updates. No A/B, preset bank or export UI is claimed.

Stable parameter identity/order: `department`, `body`, `character`, `space`.
JSON state version 1 validates the complete snapshot before applying; unknown,
oversized, truncated, nonfinite, out-of-range and future-version state must be
rejected without changing the current sound. Product code `OhDs`, manufacturer
`OmHs`, bundle `com.omegahousestudio.drumsupply`; independent of ADLIB-93/Pocket.

## Evidence gates

DSP tests exercise every category with no sample files, all 21 macro mappings,
determinism, 44.1/48/96/192 kHz extremes, reset, invalid numeric inputs and C++
allocation counting. Render metrics measure change, not subjective musical
quality. Processor tests exercise actual MIDI handling, unequal block partitions,
parameter/state recall, bus layouts, sample rates, zero blocks and compiled
editor rendering. Rendered screenshots are not host embedding or DPI evidence.

FL Studio scan/playback/save/reopen, host automation, rapid voice-stealing
listening, loudness matching, aliasing measurements, callback p95 timing, and
commercial licence eligibility remain separate acceptance gates. Danny's
listening judgment is required for sonic approval. Native synthesis is not
registered as a Sonic HTTP capability until an authorized adapter exists.

See `evidence/verification.md` for executed commands and outcomes.
