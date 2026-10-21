"""Local operator bridge: verified saved-file checkpoints -> scoped intelligence.

No HTTP/MCP endpoint, host control, raw media upload, or FLP restoration.
The integrity ledger is single-operator and has no tenant ownership schema;
therefore this bridge deliberately refuses every scope except the local one.
"""
import argparse
import hashlib
import json

from .fl_studio_integrity import verify_project
from .session_integrity import IntegrityError, IntegrityLedger
from .intelligence_store import IntelligenceStore

LOCAL_SCOPE = ("local-producer", "omega-house-studio")


def export_checkpoint(ledger, store, session_id, expected_revision, root):
    if (store.owner_id, store.workspace_id) != LOCAL_SCOPE:
        raise IntegrityError("outside_scope", "Only the local operator scope is supported")
    record = ledger.get(session_id)
    if type(expected_revision) is not int or record["revision"] != expected_revision:
        raise IntegrityError("conflict", "Refresh the checkpoint before exporting evidence")
    if record["state"].get("host") != "FL Studio" or "project_file" not in record["state"]:
        raise IntegrityError("invalid_state", "A saved FL Studio file capture is required")
    verification = verify_project(record, root)
    if not verification["verified"]:
        raise IntegrityError("file_mismatch", "Saved files no longer match the checkpoint")
    # Recheck revision after file I/O, before any evidence write.
    latest = ledger.get(session_id)
    if (latest["revision"], latest["sha256"]) != (record["revision"], record["sha256"]):
        raise IntegrityError("conflict", "Checkpoint changed during verification")
    identity = hashlib.sha256(json.dumps(
        [session_id, expected_revision, record["sha256"]], separators=(",", ":")
    ).encode()).hexdigest()
    intent_id = "session-file-checkpoint:" + identity
    evidence_id = intent_id + ":evidence"
    checkpoint_id = intent_id + ":checkpoint"
    # Stable checkpoint time and payload make retries safe after a partial write.
    # This records a historical fingerprint, never continuous/live host status.
    intent = store.put_intent({
        "intent_id": intent_id, "statement": "Preserve verified saved-project file evidence",
        "priority": 90, "payload": {"session_id": session_id, "revision": expected_revision},
    })
    evidence = store.append_evidence({
        "evidence_id": evidence_id, "intent_id": intent_id, "kind": "observation",
        "source": "sonic.session_integrity.filesystem_sha256",
        "observed_at": record["updated_at"], "confidence": 1.0,
        "claim": "Saved-file fingerprints captured in this manifest; host state unverified.",
        "scope": "/".join(LOCAL_SCOPE),
        "value": {"session_id": session_id, "revision": expected_revision,
                  "manifest_sha256": record["sha256"], "files": verification["files"],
                  "host_state_verified": False, "mode": "checkpoint_snapshot"},
        "provenance": [{"session_id": session_id, "manifest_sha256": record["sha256"]}],
    })
    checkpoint = store.append_checkpoint({
        "checkpoint_id": checkpoint_id, "intent_id": intent_id,
        "source_event_id": evidence_id, "sequence": 1, "escalation": "standard",
        "projection": {"evidence_ids": [evidence_id], "mode": "checkpoint_snapshot",
                       "next_actions": ["Validate read-only host telemetry before host-state claims"],
                       "host_rollback_available": False},
    })
    return {"intent_id": intent_id, "evidence_id": evidence_id,
            "checkpoint_id": checkpoint_id, "source_revision": expected_revision,
            "manifest_sha256": record["sha256"], "scope": "/".join(LOCAL_SCOPE),
            "status": "RECORDED" if evidence["recorded"] else "ALREADY_RECORDED",
            "recorded": {"intent": intent["recorded"], "evidence": evidence["recorded"],
                         "checkpoint": checkpoint["recorded"]},
            "host_state_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--integrity-db", required=True)
    parser.add_argument("--intelligence-db", required=True)
    parser.add_argument("--session-id", required=True)
    parser.add_argument("--expected-revision", required=True, type=int)
    parser.add_argument("--root", required=True)
    args = parser.parse_args()
    print(json.dumps(export_checkpoint(IntegrityLedger(args.integrity_db),
        IntelligenceStore(args.intelligence_db), args.session_id,
        args.expected_revision, args.root), indent=2))


if __name__ == "__main__":
    main()
