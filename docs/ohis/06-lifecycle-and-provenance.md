# OHIS-06 — Lifecycle & Provenance

## Lifecycle

```text
RAW
 ↓
WORKING
 ↓
TESTED
 ↓
APPROVED
 ↓
RELEASED
```

Alternate terminal or non-production states:

```text
EXPERIMENTAL
ARCHIVED
DEPRECATED
```

State is an operational condition. It is not a creative quality score.

## Promotion rule

An asset should only move forward when its evidence supports the next state.

Example:

```text
RAW → WORKING
```

means the source is now being intentionally developed.

```text
TESTED → APPROVED
```

means the asset has passed the applicable human/technical quality gate.

```text
APPROVED → RELEASED
```

means it has entered a published or production distribution context.

## Provenance

Every derived asset should preserve its lineage whenever the relationship is known.

Example:

```text
Preset
  ↓
Raw One-Shot
  ↓
Processed One-Shot
  ↓
16-Bar Melody
  ↓
Stems
  ↓
Composition
  ↓
Production Suite
```

The graph should answer both directions:

- What created this asset?
- What was created from this asset?

## Version vs child asset

Use a **version** when the identity remains the same and the asset is revised.

Use a **child Asset ID** when a materially different artifact is created from the parent.

Example:

```text
OH-AS-000100_v01.wav
OH-AS-000100_v02.wav
OH-AS-000100_v03.wav
```

versus:

```text
OH-AS-000100  # source one-shot
OH-AS-000101  # processed derivative
OH-AS-000102  # melody derived from source
```

## Processing provenance

Where available, preserve:

- processor/plugin identity
- plugin version
- preset
- parameter snapshot
- processing order
- routing path
- input/output relationship
- DAW/project context
- timestamp

## Reproducibility

A future Sonic agent should be able to determine, as far as available evidence allows, how an important asset was produced.

Exact reproducibility is preferred but not assumed. Missing provenance is recorded as missing rather than fabricated.

## Deprecation

Deprecated does not mean destroyed. An asset may be deprecated because it was replaced, technically invalidated, or intentionally removed from current production use.

Historical relationships remain searchable.
