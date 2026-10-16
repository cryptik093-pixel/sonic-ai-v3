# Production DSP map

The approved engineering specification contains the actual transfer functions,
normalization vectors, timing conventions and signal contract. This document
indexes the implementation; it does not replace or amend those requirements.

| Stage | Production source | Supporting notes |
|---|---|---|
| Registry/physical units | `src/core/Parameters.*` | `PARAMETERS.md` |
| Linked output protection | `src/dsp/OutputStage.h` | Instant attack, exponential release, gain before limiter; sample-peak only |
| Gate/de-esser | `src/dsp/Cleanup.*` | `DSP-cleanup-movement.md` |
| Character/filters/DC block | `src/dsp/Character.*` | `DSP-cleanup-movement.md` |
| Double/chorus | `src/dsp/Movement.*` | `DSP-cleanup-movement.md` |
| Echo/diffusion/Throw | `src/dsp/Echo.*` | `DSP-spatial.md` |
| FDN/ducking | `src/dsp/Space.*` | `DSP-spatial.md` |
| Immutable Freeze history | `src/dsp/Freeze.*` | `DSP-spatial.md`, notes below |
| Signal routing/clearing | `src/dsp/AdlibEngine.*`, `Transitions.*` | `DSP-routing.md` |
| Actual processor/state adapter | `src/plugin/PluginProcessor.*` | `PROCESSOR.md` |

Buffers are allocated in lifecycle preparation. Production sample processing
uses the same modules in the test runner, renderer and JUCE wrapper. The tests
must execute against current source before a row is called TESTED; authored
tests alone are insufficient. The verification ledger retains real outcomes.

## Edge corrections from measured review

- Invalid host BPM uses manual tempo with 4/4 for bar division, even if a host
  time signature remains available.
- `levelFromDb(-60)` uses a normal positive epsilon representation, giving
  approximately0.001 gain. Normalized zero remains exact mute. A denormal
  endpoint is avoided because real-time flush-to-zero would make it mute.
- If Freeze is re-engaged while its existing held voice remains audible, reuse
  that immutable buffer and its running playhead. A fresh capture can replace
  it after the held blend reaches zero. This avoids resetting an audible loop
  mid-waveform and never captures the frozen voice recursively. The capture
  fade remains50ms and release250ms.

See `evidence/review-regressions/README.md` for narrow native RED/GREEN probes
and their actual scope. Numerical discontinuity reduction is not proof of
inaudibility or owner listening acceptance.

## Evidence limits

C++ allocation hooks cover only the operators actually intercepted by the named
test executable. They do not prove absence of arbitrary C allocator calls,
kernel locks or filesystem activity by all loaded code. Direct DSP call paths
are also reviewed statically. Report each instrumented scope explicitly.

The ten-minute timing tool records the current machine and workload evidence.
Its thresholds remain those approved in the specification. A failed budget is
a failed budget; shorter or unpaced diagnostic runs cannot pass that gate.
Distortion aliasing, preset usefulness and perceived transparency require the
separate listening procedure.
