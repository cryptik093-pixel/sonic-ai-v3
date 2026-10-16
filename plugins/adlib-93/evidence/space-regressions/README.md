# Space FDN regression and decay measurement

Date: 2026-10-15. Windows x64, MSVC 14.51.36231, Windows SDK 10.0.26100.0,
C++17 Release core runner. This tests the production Space module, not a VST3
host or listening acceptance.

## Production defect

The original RT60 gain expression multiplied signed `-3` by unsigned
`lines_[i].size()`. On Windows x64, unsigned conversion/wrapping made the
exponent huge and positive. The gain became infinite; smoothing produced NaN;
the finite-sample safety guard discarded the injected signal. The linked
runner independently failed Space.Decay (`reverb emits impulse energy`) and
Space.Stereo (`one input channel excites nonidentical stereo returns`).

The production fix converts the line length to double before applying the
approved equation: delaySeconds=double(lineSamples)/sampleRate;
gain=10^(-3*delaySeconds/targetRT60). The eight delays, Householder mixer,
injection/output vectors, damping and feedback law were preserved.

Space.Injection now checks both input channels at 44.1/48/88.2/96 kHz: the
initial normalized stored impulse is 0.25; no output precedes the shortest
line; its first output is 0.25/sqrt(8) in each output channel. It passed.
Space.Duck and the expanded four-rate Space.Stereo also passed.

## Measurement scope and retained failures

The approved specification requires mid-band RT60 with damping open, within
25% for targets 0.5/2/6/12 seconds. The previous test integrated a broadband
impulse, including the intended frequency-dependent damping. After the
production defect was fixed, that broadband gate first failed at 88.2 kHz:
0.373197 seconds against a minimum 0.375 seconds for the 0.5-second target.
The complete subsequent matrix also measured 0.359375 seconds at 96 kHz,
which fails that broadband tolerance. These broadband results remain recorded;
they are not reclassified as passing measurements.

The corrected acceptance measurement uses an independent offline bandpass
centered at 1000 Hz with Q=sqrt(2), nominal octave bandwidth. It follows the
constant-0-dB-peak BPF equations from the [W3C Audio EQ Cookbook, 2021-06-08](https://www.w3.org/TR/audio-eq-cookbook/):

```
w = 2*pi*1000/Fs
alpha = sin(w)/(2*sqrt(2))
b = (alpha, 0, -alpha)/(1+alpha)
a = (1, -2*cos(w)/(1+alpha), (1-alpha)/(1+alpha))
```

This is a nominal analysis band; digital frequency warping prevents a claim
of an exact standardized octave filter. Both stereo outputs pass through
separate double-precision analysis states outside the audio callback. Their
squared energies are summed and reverse-integrated (Schroeder). The elapsed
time from -5 dB to -25 dB is multiplied by three to estimate RT60 (T20).
The render uses a unit left impulse, zero predelay, damping requested at
20000 Hz and clamped by production DSP where applicable, and no limiter.
Its length is target*1.4+1 seconds. All 16 mid-band checks passed the unchanged
25% tolerance. No production feedback tuning was used to change these results.

| Sample rate | Target seconds | Mid-band RT60 | Broadband RT60 |
|---:|---:|---:|---:|
| 44100 | 0.5 | 0.470068 | 0.444014 |
| 44100 | 2 | 1.97299 | 1.69061 |
| 44100 | 6 | 5.82769 | 4.90476 |
| 44100 | 12 | 11.4482 | 9.85803 |
| 48000 | 0.5 | 0.471 | 0.443937 |
| 48000 | 2 | 1.96981 | 1.65694 |
| 48000 | 6 | 5.82625 | 4.88675 |
| 48000 | 12 | 11.4056 | 9.85156 |
| 88200 | 0.5 | 0.46966 | 0.373197 |
| 88200 | 2 | 1.95915 | 1.52262 |
| 88200 | 6 | 5.75772 | 4.78575 |
| 88200 | 12 | 11.2263 | 9.71388 |
| 96000 | 0.5 | 0.468656 | 0.359375 |
| 96000 | 2 | 1.95822 | 1.52141 |
| 96000 | 6 | 5.76053 | 4.76319 |
| 96000 | 12 | 11.2321 | 9.68803 |

## Commands

From `C:/Users/david someone/Desktop/SONIC AI V3/sonic-ai-v3`:

```powershell
. ./engineering/vst3/scripts/enter-windows.ps1
cmake --build plugins/adlib-93/build/windows-release --target adlib93_tests --parallel 1
plugins/adlib-93/build/windows-release/adlib93_tests.exe --case Space.Injection
plugins/adlib-93/build/windows-release/adlib93_tests.exe --case Space.Decay
plugins/adlib-93/build/windows-release/adlib93_tests.exe --case Space.Stereo
plugins/adlib-93/build/windows-release/adlib93_tests.exe --case Space.Duck
```

The core build and each final named check completed successfully. Raw final
decay and stereo numbers are alongside this document. Full integration and
host checks remain separate; these results establish neither subjective
reverb quality nor FL Studio compatibility.
