# M2 synthesis engineering record

Question: replace the supplied timbre spike with a continuous five-family voice,
activate the frozen controls, and bound realtime cost without adding services.
Fixed constraints: Windows x64 VST3, original CIDs and parameter IDs, independent
C++17 core, 1/8/16/32 voices, offline deterministic rendering, 44.1/48/88.2/96 kHz
plus 192 kHz stress; no callback allocation, I/O, locks, or UI calls.

## Sources and derivations

- Andrew Simper, *Solving the continuous SVF equations using trapezoidal
  integration and equivalent currents*, Cytomic, 2013; corrections through
  November 2016, pp. 4–5:
  https://www.cytomic.com/files/dsp/SvfLinearTrapOptimised2.pdf
  Source inspected 2026-10-18. `g = tan(pi * cutoff / sampleRate)`, `k = 1/Q`.
  The implementation independently expresses the bounded simultaneous solve;
  Q and normalized-frequency conventions are explicit. No paper performance
  measurement is a measurement of this plugin.
- SciPy's official Blackman-window reference, inspected 2026-10-18:
  https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.windows.blackman.html
  For this symmetric 31-point design the cosine denominator is N−1 = 30.
  Formula: `.42 − .5 cos(2πn/30) + .08 cos(4πn/30)`. The documented symmetric
  convention is used for filter design, rather than the periodic FFT window.
- The modal poles are an explicit derivation: `z[n+1] = r exp(jw) z[n]`,
  `r = exp(−ln(1000)/(T60 * sampleRate))`. A struck initial state excites four
  independent modes; interpolation changes ratio, damping and weight within
  the same voice. Complex sine/cosine coefficients are normalized to unit
  magnitude before applying r so lookup interpolation does not change decay.
  This is an analytic model, not a claim of physically accurate material capture.
- The supplied polyBLEP edge correction is retained for saw/pulse oscillators.
  An eight-partial harmonic layer and sine lookup are Nyquist-tapered. Their
  aliasing and tuning require measurements; polyBLEP is not an alias-free claim.

Only equations/conventions are referenced; no third-party DSP implementation
was copied. Existing Steinberg notices remain applicable to the adapter.

## Implementation choices to measure

One common voice interpolates the five anchor profiles. Positive times/cutoff
use log interpolation; waveform weights, ratios and modulation depths are linear.
Targets smooth over an 18 ms time constant; cached coefficients update every
16 samples and also at incoming parameter offsets. A new Morph never resets
a sounding envelope. The registry remains the single normalized-to-physical map.

HQ zero-inserts to 2×, uses a normalized 31-tap symmetric half-band FIR, applies
drive at 2×, then uses a matching decimation FIR. The linear cascade's derived
group delay is (15+15)/2 = 15 host samples. Eco uses the same 15-sample delay;
the envelope is delayed equally and applied after drive. A measured impulse
must confirm this derivation. HQ/Eco changes crossfade the minimal drive stage
over 10 ms, rather than changing plugin latency or restarting notes.

Tables are prepared outside processing: 2048 intervals for sine, 4096 for odd
tanh on [−8,8]. Tests compare interpolation to analytic tanh. No claim about
HQ alias improvement is accepted until the same-rate/level/window tone experiment
is run against Eco. A 31-tap filter has a transition band and is not a brickwall.

Space uses four prepared delay lines, low-pass damping and an orthonormal
Hadamard feedback mix with gain strictly below one. Wet injection and return
both reach exact zero after smoothing settles at Space = 0. No network,
captured room, external sample or convolution asset is involved.

Mono legato preserves phase/envelope, ramps note pitch over Glide milliseconds,
and returns to the last held key. Polyphonic glide is disabled. Sustain delays
release until pedal-up; note IDs distinguish repeated pitches. Stealing fades
from the preceding output for 5 ms; this bounds discontinuity but still needs
listening and stress review. Output DC removal uses a 5 Hz pole; final soft
protection is bounded to ±0.98. It does not substitute for the stability tests.

Tempo Sync scales Motion Rate's stored Hz by tempo/120; the Hz value is the
reference frequency at 120 BPM. With no valid host tempo the deterministic
fallback is 120 BPM. This implementation claims tempo-scaled frequency, not
sample-accurate alignment to host bars or MPE.

## Evidence status

Implementation: IN PROGRESS. Numerical, allocation, latency, tuning, alias,
callback timing and binary/validator results belong in M2_TEST_REPORT.md after
actual execution. Listening, FL Studio interaction and commercial readiness
remain NOT_TESTED. The custom VSTGUI interface and 30 reviewed/gain-matched
presets remain subsequent milestones; a generic editor is not the finished UI.

M1 binary and source snapshots were preserved before M2 edits. M1's prior
sound is not claimed bit-identical to the replacement engine. Schema-1 patch
values and host identities remain compatible; audio equivalence across these
alpha engine versions is deliberately not asserted.
