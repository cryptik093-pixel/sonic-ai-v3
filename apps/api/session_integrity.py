"""Durable, host-independent session integrity ledger. No DAW mutations occur here."""
import hashlib
import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path

_LOCK = threading.RLock()

def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)

def _digest(value):
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()

def _now():
    return datetime.now(timezone.utc).isoformat()

def _db_path():
    default = Path(__file__).resolve().parent / "data" / "session_integrity.sqlite3"
    return Path(os.environ.get("SONIC_INTEGRITY_DB", str(default)))

class IntegrityError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code

class IntegrityLedger:
    def __init__(self, path=None):
        self.path = Path(path) if path is not None else _db_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        with self._connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY, revision INTEGER NOT NULL, state_json TEXT NOT NULL,
                state_hash TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS revisions (
                session_id TEXT NOT NULL, revision INTEGER NOT NULL,
                state_json TEXT NOT NULL, state_hash TEXT NOT NULL, created_at TEXT NOT NULL,
                PRIMARY KEY(session_id,revision)
            );
            CREATE TABLE IF NOT EXISTS operations (
                operation_id TEXT PRIMARY KEY, session_id TEXT NOT NULL, kind TEXT NOT NULL,
                from_revision INTEGER NOT NULL, to_revision INTEGER NOT NULL,
                before_hash TEXT NOT NULL, after_hash TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            """)

    def _connect(self):
        conn = sqlite3.connect(self.path, timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA busy_timeout=15000")
        return conn

    @staticmethod
    def _validate(state):
        if not isinstance(state, dict):
            raise IntegrityError("invalid_state", "State must be a JSON object")
        if not isinstance(state.get("project_id"), str) or not state["project_id"].strip():
            raise IntegrityError("invalid_state", "project_id must be a nonempty string")
        if not isinstance(state.get("host"), str) or not state["host"].strip():
            raise IntegrityError("invalid_state", "host must be a nonempty string")
        if not isinstance(state.get("tracks", []), list):
            raise IntegrityError("invalid_state", "tracks must be an array")
        if not isinstance(state.get("assets", []), list):
            raise IntegrityError("invalid_state", "assets must be an array")
        try:
            encoded = _canonical(state)
        except (TypeError, ValueError) as exc:
            raise IntegrityError("invalid_state", "State must be finite JSON") from exc
        if len(encoded.encode("utf-8")) > 2_000_000:
            raise IntegrityError("invalid_state", "State exceeds 2MB manifest limit")
        return encoded

    def create(self, state, session_id=None):
        encoded = self._validate(state)
        sid = session_id or str(uuid.uuid4())
        digest = _digest(state)
        now = _now()
        with self._lock, self._connect() as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                db.execute("INSERT INTO sessions VALUES(?,?,?,?,?)", (sid, 0, encoded, digest, now))
                db.execute("INSERT INTO revisions VALUES(?,?,?,?,?)", (sid, 0, encoded, digest, now))
                db.commit()
            except sqlite3.IntegrityError as exc:
                raise IntegrityError("conflict", "Session already exists") from exc
        return self.get(sid)

    def get(self, session_id):
        with self._connect() as db:
            row = db.execute("SELECT * FROM sessions WHERE session_id=?", (session_id,)).fetchone()
        if row is None:
            raise IntegrityError("not_found", "Session not found")
        state = json.loads(row["state_json"])
        if _digest(state) != row["state_hash"]:
            raise IntegrityError("corrupt", "Stored checkpoint checksum mismatch")
        return {"session_id": row["session_id"], "revision": row["revision"],
                "state": state, "sha256": row["state_hash"], "updated_at": row["updated_at"]}

    def history(self, session_id):
        self.get(session_id)
        with self._connect() as db:
            rows = db.execute("SELECT revision,state_hash,created_at FROM revisions WHERE session_id=? ORDER BY revision",
                              (session_id,)).fetchall()
        return [dict(row) for row in rows]

    def checkpoint(self, session_id, expected_revision, state, kind="checkpoint"):
        if kind not in ("checkpoint", "restore"):
            raise IntegrityError("invalid_operation", "Unsupported operation kind")
        encoded = self._validate(state)
        after_hash = _digest(state)
        now, op_id = _now(), str(uuid.uuid4())
        with self._lock, self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT revision,state_hash,state_json FROM sessions WHERE session_id=?",
                             (session_id,)).fetchone()
            if row is None:
                raise IntegrityError("not_found", "Session not found")
            if row["revision"] != expected_revision:
                raise IntegrityError("conflict", "Stale revision; refresh before writing")
            if _digest(json.loads(row["state_json"])) != row["state_hash"]:
                raise IntegrityError("corrupt", "Stored checkpoint checksum mismatch")
            if json.loads(row["state_json"])["project_id"] != state["project_id"]:
                raise IntegrityError("invalid_state", "Cannot change project_id within a session")
            revision = row["revision"] + 1
            db.execute("UPDATE sessions SET revision=?,state_json=?,state_hash=?,updated_at=? WHERE session_id=?",
                       (revision, encoded, after_hash, now, session_id))
            db.execute("INSERT INTO revisions VALUES(?,?,?,?,?)",
                       (session_id, revision, encoded, after_hash, now))
            db.execute("INSERT INTO operations VALUES(?,?,?,?,?,?,?,?)",
                       (op_id, session_id, kind, row["revision"], revision, row["state_hash"], after_hash, now))
            db.commit()
        return {"operation_id": op_id, **self.get(session_id)}

    def restore(self, session_id, expected_revision, target_revision):
        with self._connect() as db:
            row = db.execute("SELECT state_json,state_hash FROM revisions WHERE session_id=? AND revision=?",
                             (session_id, target_revision)).fetchone()
        if row is None:
            raise IntegrityError("not_found", "Target checkpoint not found")
        state = json.loads(row["state_json"])
        if _digest(state) != row["state_hash"]:
            raise IntegrityError("corrupt", "Target checkpoint checksum mismatch")
        return self.checkpoint(session_id, expected_revision, state, kind="restore")

    def operations(self, session_id):
        self.get(session_id)
        with self._connect() as db:
            return [dict(r) for r in db.execute(
                "SELECT * FROM operations WHERE session_id=? ORDER BY to_revision", (session_id,)).fetchall()]
