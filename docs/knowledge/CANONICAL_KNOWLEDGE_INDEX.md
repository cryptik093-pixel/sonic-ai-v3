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
- `docs/knowledge/metadata/METADATA_PACKAGING_LINEAGE_V1.md`
- `docs/knowledge/strategy/SONIC_AI_STRATEGY_LINEAGE_2026.md`

These documents are normalized derivatives. They do not replace the immutable archived originals; they make those originals operationally useful to Sonic AI V3.