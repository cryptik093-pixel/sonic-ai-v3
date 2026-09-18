# OHIS-05 — Asset Metadata

## Purpose

Metadata is the machine-readable layer between files and Sonic intelligence. It should preserve objective facts separately from inferred or subjective descriptors.

## Metadata domains

### Identity

```text
asset_id
name
aliases
type
role
context
state
version
created_at
updated_at
```

### Technical audio

```text
format
sample_rate
bit_depth
channels
duration_seconds
peak_dbfs
true_peak_db
integrated_lufs
```

### Musical

```text
root_key
scale
bpm
time_signature
bars
```

### Source

```text
source_type
source_asset_id
source_project_id
instrument
plugin
preset_name
recording_source
```

### Processing

```text
processing_chain
routing_depth
routing_nodes
bus_relationships
```

### Creative descriptors

```text
mood
energy
timbre
brightness
warmth
density
movement
transient_strength
harmonicity
descriptor_confidence
```

Creative descriptors may be human-authored, deterministic, model-inferred, or hybrid. The provenance of each descriptor should be retained when practical.

### Commercial

```text
product_id
pack_id
license_class
release_status
```

## Evidence rule

Metadata has a source.

Examples:

```text
bpm = 145
source = DAW project
confidence = 1.0
```

```text
mood = dark
source = model inference
confidence = 0.81
```

```text
role = 808
source = producer label
confidence = 1.0
```

Sonic must not silently turn a probabilistic inference into an authoritative fact.

## Quality scores

Quality is distinct from lifecycle state.

An asset can be:

```text
state = APPROVED
quality_score = 0.73
```

or:

```text
state = EXPERIMENTAL
quality_score = 0.96
```

The first is production-approved; the second is highly promising but not yet operationally approved.

## Retrieval intent

Metadata should support queries such as:

- Find approved F minor 808 one-shots around 145 BPM.
- Find sounds derived from a specific preset.
- Find all assets used in a released pack.
- Find chains used repeatedly in high-rated projects.
- Find sounds matching a creative descriptor with confidence above a threshold.

## Human override

Human-authored metadata has priority over model inference when the two conflict, unless the producer explicitly asks Sonic to challenge or audit the value.
