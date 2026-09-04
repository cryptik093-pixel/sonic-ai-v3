# Sonic AI V3 Canonical Knowledge Index

**Knowledge system version:** 1.0  
**Phase:** Phase 2 - Runtime Hardening  
**Purpose:** define what Sonic AI may retrieve, how strongly it may trust it, and which source owns each kind of truth.

## Canonical domains

| Domain | Canonical surface | Retrieval role |
|---|---|---|
| Production doctrine | `docs/knowledge/doctrine/` | normative production reasoning |
| Production workflow | `docs/production/` | asset lineage, QC, productization |
| Curriculum | `docs/knowledge/curriculum/` | training, assessment, certification architecture |
| Requirements | `docs/knowledge/requirements/` | doctrine-to-runtime implementation traceability |
| Metadata and packaging | `docs/knowledge/metadata/` | provenance, schemas, rights, QC, packaging evidence |
| Strategy lineage | `docs/knowledge/strategy/` | historical business/product decisions, not runtime truth |
| Operating protocols | `docs/operating-system/` | collaboration, documentation, commerce control language |
| Historical archive | `docs/knowledge/archive/` | immutable source provenance |

## Authority and retrieval weights

A future knowledge service should not treat all chunks equally. Recommended default authority tiers:

| Tier | Source class | Default use |
|---|---|---|
| A | validated runtime evidence / accepted schema | answer factual current-state questions |
| B | canonical doctrine / accepted protocol | constrain recommendations and design decisions |
| C | current dated audit | describe observed state with date attached |
| D | curriculum / explanatory reference | teach, interpret, and contextualize |
| E | historical strategy / investor / marketing | lineage and business context only |
| F | simulation / speculative material | ideation only; never factual authority |

## Retrieval invariants

1. Historical projections must never be returned as current financial performance.
2. Marketing claims must never become product capability claims without runtime evidence.
3. Curriculum recommendations may teach technique but must not override deterministic measurements.
4. Artist DNA represents producer-specific tendencies; it must remain separate from universal doctrine.
5. Doctrine may constrain behavior, but a runtime feature is only `validated` after reproducible evidence exists.
6. Every durable extracted object must preserve source filename, source hash, archive ID, lifecycle, and derivation timestamp.
7. Conflicting knowledge must be surfaced as conflict, not silently merged.
8. Audio interpretation must preserve the boundary between deterministic observations and producer-facing recommendations.
9. OH-M02 candidate signals must not be retrieved or phrased as confirmed defects, severity judgments, causal diagnoses or repair instructions.

## Canonical source lineage

### Phase 1 monument

Archive: `OH-KA-2026-09-04-001`

Primary canonical source:

`Omega_House_Production_Doctrine_First_Edition.pdf`

Editable source:

`Omega_House_Production_Doctrine_First_Edition.docx`

System audit:

`Omega_House_Full_System_Audit_2026.pdf`

The duplicate suffixed doctrine PDF in the archive is byte-identical to the canonical rendered PDF and should not be separately embedded.

### Existing repo-native production specification

`docs/production/OMEGA_HOUSE_CORE_PRODUCTION_ASSET_PIPELINE_V1.0.md`

This remains the canonical source-to-asset production specification and should be linked, not duplicated, by derived knowledge objects.

### Phase 2 deterministic measurement contract — OH-M04

Semantics:

`docs/knowledge/requirements/OH_M04_MEASUREMENT_PROFILE_V1.md`

Machine-readable result shape:

`docs/knowledge/schemas/audio-measurement-profile.schema.json`

Executable reference:

`packages/audio-analysis/python/sonic_measurement.py`

Evidence:

`docs/knowledge/requirements/evidence/OH-M04-v1.yaml`

OH-M04's deterministic v1 baseline is validated. Its unavailable LUFS/true-peak fields remain unavailable rather than being approximated.

### Phase 2 defect taxonomy contract — OH-M02

Semantics:

`docs/knowledge/requirements/OH_M02_DEFECT_TAXONOMY_V1.md`

Machine-readable record shape:

`docs/knowledge/schemas/audio-defect-record.schema.json`

Executable reference:

`packages/audio-analysis/python/defect_taxonomy.py`

Evidence:

`docs/knowledge/requirements/evidence/OH-M02-v1.yaml`

OH-M02's v1 candidate-signal baseline is validated. Authority applies to its taxonomy/lifecycle semantics and three initial candidate signals only; it does not establish automatic defect confirmation, cause or severity.

## Recommended chunk metadata

```yaml
knowledge_id: OH-KNOW-<domain>-<sequence>
canonical_id: <stable document id>
source_path: <repo or archive source>
source_hash_sha256: <hash>
document_class: <class>
authority_tier: <A-F>
lifecycle: <canonical|validated|historical|superseded|draft|evidence>
phase: <phase-1|phase-2|historical>
valid_from: <ISO date>
valid_to: null
runtime_validation: <validated|not-validated|not-applicable>
module_scope: [audio-analyzer, midi-engine, artist-dna, intelligence-core, memory, backend, frontend, pipelines]
tags: []
```

## Current canonical derivatives

- `docs/knowledge/doctrine/OMEGA_HOUSE_PRODUCTION_DOCTRINE_CANONICAL_V1.md`
- `docs/knowledge/curriculum/ELITE_AUDIO_ENGINEERING_CURRICULUM_MAP_V1.md`
- `docs/knowledge/requirements/PHASE_2_REQUIREMENT_REGISTER.md`
- `docs/knowledge/requirements/OH_M04_MEASUREMENT_PROFILE_V1.md`
- `docs/knowledge/requirements/OH_M02_DEFECT_TAXONOMY_V1.md`
- `docs/knowledge/requirements/evidence/OH-M04-v1.yaml`
- `docs/knowledge/requirements/evidence/OH-M02-v1.yaml`
- `docs/knowledge/schemas/audio-measurement-profile.schema.json`
- `docs/knowledge/schemas/audio-defect-record.schema.json`
- `docs/knowledge/metadata/METADATA_PACKAGING_LINEAGE_V1.md`
- `docs/knowledge/strategy/SONIC_AI_STRATEGY_LINEAGE_2026.md`

These documents are normalized derivatives. They do not replace the immutable archived originals; they make those originals operationally useful to Sonic AI V3.
