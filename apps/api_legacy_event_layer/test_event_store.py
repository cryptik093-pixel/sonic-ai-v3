from pathlib import Path

from event_store import EventStore


def make_event(event_id: str = "evt_test") -> dict:
    return {
        "event_id": event_id,
        "event_type": "purchase_completed",
        "schema_version": "1.0",
        "occurred_at": "2026-08-24T13:20:00.000Z",
        "source": "shopify",
        "entity": {"type": "order", "id": "order_123"},
        "properties": {"value": 19},
        "revenue_impact": 19,
        "currency": "USD",
    }


def test_event_store_persists_and_reads(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events.sqlite3")
    event = make_event()

    assert store.append(event) is True
    assert store.get("evt_test") == event
    assert store.count() == 1


def test_event_store_is_idempotent(tmp_path: Path) -> None:
    store = EventStore(tmp_path / "events.sqlite3")
    event = make_event()

    assert store.append(event) is True
    assert store.append(event) is False
    assert store.count() == 1
