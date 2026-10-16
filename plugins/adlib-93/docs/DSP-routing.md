# ADLIB-93 production engine and transitions

This implementation follows the approved specification and plan in `docs/superpowers`; those documents remain unchanged. The reusable engineering starter is separate from this C++17 product.

`AdlibEngine` owns Cleanup, Character, Movement, Echo, Space, Freeze and OutputStage. `Transitions` owns two complete preallocated engines. Preparation allocates module buffers and validates rates (8–384 kHz), positive prepared block capacity and the three supported layouts. Bulk `reset()` is lifecycle-only. Neither callback path calls bulk reset, allocates an engine, resizes a buffer or serializes state.

## Routing

Input samples are sanitized and input gain is applied before both the cleanup path and linked duck detector. Gate → complementary high-band de-esser → Character supplies direct, double, chorus and delay excitation. Double/chorus never feed delay. Delay returns are branch-leveled before the delay→reverb send; that send is pre-duck. Space supplies the common duck gain for delay plus reverb only. Freeze captures this ducked normal spatial sum, never the held layer. Its return replaces/crossfades normal spatial audio. It does not feed either network.

Direct, movement and spatial returns form one wet sum. One final mid/side-width and attenuation-only balance stage operates on that entire wet sum. Insert blends linearly with trimmed dry. Send forces the effective wet mix/direct overrides while retaining stored Insert values. Routing topology and bypass move over 20 ms. Insert bypass restores trimmed dry and suppresses new effect excitation; Send bypass never introduces dry. Existing networks keep decaying. Output gain and enabled sample-peak protection remain in both paths. De-ess Listen overrides the normal blend with Cleanup's high band through OutputStage.

Mono input is duplicated at unity; mono output is the arithmetic average after output protection. Block adapters read both channels of each frame before writing either output, supporting normal in-place and cross-channel aliasing without scratch allocations. Zero-frame calls do not dereference sample pointers. Oversized blocks are processed by a bounded per-frame loop, independent of prepared scratch capacity.

## Performance states

Freeze rising suppresses new delay/reverb excitation. Release resumes excitation using the existing Freeze blend's 250 ms recovery, while its underlying networks continue decaying. Clear releases held Freeze/Throw, fades spatial/movement branches out for 20 ms, clears their buffers incrementally while direct audio remains available, and restores branches over 20 ms. Repeated clear commands coalesce. A still-high performance parameter is inhibited after clear/preset load until observed low, so stale host snapshots cannot resurrect a hold without a new edge.

Preset/A–B requests copy fixed-size validated snapshots and release transient states. Incoming memory is cleared before beginning the 50 ms linear engine crossfade. A newer request replaces the pending snapshot; at most two engines exist. Normal automation changes the active engine when idle and the incoming engine during preparation/crossfade, preserving the outgoing tail's settings.

Clearing is charged conservatively by requested write budget because individual module APIs return completion rather than exact write counts. Controller clearing requests 128 float-buffer writes per processed frame. Automatic 180-second tail retirement reserves another 128; during a dual-engine crossfade no controller clearing runs, leaving 128 per playing engine. Zero-block controller service requests at most 64 writes. `maxClearWritesLastFrame()` reports this upper bound, not an instrumented count of all ordinary DSP state writes or proof about lock freedom. Scalar reset/coefficient work is fixed-size; numerical and callback instrumentation remain required.

Normal spatial output fades during the last second after 179 seconds of exact-zero trimmed input and is silent by 180 seconds. Residual memory then retires incrementally. Freeze intentionally has no finite held-duration limit. Input resuming during retirement remains finite and direct processing continues; spatial input resumes once memory retirement completes.

## API and measurements

Both engines expose `prepare(spec, initial)`, `reset()`, `setParameters`, `setTiming` and per-sample `process`. Transitions adds `request`, `setBypassed`, `clearTails`, `serviceZeroBlock`, `allocatedBytes` and `maxClearWritesLastFrame`. Block overloads accept explicit parameters/context or reuse the currently applied parameters with context only. APIs are audio-owned except preparation/lifecycle reset; callers must transfer requests through the processor's bounded mailbox, not call DSP concurrently.

Engine measurements provide after-trim input peak, actual output sample peak, cleanup/limiter reductions, resolved tempo/fallback/clamp state, clear/transition/freeze state, diagnostic count and allocated DSP buffer bytes. Correlation is explicitly unavailable here; the processor owns the real 300 ms correlation window. Measurements are plain audio-thread snapshots; the UI must use its atomic MeterBridge.

Tests added: Routing.Identity, Routing.Layouts, Routing.Blocks, Routing.SendBypass, Routing.ListenAndDuck, Performance.Switches and Performance.Clear. Build, numerical outcomes, allocation instrumentation and reference-machine timing must be recorded from actual coordinator-run checks. FL Studio, listening and commercial acceptance remain PENDING until completed separately.
