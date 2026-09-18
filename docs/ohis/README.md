# OHIS — Omega House Intelligence System

**Status:** Foundation v1.0 (proposed)
**Owner:** Omega House / Sonic AI V3
**Scope:** Creative assets, DAW sessions, presets, chains, projects, documentation, and machine-readable producer knowledge.

## Purpose

OHIS is the canonical information architecture for the Omega House creative system. It defines how assets are identified, named, classified, routed, colored, versioned, stored, related, and eventually interpreted by Sonic AI.

OHIS is not merely a folder structure. It is an ontology and operating standard intended to create a stable bridge between:

```text
Human Creative Workflow
        ↓
DAW / Files / Projects
        ↓
OHIS Identity + Metadata + Provenance
        ↓
Sonic AI Knowledge Layer
        ↓
Analysis / Retrieval / Recommendation / Automation
```

## Core principles

1. **One canonical identity.** Every managed asset receives a stable OHIS Asset ID.
2. **Deterministic before generative.** Facts that software can calculate should be computed rather than guessed by a model.
3. **Raw is immutable.** Source material is preserved; derived work receives new versions or child identities.
4. **Color communicates topology.** DAW color is semantic, not decorative.
5. **Labels communicate role.** A label should tell a producer what an item does.
6. **Folders communicate domain.** Location provides broad categorical context.
7. **Metadata communicates detail.** Technical, musical, creative, commercial, and lineage data live above the filename.
8. **Provenance is first-class.** Derived assets retain their relationship to parents, sources, chains, projects, and releases.
9. **Human speed matters.** OHIS must reduce cognitive load rather than create administrative work.
10. **Sonic learns from evidence.** Producer preferences and creative patterns should be reconstructed from grounded activity and asset evidence.

## Canonical documents

- [`01-ontology.md`](./01-ontology.md) — entities, vocabulary, and relationships.
- [`02-naming-standard.md`](./02-naming-standard.md) — filename and ID grammar.
- [`03-color-and-routing.md`](./03-color-and-routing.md) — DAW topology/color semantics.
- [`04-filesystem-standard.md`](./04-filesystem-standard.md) — lifetime folder architecture.
- [`05-asset-metadata.md`](./05-asset-metadata.md) — canonical metadata model.
- [`06-lifecycle-and-provenance.md`](./06-lifecycle-and-provenance.md) — lifecycle, lineage, and version rules.
- [`07-sonic-integration.md`](./07-sonic-integration.md) — how Sonic AI consumes OHIS.
- [`schemas/asset.schema.json`](./schemas/asset.schema.json) — machine-readable asset contract.

## Versioning

OHIS itself is versioned independently from individual assets.

```text
OHIS v1.0
  ├── Asset IDs: permanent
  ├── Asset versions: mutable through controlled revision
  ├── Taxonomy: governed
  ├── Color semantics: governed
  └── Implementation: evolves without silently changing historical meaning
```

Breaking changes to identity, naming, color semantics, or lifecycle rules require a new OHIS major version and migration plan.
