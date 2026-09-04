# OH-M03 — Golden Audio Fixture Set v1

**Control ID:** `OH-M03`  
**Phase:** Sonic AI V3 Phase 2 Runtime Hardening  
**Owner:** Evaluation / Audio Analyzer / CI  
**Status:** implemented / awaiting CI evidence  
**Depends on:** validated `OH-M04`, `OH-M02`, and `OH-M05` baselines  
**Doctrine links:** `OH-DR-EVID-003`, `OH-DR-LISTEN-003`, `OH-DR-STEREO-001`, `OH-DR-DYN-002`, `OH-DR-AI-001`

## Purpose

OH-M03 creates a persistent, version-controlled audio reference corpus whose exact bytes, SHA-256 hashes, deterministic OH-M04 measurements, OH-M02 candidate signals, and OH-M05 metadata envelopes are asserted in CI.

This closes the gap between generated unit-test signals and durable evidence. A future change to DSP math, PCM decoding, taxonomy logic, metadata transport, or fixture bytes must either preserve the declared outputs or deliberately version the fixture/contract.

## Corpus location

`tests/fixtures/audio/golden/`

Manifest:

`tests/fixtures/audio/golden/manifest.json`

Manifest schema:

`docs/knowledge/schemas/golden-audio-fixture-manifest.schema.json`

Integration test:

`packages/audio-analysis/python/test_golden_audio_fixtures.py`

## v1 fixtures

| Fixture | Purpose | Expected OH-M02 signal |
|---|---|---|
| `digital_silence.wav` | digital-silence handling | `OH-DEF-SIG-SIL-001` |
| `full_scale_incidence.wav` | exact full-scale incidence without causal clipping inference | `OH-DEF-DYN-FS-001` |
| `mono_sine_0p5_1khz.wav` | calibrated peak/RMS/crest reference | none |
| `stereo_in_phase_0p25_400hz.wav` | +1 stereo-correlation reference | none |
| `stereo_inverted_0p25_400hz.wav` | -1 stereo-correlation reference | `OH-DEF-ST-NEG-001` |

All files are 48 kHz, 16-bit integer PCM WAV and intentionally tiny so they can be committed directly to the repository and run in every CI job.

## Fixed content hashes

```text
digital_silence.wav
5d41ac0a816ea96ff677295a7d5f548be06465d029e4f82ef53523520d4b5465

full_scale_incidence.wav
d0a9a37be53716e93bbb33532b08ff863f5ce0dc078b2974195781565aff0f48

mono_sine_0p5_1khz.wav
8d9a122dfcc02cb6f73fd28f0b3340c3f5771c9c8475a78a6e186a62feb363ba

stereo_in_phase_0p25_400hz.wav
ca500928cbdcf8843e2c0bee7951dd5afb268b72a41b16ddd03b95d8c479fdb4

stereo_inverted_0p25_400hz.wav
39764a9ec8550397a762546ee885883057d36c88efa4a15299f0c5ff1c031c1a
```

A hash mismatch is a fixture failure even if the new audio sounds equivalent.

## Validation chain

For every fixture, CI must execute this chain:

```text
fixture bytes
  -> SHA-256 verification
  -> OH-M04 measure_pcm_wav
  -> declared measurement comparison
  -> OH-M02 detect_measurement_signals
  -> declared defect-code comparison
  -> OH-M05 build_asset_intelligence_envelope
  -> semantic envelope validation
```

The test therefore proves cross-contract compatibility, not only isolated functions.

## Measurement tolerance

Declared floating-point observations are compared with absolute tolerance `1e-9` for the current Python reference implementation.

This tolerance is an implementation regression tolerance, not an audio-quality tolerance and not a production acceptance threshold.

## What the corpus proves

OH-M03 v1 can validate:

- committed fixture bytes are unchanged;
- PCM decoding remains stable for the v1 reference files;
- sample peak/RMS/crest calculations remain stable;
- silence representation remains stable;
- stereo +1/-1 correlation anchors remain stable;
- OH-M02 candidate-signal mapping remains conservative and reproducible;
- OH-M05 can transport the measurement/signal records without changing state, cause, severity, evidence, or unknown-rights semantics.

## What the corpus does not prove

The v1 corpus does **not** validate:

- integrated LUFS;
- true peak;
- real-world kick/808 ownership;
- frequency masking diagnosis;
- transient/groove defects;
- real-device translation;
- perceptual quality scoring;
- producer preference or Artist DNA;
- automatic repair;
- commercial/release quality.

Those require broader fixtures, human/reference evidence, or additional deterministic methods.

## Fixture governance

1. Golden files are immutable within a fixture version.
2. Changing bytes requires a new hash and explicit review of expected results.
3. Changing expected measurements without changing bytes requires evidence that the measurement contract intentionally changed.
4. A fixture must declare its purpose; arbitrary audio must not enter the golden set merely because it is convenient.
5. Golden fixtures are technical evidence, not Omega House production examples or marketing assets.
6. Rights for synthetic technical fixtures are not inferred into product rights; OH-M05 keeps rights state explicitly unknown in the integration envelope.

## Acceptance conditions

OH-M03 v1 becomes validated only when CI on the exact implementation head proves:

1. all five committed WAV files exist;
2. every file hash equals the manifest hash;
3. all declared M04 format/amplitude/stereo observations match;
4. all declared M02 candidate-code sets match exactly;
5. each fixture can enter a valid M05 envelope with evidence refs preserved;
6. the M03 manifest and all upstream schemas remain valid JSON;
7. the existing M04, M02, and M05 suites continue to pass.

## Next runtime frontier

After OH-M03, the foundational evidence substrate exists. The next highest-leverage move is to use these validated contracts in a real ingestion vertical slice so an uploaded WAV produces a persisted M05 envelope containing OH-M04 observations and OH-M02 candidates, then can be retrieved without losing provenance or evidence state.
