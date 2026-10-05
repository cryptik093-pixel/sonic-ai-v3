# Sonic AI V3 Documentation Index

**Canonical repository:** `cryptik093-pixel/sonic-ai-v3`
**Canonical branch:** `main`
**Current runtime overview:** [Sonic AI V3 README](../README.md)
**Current-state audit:** [Current-State Audit](architecture/current-state-audit.md)

## Authority order

When documents disagree, use this order:

1. Checked source, schemas, configuration and observed runtime behavior.
2. Reproducible tests and output evidence for the exact behaviors they exercise.
3. The dated current-state audit, refreshed after material runtime changes.
4. Versioned production, metadata and security contracts for normative constraints.
5. Dated implementation/status reports for their stated observation window.
6. Planning documents and strategy as proposed work, not implementation proof.
7. Archived audits and legacy root reports as historical evidence only.

A document cannot promote a proposed capability to implemented or validated by assertion. Legal rights and commercial release readiness require their own evidence.

## Directory map

| Path | Role |
| --- | --- |
| `architecture/` | Current runtime boundaries and architecture contracts |
| `production/` | Omega House production pipeline doctrine |
| `knowledge/` | Requirements, metadata, lineage, curriculum and strategy |
| `operating-system/` | Documentation, collaboration and commerce protocols |
| `planning/` | Proposed or in-progress work |
| `rfc/` | Explicitly versioned design proposals |
| `audits/` | Dated evidence reconciliation |
| `status/` | Dated delivery evidence and historical reports |

## Current implementation records

- [Current-State Audit](architecture/current-state-audit.md) — local workbench runtime, API and MCP contracts, data boundary and limitations.
- [Producer Brief Intelligence delivery record](status/SONIC_PRODUCER_BRIEF_INTELLIGENCE_2026-09-23.md) — producer prompt → preview → MIDI → lineage and feedback tests.
- [Metadata, Packaging & Provenance Lineage V1](knowledge/metadata/METADATA_PACKAGING_LINEAGE_V1.md) — requirements informing asset identity, provenance and rights boundaries.
- [Production Workbench baseline report](status/SONIC_WORKBENCH_EPIC_REPORT.md) — delivery evidence observed on 2026-09-22; its 0.5 baseline predates the 0.6 producer-intelligence change.

## Historical reports

Root-level migration aliases point to preserved historical reports under `status/archive/legacy-root/`. Read those files only as historical evidence. Current implementation truth comes from the source and tests on the canonical repository branch, not a title containing “final”, “complete” or “production ready”.
