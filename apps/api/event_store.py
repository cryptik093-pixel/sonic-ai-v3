"""Tier 5 Gate 2 durable event store.

Uses SQLite from the Python standard library so the event backbone has durable
storage without introducing a new database dependency. The store preserves the
canonical event envelope and enforces event_id uniqueness for idempotency.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from datetime import UTC, datetime
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
            # Unauthenticated generic events must never become commerce evidence.
            connection.execute("""
                CREATE TABLE IF NOT EXISTS verified_shopify_receipts (
                    event_id TEXT PRIMARY KEY,
                    shop_domain TEXT NOT NULL,
                    body_sha256 TEXT NOT NULL,
                    verified_at TEXT NOT NULL
                )
            """)

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
            existing = self.get(event["event_id"])
            if existing != event:
                raise ValueError("event_id_payload_conflict") from None
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

    def append_verified_shopify(self, event: dict[str, Any], body_sha256: str) -> bool:
        """Persist a signed webhook receipt and canonical event atomically.

        Call only after raw-body HMAC and configured shop verification.
        """
        if event.get("source") != "shopify_webhook":
            raise ValueError("verified receipt requires shopify_webhook source")
        shop = (event.get("context") or {}).get("shop_domain")
        if not shop or len(body_sha256) != 64:
            raise ValueError("missing receipt provenance")
        encoded = json.dumps(event, separators=(",", ":"), sort_keys=True)
        with self._connect() as c:
            c.execute("BEGIN IMMEDIATE")
            row = c.execute(
                "SELECT event_json FROM business_events WHERE event_id=?",
                (event["event_id"],),
            ).fetchone()
            if row and row["event_json"] != encoded:
                raise ValueError("event_id_payload_conflict")
            existing = c.execute(
                "SELECT shop_domain,body_sha256 FROM verified_shopify_receipts WHERE event_id=?",
                (event["event_id"],),
            ).fetchone()
            if row and not existing:
                raise ValueError("existing event lacks signed receipt; refusing to upgrade")
            if existing and (existing["shop_domain"] != shop or existing["body_sha256"] != body_sha256):
                raise ValueError("verified_receipt_payload_conflict")
            if not row:
                c.execute(
                    """INSERT INTO business_events
                       (event_id,event_type,schema_version,occurred_at,source,entity_type,entity_id,event_json)
                       VALUES (?,?,?,?,?,?,?,?)""",
                    (event["event_id"], event["event_type"], event["schema_version"],
                     event["occurred_at"], event["source"], event["entity"]["type"],
                     event["entity"]["id"], encoded),
                )
            if not existing:
                c.execute(
                    """INSERT INTO verified_shopify_receipts
                       (event_id,shop_domain,body_sha256,verified_at) VALUES (?,?,?,?)""",
                    (event["event_id"], shop, body_sha256, datetime.now(UTC).isoformat()),
                )
            return row is None


    def has_verified_shopify_receipt(self, event_id: str, shop_domain: str) -> bool:
        with self._connect() as c:
            row = c.execute(
                "SELECT 1 FROM verified_shopify_receipts WHERE event_id=? AND shop_domain=?",
                (event_id, shop_domain),
            ).fetchone()
        return row is not None

    def verified_shopify_events(self, shop_domain: str | None = None) -> list[dict[str, Any]]:
        """Read signed receipts only, never generic business events."""
        with self._connect() as c:
            if shop_domain:
                rows = c.execute(
                    """SELECT b.event_json FROM business_events b
                       JOIN verified_shopify_receipts r USING (event_id)
                       WHERE r.shop_domain=? ORDER BY b.event_id""",
                    (shop_domain,),
                ).fetchall()
            else:
                rows = c.execute(
                    """SELECT b.event_json FROM business_events b
                       JOIN verified_shopify_receipts r USING (event_id)
                       ORDER BY b.event_id"""
                ).fetchall()
        return [json.loads(row["event_json"]) for row in rows]
