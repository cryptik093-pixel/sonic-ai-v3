"""Stage One commerce trust boundaries and signed-ledger reconciliation contracts."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

from apps.api.event_store import EventStore
from apps.api.intelligence_store import IntelligenceStore
from apps.api.main import app
from apps.api.services.commerce_evidence import CommerceEvidenceService
from apps.api.shopify_webhooks import canonicalize_shopify_webhook

SHOP = "omega-house.myshopify.com"
SECRET = "local-test-webhook-secret"
TOKEN = "local-commerce-operator-token"
AT = "2026-10-19T16:00:00Z"


def _headers(topic: str, event_id: str, payload: dict, *, shop: str = SHOP) -> tuple[bytes, dict]:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    signature = base64.b64encode(hmac.new(SECRET.encode(), body, hashlib.sha256).digest()).decode()
    return body, {
        "x-shopify-topic": topic,
        "x-shopify-event-id": event_id,
        "x-shopify-shop-domain": shop,
        "x-shopify-triggered-at": AT,
        "x-shopify-hmac-sha256": signature,
    }


def _order(order_id=1001, *, status="paid", total="35.00", updated_at=AT, landing="/collections/beats?utm_source=instagram&utm_campaign=field001"):
    return {
        "id": order_id, "admin_graphql_api_id": f"gid://shopify/Order/{order_id}",
        "current_total_price": total, "currency": "USD",
        "financial_status": status, "updated_at": updated_at, "landing_site": landing,
        "line_items": [{"sku": "OHB-FPS-001", "quantity": 1, "product_id": 789}],
    }


@pytest.fixture
def harness(monkeypatch, tmp_path):
    monkeypatch.delenv("SONIC_DESKTOP_MODE", raising=False)
    monkeypatch.setenv("SONIC_CONTROL_PLANE_TOKEN", TOKEN)
    monkeypatch.setenv("SONIC_SHOPIFY_SHOP_DOMAIN", SHOP)
    monkeypatch.setenv("SONIC_SHOPIFY_WEBHOOK_SECRET", SECRET)
    monkeypatch.setenv("SONIC_EVENT_DB", str(tmp_path / "events.sqlite3"))
    monkeypatch.setenv("SONIC_INTELLIGENCE_DB", str(tmp_path / "intelligence.sqlite3"))
    monkeypatch.setenv("SONIC_DATA_DIR", str(tmp_path))
    with TestClient(app, base_url="http://localhost") as client:
        yield client, tmp_path


def _post(client, topic, event_id, payload, **overrides):
    body, headers = _headers(topic, event_id, payload, **overrides)
    return client.post("/api/v1/webhooks/shopify", content=body, headers=headers)


def _status(client):
    r = client.get("/workbench/api/intelligence/commerce/status",
                   headers={"Authorization": f"Bearer {TOKEN}"})
    assert r.status_code == 200, r.text
    return r.json()


def test_signed_order_is_projected_once_and_replayed_idempotently(harness):
    client, root = harness
    assert client.get("/workbench/api/intelligence/commerce/status").status_code == 401
    payload = _order()
    first = _post(client, "orders/create", "order-event-1", payload)
    assert first.status_code == 202, first.text
    assert first.json()["duplicate"] is False

    again = _post(client, "orders/create", "order-event-1", payload)
    assert again.status_code == 202, again.text
    assert again.json()["duplicate"] is True

    reported = _status(client)
    assert reported["signed_event_count"] == 1
    assert reported["unique_order_count"] == 1
    assert reported["reported_paid_order_count"] == 1
    assert reported["reported_paid_order_totals_by_currency"] == {"USD": "35.00"}
    assert reported["reported_paid_orders_with_campaign_parameters"] == 1
    assert reported["settled_net_revenue"] is None

    ledger = IntelligenceStore(root / "intelligence.sqlite3")
    assert ledger.counts()["evidence"] == 1
    replay = client.post("/workbench/api/intelligence/commerce/replay",
                         headers={"Authorization": f"Bearer {TOKEN}"})
    assert replay.status_code == 200, replay.text
    assert replay.json() == {"projected": 0, "already_projected": 1}
    assert ledger.counts()["evidence"] == 1


def test_paid_order_update_replaces_snapshot_without_double_counting(harness):
    client, _ = harness
    _post(client, "orders/create", "order-new", _order(status="pending"))
    _post(client, "orders/updated", "order-paid", _order(status="paid", updated_at="2026-10-19T17:00:00Z"))
    report = _status(client)
    assert report["signed_event_count"] == 2
    assert report["unique_order_count"] == 1
    assert report["reported_paid_order_count"] == 1


def test_product_and_refund_are_separate_evidence_without_assumed_net(harness):
    client, _ = harness
    product = {"id": 42, "admin_graphql_api_id": "gid://shopify/Product/42",
               "status": "active", "handle": "producer-starter",
               "variants": [{"id": 777, "sku": "OHB-FPS-001", "price": "5.00"}]}
    assert _post(client, "products/update", "product-event-1", product).status_code == 202
    refund = {"id": 2001, "order_id": 1001, "transactions": [{"amount": "5.00", "currency": "USD"}]}
    assert _post(client, "refunds/create", "refund-event-1", refund).status_code == 202
    report = _status(client)
    assert report["unique_product_count"] == 1
    assert report["unique_refund_count"] == 1
    assert report["unmatched_refund_count"] == 1
    assert report["settled_net_revenue"] is None
    assert _post(client, "orders/create", "order-event-1", _order()).status_code == 202
    assert _status(client)["unmatched_refund_count"] == 0


def test_invalid_signature_shop_and_modified_duplicate_are_rejected(harness):
    client, _ = harness
    body, headers = _headers("orders/create", "evt", _order())
    bad = dict(headers, **{"x-shopify-hmac-sha256": "tampered"})
    assert client.post("/api/v1/webhooks/shopify", content=body, headers=bad).status_code == 401
    assert _post(client, "orders/create", "evt", _order(), shop="attacker.myshopify.com").status_code == 403
    assert _post(client, "orders/create", "evt", _order()).status_code == 202
    assert _post(client, "orders/create", "evt", _order(total="99.00")).status_code == 409
    assert _status(client)["signed_event_count"] == 1


def test_generic_events_cannot_forge_signed_shopify_receipts(harness):
    client, root = harness
    forged = {"event_id": "shopify:orders/create:fake", "event_type": "order_created",
              "occurred_at": AT, "source": "shopify_webhook",
              "entity": {"type": "order", "id": "gid://shopify/Order/999"}}
    assert client.post("/api/v1/events", json=forged).status_code == 403
    assert _status(client)["signed_event_count"] == 0

    event = canonicalize_shopify_webhook("orders/create",
        {"x-shopify-event-id": "legacy", "x-shopify-shop-domain": SHOP, "x-shopify-triggered-at": AT},
        _order())
    store = EventStore(root / "events.sqlite3")
    assert store.append(event) is True
    with pytest.raises(ValueError, match="lacks signed receipt"):
        store.append_verified_shopify(event, "0" * 64)
    assert _status(client)["signed_event_count"] == 0


def test_replay_repairs_durable_receipt_after_projection_interruption(harness):
    client, root = harness
    event = canonicalize_shopify_webhook("orders/create",
        {"x-shopify-event-id": "repair", "x-shopify-shop-domain": SHOP, "x-shopify-triggered-at": AT},
        _order())
    store = EventStore(root / "events.sqlite3")
    assert store.append_verified_shopify(event, "0" * 64)
    assert IntelligenceStore(root / "intelligence.sqlite3").counts()["evidence"] == 0

    repair = client.post("/workbench/api/intelligence/commerce/replay",
                         headers={"Authorization": f"Bearer {TOKEN}"})
    assert repair.status_code == 200, repair.text
    assert repair.json()["projected"] == 1
    assert IntelligenceStore(root / "intelligence.sqlite3").counts()["evidence"] == 1
