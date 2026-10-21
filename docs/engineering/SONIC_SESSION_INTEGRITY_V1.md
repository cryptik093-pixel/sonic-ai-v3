# Sonic Session Integrity V1 — checkpoint ledger

This module adds an **immutable revision history**, SHA-256 integrity checks, SQLite durability, optimistic revision guards, and audit records for manifest checkpoints/restores.

**Boundary:** Restoring a checkpoint restores the *recorded manifest*, NOT an FL Studio project or a VST's runtime state. No file on disk, audio render, DAW routing, plugin parameter or approved render is modified by this API.

Use this in the local Sonic API only. Authentication and policy middleware in `main.py` still apply. Do not publicly expose or connect an untrusted client to this write API without explicit per-session authorization. SQLite paths are isolated by `SONIC_INTEGRITY_DB`; default: `apps/api/data/session_integrity.sqlite3`.

Endpoints:
- `POST /session-integrity/sessions`: `{"state":{"project_id":"demo","host":"FL Studio","tracks":[],"assets":[]} }`
- `GET /session-integrity/sessions/{id}`
- `GET /session-integrity/sessions/{id}/history`
- `GET /session-integrity/sessions/{id}/operations`
- `POST /session-integrity/sessions/{id}/checkpoints`: `{"expected_revision":0,"state":{...}}`
- `POST /session-integrity/sessions/{id}/restores`: `{"expected_revision":1,"target_revision":0}`

`expected_revision` prevents overwriting newer session state; stale writes return HTTP 409. Immutable revisions survive process restarts. Every checkpoint includes a state hash; history retains the original state for later audit and recovery.

### Next gated stage (not implemented)

1. Confirm the exact FL Studio installation and supported host-control surface on Windows.
2. Build a read-only FL Studio state acquisition adapter; mark every field as verified/unavailable rather than guessing plugin or routing values.
3. For any host mutation, capture a host checkpoint; require explicit allowlist and confirmation; perform one bounded change; re-read and compare host state; run host-native undo when proven. Re-check routing, plugin state, source files and renders.
4. Add native VST3 `getState`/`setState` round-trip and FL Studio save/reopen tests. Never treat a manifest-only restore as a completed host rollback.

To run unit tests from repo root: `python -m unittest apps.api.test_session_integrity -v`.
