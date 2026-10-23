"""Fail-closed, read-only transaction planning against saved FL Studio artifacts.

A plan never executes a host or filesystem mutation. It binds a proposed action
to a ledger revision AND a freshly verified on-disk project/asset baseline.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .fl_studio_integrity import fingerprint
from .session_integrity import IntegrityError, IntegrityLedger, _digest

ALLOWED_ACTIONS = frozenset({"analyze_audio", "render_candidate_offline", "propose_midi"})
MAX_ACTION_BYTES = 32768

def _timestamp():
    return datetime.now(timezone.utc).isoformat()

class SessionTransactionController:
    def __init__(self, ledger: IntegrityLedger, workspace_root):
        self.ledger = ledger
        self.root = Path(workspace_root).expanduser().resolve(strict=True)
        if not self.root.is_dir():
            raise IntegrityError("invalid_root", "Workspace root must exist")

    def validate(self, session_id, expected_revision, expected_hash):
        current = self.ledger.get(session_id)
        if current["revision"] != expected_revision or current["sha256"] != expected_hash:
            raise IntegrityError("conflict", "Session revision or manifest hash changed")
        state = current["state"]
        if state.get("host") != "FL Studio":
            raise IntegrityError("invalid_session", "Expected FL Studio session")
        if state.get("capture", {}).get("method") != "filesystem_sha256":
            raise IntegrityError("unverified_baseline", "Requires a file-hash baseline")
        baseline = [state.get("project_file"), *state.get("assets", [])]
        if not baseline[0] or not isinstance(state.get("assets"), list):
            raise IntegrityError("unverified_baseline", "Baseline project or assets missing")
        paths = [item.get("relative_path") for item in baseline if isinstance(item, dict)]
        if len(paths) != len(baseline) or len(set(paths)) != len(paths):
            raise IntegrityError("unverified_baseline", "Incomplete or duplicate baseline")
        checks = []
        for item in baseline:
            try:
                live = fingerprint(item["relative_path"], self.root)
            except (OSError, IntegrityError) as exc:
                raise IntegrityError("baseline_mismatch", "Baseline file unavailable: " + item["relative_path"]) from exc
            if live["sha256"] != item.get("sha256") or live["bytes"] != item.get("bytes"):
                raise IntegrityError("baseline_mismatch", "Baseline file changed: " + item["relative_path"])
            checks.append({"path": item["relative_path"], "sha256": live["sha256"]})
        # Recheck revision after hashing to reject concurrent ledger updates.
        last = self.ledger.get(session_id)
        if last["revision"] != expected_revision or last["sha256"] != expected_hash:
            raise IntegrityError("conflict", "Session changed during validation")
        return {"session_id": session_id, "revision": expected_revision,
                "sha256": expected_hash, "files": checks, "verified_at": _timestamp(),
                "host_state_verified": False}

    def plan(self, session_id, expected_revision, expected_hash, action, parameters=None):
        if action not in ALLOWED_ACTIONS:
            raise IntegrityError("operation_denied", "Action not on offline proposal allowlist")
        if not isinstance(parameters, dict):
            raise IntegrityError("invalid_operation", "Parameters must be a JSON object")
        try:
            encoded = json.dumps(parameters, sort_keys=True, allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise IntegrityError("invalid_operation", "Parameters must be finite JSON") from exc
        if len(encoded.encode("utf-8")) > MAX_ACTION_BYTES:
            raise IntegrityError("invalid_operation", "Parameters exceed plan size limit")
        evidence = self.validate(session_id, expected_revision, expected_hash)
        proposal = {
            "schema": "sonic.session.transaction.v1",
            "action": action, "parameters": parameters,
            "precondition": {"revision": expected_revision, "manifest_sha256": expected_hash,
                             "files": evidence["files"]},
            "status": "proposed_only",
            "host_mutation_permitted": False,
            "files_mutated": False,
        }
        proposal["proposal_sha256"] = _digest(proposal)
        return proposal
