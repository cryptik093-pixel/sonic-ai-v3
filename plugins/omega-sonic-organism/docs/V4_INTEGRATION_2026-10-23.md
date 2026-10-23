# V4 production integration - 2026-10-23

Baseline: recovery/actual-project-state, df8249cc020a0a887bb1a7bc461918488dc71ea7.
Evidence directory: test-results/v4-integration-20261023. Development build only.

## Implemented production path

The existing instrument now incorporates the prepared deterministic Motion16 lane.
Step Depth (115) smoothly controls up to one octave of cutoff modulation. Step Pattern
(116) selects Static, Pulse, Rise or seeded Orbit. All four fixed patterns are prepared
before processing; selection neither allocates nor resets phase. The shared step clock
uses sixteenth notes at the host tempo and preserves fractional phase across tempo changes.
Processing restart resets phase deterministically. Valid musical-position context now
synchronizes transport starts, loops and seeks; contiguous callbacks preserve smoothing.
Without valid musical position the lane free-runs. Actual FL Studio acceptance remains pending.

Chamber Coupling (117) smoothly exchanges the real states of body modes 0 and 1 before
their existing normalized rotations and damping. The exchange matrix has eigenvalues
1 and 1-2k, with k in [0,.02], so it cannot add pair energy. It uses two of the existing
four modes, with their pitch tracking, material response, antialias weights and conditional
processing. It is a musical research-inspired interaction, not a measured reconstruction
of any archaeological chamber. The isolated ModContour experiment is not required for
LIFE articulation; the existing production ADSR remains in use.

The existing seven-sector UI exposes the new controls on its advanced page. BODY and
MOTION navigation focus their applicable new controls. Legacy preset loading resets all
three new controls to zero. Native and JSON save/restore persist enabled V4 behavior.

## Compatibility and explicit extension

IDs 100-114 and both CIDs retain their original definitions. The original 30 factory
JSON files and embedded content are unchanged. V4 controls use additive IDs 115-117.

When all three V4 values are zero, native encoding remains the byte-identical 140-byte
OSO1 schema 1 (15 doubles). Six- through fifteen-value legacy states still decode with
missing values defaulted. Nonzero V4 values require OSO2 schema 2: magic OSO2, version 2,
count 18, payload 144, eighteen little-endian doubles, FNV1a checksum; total 164 bytes.
A legacy build cannot load OSO2; it must safely reject it. This is an explicit forward
extension, not reinterpretation of existing values. New builds read both formats.
JSON schema 1 adds optional keys step_depth, step_pattern and chamber_coupling; legacy
exports omit these when zero. All legacy values and meanings are preserved.

State handoff uses the existing bounded fixed-atomic snapshot mechanism, extended to
18 values; host-only publication locking remains outside the processing callback.

## Acceptance criteria and current status

- State: all OSO2 truncated lengths and single-byte corruptions rejected atomically;
  OSO1 reload resets V4 controls to defaults; extended native and JSON round trips exact.
- DSP: each route changes actual audio (>1e-8 summed absolute sample difference for coupling,
  >1e-7 for steps); exact repeat renders; finite peak <= .980001 across all anchors and
  44.1/48/96 kHz. Sample-timed events produce identical stereo output with block sizes
  1, 64, 256 and 1024; no measured C++ callback allocations/deallocations.
- Adapter: V4 queues at offsets 0/37/96 match a per-sample reference; native controller
  restores all new controls. Existing MIDI queues retain their IDs and behavior.
- CPU: unchanged G07 threshold P95 <= 1 ms, P99 <= 2 ms, zero deadline overruns at
  48 kHz/256 frames/16 voices, 30 seconds per quality. Results pending this build.
- Native validator, actual DLL renders, editor capture and FL Studio acceptance pending
  this build. Subjective listening and commercial release approval remain pending.

No candidate or release approval follows from compiling this change.

## First integration checkpoint

Build-3: native x64 linked; 7/7 CTest and 3/3 Python gate evaluator tests passed.
Actual DLL SHA-256: 3F4B0D8B07AD5DB85DACB9F2898FD07F8E43712C817390C211795FA0B7024B5A.
15 V4 native renders passed finite/nonzero output and exact recall after destruction
and recreation. All 27 default Eco legacy renders are byte-identical to the preserved
previous development DLL. Editor attach/remove/reopen and seven-sector navigation
passed; the captured MOTION page was visually inspected for the added controls.

Production-function profile: Eco 100,000 voice samples 62.5589 ms, global room
100,000 samples 27.0908 ms; HQ 70.3746 / 18.0158 ms respectively. These are
isolated diagnostic timings, not callback percentage attribution or G07 acceptance.

## Transport and optimization checkpoint

New actual-adapter tests match the core sample for sample across starts, contiguous
callbacks, tempo changes, loop jumps, stop and restart. Motion phase seek supports
negative preroll and rejects nonfinite positions. New V4 stress-matrix mode enables
maximum Step Depth, Orbit and Chamber Coupling without altering the original G07 load.

The first normalized harmonic recurrence increased median thread cycles by roughly
17% Eco / 12% HQ; its Newton-normalized variant increased them 9% / 6%. Both were
rejected and their source/results retained only in test evidence. Original oscillator
lookup arithmetic is preserved. A targeted MSVC voice-function inline produced zero
sample difference against the preserved baseline and reduced median cycles 6.3% Eco /
2.3% HQ in a 1024-callback-per-variant alternating run. This is a measured diagnostic
improvement, not a passing CPU release gate. Global /O2 /Ob2 and FIR are unchanged.

Review also found that a malformed MIDI note-on could put NaN in velocity telemetry.
The adapter now ignores nonfinite velocity and out-of-range pitch before audio or meter
updates. The actual processor test injects both and verifies unchanged finite meters.
