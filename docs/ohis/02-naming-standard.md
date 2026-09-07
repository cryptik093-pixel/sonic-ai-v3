# OHIS-02 — Naming Standard

## Objective

A filename should provide enough immediate context for a human and enough structured signal for Sonic to classify the asset without opening it.

## Canonical filename grammar

```text
OH_[TYPE]_[ROLE]_[DESCRIPTOR]_[KEY]_[BPM]_[VARIANT]_[VERSION]
```

Only applicable fields are required. Do not insert meaningless placeholders.

### Examples

```text
OH_808_SUB_HEAVY_FMIN_145_V01.wav
OH_ONE_SHOT_KICK_DRY_FMIN_145_V02.wav
OH_PRESET_LEAD_DARKGLASS_FMIN_145_V03.fst
OH_CHAIN_808_WARMTH_D2_V02.fst
OH_MIXER_PRESET_MASTER_CINEMATIC_D3_V04.fst
OH_MIDI_MELODY_HAUNTED_FMIN_145_V01.mid
```

## Rules

1. Use uppercase canonical tokens for machine-stable fields.
2. Use underscores as field separators.
3. Do not use spaces in canonical filenames.
4. Do not use `final`, `final2`, `new`, `newnew`, `use_this`, or similar uncontrolled version markers.
5. Version with zero-padded `V##`.
6. Keep descriptive creative language in `DESCRIPTOR`, not in structural fields.
7. Key uses canonical musical notation such as `FMIN`, `C#MIN`, `GMAJ`.
8. BPM is an integer where applicable; omit BPM for assets where tempo has no meaning.
9. Variant identifies meaningful alternates: `DRY`, `WET`, `ALT1`, `LONG`, `SHORT`, `STEM`, etc.
10. File extension remains the actual format and is not part of the semantic name.

## Asset IDs

Filename identity and system identity are different.

```text
Asset ID: OH-AS-000382
Filename: OH_808_SUB_HEAVY_FMIN_145_V03.wav
```

The ID never changes because the filename changes.

## Version semantics

`V01` means first managed revision. It does not necessarily mean the first time the sound existed on disk.

A meaningful revision includes:

- changed processing
- changed edit
- changed musical content
- changed source
- changed metadata that changes identity interpretation

A metadata-only correction may be recorded without creating an audio version when the underlying binary asset is unchanged.

## Legacy normalization

Existing Omega House files must not be destructively renamed in bulk.

Migration pattern:

```text
Legacy filename
      ↓
Scan
      ↓
Assign Asset ID
      ↓
Extract metadata
      ↓
Generate canonical filename
      ↓
Preserve original filename as alias
      ↓
Verify
      ↓
Promote to managed library
```

## Naming examples to avoid

```text
808 final.wav
808 final 2.wav
new 808.wav
808 REAL FINAL.wav
sample_good.wav
sound.wav
```

The problem is not aesthetics. These names destroy deterministic retrieval and provenance.
