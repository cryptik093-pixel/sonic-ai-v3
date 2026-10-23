> Implementation update 2026-10-23: motion and coupling now run in the instrument
> through additive controls with legacy defaults preserved. The original R&D stage
> below is historical. See [current integration](V4_INTEGRATION_2026-10-23.md).

# OSO V4 Instrument V2 — Seven Sectors, Envelopes, Generative States and Coupled-Mode Effects
**Decision:** V4 architecture is APPROVED; implementation below is an additive R&D extension to RC2, not proof of V2 readiness.
**Cross-reference:** docs/research/GIZA_COUPLED_CHAMBERS_2026-10-21.md and the archived OMEGA_SONIC_ORGANISM_V4_ARCHITECTURE_LOCK.md.
**Immutable contracts:** 100 Morph; 101 Energy; 102 Motion; 103 Material; 104 Space; 105 Output. Existing advanced IDs 106–114, Steinberg component/controller class IDs, 15-value OSO1 native state and 30 presets unchanged. No new host-visible parameter IDs allocated in this stage. Windows x64 VST3, stereo instrument, audio offline, zero paid/cloud dependencies.

## Exact seven-sector signal graph
01 DNA -> 02 EXCITE -> 03 BODY -> 04 LIFE amplitude/articulation -> 05 CONTOUR nonlinear color/filter -> 07 SPACE single global stereo delay network/output.
06 MOTION is a control source targeting DNA coefficient shifts / LIFE nuance / BODY weights / CONTOUR cutoff, never a parallel full synth or MIDI composer.
Existing RC2 executes these logical responsibilities inside OrganismCore and DspPrimitives; V4 makes the division explicit before refactoring. Avoid whole-engine rewrite while RC2 CPU gate is failing.

### S01 DNA
Input: Morph 0..1. Anchor knots Bass 0, Bells .25, Lead .50, Synth .75, Percussion 1. Interpolate local harmonic/noise balance, transient, modal decay/ratios, envelope/drive/filter/space traits. Ensure click-free interpolation. Fixed size; no allocation. Do not crossfade five finished voices.

### S02 EXCITE
One phase-continuous bandlimited harmonic source (polyBLEP saw/pulse, sine and bounded additive harmonics) + one seeded noise/transient impulse. Per-note RNG seed from note + deterministic voice serial. Note velocity affects excitation, not merely level. No sampling, neural generation or new oscillator bank.

### S03 BODY
At most four per-voice damped complex/modal modes, conditional on meaningful mode energy. Four-body archetypes: (A) harmonic woodlike, (B) inharmonic metallic, (C) membrane/short percussive, (D) coupled-cavity-inspired two-node interaction occupying two of the FOUR modes, not adding extra mode arrays. Pair at representative 32.76 / 32.79 Hz for **reference science only**; instrument performance transposes/rescales mode ratios relative to MIDI note. Coupling 0..safe limit and Q/decay bounded; opt-in OFF until scientific and CPU tests. The experimental coupled-cavity primitive is NOT a claim of exact chamber emulation. Real architecture involves waveguides, not simply two mass-spring oscillators. Audio-rate excitation only on note strike, then damped evolution.

### S04 LIFE
Existing Attack/Decay/Sustain/Release engine + release on noteoff; advanced attack/release scaling 106/107, glide 108, mono legato 114, velocity, sustain, deterministic note stealing and click-managed retriggers. Add optional **modulation contour** (not a second per-voice amplitude envelope) with A/H/D/S/R, 0-1 bound, note-trigger state machine. No phase flip or hanging notes. Default contour effect depth = 0 for backward compatibility.

### S05 CONTOUR
Trapezoidal SVF lowpass currently implemented + calibrated nonlinear drive with Eco/HQ. Additional highpass/bandpass/notch mode ideas belong to later opt-in migrated controls; do not modify old patches implicitly. Safety: below Nyquist cutoff, fixed Q upper bound, no DC, bounded output, alias/drive tests. Preserve existing 15-sample latency account.

