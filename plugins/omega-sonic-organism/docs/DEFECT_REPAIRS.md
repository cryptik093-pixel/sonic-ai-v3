# Repaired defects and regression evidence

## Long-held zero-sustain envelope

The percussion envelope continued exponentially approaching zero in Sustain. A sixty-second hold at the engine's supported 8 kHz lower rate reproduced a subnormal value in the actual production engine. The new test failed at `std::fpclassify(longHeld.currentEnvelope()) != FP_SUBNORMAL`; core/state/preset tests passed in the same run. `denormal-reproduction.log` and its JUnit XML preserve this failure.

The envelope and pitch-bend smoothing now use the existing `dsp::zap` primitive to zero magnitudes below 1e-20. This is below audible resolution and avoids a denormal tail. The voice remains held, allowing structural morphing to restore a sustaining identity without a fresh note. The regression checks every rendered block for a subnormal envelope and requires exact zero after sixty seconds. Its repaired outcome belongs to the final clean-build engine suite, rather than the earlier interrupted qualification.

## Drive computation

The HQ path previously computed inserted zeros and discarded FIR output phases. It now uses a mathematically equivalent polyphase form, with the same half-band taps, saturation and 15-sample latency. Randomized comparisons at four drive values, including resets, require agreement within 1e-12 with the original literal algorithm. This is a computation reduction, not a sound redesign or a claim that CPU release goals passed.

## Event scheduling

The adapter previously scanned event/parameter cursors and invoked the engine per sample. It now renders segments between sample-offset boundaries. Adapter tests compare production output sample-for-sample with the reference ordering, including note/parameter collisions, bend, sustain and all-notes/sounds-off. The original permanent IDs and sound-state bytes are preserved.

## Editor capture host

The native probe's first 150% capture was silently clipped to the development monitor's track limits. The probe now uses its own bounded 4096x4096 maximum track size and asserts actual client dimensions before capture. This fixes the test surface; it does not stand in for interactive DAW acceptance.
