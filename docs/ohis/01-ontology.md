# OHIS-01 — Ontology

## 1. Identity model

Every managed entity is described across five primary dimensions:

```text
TYPE → ROLE → CONTEXT → STATE → RELATIONSHIPS
```

### Type

What the thing is.

Canonical initial vocabulary:

- `ONE_SHOT`
- `SAMPLE`
- `LOOP`
- `VOCAL`
- `STEM`
- `MIDI`
- `PRESET`
- `CHAIN`
- `MIXER_PRESET`
- `MASTER_CHAIN`
- `PROJECT`
- `BEAT`
- `PACK`
- `TEMPLATE`
- `DOCUMENT`
- `MODEL`
- `PROMPT`
- `AGENT`

New types require a documented reason. Avoid synonyms such as `SAMPLE`, `AUDIO`, and `WAV` when they describe the same conceptual class.

### Role

What the entity does or represents musically/operationally.

Initial vocabulary includes:

`KICK`, `808`, `BASS`, `SNARE`, `CLAP`, `HAT`, `PERCUSSION`, `DRUM_BUS`, `VOCAL`, `MELODY`, `CHORD`, `PAD`, `LEAD`, `TEXTURE`, `FX`, `UTILITY`, `EQ`, `SATURATION`, `DISTORTION`, `COMPRESSION`, `LIMITING`, `SPACE`, `MOVEMENT`, `MIX_BUS`, `MASTER`, `REFERENCE`.

Role vocabulary may expand, but aliases should map to one canonical role.

### Context

Where the entity has meaning.

- `LIBRARY`
- `PROJECT`
- `PACK`
- `CHAIN`
- `BUS`
- `MASTER`
- `TEMPLATE`
- `RELEASE`
- `ARCHIVE`

### State

Lifecycle state, not quality score.

- `RAW`
- `WORKING`
- `TESTED`
- `APPROVED`
- `RELEASED`
- `ARCHIVED`
- `DEPRECATED`
- `EXPERIMENTAL`

### Relationships

OHIS treats relationships as first-class data.

Important relationship types:

- `derived_from`
- `processed_by`
- `preset_of`
- `member_of`
- `contained_in`
- `used_in`
- `routed_to`
- `references`
- `variant_of`
- `supersedes`
- `licensed_as`
- `created_from`
- `approved_by`

## 2. Asset identity

Each durable asset receives an ID using this family:

```text
OH-AS-000001
OH-PR-000001   # preset
OH-CH-000001   # chain
OH-MX-000001   # mixer preset
OH-BT-000001   # beat
OH-PK-000001   # pack
OH-PJ-000001   # project
```

The ID is stable. Human-readable names and filenames may change.

## 3. Canonical record vs aliases

A canonical asset record may have multiple historical or human aliases.

```text
Canonical ID: OH-AS-000382
Canonical role: 808
Aliases:
  - filthy 808
  - dark sub
  - 808 test 7
```

Aliases must never create a second canonical identity unless the underlying asset is materially different.

## 4. Human vocabulary vs machine vocabulary

Human descriptions remain expressive:

> dark glass, filthy, cinematic, haunted

Sonic may additionally attach normalized attributes:

```text
brightness: 0.31
warmth: 0.74
density: 0.82
movement: 0.57
transient_strength: 0.66
```

Model-derived descriptors are evidence with confidence, not authoritative facts.

## 5. Governance rule

When two labels can reasonably describe the same concept, choose one canonical term and preserve the other as an alias. Taxonomy drift is treated as a data-integrity problem because it damages retrieval, analytics, and future Sonic reasoning.
