# Gate C — Doctrine-to-Runtime Evidence Binding

**Gate:** C  
**Phase:** Sonic AI V3 Runtime Hardening  
**State:** LOCKED FOR RECONCILIATION  
**Evidence rule:** implementation presence is not equivalent to validation.

## 1. Repository/runtime reconciliation

The current canonical `main` lineage represented by the documentation branch contains a monorepo/bootstrap skeleton, not the full FastAPI/Next.js runtime described in some later operational notes. `docs/architecture/current-state-audit.md` therefore remains the strongest repository-grounded statement for `main`: runtime services are not present there.

A separate repository branch, `tier5/gate-2-durable-ingestion`, contains concrete durable event-ingestion implementation:

- `apps/api/event_store.py`
- `apps/api/events_router.py`
- `apps/api/test_event_store.py`
- `apps/api/TIER_5_GATE_2_INTEGRATION.md`

Branch head observed during Gate C:

`291c57ce0d3e34dcf3e8e47b76f286d90537dfb3`

That implementation provides a SQLite-backed `EventStore`, event-id uniqueness/idempotency, retrieval, count, and indexes by event type/time and entity. The accompanying tests exercise persistence/readback and duplicate-event rejection.

No GitHub Actions workflow run is recorded for that branch-head commit. Therefore these artifacts are classified as **IMPLEMENTED / UNVALIDATED**, not `validated`.

## 2. Evidence packets

### OH-M14 — repository/runtime reconciliation

```yaml
control_id: OH-M14
status: validated
scope: repository topology and branch reconciliation only
implementation_ref:
  canonical_ref: main
  canonical_runtime_state: bootstrap skeleton
  implementation_branch: tier5/gate-2-durable-ingestion
  implementation_commit: 291c57ce0d3e34dcf3e8e47b76f286d90537dfb3
evidence_refs:
  - docs/architecture/current-state-audit.md
  - apps/api/event_store.py@tier5/gate-2-durable-ingestion
  - apps/api/test_event_store.py@tier5/gate-2-durable-ingestion
observed_result: runtime implementation exists off-main; main does not yet contain that implementation
acceptance_result: pass for reconciliation, fail for canonical-runtime convergence
```

`validated` here means the discrepancy itself has been reproducibly established. It does **not** mean the Sonic runtime is validated.

### OH-DR-COM-002 — joinable commercial events

```yaml
requirement_id: OH-DR-COM-002
status: implemented
implementation_ref:
  branch: tier5/gate-2-durable-ingestion
  commit: 291c57ce0d3e34dcf3e8e47b76f286d90537dfb3
  repo_path: apps/api/event_store.py
  symbol_or_contract: EventStore
acceptance:
  test_ref: apps/api/test_event_store.py
  expected_result: events persist, round-trip, and reject duplicate event_id values
observed:
  ci_run: none recorded for branch head
  result: implementation/test code present; automated execution evidence absent
limitations:
  - not merged to main
  - no recorded CI run for branch head
  - current fixture proves order event persistence/idempotency, not full release/version/campaign/action/payout joins
```

### OH-DR-LINEAGE-005 — downstream invalidation events

```yaml
requirement_id: OH-DR-LINEAGE-005
status: planned
reason: durable event persistence exists on the Tier 5 branch, but no inspected invalidation-event contract or downstream lineage test currently proves this doctrine requirement
```

### OH-DR-AI-006 — auditable agent/tool actions

```yaml
requirement_id: OH-DR-AI-006
status: planned
reason: no inspected canonical-branch implementation currently proves permission matrices, audit logging, timeout policy, or idempotent agent/tool execution
```

## 3. Gate C status model

| Evidence class | Meaning |
|---|---|
| `validated` | reproducible acceptance evidence exists for the exact scoped claim |
| `implemented` | code and/or tests exist, but acceptance execution evidence is incomplete |
| `in-progress` | partial implementation or branch reconciliation exists |
| `planned` | doctrine accepted; implementation evidence absent |
| `blocked` | dependency prevents evidence completion |

## 4. Locked conclusions

1. `OH-M14` is **validated for repository reconciliation**: the canonical branch/runtime divergence is now explicitly documented.
2. Tier 5 Gate 2 durable ingestion is **implemented but unvalidated** because no recorded CI execution is attached to its branch-head commit.
3. No audio doctrine requirement is promoted to `validated` merely from curriculum or documentation.
4. Gate C requires future runtime convergence to `main` plus reproducible tests/fixtures before broader validation states are granted.
5. The next evidence priorities remain `OH-M04` measurement profile, `OH-M02` defect taxonomy, `OH-M05` canonical metadata schema, and `OH-M03` golden audio fixtures.

## 5. Merge criterion

The documentation normalization PR may merge without pretending the runtime is complete. After merge, runtime work should either:

- merge/reconcile proven implementation branches into `main`, or
- explicitly supersede them with stronger implementations carrying equivalent or better acceptance evidence.

Gate C is therefore **locked as an evidence-governance gate**, while runtime validation remains an engineering program rather than a documentation claim.
