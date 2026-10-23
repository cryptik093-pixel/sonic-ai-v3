# Offline DSP Executor V1

Status: Windows unit-tested, isolated offline candidate renderer; no FL Studio runtime control.

The API `execute_gain(controller, session_id, expected_revision, expected_hash, source_relative, gain, output_dir, output_name)` supports **16-bit uncompressed mono or stereo PCM WAV only**, with linear gain from 0.0 to 1.0. It requires the input WAV to be listed in an existing Session Integrity manifest and under the approved project root.

Process:
1. Verify ledger revision, manifest checksum, and each selected project/asset SHA-256.
2. Reject unsupported/changed source files, invalid parameters, or an output directory inside the project.
3. Render a candidate into a randomly named staging WAV in an existing separate output directory.
4. Verify output frames, channels and sample rate, and revalidate input and manifest.
5. Publish using a same-volume no-overwrite filesystem hardlink and remove the staging name.
6. Return output SHA-256 and size, without editing the source project, DAW, ledger or existing renders.

This is **not** multiband mastering, undo/redo, live host rollback, or transaction-grade filesystem snapshotting. Concurrent file changes after revalidation and before publication remain a possible race; processing an actively edited project is not supported. Never claim an approved master or final mix from this operator.

Windows unit verification: `python -m unittest apps.api.test_offline_dsp_executor -v` (eight passing tests). All tests use generated disposable files and folders. Full existing regression suite must also pass prior to integration.

Next gate: streaming larger formats through vetted audio decoders with isolated copies, explicit audition approval, and integration-level output provenance storage.
