# Omega House Contracts — v1 design

**Contract state:** Proposed adapter interface. Current `forge_core` includes an offline implementation only. Route names below are **not currently verified existing API routes**. Codex must confirm legacy routes before adding them.

## Shared envelope

Every persistent command requires: `request_id` (UUID for deduplication), `actor_id`, `tenant_id` or local workspace owner, `resource_id`, `expected_revision`, approved action scope, and correlation ID. The server derives identity from verified auth; a caller-supplied actor alone has **no authority**. Every response includes `status`, `revision`, `evidence_refs`, `errors`, and an opaque download or job reference when applicable.

Events use `contracts/omega-workflow-event.schema.json` and are append-only when deployed. No event bus is implemented by this package.

## FORGE — integration surface (design)

| Operation | Example route (not deployed) | Requirement |
| --- | --- | --- |
| Upload | `POST /workbench/api/forge/packs` | Auth, ZIP body, workspace owner, max size and archive validation; accepted request ID |
| Read status | `GET /workbench/api/forge/packs/{id}` | Owner/tenant authorization, current manifest revision |
| Analyze | `POST /workbench/api/forge/packs/{id}/analysis` | Measured numerical/tonal results only; versioned report; may return null/unknown |
| Review | `PATCH /workbench/api/forge/packs/{id}/review` | Expected revision + explicit per-asset edit/approval; zero partial writes |
| Export | `POST /workbench/api/forge/packs/{id}/export` | Approved revision, idempotency, checksum verification, immutable artifact |
| Retrieve | `GET /workbench/api/forge/exports/{id}` | Authorized bounded download, manifest and hash |
| Shopify draft | `POST /workbench/api/forge/packs/{id}/shopify-draft` | Explicit rights clearance and actor approval; offline CSV unless a live authorized draft adapter is independently verified |

### Asset schema

| Field | Contract |
| --- | --- |
| `asset_id` | Stable ID derived from original relative path + original content SHA, not renamed filename |
| `original_path` / `proposed_path` | ZIP member path, POSIX relative, Unicode NFC, case-insensitive collision validation |
| `sha256` | SHA-256 bytes; verify again at export |
| `asset_type` | Audio, MIDI, preset, artwork, document. Creative sub-taxonomy comes from explicit operator labels or measured evidence |
| `bpm` / `key` | `{value, confidence, method, reason}`; unknown means `value=null` and explicit reason |
| `rights_state` | `unverified | cleared | restricted`; user review required for commerce, upload does not imply ownership |
| `review_state` | `pending | approved` in offline core; persistent implementation adds actor/revision/audit |
| `source_zip_sha256` | Hash of unchanged original ZIP; changes invalidate prior manifest approvals |

### Analysis quality gate

- **BPM:** onset envelope + autocorrelation or defensible DSP alternative; candidates include half/double tempo; periodicity, length, transient density and ambiguity inform confidence. A detected BPM is not a fact until validated. Nonrhythmic material returns null.
- **Key:** pitched/harmonic evidence plus pitch-class distribution; silence, noisy percussion and weak/unresolved tonal cues return null. Explicit artist/operator key override is labeled `operator_override`, not measured certainty.
- Store analyzer algorithm version, signal selection, effective frame count, sample rate, result method, candidate distribution/confidence and failures. Do not infer ownership or rights.
- Synthetic clicks/chords test numerical behavior, while curated licensed real-world clips establish practical error tolerances. Never use invented accuracy percentages.

## ACQUIRE — design contract

`lead.proposed -> lead.qualified -> outreach.proposed -> outreach.reviewed -> outreach.authorized_sent -> response.observed -> sale.observed`.

Lead stores platform handle, public source URL, genre/offer matching evidence, acquisition timestamp, consent/contact-channel eligibility and duplicate key; no scraped private profiles. Human review gates the outbound message. Shopify order/refund measurement includes shop ID, currency, actual timestamps and explicit attribution basis. `sale.observed` is not equivalent to `sale.caused_by_campaign`; missing attribution remains null.

## SIGNAL — design contract

`asset.approved -> content.draft -> content.reviewed -> content.scheduled -> content.published -> outcome.measured`.

Only use approved rights-bearing assets. A content plan stores platform/channel, copy, media IDs, content hash, license disposition, scheduled time and necessary human approval. Publishing and ad spend are disabled until authenticated external adapters and explicit operator authorization have been verified. Metrics include platform-origin timestamps and event IDs, not estimates from follower counts.

## Omega House OS handoff model

A request goes from a user-authenticated surface to a policy/permissions check, then a typed versioned tool call into Sonic. Sonic returns immutable observation artifacts and their hashes. Sonic Intelligence may score options by referencing those observations. Omega OS stores action proposals/decisions separately from completed outcomes. Tribe receives only reviewed, authorized artifact references. Shopify remains the only authoritative source for order commerce facts.

Live adapter and tenant isolation are future work. The present core does not grant those permissions or make those network calls.
