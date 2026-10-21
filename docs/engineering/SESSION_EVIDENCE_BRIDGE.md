# Local session checkpoint to intelligence bridge

The operator CLI in `apps/api/session_evidence_bridge.py` verifies saved FL Studio file fingerprints against a selected integrity revision, then appends one intent, evidence record and checkpoint to the existing Sonic Intelligence store. Repeating the same export does not duplicate records. A retry can finish a checkpoint after an interrupted export.

The preflight refuses stale revisions, changed or missing files, and any store owner/workspace other than `local-producer/omega-house-studio`. The session ledger has no tenant authorization model; this is a local operator command, not a tenant-safe network API. Do not expose it as HTTP or MCP.

The source manifest hash and revision are retained. The evidence observation time is the checkpoint time; it is historical fingerprint evidence. This command does not continuously monitor file changes. Verification and evidence persistence span two databases and file I/O; concurrent changes after validation remain possible. The caller should keep the selected project saved and stable during the operation.

```powershell
python -m apps.api.session_evidence_bridge --integrity-db "C:\OmegaHouse\integrity.sqlite3" --intelligence-db "C:\OmegaHouse\intelligence.sqlite3" --session-id "<captured-session-id>" --expected-revision 0 --root "C:\OmegaHouse\Studio"
python -m unittest apps.api.test_session_evidence_bridge apps.api.test_session_integrity apps.api.test_fl_studio_integrity apps.api.test_fl_studio_probe_import -v
python -m pytest apps/api/tests/test_intelligence_store.py apps/api/tests/test_intelligence_retrieval.py apps/api/tests/test_intelligence_materialization.py -q
```

The Windows tests exposed leaked SQLite connections in IntelligenceStore. Its connection context now commits/rolls back and explicitly closes on both success and failure. No schema or record migration is required.

No real FLP internals, routing, automation or VST state are inspected or changed. No FL Studio restore is available. No Shopify operation, OS service deployment, customer action or paid provider is involved. The bridge does not claim an OS UI integration.

Rollback: stop using the new CLI and use the parent branch; keep all SQLite evidence for audit. Do not delete or rewrite evidence to roll back code. Existing source, the running API and the open DAW are untouched by an isolated worktree.
