# Sonic AI V3 Documentation System

**Documentation standard:** evidence-first, runtime-aware, versioned, and retrieval-safe  
**Current phase:** Phase 2 - Runtime Hardening  
**Canonical branch for this normalization pass:** `docs/omega-house-knowledge-archive-2026-09-04`

This directory is the documentation control plane for Sonic AI V3. It separates executable truth, normative doctrine, operational protocols, current architecture evidence, planning material, and historical source archives so that documentation can support the runtime without overstating it.

## Authority order

When two documents disagree, use this order unless an ADR explicitly changes it:

1. **Validated runtime evidence** - tests, fixtures, schemas, API behavior, reproducible outputs.
2. **Current architecture contracts** - canonical interfaces, domain models, event contracts, permissions.
3. **Omega House Production Doctrine** - normative production and decision principles.
4. **Operating-system protocols** - collaboration, documentation, commerce, and evidence handling.
5. **Current audits and readiness reports** - dated observations, never timeless truth.
6. **Planning/backlog documents** - intended work, not implementation evidence.
7. **Historical strategy, investor, marketing, and simulation material** - context only unless revalidated.

Documentation never upgrades a runtime capability to `validated` by assertion.

## Directory map

| Path | Purpose | Authority |
|---|---|---|
| `docs/architecture/` | Current-state architecture and reconciliation evidence | high when dated/current |
| `docs/production/` | Production specifications and source-to-asset systems | normative |
| `docs/knowledge/` | Canonical machine-readable knowledge and retrieval surfaces | governed |
| `docs/operating-system/` | Human-AI collaboration and operating protocols | normative operational |
| `docs/planning/` | Backlogs, milestones, implementation plans | proposed/in-progress |
| `docs/rfc/` | Design proposals requiring explicit acceptance | proposed/accepted by status |
| `docs/audits/` | Dated audits, normalization reports, and evidence reconciliation | evidence |
| `docs/knowledge/archive/` | Immutable historical source packages | provenance only |

## Knowledge classes

Every durable knowledge document should declare one class:

- `doctrine` - normative Omega House production principle.
- `architecture` - system boundary, contract, or implementation model.
- `runtime-evidence` - reproducible proof of current behavior.
- `curriculum` - teaching/assessment structure derived from doctrine.
- `operating-protocol` - collaboration, documentation, or commerce protocol.
- `metadata-contract` - schema, vocabulary, lineage, rights, QC, or packaging contract.
- `strategy-historical` - superseded or historical strategy/business context.
- `audit` - dated observation and reconciliation.

## Evidence states

Use exactly these evidence states in documentation and runtime-adjacent records:

- `PROVEN` - reproducible evidence exists.
- `SUPPORTED` - coherent and substantially evidenced, but at least one empirical check remains.
- `PROPOSED` - designed but not implemented and verified.
- `UNCERTIFIED` - relevant work may exist, but the complete acceptance gate remains open.

For engineering task status, use: `planned`, `in-progress`, `implemented`, `blocked`, `validated`.

`implemented` and `validated` are not synonyms.

## Phase 2 rule

Phase 1 doctrine is preserved. Phase 2 aligns runtime behavior to that doctrine. If implementation reveals ambiguity or a necessary change, create an ADR or versioned Phase 2 addendum; do not silently rewrite archived source material.

## Required traceability

Applicable doctrine requirements should resolve through this chain:

```text
SOURCE -> REQUIREMENT ID -> MODULE OWNER -> IMPLEMENTATION REF -> TEST/EVIDENCE -> STATUS -> DECISION/ADDENDUM
```

The primary Phase 2 requirement register lives at:

`docs/knowledge/requirements/PHASE_2_REQUIREMENT_REGISTER.md`

The historical source archive is indexed at:

`docs/knowledge/archive/omega-house-curriculum/2026-09-04/`

## Naming standard

New canonical files use stable uppercase semantic names for major specifications and registries, with explicit versions where the artifact is versioned. Dated audits use ISO dates.

Examples:

- `OMEGA_HOUSE_PRODUCTION_DOCTRINE_CANONICAL_V1.md`
- `PHASE_2_REQUIREMENT_REGISTER.md`
- `DOCUMENTATION_NORMALIZATION_AUDIT_2026-09-04.md`

Avoid filenames such as `final-final`, numbered duplicate suffixes, ambiguous `status` files without dates, and names that imply current truth when the content is historical.
