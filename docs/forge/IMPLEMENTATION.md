# OMEGA FORGE local Workbench integration

The Forge tab extends the existing FastAPI-served `/workbench`, not a second app.
Legacy MIDI, audio analysis, import, pack, release, history and MCP routes remain.
The supplied foundation contracts in `contracts/` are retained as design/source
material; this document describes the implemented boundary.

## Authentication and ownership

The existing `WorkbenchAuth` verifies `SONIC_DESKTOP_TOKEN` (preferred) or
`SONIC_CONTROL_PLANE_TOKEN`, the loopback Host, and the allowed Origin. It supplies
the verified `local-producer` / `omega-house-studio` identity in request state.
Forge derives its composite owner/workspace key from that state. No request body,
query, or caller-selected actor grants ownership. All pack reads, writes, listing,
and artifact downloads filter by that key. Other owners/workspaces return 404.

This is the existing **single local operator** model. Hosted user accounts,
organization membership, Tribe identity, OAuth tenancy, public URLs and signed
object storage are NOT IMPLEMENTED by this change. The existing browser connection
and desktop token handoff are reused. Do not expose the desktop API publicly.

## Operations

All paths start with `/workbench/api/forge` and require Workbench authentication.

| Method/path | Behavior |
| --- | --- |
| `POST /packs?request_id=<UUID>&title=...&taxonomy=...` | Raw `application/zip` body; bounded inventory and format validation |
| `GET /packs` | Current operator/workspace's most recent 100 packs |
| `GET /packs/{UUID}` | Manifest, current revision, approvals, history and artifact references |
| `PATCH /packs/{UUID}/review` | Atomic batch metadata/path/rights edits and explicit per-asset review |
| `POST /packs/{UUID}/approve` | Approve the current fully reviewed revision as the authenticated actor |
| `POST /packs/{UUID}/export` | Verify unchanged source and export exact bytes plus JSON/CSV manifests |
| `POST /packs/{UUID}/shopify-draft` | Rights-gated offline CSV with `Published=FALSE`, `Status=draft` |
| `GET /exports/{UUID}` | Authorized download; SHA-256 verified before response |

Mutation JSON contains a UUID `request_id` and integer `expected_revision`.
Review adds `updates`, keyed by original stable asset IDs. Allowed edits:
`proposed_path`, `taxonomy`, `tags`, `rights_state`, `bpm_override`, `key_override`.
Omitted fields are preserved; explicit null edits are rejected. Draft adds `price`
and `sku`. Identity, source hashes and asset types cannot be overwritten by edits.

Responses carry `manifest_revision`, `status`, `correlation_id`, `evidence_refs`
and `errors`; export responses include an opaque artifact ID and checksum.
Conflict returns 409; invalid ZIP/metadata/business rules return 400 or 422;
oversize raw upload returns 413; unavailable auth/storage returns 503.

## Persistence and recovery

Forge tables use the **existing Sonic SQLite database**, selected by
`SONIC_DB_PATH`; no additional service or provider is introduced. Bounded original
ZIPs and derived artifacts are stored as immutable BLOBs alongside their metadata.
`forge_packs` links to the existing `workbench_runs` table. Successful commands
also append existing `workbench_events`, so Forge appears in Workbench history.
Forge's revision and approval records have their own explicit aggregate boundary.

SQLite `BEGIN IMMEDIATE` serializes the idempotency/revision check with the write.
Artifact BLOB, revision, audit event and retry response commit together. A crash
before commit cannot leave a downloadable partial artifact. A repeated request ID
with identical inputs returns its original response; changed inputs return 409.
ZIP exports are reused per approved revision even under new request IDs.
The UI retains command IDs in page memory for network retries. Request history is
durable on the server, including after API restart. Saving edits increments the
revision and invalidates its prior approval. Rejected authorized mutations record
a failure event after rollback. Source/hash corruption blocks further writes.

Source bytes never leave the database except into a unique temporary directory
for validation/export. Core export uses create-if-absent paths. Temporary files
are removed by the context manager; no original or existing export is overwritten.
There is deliberately no user-facing delete/rollback mutation in this alpha.
An exception-injected export test proves transaction rollback leaves the prior
approved state and no partial artifact. Uninstall rollback is removal of the
additive route/UI code; retain the database and its Forge tables for recovery.

## Bounds and validation

* Compressed upload: 32 MiB, streamed with a hard cap before persistence.
* Expanded archive: 500 entries, 32 MiB/member, 128 MiB total, compression ratio
  limit inherited from the core. Recursive paths are inventoried without extraction.
* Reject traversal, backslashes in original ZIP headers (before Windows
  normalization), symlinks/special files, encrypted members, case/Unicode path
  collisions, Windows reserved names, format-changing renames and manifest-name
  collisions. JSON/UTF-8 text is separately capped at 2 MiB.
* Media signatures must match suffixes. Audio also goes through the existing
  SoundFile dependency with bounded chunks and sample budgets; PCM WAV length is
  checked. Non-audio binary signatures are container checks, not full validators
  or a claim that a preset/document is safe to execute. NKI is rejected until a
  validator exists. No imported content is executed or rendered as HTML.
* CSV cells are protected against spreadsheet formula prefixes. ZIP/member hashes
  are recomputed at export; browser downloads are checked against recorded SHA-256.

## Music and external-service boundaries

Automatic BPM/key estimation remains null with `method=not_measured` and a reason.
Operator entries use `method=operator_override`, confidence null and an explicit
human-decision explanation. Existing `workbench/audio.py` and its legacy sample,
peak and measurement contracts are unchanged. No new analysis route pretends to
implement the proposed estimator. Curated licensed truth-labeled audio and actual
calibration are required before implementing gate F2.

Shopify output is an offline draft only; no authentication to a live store, scopes,
product publishing, pricing change, message sending, Tribe migration, production
deployment or Omega House OS PR merge is performed. Rights are operator assertions,
not verified legal entitlements. The source SHA and individual byte hashes remain
available for review.

## Reproduction

Use an environment installed from `apps/api/requirements.txt`:

```powershell
python -m pytest apps/api/tests/test_forge_core_foundation.py apps/api/tests/test_forge_workflow.py -q --basetemp=output/forge-focused-run
python -m pytest apps/api/tests -q --basetemp=output/forge-full-run
node --check apps/api/workbench/static/app.js
node --check apps/api/workbench/static/forge.js
python scripts/verify-forge-local.py
```

Use a fresh `--basetemp` name for each run; do not point it at user data. The explicit
test directory avoids an existing Windows pytest cleanup permission problem in the
global temp junction. The smoke script starts its own loopback API on port 18765,
uses disposable synthetic fixtures and a disposable test credential, verifies a
full HTTP roundtrip, saves hashes in `output/forge/http-smoke.json`, then stops.
`--serve` leaves that disposable server open for a browser walkthrough; Ctrl+C ends it.
