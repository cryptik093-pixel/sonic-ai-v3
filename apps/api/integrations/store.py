"""Tier 5 Gate 2 durable event store.

Uses SQLite from the Python standard library so the event backbone has durable
storage without introducing a new database dependency. The store preserves the
canonical event envelope and enforces event_id uniqueness for idempotency.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any


class EventStore:
    def __init__(self, database_path: str | Path = "data/sonic_events.sqlite3") -> None:
        self.database_path = str(database_path)
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("CREATE TABLE IF NOT EXISTS integration_decisions (trace_id TEXT PRIMARY KEY, record_json TEXT NOT NULL)")
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS business_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    schema_version TEXT NOT NULL,
                    occurred_at TEXT NOT NULL,
                    source TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    entity_id TEXT NOT NULL,
                    event_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_business_events_type_time "
                "ON business_events(event_type, occurred_at)"
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_business_events_entity "
                "ON business_events(entity_type, entity_id)"
            )

    def append(self, event: dict[str, Any]) -> bool:
        """Persist an event.

        Returns True when inserted and False when event_id already exists.
        """
        entity = event["entity"]
        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO business_events (
                        event_id, event_type, schema_version, occurred_at,
                        source, entity_type, entity_id, event_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event["event_id"],
                        event["event_type"],
                        event["schema_version"],
                        event["occurred_at"],
                        event["source"],
                        entity["type"],
                        entity["id"],
                        json.dumps(event, separators=(",", ":"), sort_keys=True),
                    ),
                )
            return True
        except sqlite3.IntegrityError:
            if self.get(event["event_id"]) is not None:
                return False
            raise

    def record(self, record: dict) -> None:
        with self._connect() as connection:
            connection.execute("INSERT INTO integration_decisions VALUES (?, ?)",
                               (record["trace_id"], json.dumps(record)))

    def trace(self, trace_id: str) -> dict | None:
        with self._connect() as connection:
            row = connection.execute("SELECT record_json FROM integration_decisions WHERE trace_id = ?", (trace_id,)).fetchone()
            return json.loads(row[0]) if row else None

    def ingest(self, event: dict, record: dict) -> tuple[bool, str]:
        """Commit normalized ingestion and its routing decision atomically."""
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute("SELECT event_json FROM business_events WHERE event_id = ?", (event["event_id"],)).fetchone()
            if row:
                original = json.loads(row[0])
                if original["context"]["body_sha256"] != event["context"]["body_sha256"]:
                    raise ValueError("event_id_payload_conflict")
                return False, original["context"]["correlation_id"]
            connection.execute("INSERT INTO business_events (event_id,event_type,schema_version,occurred_at,source,entity_type,entity_id,event_json) VALUES (?,?,?,?,?,?,?,?)",
                (event["event_id"], event["event_type"], event["schema_version"], event["occurred_at"], event["source"], event["entity"]["type"], event["entity"]["id"], json.dumps(event)))
            connection.execute("INSERT INTO integration_decisions VALUES (?,?)", (record["trace_id"], json.dumps(record)))
            return True, record["trace_id"]

    def get(self, event_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT event_json FROM business_events WHERE event_id = ?",
                (event_id,),
            ).fetchone()
        return json.loads(row["event_json"]) if row else None

    def count(self) -> int:
        with self._connect() as connection:
            row = connection.execute("SELECT COUNT(*) AS count FROM business_events").fetchone()
        return int(row["count"])
