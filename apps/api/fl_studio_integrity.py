"""Read-only Windows FL Studio artifact evidence adapter.

This adapter hashes explicitly selected local files; it does not parse FLP internals,
control FL Studio, inspect VST state, or modify host projects.
"""
import hashlib
from pathlib import Path

from .session_integrity import IntegrityError, IntegrityLedger

BLOCK_SIZE = 1024 * 1024
ALLOWED_EXTENSIONS = {".flp", ".zip", ".wav", ".aiff", ".aif", ".flac", ".mid", ".midi"}

def fingerprint(path, allowed_root):
    root = Path(allowed_root).expanduser().resolve(strict=True)
    if not root.is_dir():
        raise IntegrityError("invalid_root", "Allowed root must be an existing directory")
    candidate = Path(path).expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    resolved = candidate.resolve(strict=True)
    if not resolved.is_relative_to(root):
        raise IntegrityError("outside_root", "File is outside the approved workspace")
    if not resolved.is_file() or resolved.suffix.lower() not in ALLOWED_EXTENSIONS:
        raise IntegrityError("invalid_file", "Not an allowed regular audio, MIDI, or project file")
    before = resolved.stat()
    h = hashlib.sha256()
    with resolved.open("rb") as handle:
        while chunk := handle.read(BLOCK_SIZE):
            h.update(chunk)
    after = resolved.stat()
    if (before.st_size, before.st_mtime_ns, before.st_ino) != (
        after.st_size, after.st_mtime_ns, after.st_ino
    ):
        raise IntegrityError("changed_during_scan", "File changed during hashing; retry after saving")
    return {
        "relative_path": resolved.relative_to(root).as_posix(),
        "bytes": after.st_size,
        "sha256": h.hexdigest(),
        "mtime_ns": after.st_mtime_ns,
        "kind": resolved.suffix.lower(),
        "verification": "file_bytes_only",
    }

def capture_project(ledger: IntegrityLedger, root, project_path, session_id=None,
                    expected_revision=None, assets=()):
    """Hash a saved FLP and optionally listed files. Nothing is modified on disk.

    A host-state capture is explicitly UNAVAILABLE unless a separately validated
    host bridge provides it; file hashes cannot prove restored mixer/VST state.
    """
    project = fingerprint(project_path, root)
    if project["kind"] != ".flp":
        raise IntegrityError("invalid_project", "Select a saved .flp project")
    files = [fingerprint(path, root) for path in assets]
    if len({f["relative_path"] for f in [project, *files]}) != len(files) + 1:
        raise IntegrityError("duplicate_asset", "Duplicate paths are not allowed")
    state = {
        "project_id": project["relative_path"],
        "host": "FL Studio",
        "tracks": [],
        "assets": files,
        "project_file": project,
        "capture": {
            "method": "filesystem_sha256",
            "host_connected": False,
            "mixer_routing": "unavailable",
            "vst_parameters": "unavailable",
            "automation": "unavailable",
            "midi": "unavailable",
            "undo_available": False,
        },
    }
    if session_id is None:
        if expected_revision is not None:
            raise IntegrityError("invalid_revision", "New captures cannot specify a revision")
        return ledger.create(state)
    if expected_revision is None:
        raise IntegrityError("invalid_revision", "Expected revision required for subsequent captures")
    return ledger.checkpoint(session_id, expected_revision, state)

def verify_project(record, root):
    """Compare current saved files to a manifest without writing anything."""
    state = record["state"]
    expected = [state["project_file"], *state.get("assets", [])]
    results = []
    for file in expected:
        try:
            actual = fingerprint(file["relative_path"], root)
            match = actual["sha256"] == file["sha256"] and actual["bytes"] == file["bytes"]
            results.append({"path": file["relative_path"], "match": match,
                            "status": "unchanged" if match else "changed"})
        except (IntegrityError, OSError) as exc:
            results.append({"path": file["relative_path"], "match": False,
                            "status": "unavailable", "reason": str(exc)})
    return {
        "session_id": record["session_id"],
        "revision": record["revision"],
        "verified": all(x["match"] for x in results),
        "files": results,
        "host_state_verified": False,
    }
