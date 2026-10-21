# Current implementation contract
The current release contract is docs/MANUAL.md and the executed evidence in Verification/REPORT.md. Historical sampler contract is preserved in legacy/0.2.0-sampler/docs/IMPLEMENTATION_CONTRACT.md.

Runtime: one extended original fixed-16-voice modal oscillator/noise synthesis engine. No callback allocation/deallocation, locks, decoding or filesystem operations. Atomic parameter reads, preview/panic/activity mailboxes and a bounded immutable-sample hazard protocol. Sample decoding/publication/reclamation runs on one control worker. New slot parameters append to preserved original 82 IDs/order. JSON max 64 KiB and nesting 12; sample encoded max 64 MiB, decoded memory pool 256 MiB; portable kit max 256 MiB. State restore is a non-realtime control operation with bounded 30-second worker wait. No external calls or telemetry.

Performance measurement is actual sustained 48 kHz/128-buffer/16-voice wall-time callbacks for >=10 seconds. Predeclared p95 engineering budget remains 0.666667 ms (25 percent of callback deadline). Failed performance is reported as FAIL, not hidden by functional success. Functional gates, validators, human listening and FL acceptance are separate evidence categories.

Production depends on immutable SampleData.h and the single DrumEngine.h synthesizer. SampleEngine.h is a preserved regression-only sampler reference used by DrumSampleTests, not included or instantiated by the product. Fixed onset coefficient templates and cached unchanged coefficients reduce repeated transcendental work; they are never rendered voices.
