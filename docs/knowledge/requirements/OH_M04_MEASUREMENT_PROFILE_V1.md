# OH-M04 — Deterministic Audio Measurement Profile v1

**Control ID:** `OH-M04`  
**Phase:** Sonic AI V3 Phase 2 Runtime Hardening  
**Owner:** Audio Analyzer / Evaluation / CI  
**Status:** validated deterministic v1 baseline  
**Evidence:** `docs/knowledge/requirements/evidence/OH-M04-v1.yaml`  
**Doctrine links:** `OH-DR-AI-001`, `OH-DR-DYN-002`, `OH-DR-STEREO-001`, `OH-DR-EVID-003`  
**Executable reference:** `packages/audio-analysis/python/sonic_measurement.py`

## Purpose

OH-M04 establishes the first deterministic measurement boundary for Sonic AI V3. It exists so Audio Analyzer facts can be reproduced, tested and separated from interpretation.

The profile does **not** decide whether a mix is good, bad, muddy, weak, loud enough, over-limited or release-ready. It produces observations. Interpretation belongs to Producer Intelligence and must cite these observations plus doctrine/policy.

## v1 accepted input

OH-M04 v1 accepts uncompressed integer PCM WAV files using 8-, 16-, 24- or 32-bit sample widths.

Unsupported codecs/containers must fail explicitly rather than silently converting or estimating.

## Required deterministic observations

| Field | Unit | Method | Interpretation allowed? |
|---|---|---|---|
| sample rate | Hz | WAV header | no |
| channel count | count | WAV header | no |
| bit depth | bits | sample width | no |
| frame count | frames | WAV header | no |
| duration | seconds | frames / sample rate | no |
| SHA-256 | hex digest | source-file bytes | no |
| sample peak | dBFS | maximum absolute PCM sample | no |
| RMS | dBFS | root mean square across samples | no |
| crest factor | dB | sample peak dBFS - RMS dBFS | no |
| DC offset | normalized amplitude | arithmetic mean per channel | no |
| full-scale samples | count / ratio | exact PCM positive-max or negative-min sample | no |
| near-full-scale samples | count / ratio | absolute normalized sample >= 0.999 | no |
| silent sample ratio | ratio | absolute sample <= -60 dBFS threshold | no |
| stereo correlation | -1..1 | centered normalized covariance for exactly two channels | no |

## Explicit non-equivalences

Sonic must not collapse distinct concepts into a single field.

- `sample_peak_dbfs` is **not** true peak.
- RMS is **not** integrated loudness.
- full-scale sample incidence is **not** proof that clipping occurred upstream.
- near-full-scale density is **not** proof that a limiter was used.
- stereo correlation is **not** a complete mono-compatibility score.
- a deterministic measurement is **not** a production recommendation.

These distinctions directly enforce `OH-DR-AI-001` and begin satisfying `OH-DR-DYN-002` without inventing unsupported measurements.

## LUFS and true peak policy

The result contract contains dedicated loudness and true-peak objects. In v1:

- `integrated_lufs = null`
- loudness `status = unavailable`
- `dbtp = null`
- true-peak `status = unavailable`

They remain unavailable until Sonic contains a reproducible implementation validated against a standards-compliant reference corpus. A later implementation may populate these fields without renaming sample peak or RMS.

## Silence representation

Digital silence must not emit JSON `Infinity` or `-Infinity`. When a logarithmic amplitude value is mathematically undefined because the linear value is zero, the field is `null`.

This keeps persisted measurements valid JSON and forces downstream intelligence to handle silence deliberately.

## Determinism rules

Given the same source bytes and profile version, OH-M04 must produce identical measurement values within the same numeric implementation contract.

The output records:

- `profile_id`
- `profile_version`
- source SHA-256
- source format
- deterministic observations
- explicit unavailable states
- explicit `interpretation.status = not_performed`

## Machine-readable contract

Schema:

`docs/knowledge/schemas/audio-measurement-profile.schema.json`

The schema is the persistence/API shape; this document is the measurement semantics.

## Acceptance tests

Executable tests live at:

`packages/audio-analysis/python/test_sonic_measurement.py`

The first acceptance set proves:

1. a known 0.5-amplitude sine reports approximately -6.02 dBFS sample peak, -9.03 dBFS RMS and 3.01 dB crest factor;
2. identical stereo channels report correlation +1;
3. polarity-inverted stereo channels report correlation -1;
4. exact positive/negative full-scale PCM samples are counted;
5. digital silence is represented with null logarithmic values rather than infinities;
6. LUFS and true peak remain explicitly unavailable;
7. interpretation remains outside the measurement function.

## Evidence state

The deterministic v1 baseline is validated by CI run `33897033199` on implementation commit `659e33a8c1f1d034f0b2cf7d7ea6809b93ca7481`.

Evidence packet:

`docs/knowledge/requirements/evidence/OH-M04-v1.yaml`

This validation is deliberately scoped. It does **not** validate integrated LUFS, true peak, limiter detection, clipping-cause inference, complete mono compatibility, defect diagnosis or recommendations.

## Next controls unlocked by OH-M04

- `OH-M02` defect taxonomy can reference stable measurement fields.
- `OH-M03` golden audio fixtures can encode expected deterministic observations.
- `OH-DR-DYN-002` can later add validated loudness and true-peak methods without conflating them with v1 metrics.
- `OH-DR-STEREO-001` can build center-authority and mono-translation tests on top of correlation plus future mid/side metrics.
