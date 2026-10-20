# Trait Model (DSP Engineering Reference)

This document defines the interpolation domains. `core/` demonstrates a minimal subset; production engine must implement the full contract.

## Profile record
```
name                  : anchor enum
harmonic_weights[8]   : per-partial nonnegative weights; normalize by total energy
waveform_mix          : [sine, saw, pulse] weights, nonnegative
modal_ratios[4]       : frequency ratios, positive; harmonic/inharmonic control
modal_decay_ms[4]     : 10..6000, log interpolation
modal_gain[4]         : nonnegative, bounded
noise_excitation      : 0..1
impulse_hardness      : 0..1
pitch_drop_semitones  : 0..24
pitch_drop_ms         : 10..400
filter_cutoff_hz      : 30..(0.45 * sampleRate), log interpolation
filter_q              : 0.5..12, clamped stable
attack_ms             : 1..4000, log interpolation
decay_ms              : 5..8000, log interpolation
sustain               : 0..1, linear
release_ms            : 10..10000, log interpolation
saturation_drive      : bounded linear/perceptual map
motion_mode           : profile-controlled; no random parameter changes
stereo_spread         : 0..1
```

## Runtime mapping
- Macro Energy modifies filter/spectral tilt and saturation with gain compensation.
- Material expands noise/inharmonicity (can make Bass more metallic or Bells darker) but must retain tonal identity at 0.5.
- Motion scales a profile's permitted modulations: Bass wobble/filter, Bells beating, Lead vibrato, Synth evolving harmonic modulation, Perc decay/strike variation.
- Space is post-voice stereo room/send and may have a legitimate tail.
- Macro changes interpolate at **audio-rate or stable block ramp**; event scheduler honors actual sample offset.
- Linear spectral energy interpolation requires recalibration: prevent level dips/spikes at midpoints. Use common envelope and shared partial generator, not five parallel instrument outputs.

## Nonlinear boundaries
Switching oscillator table resolution or oversampling mode is a topology change; initiate at next safe block/voice boundary or use a short internally managed transition. Core tests must ensure it cannot produce an uncontrolled transient.
