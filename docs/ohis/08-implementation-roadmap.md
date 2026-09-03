# OHIS-08 — Implementation Roadmap

## Phase 0 — Specification

- [x] Establish OHIS namespace.
- [x] Define ontology.
- [x] Define Asset ID families.
- [x] Define naming grammar.
- [x] Define DAW color/routing semantics.
- [x] Define lifetime filesystem.
- [x] Define metadata domains.
- [x] Define lifecycle/provenance.
- [x] Define Sonic integration boundary.
- [x] Add machine-readable asset schema.

## Phase 1 — Deterministic asset ingestion

Build a scanner that can:

1. Discover managed files.
2. Calculate stable file hashes.
3. Identify supported media formats.
4. Extract deterministic technical metadata.
5. Detect likely musical metadata where reliable.
6. Assign or resolve an OHIS Asset ID.
7. Preserve legacy filename as an alias.
8. Generate canonical naming suggestions.
9. Emit an asset-ingested event.

### Gate

No model inference is required for the scanner to create a valid base asset record.

## Phase 2 — Classification and normalization

Build:

- controlled vocabulary resolver
- role/type classifier
- filename normalizer
- duplicate detector
- human override mechanism
- confidence/provenance tracking

### Gate

Equivalent concepts normalize to the same canonical vocabulary without destroying original labels.

## Phase 3 — DAW topology intelligence

Support project/session inspection where technically possible.

Capture:

- mixer channels
- inserts
- insert order
- sends
- buses
- returns
- sidechains
- routing depth
- color semantics
- labels
- plugin identity and versions

### Gate

Sonic can represent a supported session as a routing graph and distinguish D1/D2/D3 from instrument role.

## Phase 4 — Provenance graph

Persist relationships between:

```text
Source → Derivative → Project → Pack → Release
```

### Gate

Given any canonical asset, the system can retrieve its known ancestors and descendants.

## Phase 5 — Intelligence

Expose OHIS to Sonic's memory/retrieval layer.

Capabilities:

- semantic asset search
- contextual retrieval
- creative similarity
- workflow pattern discovery
- accepted/rejected recommendation learning
- Creator DNA reconstruction

### Gate

Every inference includes evidence/provenance and confidence where applicable.

## Phase 6 — Automation

Only after identity and provenance are stable:

- auto-organize imports
- generate naming proposals
- create project structures
- detect inconsistent labels/colors
- suggest mixer routing
- build asset indexes
- run migration jobs

Human approval remains required for destructive or ambiguous operations.

## Non-goals for v1

- replacing the DAW
- forcing a single creative style
- requiring perfect metadata for every file
- using AI to invent authoritative technical facts
- automatically deleting uncertain or duplicate material

## Acceptance philosophy

OHIS is successful when it makes the creative system:

```text
faster
+ more searchable
+ more reproducible
+ more explainable
+ more recoverable
+ more intelligent
```

without making the producer stop creating music to administer the system.
