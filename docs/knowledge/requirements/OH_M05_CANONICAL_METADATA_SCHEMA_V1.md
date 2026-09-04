# OH-M05 — Canonical Asset Intelligence Metadata Schema v1

**Control ID:** `OH-M05`  
**Phase:** Sonic AI V3 Phase 2 Runtime Hardening  
**Owner:** Metadata / Backend / Memory  
**Status:** implemented / awaiting CI evidence  
**Depends on:** validated `OH-M04` measurement baseline and validated `OH-M02` defect taxonomy baseline  
**Doctrine links:** `OH-DR-EVID-001`, `OH-DR-AI-001`, `OH-DR-AI-004`, `OH-DR-LINEAGE-001`, `OH-DR-LINEAGE-002`, `OH-DR-LINEAGE-006`, `OH-DR-EXPORT-001`

## Purpose

OH-M05 defines the durable transport envelope that allows Sonic AI V3 to move asset identity, lineage, deterministic measurement, candidate defects, evidence state, provenance, and rights state between Audio Analyzer, Backend, Memory, Intelligence Core, and later release/product pipelines without losing semantic boundaries.

The envelope is not a database implementation. It is the canonical domain contract that a database/API/event payload must preserve.

## Core invariant

A durable Sonic asset record must answer:

1. **What production is this part of?**
2. **What exact asset is this?**
3. **What bytes were observed?**
4. **Where did the asset come from?**
5. **What is its parent/derivative relationship?**
6. **What deterministic measurements exist?**
7. **What candidate defects exist, and what state are they actually in?**
8. **What evidence supports the record?**
9. **What rights are known—and what rights remain unknown?**

## Canonical envelope

```yaml
schema_id: OH-M05
schema_version: 1.0.0
record_id: <stable-record-id>
production_id: <stable-production-id>
asset_id: <stable-asset-id>
asset:
  filename: <name>
  class: <beat|melody|stem|midi|one_shot|drum_loop|preset|preview|document|other>
  content_sha256: <64-char lowercase sha256>
  media_type: <mime-type>
lineage:
  derivation_type: <original|derived|render|export|package>
  parent_asset_ids: []
  invalidation_state: <current|stale|unknown>
analysis:
  measurement: <OH-M04 object or null>
  defects: [<OH-M02 records>]
evidence:
  state: <unvalidated|validated|historical|not_applicable>
  refs: []
provenance:
  source_type: <runtime|import|archive|manual>
  source_ref: <stable source reference>
  method: <ingestion/derivation method>
  observed_at: <ISO-8601>
rights:
  status: <unknown|known>
  rights_state_id: <id|null>
  license_id: <id|null>
  ai_ml_training_permission: <unknown|permitted|prohibited>
```

## Identity rules

### `production_id`

Every asset belongs to a stable production identity. Filename, folder path, UI label, or product title must not substitute for the production ID.

### `asset_id`

Every durable asset has a stable ID independent from filename.

### `content_sha256`

The asset hash identifies the observed bytes. Reusing an asset ID after bytes change requires an explicit replacement/version policy; OH-M05 does not silently treat changed bytes as the same evidence.

## Lineage rules

- `original` assets have no parent IDs.
- `derived`, `render`, `export`, and `package` assets require at least one parent asset ID.
- duplicate parent IDs are invalid.
- `invalidation_state` is explicit and never inferred from age or filename.

This begins operationalizing `OH-DR-LINEAGE-001/002/006` while leaving replacement propagation (`OH-DR-LINEAGE-005`) for its dedicated runtime event contract.

## Analysis rules

### Measurement

If present, `analysis.measurement` must be an OH-M04 result and must preserve:

- source SHA-256;
- profile identity;
- `interpretation.status = not_performed`.

OH-M05 must not transform an OH-M04 deterministic observation into interpretation while transporting it.

### Defects

If present, `analysis.defects` must contain OH-M02 records.

For v1 candidate records:

- `severity` must remain `unrated`;
- `cause_status` must remain `unknown`.

Measurement-derived OH-M02 records may not travel without the OH-M04 measurement that supports them. This prevents detached diagnosis-like records from losing their underlying evidence.

## Evidence rules

Evidence state is explicit:

- `unvalidated` — source exists but acceptance evidence is incomplete;
- `validated` — reproducible proof exists and at least one evidence reference is required;
- `historical` — dated evidence retained for lineage/forensics, not current truth;
- `not_applicable` — validation is not meaningful for the record type.

A `validated` state with no evidence reference is invalid.

## Rights rules

Rights metadata is intentionally fail-closed with respect to knowledge.

### Unknown rights

When `rights.status = unknown`:

- `rights_state_id = null`;
- `license_id = null`;
- `ai_ml_training_permission = unknown`.

Unknown rights cannot be upgraded into a permission by omission or default.

### Known rights

When `rights.status = known`, an authoritative `rights_state_id` is required. OH-M05 can transport known rights state, but it does **not** validate derivative rights inheritance; that remains `OH-M07`.

## Provenance rules

Every envelope records:

- source class (`runtime`, `import`, `archive`, `manual`);
- stable source reference;
- observation/ingestion method;
- observation timestamp.

The provenance block describes how the envelope was created. It does not prove the content is correct; evidence state and references perform that role.

## Machine-readable contract

Schema:

`docs/knowledge/schemas/asset-intelligence-envelope.schema.json`

Semantic reference implementation:

`packages/audio-analysis/python/metadata_envelope.py`

Tests:

`packages/audio-analysis/python/test_metadata_envelope.py`

The JSON Schema defines the portable shape. Python semantic validation enforces cross-field rules that must also be enforced by future Backend/domain implementations.

## Acceptance conditions

OH-M05 v1 passes when CI proves:

1. a valid original asset can be represented with explicit unknown rights;
2. unknown rights cannot silently grant AI/ML training permission;
3. derived/render/export/package assets require parent lineage;
4. duplicate parent IDs are rejected;
5. an OH-M02 measurement-derived candidate cannot travel without its supporting OH-M04 measurement;
6. OH-M02 candidate severity/cause cannot be promoted during transport;
7. validated evidence requires an evidence reference;
8. OH-M04 measurement records preserve the no-interpretation boundary;
9. invalid SHA-256 asset identity is rejected;
10. the machine-readable schema is valid JSON.

## Scope boundary

OH-M05 v1 does not claim:

- database persistence is implemented;
- asset replacement invalidation is implemented;
- rights inheritance is validated;
- release manifests are complete;
- product/customer delivery state is certified;
- OH-M04 or OH-M02 analysis is automatically run on upload.

Those are runtime integration gates built on top of this domain contract.

## Next dependency

With OH-M04, OH-M02, and OH-M05 in place, `OH-M03` can create persistent golden audio fixtures whose files, hashes, expected measurements, expected candidate signals, lineage, and evidence refs are represented with the same canonical metadata model.
