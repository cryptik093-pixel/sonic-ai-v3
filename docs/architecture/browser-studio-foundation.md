# Browser Studio Foundation — experimental / not deployed

**Authority:** ACTIVE implementation proposal. Existing Sonic Desktop, SQLite persistence, workbench assets, local MIDI/audio, MCP, and Omega House integrations remain authoritative and unchanged.

## What the first change introduces

- `apps/api/schemas/studio_state.py`: isolated Pydantic V2 **StudioState** contract with existing integer `projects.id`, UTC timestamps, owner/workspace fields (server-asserted), stable 960-tick-per-quarter timeline, typed audio/MIDI regions, MIDI notes, effects, automation, and output routing validation.
- `apps/api/tests/test_studio_state.py`: unit-level invalid-state protection, identity uniqueness, media/timeline bounds, nonfinite number rejection, routing cycle detection, serialization.
- `infrastructure/postgres/browser_studio_001.sql`: an *opt-in*, future PostgreSQL migration candidate. It requires the original `projects` and `workbench_assets` identities migrated intact; it does not write to or delete SQLite. New tables store revisioned session state, project memberships, durable mutation events, checkpoints, and versioned 512-D CLAP vectors.

## Deployment gates (not satisfied by this PR)

1. Preserve and back up the existing SQLite file and workbench imports. Define and validate a **repeatable** SQLite → PostgreSQL data migration, including IDs, files, hashes, rights metadata, and rollback/recovery.
2. Bind a verified principal to each user connection (HTTP and WebSocket) and implement permission-aware membership onboarding. Today, local workbench uses a fixed owner token and cannot safely authorize external collaborators. The SQL RLS policies do **not** replace server-side authorization.
3. Enforce mutation validation and atomic commit: `BEGIN`; derive actor from verified token; authorize project; resolve idempotency by `(project_id, actor_id, client_mutation_id)`; `SELECT studio_project_states ... FOR UPDATE`; compare `base_revision`; apply the typed reducer; update state/revision/hash; insert durable event; `COMMIT`. On mismatch respond with current revision and require rebase/replay.
4. Publish the committed event to Redis **after** commit; WebSocket clients track monotonic `revision` and replay missing events from PostgreSQL on disconnect/restart. Redis Pub/Sub is not a durable log; each worker/project channel must have a single isolated subscription reader. Never broadcast uncommitted client payloads.
5. Bind each sample to an owned existing workbench asset and exact SHA-256. Validate size, decode format, safe storage path, quarantine behavior, quotas, and signed access before embedding. Keep separate `(model_id, model_version)` spaces; test dimension 512 **with the chosen CLAP encoder**. Do not claim millisecond lookup without measured workloads.
6. Run PostgreSQL integration tests (extension availability, referential integrity, RLS under distinct principals, unauthorized access, concurrency/idempotency, replay), browser render tests, and regression suites **before** enabling a hosted endpoint.

## Security and access

- Audio never travels over Redis event payloads. Only change metadata and IDs travel in room events. Audio bytes remain in protected asset storage.
- Do not let browser JSON set owner/workspace identities or DB session variables. Verified authentication on the server must establish them.
- Do not use the current desktop bearer token as an Internet multi-user token. Desktop remains loopback-only.
- This SQL intentionally omits application role grants and membership INSERT policies. Membership bootstrap is an admin-only, audited server operation and needs its own scoped implementation before multi-user access.
- Apply explicit permissions for an application database role with no `BYPASSRLS`; review migration and view ownership carefully. Database superusers bypass RLS. Without principal setting, normal reads and writes fail closed.
- PGVector, PostgreSQL, and Redis can run locally as free software. No managed service, deployment, or paid infrastructure is assumed or authorized.

## Limits

This change does not establish live PostgreSQL persistence, pgvector search, multi-user WebSocket sync, an embedding pipeline, offline audio rendering, or a production-ready deployment. The SQL is a forward migration proposal and should not be run against an unprepared database. Audio export/replay, clock sync, conflict policy, and undo need the subsequent reducer and persistence slices.
