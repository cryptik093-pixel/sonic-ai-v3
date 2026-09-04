# Sonic AI V3 Status & Historical Evidence

**Authority:** lifecycle index for status, readiness, audit, failure, and milestone reports.

## Current-state rule

No document in `docs/status/archive/` is authoritative for the present runtime merely because its title contains `FINAL`, `COMPLETION`, `READINESS`, `LAUNCH`, or `VALIDATION`.

Current implementation truth is established in this order:

1. repository state on the canonical branch;
2. reproducible runtime behavior;
3. automated tests and CI evidence;
4. current evidence packets in `docs/knowledge/requirements/`;
5. dated audits/status reports;
6. historical strategy or narrative documents.

## Legacy root migration

Historical root-level reports are preserved under:

`docs/status/archive/legacy-root/`

The original root paths remain as compatibility aliases only. Their content has been replaced by a migration notice so old links do not silently present historical assertions as current truth.

## Lifecycle metadata

A new status report should include:

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

## Phase 2

Gate B is considered structurally complete when legacy root reports are archived with compatibility aliases and indexed here. Runtime claims still require Gate C evidence binding.
