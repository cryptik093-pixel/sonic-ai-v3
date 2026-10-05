# Studio Drop 002 — Tier 1 Evidence Classification

Date: 2026-10-05
Source branch: `feat/studio-drop-002-packaging`
Source state versus canonical Sonic main at Tier 1 start: 19 commits ahead / 69 behind.

## Decision

Preserve the **seven unique Studio Drop 002 product/package documents** as recovered source evidence, but do not promote them as a current certified release.

The source files are copied verbatim under:

`docs/recovery/studio-drop-002-source/`

Their original branch paths were:

`docs/products/studio-drops/SD-002/`

## Why the product documents are quarantined

The asset manifest labels the product/release state `MVP_CERTIFIED`, while the same manifest explicitly records unresolved release-critical fields:

- actual filenames pending
- formats pending
- key/BPM/duration/sample-rate/channel metadata unresolved
- SHA-256 checksums pending
- final manifest/package validation pending
- governing license/certification/package contents still requiring verification

Therefore `MVP_CERTIFIED` is historical/source-branch language, **not current release truth**.

No customer distribution or release certification should be inferred from these recovered files until the actual asset package is present and every listed validation checkpoint is satisfied.

## Event/infrastructure code excluded

The Studio Drop branch also contains Tier-5 event architecture and ingestion code. That code is intentionally excluded from this recovery because comparison by blob SHA confirmed it is byte-identical to the dedicated infrastructure branches:

- `tier5/gate-1-event-architecture`
- `tier5/gate-2-durable-ingestion`

The Studio Drop branch is therefore not the authoritative recovery source for those runtime components.

## Recovery result

Recovered here:
- package README
- asset manifest
- producer metadata card
- stem map
- provenance/version record
- workflow guide
- collaborative license insert

Excluded:
- event bus/runtime code
- durable ingestion code
- event architecture RFC copies
- any certification claim not backed by present package evidence
