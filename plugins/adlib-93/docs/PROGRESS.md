# ADLIB93 release recovery checkpoint

2026-10-16. Owner directive: release completion; P0/P1 repairs only.
Repository branch recovery/actual-project-state. Isolated product plugins/adlib-93.
Approved specification/plan, JUCE9.0.4 pin, C++17, class IDs, 70 product IDs and24 factory recipes preserved.

## Verified

- Windows x64 optimized Release VST3 build PASS (exit0); final narrow bypass/editor rebuild PASS.
- Full core/native CTest63/63 PASS; final adapter/editor rerun7/7 PASS after the two last repairs.
- Corrected dist/rc1/ADLIB93.vst3: pluginval strictness10 PASS and official Steinberg validator47passed/0failed. Bundle unchanged under validation.
- Host bypass now persists through JUCE wrapper state independently of transient internal bypass. Product IDs unchanged.
- Native editor captures75/100/150 exist; title/header encoding corrected and inspected. Host/DPI/manual interaction remains pending.
-24 generated-tone factory renders completed with finite output. No listening acceptance inferred.
- Two-engine buffers at96k:7,572,616bytes (<64MiB).
- DSP/state repairs cover reverb unsigned RT60 exponent, manual-tempo4/4 fallback, finite-60dB endpoint, Freeze retrigger/release, bounded transitions, and user-recipe baseline recall.

## Remaining release blockers

- P1 performance FAIL:600wallseconds per mode at48k/128, steady p99=4.572ms, transitions p99=4.155ms; maxima184.963/63.3739ms. Output finite. Bounded module probe retained; no passing CPU or host scheduling claim.
- P1 commercial acceptance OPEN: FL Studio scan/routing/session recall, owner listening, clean-profile install/DPI behavior, and applicable distribution-license approval.
- No unresolved compiler/linker/validator defect is known from these executed checks.

See VERIFICATION.md for exact commands/results, candidate hash and preserved failed attempts.
The earlier dist/ADLIB93.vst3 failed bypass persistence and is retained for history: DO NOT INSTALL IT.
Only the corrected rc1 bundle is eligible for INTERNAL_EVALUATION_ONLY packaging.
No system VST3 installation, FL project/recording change, signing, publication, license purchase or paid service occurred.
