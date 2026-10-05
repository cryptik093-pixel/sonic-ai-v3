"""Tier 2 persistent intelligence ledger.

The ledger is intentionally separate from legacy studio memories. Evidence,
checkpoints, and candidates are durable/auditable, but candidate acceptance does
not silently materialize into operational MemoryORM state.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .workbench.models import OWNER, WORKSPACE

CANDIDATE_TYPES = {"memory", "creator_dna", "foresight"}
TERMINAL_STATUSES = {"rejected", "superseded"}


def now() -> str:
    return datetime.now(UTC).isoformat()


def canonical(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def fingerprint(value: Any) -> str:
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


class IntelligenceStore:
    def __init__(
        self,
        database_path: str | Path | None = None,
        *,
        owner_id: str = OWNER,
        workspace_id: str = WORKSPACE,
    ) -> None:
        if database_path is None:
            root = Path(os.getenv("SONIC_DATA_DIR", str(Path(__file__).resolve().parent / "data")))
            database_path = os.getenv("SONIC_INTELLIGENCE_DB", str(root / "sonic_intelligence.sqlite3"))
        self.database_path = str(Path(database_path).resolve())
        self.owner_id = owner_id
        self.workspace_id = workspace_id
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    def _initialize(self) -> None:
        with self._connect() as c:
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS intelligence_intents (
                    owner_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL,
                    intent_id TEXT NOT NULL,
                    statement TEXT NOT NULL,
                    status TEXT NOT NULL,
                    priority INTEGER NOT NULL,
                    horizon TEXT,
                    payload_json TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (owner_id, workspace_id, intent_id)
                );

                CREATE TABLE IF NOT EXISTS intelligence_evidence (
                    owner_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL,
                    evidence_id TEXT NOT NULL,
                    intent_id TEXT,
                    kind TEXT NOT NULL,
                    source TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    confidence REAL NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
                    claim TEXT,
                    payload_json TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (owner_id, workspace_id, evidence_id)
                );

                CREATE TABLE IF NOT EXISTS intelligence_checkpoints (
                    owner_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL,
                    checkpoint_id TEXT NOT NULL,
                    intent_id TEXT NOT NULL,
                    source_event_id TEXT NOT NULL,
                    sequence INTEGER NOT NULL CHECK (sequence > 0),
                    escalation TEXT NOT NULL,
                    projection_json TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (owner_id, workspace_id, checkpoint_id),
                    UNIQUE (owner_id, workspace_id, intent_id, sequence),
                    UNIQUE (owner_id, workspace_id, source_event_id)
                );

                CREATE TABLE IF NOT EXISTS intelligence_candidates (
                    owner_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL,
                    candidate_id TEXT NOT NULL,
                    intent_id TEXT NOT NULL,
                    candidate_type TEXT NOT NULL,
                    content_json TEXT NOT NULL,
                    evidence_ids_json TEXT NOT NULL,
                    confidence REAL NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
                    source_checkpoint_id TEXT,
                    supersedes_candidate_id TEXT,
                    payload_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY (owner_id, workspace_id, candidate_id)
                );

                CREATE TABLE IF NOT EXISTS intelligence_candidate_decisions (
                    owner_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL,
                    decision_id TEXT NOT NULL,
                    candidate_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    rationale TEXT NOT NULL,
                    decided_at TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    PRIMARY KEY (owner_id, workspace_id, decision_id)
                );

                CREATE TABLE IF NOT EXISTS intelligence_materialization_events (
                    owner_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL,
                    materialization_event_id TEXT NOT NULL,
                    candidate_id TEXT NOT NULL,
                    action TEXT NOT NULL CHECK (action IN ('activate','retire')),
                    rationale TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    PRIMARY KEY (owner_id, workspace_id, materialization_event_id)
                );

                CREATE INDEX IF NOT EXISTS idx_intelligence_evidence_intent
                    ON intelligence_evidence(owner_id, workspace_id, intent_id, observed_at);
                CREATE INDEX IF NOT EXISTS idx_intelligence_checkpoints_intent
                    ON intelligence_checkpoints(owner_id, workspace_id, intent_id, sequence);
                CREATE INDEX IF NOT EXISTS idx_intelligence_candidates_intent
                    ON intelligence_candidates(owner_id, workspace_id, intent_id, candidate_type, created_at);
                CREATE INDEX IF NOT EXISTS idx_intelligence_candidate_decisions
                    ON intelligence_candidate_decisions(owner_id, workspace_id, candidate_id, decided_at);
                CREATE INDEX IF NOT EXISTS idx_intelligence_materialization_events
                    ON intelligence_materialization_events(owner_id, workspace_id, candidate_id, occurred_at);
                """
            )

    @property
    def scope(self) -> tuple[str, str]:
        return self.owner_id, self.workspace_id

    def put_intent(self, record: dict[str, Any]) -> dict[str, Any]:
        payload = {
            "intent_id": record["intent_id"],
            "statement": record["statement"],
            "status": record.get("status", "active"),
            "priority": int(record.get("priority", 50)),
            "horizon": record.get("horizon"),
            "payload": record.get("payload", {}),
        }
        if not 0 <= payload["priority"] <= 100:
            raise ValueError("priority must be between 0 and 100")
        encoded, digest = canonical(payload), fingerprint(payload)
        stamp = record.get("updated_at") or record.get("created_at") or now()
        with self._connect() as c:
            row = c.execute(
                """SELECT payload_hash FROM intelligence_intents
                   WHERE owner_id=? AND workspace_id=? AND intent_id=?""",
                (*self.scope, payload["intent_id"]),
            ).fetchone()
            if row:
                if row["payload_hash"] != digest:
                    raise ValueError("Intent ID already exists with different content; create an explicit new intent/revision ID.")
                return self.get_intent(payload["intent_id"]) | {"recorded": False}
            c.execute(
                """INSERT INTO intelligence_intents
                   (owner_id,workspace_id,intent_id,statement,status,priority,horizon,
                    payload_json,payload_hash,created_at,updated_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                (*self.scope, payload["intent_id"], payload["statement"], payload["status"],
                 payload["priority"], payload["horizon"], encoded, digest, stamp, stamp),
            )
        return self.get_intent(payload["intent_id"]) | {"recorded": True}

    def get_intent(self, intent_id: str) -> dict[str, Any]:
        with self._connect() as c:
            row = c.execute(
                """SELECT * FROM intelligence_intents
                   WHERE owner_id=? AND workspace_id=? AND intent_id=?""",
                (*self.scope, intent_id),
            ).fetchone()
        if not row:
            raise ValueError("Intent not found in this workspace.")
        payload = json.loads(row["payload_json"])
        return {**payload, "created_at": row["created_at"], "updated_at": row["updated_at"]}

    def append_evidence(self, record: dict[str, Any]) -> dict[str, Any]:
        if record.get("intent_id"):
            self.get_intent(record["intent_id"])
        payload = {
            "evidence_id": record["evidence_id"],
            "intent_id": record.get("intent_id"),
            "kind": record["kind"],
            "source": record["source"],
            "observed_at": record["observed_at"],
            "confidence": float(record["confidence"]),
            "claim": record.get("claim"),
            "value": record.get("value"),
            "scope": record.get("scope"),
            "provenance": record.get("provenance", []),
            "supersedes": record.get("supersedes"),
        }
        if not 0 <= payload["confidence"] <= 1:
            raise ValueError("confidence must be between 0 and 1")
        encoded, digest = canonical(payload), fingerprint(payload)
        with self._connect() as c:
            existing = c.execute(
                """SELECT payload_hash,payload_json,created_at FROM intelligence_evidence
                   WHERE owner_id=? AND workspace_id=? AND evidence_id=?""",
                (*self.scope, payload["evidence_id"]),
            ).fetchone()
            if existing:
                if existing["payload_hash"] != digest:
                    raise ValueError("Evidence ID collision: immutable evidence cannot be rewritten.")
                return json.loads(existing["payload_json"]) | {"created_at": existing["created_at"], "recorded": False}
            created = record.get("created_at") or now()
            c.execute(
                """INSERT INTO intelligence_evidence
                   (owner_id,workspace_id,evidence_id,intent_id,kind,source,observed_at,
                    confidence,claim,payload_json,payload_hash,created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (*self.scope, payload["evidence_id"], payload["intent_id"], payload["kind"],
                 payload["source"], payload["observed_at"], payload["confidence"], payload["claim"],
                 encoded, digest, created),
            )
        return payload | {"created_at": created, "recorded": True}

    def append_checkpoint(self, record: dict[str, Any]) -> dict[str, Any]:
        self.get_intent(record["intent_id"])
        payload = {
            "checkpoint_id": record["checkpoint_id"],
            "intent_id": record["intent_id"],
            "source_event_id": record["source_event_id"],
            "sequence": int(record["sequence"]),
            "escalation": record.get("escalation", "none"),
            "projection": record["projection"],
        }
        if payload["sequence"] < 1:
            raise ValueError("checkpoint sequence must be positive")
        encoded, digest = canonical(payload), fingerprint(payload)
        created = record.get("created_at") or now()
        try:
            with self._connect() as c:
                existing = c.execute(
                    """SELECT payload_hash,projection_json,created_at FROM intelligence_checkpoints
                       WHERE owner_id=? AND workspace_id=? AND checkpoint_id=?""",
                    (*self.scope, payload["checkpoint_id"]),
                ).fetchone()
                if existing:
                    if existing["payload_hash"] != digest:
                        raise ValueError("Checkpoint ID collision: checkpoint history is append-only.")
                    return payload | {"created_at": existing["created_at"], "recorded": False}
                c.execute(
                    """INSERT INTO intelligence_checkpoints
                       (owner_id,workspace_id,checkpoint_id,intent_id,source_event_id,sequence,
                        escalation,projection_json,payload_hash,created_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (*self.scope, payload["checkpoint_id"], payload["intent_id"],
                     payload["source_event_id"], payload["sequence"], payload["escalation"],
                     canonical(payload["projection"]), digest, created),
                )
        except sqlite3.IntegrityError as exc:
            raise ValueError("Checkpoint sequence or source event already exists in this intent stream.") from exc
        return payload | {"created_at": created, "recorded": True}

    def append_candidate(self, record: dict[str, Any]) -> dict[str, Any]:
        self.get_intent(record["intent_id"])
        candidate_type = record["candidate_type"]
        if candidate_type not in CANDIDATE_TYPES:
            raise ValueError(f"candidate_type must be one of {sorted(CANDIDATE_TYPES)}")
        payload = {
            "candidate_id": record["candidate_id"],
            "intent_id": record["intent_id"],
            "candidate_type": candidate_type,
            "content": record["content"],
            "evidence_ids": sorted(set(record.get("evidence_ids", []))),
            "confidence": float(record["confidence"]),
            "source_checkpoint_id": record.get("source_checkpoint_id"),
            "supersedes_candidate_id": record.get("supersedes_candidate_id"),
        }
        if not 0 <= payload["confidence"] <= 1:
            raise ValueError("confidence must be between 0 and 1")
        encoded, digest = canonical(payload), fingerprint(payload)
        created = record.get("created_at") or now()
        with self._connect() as c:
            if payload["source_checkpoint_id"]:
                checkpoint = c.execute(
                    """SELECT intent_id FROM intelligence_checkpoints
                       WHERE owner_id=? AND workspace_id=? AND checkpoint_id=?""",
                    (*self.scope, payload["source_checkpoint_id"]),
                ).fetchone()
                if not checkpoint or checkpoint["intent_id"] != payload["intent_id"]:
                    raise ValueError("Source checkpoint does not exist for this intent.")
            if payload["evidence_ids"]:
                placeholders = ",".join("?" for _ in payload["evidence_ids"])
                rows = c.execute(
                    f"""SELECT evidence_id,intent_id FROM intelligence_evidence
                        WHERE owner_id=? AND workspace_id=? AND evidence_id IN ({placeholders})""",
                    [*self.scope, *payload["evidence_ids"]],
                ).fetchall()
                found = {row["evidence_id"] for row in rows if row["intent_id"] in {None, payload["intent_id"]}}
                missing = sorted(set(payload["evidence_ids"]) - found)
                if missing:
                    raise ValueError("Candidate references missing or cross-intent evidence: " + ", ".join(missing))
            existing = c.execute(
                """SELECT payload_hash,created_at FROM intelligence_candidates
                   WHERE owner_id=? AND workspace_id=? AND candidate_id=?""",
                (*self.scope, payload["candidate_id"]),
            ).fetchone()
            if existing:
                if existing["payload_hash"] != digest:
                    raise ValueError("Candidate ID collision: candidate history is immutable.")
                return self.get_candidate(payload["candidate_id"]) | {"recorded": False}
            if payload["supersedes_candidate_id"]:
                prior = c.execute(
                    """SELECT intent_id,candidate_type FROM intelligence_candidates
                       WHERE owner_id=? AND workspace_id=? AND candidate_id=?""",
                    (*self.scope, payload["supersedes_candidate_id"]),
                ).fetchone()
                if not prior:
                    raise ValueError("Superseded candidate does not exist in this workspace.")
                if prior["intent_id"] != payload["intent_id"] or prior["candidate_type"] != payload["candidate_type"]:
                    raise ValueError("Candidates may supersede only the same type within the same intent.")
            c.execute(
                """INSERT INTO intelligence_candidates
                   (owner_id,workspace_id,candidate_id,intent_id,candidate_type,content_json,
                    evidence_ids_json,confidence,source_checkpoint_id,supersedes_candidate_id,
                    payload_hash,created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                (*self.scope, payload["candidate_id"], payload["intent_id"], payload["candidate_type"],
                 canonical(payload["content"]), canonical(payload["evidence_ids"]), payload["confidence"],
                 payload["source_checkpoint_id"], payload["supersedes_candidate_id"], digest, created),
            )
        return self.get_candidate(payload["candidate_id"]) | {"recorded": True}

    def decide_candidate(self, candidate_id: str, decision: dict[str, Any]) -> dict[str, Any]:
        status = decision["status"]
        if status not in {"accepted", "rejected", "superseded"}:
            raise ValueError("status must be accepted, rejected, or superseded")
        candidate = self.get_candidate(candidate_id)
        current = candidate["status"]
        if current in TERMINAL_STATUSES:
            raise ValueError(f"Candidate is already terminal: {current}")
        if current == "accepted" and status not in {"accepted", "superseded"}:
            raise ValueError("Accepted candidates may only remain accepted or be explicitly superseded.")
        payload = {
            "decision_id": decision["decision_id"],
            "candidate_id": candidate_id,
            "status": status,
            "rationale": decision.get("rationale", ""),
            "decided_at": decision.get("decided_at") or now(),
        }
        digest = fingerprint(payload)
        with self._connect() as c:
            existing = c.execute(
                """SELECT payload_hash FROM intelligence_candidate_decisions
                   WHERE owner_id=? AND workspace_id=? AND decision_id=?""",
                (*self.scope, payload["decision_id"]),
            ).fetchone()
            if existing:
                if existing["payload_hash"] != digest:
                    raise ValueError("Decision ID collision: candidate decisions are immutable.")
                return self.get_candidate(candidate_id) | {"decision_recorded": False}
            c.execute(
                """INSERT INTO intelligence_candidate_decisions
                   (owner_id,workspace_id,decision_id,candidate_id,status,rationale,decided_at,payload_hash)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (*self.scope, payload["decision_id"], candidate_id, status,
                 payload["rationale"], payload["decided_at"], digest),
            )
        return self.get_candidate(candidate_id) | {"decision_recorded": True}

    def get_candidate(self, candidate_id: str) -> dict[str, Any]:
        with self._connect() as c:
            row = c.execute(
                """SELECT * FROM intelligence_candidates
                   WHERE owner_id=? AND workspace_id=? AND candidate_id=?""",
                (*self.scope, candidate_id),
            ).fetchone()
            if not row:
                raise ValueError("Candidate not found in this workspace.")
            decisions = c.execute(
                """SELECT decision_id,status,rationale,decided_at
                   FROM intelligence_candidate_decisions
                   WHERE owner_id=? AND workspace_id=? AND candidate_id=?
                   ORDER BY decided_at ASC, decision_id ASC""",
                (*self.scope, candidate_id),
            ).fetchall()
        status = decisions[-1]["status"] if decisions else "proposed"
        return {
            "candidate_id": row["candidate_id"],
            "intent_id": row["intent_id"],
            "candidate_type": row["candidate_type"],
            "content": json.loads(row["content_json"]),
            "evidence_ids": json.loads(row["evidence_ids_json"]),
            "confidence": row["confidence"],
            "source_checkpoint_id": row["source_checkpoint_id"],
            "supersedes_candidate_id": row["supersedes_candidate_id"],
            "created_at": row["created_at"],
            "status": status,
            "decisions": [dict(d) for d in decisions],
        }

    def materialization_state(self, candidate_id: str) -> dict[str, Any]:
        candidate = self.get_candidate(candidate_id)
        with self._connect() as c:
            rows = c.execute(
                """SELECT materialization_event_id,action,rationale,occurred_at
                   FROM intelligence_materialization_events
                   WHERE owner_id=? AND workspace_id=? AND candidate_id=?
                   ORDER BY occurred_at ASC, materialization_event_id ASC""",
                (*self.scope, candidate_id),
            ).fetchall()
        events = [dict(row) for row in rows]
        requested_active = bool(events and events[-1]["action"] == "activate")
        eligible = candidate["candidate_type"] == "memory" and candidate["status"] == "accepted"
        return {
            "candidate_id": candidate_id,
            "candidate_type": candidate["candidate_type"],
            "candidate_status": candidate["status"],
            "requested_active": requested_active,
            "active": requested_active and eligible,
            "blocked_reason": None if (not requested_active or eligible) else "candidate_not_accepted",
            "events": events,
        }

    def _record_materialization(self, candidate_id: str, event: dict[str, Any], action: str) -> dict[str, Any]:
        candidate = self.get_candidate(candidate_id)
        if candidate["candidate_type"] != "memory":
            raise ValueError("Only memory candidates can be materialized at Gate 2.3.")

        payload = {
            "materialization_event_id": event["materialization_event_id"],
            "candidate_id": candidate_id,
            "action": action,
            "rationale": event.get("rationale", ""),
            "occurred_at": event.get("occurred_at") or now(),
        }
        digest = fingerprint(payload)
        with self._connect() as c:
            existing = c.execute(
                """SELECT payload_hash FROM intelligence_materialization_events
                   WHERE owner_id=? AND workspace_id=? AND materialization_event_id=?""",
                (*self.scope, payload["materialization_event_id"]),
            ).fetchone()
            if existing:
                if existing["payload_hash"] != digest:
                    raise ValueError("Materialization event ID collision.")
                return self.materialization_state(candidate_id) | {"recorded": False}

        if action == "activate" and candidate["status"] != "accepted":
            raise ValueError("Memory candidate must be explicitly accepted before materialization.")
        state = self.materialization_state(candidate_id)
        if action == "activate" and state["active"]:
            raise ValueError("Memory candidate is already active.")
        if action == "retire" and not state["requested_active"]:
            raise ValueError("Memory candidate is not currently materialized.")

        with self._connect() as c:
            c.execute(
                """INSERT INTO intelligence_materialization_events
                   (owner_id,workspace_id,materialization_event_id,candidate_id,action,rationale,occurred_at,payload_hash)
                   VALUES (?,?,?,?,?,?,?,?)""",
                (*self.scope, payload["materialization_event_id"], candidate_id, action,
                 payload["rationale"], payload["occurred_at"], digest),
            )
        return self.materialization_state(candidate_id) | {"recorded": True}

    def materialize_memory(self, candidate_id: str, event: dict[str, Any]) -> dict[str, Any]:
        candidate = self.get_candidate(candidate_id)
        content = candidate["content"].get("content") or candidate["content"].get("claim")
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Memory candidate must contain non-empty 'content' or 'claim' text.")
        return self._record_materialization(candidate_id, event, "activate")

    def retire_materialized_memory(self, candidate_id: str, event: dict[str, Any]) -> dict[str, Any]:
        return self._record_materialization(candidate_id, event, "retire")

    def list_materialized_memories(self, *, intent_id: str | None = None) -> list[dict[str, Any]]:
        query = """SELECT DISTINCT candidate_id FROM intelligence_materialization_events
                   WHERE owner_id=? AND workspace_id=?"""
        params: list[Any] = [*self.scope]
        with self._connect() as c:
            ids = [row["candidate_id"] for row in c.execute(query, params).fetchall()]
        result: list[dict[str, Any]] = []
        for candidate_id in ids:
            candidate = self.get_candidate(candidate_id)
            if intent_id and candidate["intent_id"] != intent_id:
                continue
            state = self.materialization_state(candidate_id)
            if not state["active"]:
                continue
            content = candidate["content"].get("content") or candidate["content"].get("claim")
            result.append({
                "candidate_id": candidate_id,
                "intent_id": candidate["intent_id"],
                "content": content,
                "confidence": candidate["confidence"],
                "evidence_ids": candidate["evidence_ids"],
                "created_at": candidate["created_at"],
                "materialization": state,
            })
        return sorted(result, key=lambda item: (item["created_at"], item["candidate_id"]))

    def retrieve_materialized_memories(
        self,
        query_text: str,
        *,
        intent_id: str | None = None,
        limit: int = 8,
    ) -> list[dict[str, Any]]:
        query = query_text.strip().lower()
        if not query:
            raise ValueError("query_text is required")
        if limit < 1 or limit > 20:
            raise ValueError("limit must be between 1 and 20")

        tokens = sorted({token for token in re.findall(r"[a-z0-9][a-z0-9_'-]+", query) if len(token) >= 3})
        if not tokens:
            raise ValueError("query_text must contain at least one meaningful token")

        ranked: list[dict[str, Any]] = []
        for memory in self.list_materialized_memories(intent_id=intent_id):
            text = str(memory["content"]).lower()
            hits = [token for token in tokens if token in text]
            if not hits and query not in text:
                continue
            coverage = len(hits) / len(tokens)
            exact_phrase = 1.0 if query in text else 0.0
            confidence = float(memory["confidence"])
            evidence_strength = min(len(memory["evidence_ids"]) / 5.0, 1.0)
            score = (
                0.55 * coverage
                + 0.20 * confidence
                + 0.15 * evidence_strength
                + 0.10 * exact_phrase
            )
            ranked.append({
                **memory,
                "retrieval": {
                    "score": round(score, 6),
                    "token_coverage": round(coverage, 6),
                    "matched_tokens": hits,
                    "exact_phrase": bool(exact_phrase),
                    "confidence_component": round(confidence, 6),
                    "evidence_strength": round(evidence_strength, 6),
                    "method": "tier2_lexical_evidence_v1",
                },
            })

        ranked.sort(
            key=lambda item: (
                item["retrieval"]["score"],
                item["confidence"],
                len(item["evidence_ids"]),
                item["created_at"],
                item["candidate_id"],
            ),
            reverse=True,
        )
        return ranked[:limit]

    def list_candidates(self, *, intent_id: str | None = None, candidate_type: str | None = None) -> list[dict[str, Any]]:
        query = """SELECT candidate_id FROM intelligence_candidates
                   WHERE owner_id=? AND workspace_id=?"""
        params: list[Any] = [*self.scope]
        if intent_id:
            query += " AND intent_id=?"
            params.append(intent_id)
        if candidate_type:
            if candidate_type not in CANDIDATE_TYPES:
                raise ValueError(f"candidate_type must be one of {sorted(CANDIDATE_TYPES)}")
            query += " AND candidate_type=?"
            params.append(candidate_type)
        query += " ORDER BY created_at ASC, candidate_id ASC"
        with self._connect() as c:
            ids = [row["candidate_id"] for row in c.execute(query, params).fetchall()]
        return [self.get_candidate(candidate_id) for candidate_id in ids]

    def counts(self) -> dict[str, int]:
        tables = {
            "intents": "intelligence_intents",
            "evidence": "intelligence_evidence",
            "checkpoints": "intelligence_checkpoints",
            "candidates": "intelligence_candidates",
            "decisions": "intelligence_candidate_decisions",
            "materialization_events": "intelligence_materialization_events",
        }
        result: dict[str, int] = {}
        with self._connect() as c:
            for key, table in tables.items():
                row = c.execute(
                    f"SELECT COUNT(*) AS n FROM {table} WHERE owner_id=? AND workspace_id=?",
                    self.scope,
                ).fetchone()
                result[key] = int(row["n"])
        return result
