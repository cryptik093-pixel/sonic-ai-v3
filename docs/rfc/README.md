# Sonic AI V3 RFC & Architecture Decision Standard

**Purpose:** preserve consequential Phase 2 decisions without rewriting historical doctrine or allowing implementation changes to become undocumented architecture.

Use an RFC when the decision changes a public/internal contract, crosses module boundaries, alters persistent data, changes agent permissions, changes doctrine interpretation, or creates a migration requirement.

Use a lightweight ADR when the decision is narrower but still needs durable rationale.

## Status vocabulary

- `proposed`
- `accepted`
- `implemented`
- `validated`
- `rejected`
- `superseded`

`implemented` means the change exists. `validated` means the acceptance evidence is reproducible.

## Naming

```text
RFC-0001-short-semantic-title.md
ADR-0001-short-semantic-title.md
```

Never use `final`, `new`, or numbered duplicate suffixes as lifecycle metadata.

## Required front matter

```yaml
id: RFC-0001
title: <decision title>
status: proposed
created_at: YYYY-MM-DD
authors: []
requirement_refs: []
doctrine_refs: []
affected_modules: []
supersedes: null
superseded_by: null
implementation_refs: []
evidence_refs: []
```

## Required sections

### 1. Context

Describe the observed problem, constraints, and evidence that make a decision necessary.

### 2. Decision

State the chosen behavior precisely enough to implement and test.

### 3. Invariants

List the conditions that must remain true after implementation.

### 4. Alternatives considered

Record meaningful alternatives and why they were not selected.

### 5. Data / API / event impact

Identify schema, persistence, endpoint, event, compatibility, and migration consequences.

### 6. Security / permission impact

Identify changes to credentials, data exposure, agent/tool permissions, auditability, retries, idempotency, or destructive actions.

### 7. Doctrine relationship

Reference applicable `OH-DR-*` requirements. If the decision clarifies or extends Phase 1 doctrine, identify the Phase 2 addendum rather than editing the archived source.

### 8. Implementation plan

Map modules, repo paths, migrations, rollout order, and rollback path.

### 9. Acceptance evidence

Define the exact tests, fixtures, benchmark outputs, or runtime checks required for `validated` status.

### 10. Consequences

Document positive consequences, tradeoffs, known limitations, and follow-up work.

## Decision rule

A decision is not durable merely because code was merged. If it changes the system model, its contract and rationale must remain discoverable after the implementation details move.
