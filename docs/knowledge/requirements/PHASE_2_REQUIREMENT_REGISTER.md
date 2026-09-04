# Sonic AI V3 Phase 2 Requirement Register

**Register ID:** `SAV3-P2-REQ-001`  
**Phase:** Runtime Hardening  
**Source doctrine:** `docs/knowledge/doctrine/OMEGA_HOUSE_PRODUCTION_DOCTRINE_CANONICAL_V1.md`  
**Status rule:** documentation may prove a specification exists; only runtime/test evidence can validate implementation.

## Status semantics

- `planned` - requirement accepted; implementation evidence not yet established.
- `in-progress` - relevant implementation exists or is actively being reconciled; acceptance evidence incomplete.
- `implemented` - implementation is present, but full acceptance evidence is incomplete.
- `blocked` - a known dependency prevents completion.
- `validated` - acceptance evidence is reproducible and linked.

## Phase 2 register

| Requirement | Principle | Primary owner | Spec state | Runtime status | Required proof |
|---|---|---|---|---|---|
| OH-DR-TRUTH-001 | Separate observation, interpretation, action, outcome | Intelligence Core | PROVEN doctrine | in-progress | OH-M02 lifecycle boundary + structured response contract/tests |
| OH-DR-EVID-001 | Evidence state travels with durable conclusions | Intelligence Core / Memory | PROVEN doctrine | in-progress | persisted evidence-state field + retrieval test |
| OH-DR-EVID-003 | Runtime outranks documentation claims | Backend / CI | PROVEN doctrine | in-progress | boot/integration test evidence and current health map |
| OH-DR-GATE-001 | Each stage has a Pass Gate | Pipelines | PROVEN doctrine | planned | pipeline state machine + transition tests |
| OH-DR-GATE-002 | Release requires a Ship Gate | Pipelines / Product | PROVEN doctrine | planned | release checklist encoded as contract/test |
| OH-DR-LISTEN-001 | Material comparisons are level controlled | Audio Analyzer / Evaluation | PROVEN doctrine | planned | controlled A/B fixture and scoring test |
| OH-DR-LISTEN-003 | Mono checks evaluate hierarchy preservation | Audio Analyzer | PROVEN doctrine | planned | stereo/mono fixture + deterministic metrics |
| OH-DR-RESCUE-001 | Rank dominant failures before processing | Intelligence Core | PROVEN doctrine | in-progress | validated OH-M02 defect vocabulary + prioritization policy/fixture |
| OH-DR-RESCUE-002 | Gain/hierarchy precede downstream decisions | Intelligence Core | PROVEN doctrine | planned | ordered recommendation policy test |
| OH-DR-RESCUE-003 | Resolve kick/808 ownership before bus dynamics | Audio Analyzer / Intelligence Core | PROVEN doctrine | planned | low-end role fixture + policy test |
| OH-DR-RESCUE-005 | Translation failure triggers targeted rollback | Intelligence Core / Pipelines | PROVEN doctrine | planned | failure-to-stage mapping + rollback test |
| OH-DR-RESCUE-007 | Preserve a compact rescue record | Backend / Memory | PROVEN doctrine | planned | rescue-record schema + persistence/retrieval test |
| OH-DR-LOWEND-001 | Kick and 808 roles are deliberately assigned | Audio Analyzer | PROVEN doctrine | planned | role classification fixture + confidence output |
| OH-DR-LOWEND-005 | Monitoring limits affect confidence | Intelligence Core | PROVEN doctrine | in-progress | OH-M02 confidence/severity separation + uncertainty contract |
| OH-DR-MASK-001 | Diagnose target/masker pairs | Audio Analyzer | PROVEN doctrine | planned | masking-pair output schema + golden fixtures |
| OH-DR-MASK-004 | Recommendations name competing objects, not only bands | Intelligence Core | PROVEN doctrine | planned | recommendation contract + regression tests |
| OH-DR-STEREO-001 | Preserve center authority | Audio Analyzer | PROVEN doctrine | in-progress | validated OH-M04 correlation baseline + OH-M02 negative-correlation candidate + mid/side/mono fixtures |
| OH-DR-DYN-002 | Distinguish clipping, limiting, loudness, true peak | Audio Analyzer | PROVEN doctrine | in-progress | validated OH-M04 amplitude baseline + OH-M02 non-causal full-scale signal; standards-compliant LUFS/true-peak proof still required |
| OH-DR-TRANS-001 | Consequential translation uses multiple playback contexts | Evaluation / Frontend | PROVEN doctrine | planned | translation-test workflow + evidence record |
| OH-DR-EXPORT-001 | Render configuration is evidence | Metadata / Backend | PROVEN doctrine | planned | export metadata schema + ingestion test |
| OH-DR-EXPORT-002 | Rendered deliverable is verified independently | Pipelines | PROVEN doctrine | planned | post-render verification step + fixture |
| OH-DR-LINEAGE-001 | Every production has a stable production ID | Backend | PROVEN specification | in-progress | uniqueness/persistence tests |
| OH-DR-LINEAGE-002 | Derivatives retain source relationship | Backend / Pipelines | PROVEN specification | in-progress | lineage graph test across asset derivation |
| OH-DR-LINEAGE-003 | Presets/chains are durable reproducibility assets | Metadata / Asset model | PROVEN specification | planned | asset-class schema + association test |
| OH-DR-LINEAGE-004 | MIDI preserves source performance intent | MIDI Engine | PROVEN doctrine | in-progress | MIDI round-trip / fixture comparison |
| OH-DR-LINEAGE-005 | Replacement defines downstream invalidation | Backend / Events | PROVEN doctrine | planned | invalidation event contract + tests |
| OH-DR-LINEAGE-006 | Final assets/manifests support hashes | Metadata / Pipelines | SUPPORTED | planned | SHA-256 manifest generation + verification |
| OH-DR-LINEAGE-007 | Rights/license inheritance follows derivatives | Metadata / Product | SUPPORTED | planned | rights schema + derivative propagation tests |
| OH-DR-AI-001 | Deterministic facts are separate from interpretation | Audio Analyzer / Intelligence Core | PROVEN doctrine | in-progress | validated OH-M04 observation boundary + validated OH-M02 candidate/diagnosis boundary + typed integration contract |
| OH-DR-AI-002 | Recommendations expose evidence/rule/uncertainty | Intelligence Core / Frontend | PROVEN doctrine | planned | explainability payload + UI acceptance test |
| OH-DR-AI-003 | Producer DNA does not become universal doctrine | Artist DNA / Memory | PROVEN doctrine | planned | scoped memory policy + conflict test |
| OH-DR-AI-004 | Durable memory requires provenance/confidence | Memory | SUPPORTED architecture | in-progress | memory schema + provenance persistence test |
| OH-DR-AI-005 | Contradictions are resolved or preserved | Memory | SUPPORTED architecture | planned | contradiction policy + regression test |
| OH-DR-AI-006 | Agent/tool actions are permissioned and auditable | Agents / MCP | SUPPORTED architecture | planned | permission matrix + audit log + timeout/idempotency tests |
| OH-DR-COM-001 | Commercial outcome is not proof of audio quality | Intelligence Core / Analytics | PROVEN doctrine | planned | data model separation + evaluation rule |
| OH-DR-COM-002 | Release/version/campaign/action/payout are joinable | Events / Commerce | PROVEN operating protocol | in-progress | shared IDs + event schema + attribution fixture |
| OH-DR-COM-003 | Correlation is not presented as causality | Intelligence Core | PROVEN doctrine | planned | recommendation-language guardrail tests |
| OH-DR-COM-004 | Outcome produces successor learning objective | Intelligence Core / Memory | PROVEN operating protocol | in-progress | learning event + successor-intent persistence test |

