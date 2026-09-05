from __future__ import annotations

import base64
import hashlib
import hmac

from shopify_webhooks import canonicalize_shopify_webhook, verify_shopify_hmac


class Headers(dict):
    def get(self, key: str, default=None):
        return super().get(key.lower(), default)


def _headers(topic: str, event_id: str = "evt-123") -> Headers:
    return Headers(
        {
            "x-shopify-topic": topic,
            "x-shopify-event-id": event_id,
            "x-shopify-webhook-id": "delivery-456",
            "x-shopify-shop-domain": "omega-house.myshopify.com",
            "x-shopify-api-version": "2026-04",
            "x-shopify-triggered-at": "2026-09-05T08:00:00Z",
        }
    )


def test_verify_shopify_hmac_accepts_valid_signature() -> None:
    body = b'{"id":123}'
    secret = "test-secret"
    signature = base64.b64encode(
        hmac.new(secret.encode("utf-8"), body, hashlib.sha256).digest()
    ).decode("utf-8")
    assert verify_shopify_hmac(body, signature, secret) is True


def test_verify_shopify_hmac_rejects_invalid_signature() -> None:
    assert verify_shopify_hmac(b'{"id":123}', "invalid", "test-secret") is False


def test_order_create_maps_to_canonical_event() -> None:
    event = canonicalize_shopify_webhook(
        "orders/create",
        _headers("orders/create"),
        {
            "id": 1001,
            "admin_graphql_api_id": "gid://shopify/Order/1001",
            "name": "#1001",
            "current_total_price": "35.00",
            "currency": "USD",
            "financial_status": "paid",
            "customer": {
                "id": 501,
                "admin_graphql_api_id": "gid://shopify/Customer/501",
            },
            "line_items": [{"id": 1, "title": "Wasted", "quantity": 1}],
        },
    )
    assert event["event_id"] == "shopify:orders/create:evt-123"
    assert event["event_type"] == "order_created"
    assert event["entity"] == {"type": "order", "id": "gid://shopify/Order/1001"}
    assert event["actor"]["customer_id"] == "gid://shopify/Customer/501"
    assert event["revenue_impact"] == 35.0
    assert event["currency"] == "USD"


def test_refund_create_maps_negative_revenue_impact() -> None:
    event = canonicalize_shopify_webhook(
        "refunds/create",
        _headers("refunds/create", event_id="refund-action"),
        {
            "id": 2001,
            "admin_graphql_api_id": "gid://shopify/Refund/2001",
            "order_id": 1001,
            "transactions": [
                {"amount": "20.00", "currency": "USD"},
                {"amount": "5.00", "currency": "USD"},
            ],
            "refund_line_items": [],
        },
    )
    assert event["event_id"] == "shopify:refunds/create:refund-action"
    assert event["event_type"] == "refund"
    assert event["revenue_impact"] == -25.0
    assert event["currency"] == "USD"


def test_customer_update_maps_customer_entity() -> None:
    event = canonicalize_shopify_webhook(
        "customers/update",
        _headers("customers/update", event_id="customer-action"),
        {
            "id": 501,
            "admin_graphql_api_id": "gid://shopify/Customer/501",
            "orders_count": 3,
            "total_spent": "110.00",
        },
    )
    assert event["event_type"] == "customer_updated"
    assert event["entity"] == {"type": "customer", "id": "gid://shopify/Customer/501"}
    assert event["actor"]["customer_id"] == "gid://shopify/Customer/501"
