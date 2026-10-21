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

## FL Studio local file evidence adapter (implemented)

The read-only filesystem adapter connects saved `.flp` evidence and explicitly specified asset checksums to the integrity ledger. It does **not** parse the FLP binary or report mixer, VST, or automation state. The adapter records these fields as `unavailable`; it never simulates FL Studio control.

From the Sonic V3 repository root on Windows:

```powershell
python -m apps.api.fl_studio_integrity_cli capture --root "C:\\OmegaHouse\\Studio" --project "My Track.flp" --asset "Stems\\Kick.wav"
python -m apps.api.fl_studio_integrity_cli verify --root "C:\\OmegaHouse\\Studio" --session-id "<capture-session-id>"
```

The approved root must exist. Captures only read explicitly named saved project/audio/MIDI files under that root. Symlink traversal outside the root, duplicate paths, and unsupported file types are rejected. The project and asset file hashes are recorded in the same SQLite ledger as checkpoint history. A modified file is detected during later verification. A file changing while being hashed causes capture to abort when its metadata changes.

**Limitations:** This is not live FL Studio/VST telemetry. Successful SHA-256 verification means the selected file bytes match; it does not prove plugin state is restored, nor the completeness of a project backup. Source files stay in place; no copies/backups are generated. Host save/reopen acceptance remains a hard release gate.

CI exercises unit tests on Windows and Linux; no live FL Studio integration test is claimed.