## Missing-control register from the 2026 full-system audit

| Audit ID | Contract to build | Sonic owner | Phase 2 disposition |
|---|---|---|---|
| OH-M01 | critical-listening calibration | Evaluation / Curriculum | design fixture contract |
| OH-M02 | defect taxonomy and severity | Audio Analyzer / Metadata | **validated v1 candidate-signal baseline** — evidence `evidence/OH-M02-v1.yaml` |
| OH-M03 | golden audio fixture set | Evaluation / CI | queued after M05 - validation substrate |
| OH-M04 | measurement profile | Audio Analyzer | **validated v1 deterministic baseline** — evidence `evidence/OH-M04-v1.yaml` |
| OH-M05 | canonical metadata schema | Metadata / Backend | **next execution gate** — durable domain/evidence envelope |
| OH-M06 | content-addressed integrity | Pipelines | implement hashes + invalidation |
| OH-M07 | rights/license inheritance | Metadata / Product | implement before publication automation |
| OH-M08 | asset-class tolerances | Pipelines / QC | encode per asset class |
| OH-M09 | rubric/assessor calibration | Curriculum | Phase 3/4 educational readiness |
| OH-M10 | accessibility | Frontend / LMS | public enrollment gate |
| OH-M11 | failure recovery/rollback | Backend / Pipelines | runtime-hardening priority |
| OH-M12 | memory governance | Memory | runtime-hardening priority |
| OH-M13 | agent/tool permissions | Agents / MCP | autonomy gate |
| OH-M14 | repository/runtime reconciliation | Repo / CI | Gate B/C baseline locked on `main`; implementation-branch convergence remains runtime work |
| OH-M15 | commerce attribution | Events / Analytics | intelligence-learning gate |
| OH-M16 | faculty operations | Curriculum | cohort-delivery gate |

