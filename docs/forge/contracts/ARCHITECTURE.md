# Omega House Engineering Architecture — Approved Foundation

**Status:** integration design with a tested local Forge core. No claim of active inter-system deployment.

## System boundaries

```text
Tribal Network — creative workspace, identity/permissions, asset review UI
      | verified actor + access token + bounded artifact refs (PLANNED)
      v
Omega House OS — orchestration, request routing, approvals, durable workflow state
      | authenticated commands/events via versioned contract (PLANNED)
      +------------------------------+
      |                              |
      v                              v
Sonic AI V3 — production      Sonic Intelligence — evidence-based
workbench, analysis,          decision records / recommendations,
packaging, local files        without fabricating measurements
      |                              |
      +------------------------------+
      |
      v
Shopify — product/order commerce truth, draft import and license workflows
      ^    (any live store write requires verified auth + approval)
      |
OMEGA ACQUIRE <> measured storefront signals <> OMEGA SIGNAL
```

The small `forge_core` overlay is **offline, local and standard-library**. It does not claim the OS/Tribe/Shopify/MCP services are currently connected.

## Canonical ownership and engineering constraints

| Domain | System of record | Rules |
| --- | --- | --- |
| Audio and MIDI source files | Sonic local workspace / authorized source storage | Content SHA, no destructive edits, explicit owner |
| Asset metadata and lineage | Sonic for generated analysis; Tribal/OS integration only after contract | Immutable source hash, versioned manifest, validated transforms |
| User identity, Tribe memberships and permissions | Live Tribal service | Do not transpose unmerged Supabase model into existing D1 by assumption |
| Workflow execution/approvals | Omega House OS | Actor/tenant/resource/revision/result in audit |
| Music inference | Sonic deterministic DSP first | Unknown when unmeasurable, evidence and confidence required |
| Commerce records | Shopify | Merchant/store scoped APIs, refunds separated, no invented attribution |
| License issuance | Flagship Beats Licensing authority | Never infer rights/entitlement from copied ZIP or Shopify product text |
| Commercial intelligence | Sonic Intelligence | Derived facts keep source IDs and measurement lineage |

## Workflow execution model

`submitted -> validating -> inventoried -> awaiting_review -> approved -> exporting -> exported`

Failure transitions may occur from any state to `failed` with reproducible code and retained inputs. `rejected` is a separately audited operator decision. `approved` must reference manifest revision and actor, not a global boolean. Re-running an approved command must be idempotent under an explicit request ID; outputs use create-if-absent semantics and content hashes. An updated source hash invalidates prior analysis and approvals.

Review-stage permissions and persisted transitions must be added via the existing Sonic service; offline `forge_core` provides only explicit in-memory transformations and no multiuser persistence. Do not conflate the two.

## Deployment boundaries

- **Local alpha:** existing Windows Sonic workbench with loopback authentication, existing API routes, SQLite; isolated files and no public exposure.
- **Hosted staging (later):** authenticated owner/tenant, object storage with signed URLs, queue worker, audit/events, strict rate/upload caps, test store only. Evaluate against existing approved infrastructure before adding anything.
- **Production:** only after deployed smoke tests, real tenant isolation, rights approval, migration/rollback, observable queues, validated Shopify OAuth/webhooks, and operator permission gates.

## Engineering phases

- P0.1 — audit canonical `sonic-ai-v3` repository and dependency graph; record SHA, baseline tests.
- P0.2 — merge *additive* `forge_core`, verify test suite; ensure host/provenance compatibility.
- P0.3 — add real file decoding, tempo onset analysis, tonal pitch-class analysis, confidence thresholds, curated validation fixtures and 'undetermined' outcomes.
- P0.4 — authenticated upload/import, job state, review revisions and Workbench batch editor.
- P0.5 — exports, owner/download authorization, negative tests, smoke run with real approved pack.
- P1 — ACQUIRE integration recovery from existing stacked OS PRs and Shopify read-only proof.
- P2 — SIGNAL content pipeline, measured attribution and channel publishing approvals.

## Measurable acceptance targets

Forge: a nested licensed test pack can be uploaded, inventoried, review-edited, exported and byte-verified without changing the original. 100% test coverage for specified security adversarial cases in release gates (not blanket line coverage). Audio inference passes curated truth-labeled tolerances **defined from representative test assets**, otherwise return unknown. Preserve all source checksums and exported manifest hashes. Explicitly report unknown/ambiguous instruments and near-boundary analyses.

Acquire: evidence-based qualified lead, offer and store-scoped outcome records, no auto-send by default, sales attribution not claimed unless actually measurable. Initial business target: first $500 in 14 days, tracked independently of implementation status.

Signal: approved outputs per platform, provenance and publication record if authorized, no falsely attributed view/conversion metrics.