### S06 MOTION
One shared LFO already present, host tempo optional; add fixed 16-step **timbral** modulator with seeded deterministic state, depth 0 at default, temporal phase continuity and single sample rate. Sixteen states are motion coefficients, NOT sixteen MIDI notes and not a full song/chord generator. Modes: Static/Hold, Pulse, Rise, Orbit; generative variation via fixed-seed offline/prepared xorshift and step constraints only; no heap, time clock or random device in callback. MIDI sync may depend on supplied host tempo; no network/AI dependence. Per-voice regeneration only at lifecycle boundaries.

### S07 SPACE
Exactly one global four-delay stereo FDN/diffusion implementation plus stereo headroom/limiter and DC control. Current DSP Room already global. Physically informed reflection density is a candidate modulation of EXISTING FDN coefficients, not a new convolution, granular or full chamber-by-chamber room model. Energy never grows after input stops; global reset must clear state safely without callback allocation.

## Generative states (specific and bounded)
- STATIC: fixed step values -> traditional held timbre.
- PULSE: 16-step deterministic accent/velocity/timbre cycle; weak steps retained (no automatic note generation).
- RISE: bounded ascending/descending 16-step modulation contour; fixed endpoint continuity.
- ORBIT: seeded 16-step pseudo-random, replayable for same seed, tempo and note events. No crypto RNG, recording or autonomous DAW control.
- Each state maps its scalar to at most 3 musical targets (exciter harmonic mix, BODY decay/brightness, CONTOUR cutoff); scaled by Motion intensity, clipped/smoothed. Material remains independent structural damping, Energy remains excitation/dynamics, Space remains one global FDN wetness. No macro role reassignment.
- Envelope states: IDLE -> ATTACK -> HOLD -> DECAY -> SUSTAIN -> RELEASE -> IDLE; retrigger policy restart from current level, noteoff always terminates, reset clears all. Samples counted rather than callback time.

## Release and testing gates for changes
1. Existing 30 JSON patches, host ID registry, OSO1 state bytes and CIDs unchanged (verified by fixture round trips / golden sound recalls).
2. New R&D primitives compile/run as host-independent pure C++17 and zero file reads, lock, memory allocation or exception on audio thread.
3. Determinism by block segmentation, sample rates 44.1/48/96 kHz; zero depth truly identical bypass; no NaN/Inf; no unbounded growth; note-off and reset clear tail.
4. A/B compare current RC2 with new feature off: byte-identical audio in supported test harness, restore legacy session/multiple instances.
5. With feature enabled, scan spectra and mode splitting only in a controlled two-resonator model; no false proof of real pyramid coupling.
6. Keep G07 CPU gate FAILED until an actual comparable p95/p99/overrun benchmark demonstrates improvement; do not relax sample rate 48k, block 256, 16 voices or threshold.
7. Complete FL Studio Producer Edition VST3 host acceptance, sample-offset automation, GUI interaction, offline render and listening approval before commercial V2.

## Curriculum V2 application (additive, not replacement)
Use the locked V2 syllabus in the Library and preserve the ORIGINAL PDF source unchanged. The actual syllabus identifies the original artifact as 74 **printed pages**, 22 chapters, 24 technical modules, 72 lessons, 168 hours; user shorthand calling it '74 chapters' should not lead to inventing additional chapters. V2 adds 24 specialization modules/72 lessons/192 hours. Curriculum exercises: wave modes, inverse measurement, phase/impedance, stable resonator design, envelopes/ADSR math, generative modulation with deterministic seeds, artifact lineage/state compatibility, reference level-matched listening, paired CPU profiling, and verified FL Studio exports. Evidence-first rubric: derivation + reproducible test + listening + host acceptance where applicable.

## Status / integration policy
The existing RC2 already contains most sector responsibilities but is not V4 architecturally refactored. R&D helper code will be tested in isolation before insertion into the audio path. No user-visible generative preset or new mode should be represented as already playable in FL Studio until controller/state migration and acceptance pass.
