# Sonic AI V3 OH-M04 Reference Analyzer

This directory contains the dependency-free Python reference implementation of the Phase 2 deterministic audio measurement contract.

## Run

```bash
python sonic_measurement.py /path/to/file.wav
```

Compact JSON:

```bash
python sonic_measurement.py /path/to/file.wav --compact
```

## Test

```bash
python -m unittest -v test_sonic_measurement.py
```

## Contract

Semantics:

`docs/knowledge/requirements/OH_M04_MEASUREMENT_PROFILE_V1.md`

Schema:

`docs/knowledge/schemas/audio-measurement-profile.schema.json`

## Boundary

This implementation emits deterministic observations only. It does not produce mixing advice, defect labels, producer-DNA conclusions, LUFS estimates or true-peak estimates.

LUFS and true peak are deliberately represented as unavailable until a standards-compliant implementation and reference corpus are validated.