## Validated evidence

### OH-M04 — deterministic measurement baseline

- Semantics: `docs/knowledge/requirements/OH_M04_MEASUREMENT_PROFILE_V1.md`
- Schema: `docs/knowledge/schemas/audio-measurement-profile.schema.json`
- Implementation: `packages/audio-analysis/python/sonic_measurement.py`
- Tests: `packages/audio-analysis/python/test_sonic_measurement.py`
- Evidence: `docs/knowledge/requirements/evidence/OH-M04-v1.yaml`
- CI evidence: run `33897033199` / #79 / success.

OH-M04 intentionally leaves LUFS and true peak unavailable. `OH-DR-DYN-002` therefore remains `in-progress`.

### OH-M02 — defect taxonomy baseline

- Semantics: `docs/knowledge/requirements/OH_M02_DEFECT_TAXONOMY_V1.md`
- Schema: `docs/knowledge/schemas/audio-defect-record.schema.json`
- Implementation: `packages/audio-analysis/python/defect_taxonomy.py`
- Tests: `packages/audio-analysis/python/test_defect_taxonomy.py`
- Evidence: `docs/knowledge/requirements/evidence/OH-M02-v1.yaml`
- Validated implementation/test commit: `5a681d5b560cd8cecaa0da711dc2c4cc0e3915f7`
- CI evidence: run `33897530294` / #85 / success.

OH-M02 validates conservative candidate-signal semantics only. It does not validate automatic confirmation, severity scoring, cause diagnosis or repair.

## Required evidence packet

A requirement can move to `validated` only when its evidence packet includes:

```yaml
requirement_id: OH-DR-...
implementation_ref:
  repo_path: <path>
  symbol_or_contract: <name>
acceptance:
  test_ref: <test path or workflow>
  fixture_ref: <fixture/hash if applicable>
  expected_result: <concise invariant>
observed:
  commit_sha: <sha>
  run_id: <CI/runtime evidence>
  result: pass
validated_at: <ISO-8601>
validator: <human or automation identity>
notes: <limitations or unresolved defects>
```

## Immediate Phase 2 proof order

1. `OH-M14` repository/runtime reconciliation baseline - locked through Gate B/C governance; continue branch convergence as runtime work.
2. `OH-M04` deterministic measurement profile - **validated v1 baseline**.
3. `OH-M02` shared defect taxonomy - **validated v1 baseline**.
4. `OH-M05` canonical metadata schema - **next execution gate**.
5. `OH-M03` golden fixtures.
6. Validate the first vertical slice: **Upload -> Analyze -> Normalize -> Intelligence -> Memory -> Retrieve**.
7. Add lineage, MIDI, agent permissions, and commerce-learning contracts after the vertical slice is reproducible.

This register is intentionally conservative. Existing code is not promoted to `validated` until evidence is attached.
