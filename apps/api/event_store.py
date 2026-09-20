"""Durable business-event store for Sonic AI V3."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class EventStore:
    def __init__(self, database_path: str | Path = "data/sonic_events.sqlite3") -> None:
        self.database_path = str(database_path)
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
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
            return False

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
