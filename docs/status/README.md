# Sonic AI V3 Status and Evidence Index

**Authority:** lifecycle index for dated implementation, runtime and historical reports.

## Current-state rule

A status report describes its stated observation window. It does not become timeless runtime truth because its filename contains `FINAL`, `COMPLETION`, `READINESS`, `LAUNCH` or `VALIDATION`. Revalidate it after a material source or runtime change.

## Current reports

- `SONIC_PRODUCER_BRIEF_INTELLIGENCE_2026-09-23.md` — current feature implementation evidence for the 0.6 prompt-to-MIDI, deterministic brief compiler, saved feedback continuity, composition lineage and MCP contracts.
- `SONIC_WORKBENCH_EPIC_REPORT.md` — 2026-09-22 baseline for the 0.5 workbench epic; historical after the 0.6 feature.
- Other dated reports in this directory record their original commerce, lifecycle or runtime context and are not product certification.

## Legacy root migration

Historical root-level reports are preserved in `archive/legacy-root/`. Their root paths are compatibility notices, not active status documents. See that folder's `MIGRATION_MAP.md`.

## Required metadata for new reports

```yaml
document_id: SAV3-STATUS-...
observed_at: <ISO-8601>
commit_scope: <commit/ref>
lifecycle: current|superseded|historical
claim_state: PROVEN|SUPPORTED|PROPOSED
supersedes: <document IDs if applicable>
evidence_refs:
  - <tests/runs/fixtures/logs>
```
