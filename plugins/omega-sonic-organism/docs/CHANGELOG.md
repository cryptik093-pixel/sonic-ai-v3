# Candidate changes

## 1.0.0-rc.1 - unqualified engineering candidate

- Retained the shared structural synthesis engine, original permanent parameter IDs, CIDs and OSO1/schema-1 state.
- Added native VSTGUI primary/Advanced editor, exact values, anchors, host gestures, patch menu, JSON load/save and host-routed output telemetry.
- Added strict bounded atomic JSON parsing/export, 30 embedded/exported factory configurations and numerical level calibration.
- Replaced literal zero-insertion drive FIR computation with an equivalent polyphase implementation, verified against the original formula. Reused modal coefficients and used bounded signed table-index conversion.
- Reproduced a long-held percussion envelope entering subnormal values, then added a sixty-second regression and tiny-value cleanup for envelopes and bend smoothing.
- Rendered host audio in segments between timed note/parameter events, retaining parameter-before-note ordering and sample-for-sample adapter comparisons.
- Added actual-DLL regression/recall, editor lifecycle/scaling and PCM24 audition probes, machine-readable reports, guarded Windows Setup and install/uninstall preservation tests.
- Kept CPU, interactive editor, FL Studio and listening gates explicit. This version number does not represent commercial approval.

## 0.2 alpha

Original M2 source, binaries and evidence remain preserved separately in the workspace. Read M2_TEST_REPORT.md and IMPLEMENTATION_REPORT.md for historical scope; they are not proof for the candidate DLL.
