"""Authenticated Shopify webhook adapter for the Sonic AI V3 event backbone.

This router converts authoritative Shopify commerce webhooks into the canonical
BusinessEvent envelope persisted by Gate 2. It deliberately accepts only topics
with explicit mappings so unsupported Shopify events cannot silently pollute the
Sonic Intelligence event store.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response, status

from event_store import EventStore


router = APIRouter(prefix="/api/v1/webhooks/shopify", tags=["shopify-webhooks"])
store = EventStore(os.getenv("SONIC_EVENT_DB", "data/sonic_events.sqlite3"))

_TOPIC_MAP = {
    "orders/create": "order_created",
    "refunds/create": "refund",
    "customers/update": "customer_updated",
}


def verify_shopify_hmac(raw_body: bytes, provided_hmac: str, secret: str) -> bool:
    """Verify Shopify's base64-encoded HMAC-SHA256 signature."""
    if not raw_body or not provided_hmac or not secret:
        return False
    digest = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).digest()
    computed = base64.b64encode(digest).decode("utf-8")
    return hmac.compare_digest(provided_hmac, computed)


def _string_id(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _occurred_at(headers: Any, payload: dict[str, Any]) -> str:
    return (
        headers.get("x-shopify-triggered-at")
        or payload.get("updated_at")
        or payload.get("created_at")
        or datetime.now(UTC).isoformat()
    )


def _event_id(topic: str, headers: Any, payload: dict[str, Any]) -> str:
    # Event ID is stable across retries caused by the same merchant action. Prefix
    # with topic so a single merchant action producing multiple topics cannot clash.
    stable_id = (
        headers.get("x-shopify-event-id")
        or headers.get("x-shopify-webhook-id")
        or _string_id(payload.get("id"))
    )
    if stable_id is None:
        raise HTTPException(status_code=400, detail="Shopify webhook has no stable event identifier")
    return f"shopify:{topic}:{stable_id}"


def _order_event(topic: str, headers: Any, payload: dict[str, Any]) -> dict[str, Any]:
    order_id = _string_id(payload.get("admin_graphql_api_id") or payload.get("id"))
    if order_id is None:
        raise HTTPException(status_code=400, detail="Order webhook is missing order id")

    customer = payload.get("customer") if isinstance(payload.get("customer"), dict) else {}
    customer_id = _string_id(customer.get("admin_graphql_api_id") or customer.get("id"))
    total = payload.get("current_total_price") or payload.get("total_price")
    currency = payload.get("currency") or payload.get("presentment_currency")

    revenue_impact: float | None = None
    try:
        if total is not None:
            revenue_impact = float(total)
    except (TypeError, ValueError):
        revenue_impact = None

    return {
        "event_id": _event_id(topic, headers, payload),
        "event_type": "order_created",
        "schema_version": "1.0",
        "occurred_at": _occurred_at(headers, payload),
        "source": "shopify_webhook",
        "entity": {"type": "order", "id": order_id},
        "actor": {"customer_id": customer_id} if customer_id else None,
        "context": {
            "shop_domain": headers.get("x-shopify-shop-domain"),
            "shopify_topic": topic,
            "api_version": headers.get("x-shopify-api-version"),
            "webhook_id": headers.get("x-shopify-webhook-id"),
            "shopify_event_id": headers.get("x-shopify-event-id"),
        },
        "properties": {
            "name": payload.get("name"),
            "financial_status": payload.get("financial_status"),
            "fulfillment_status": payload.get("fulfillment_status"),
            "source_name": payload.get("source_name"),
            "landing_site": payload.get("landing_site"),
            "referring_site": payload.get("referring_site"),
            "line_items": payload.get("line_items", []),
        },
        "outcome": "order_created",
        "revenue_impact": revenue_impact,
        "currency": currency,
    }


def _refund_event(topic: str, headers: Any, payload: dict[str, Any]) -> dict[str, Any]:
    refund_id = _string_id(payload.get("admin_graphql_api_id") or payload.get("id"))
    if refund_id is None:
        raise HTTPException(status_code=400, detail="Refund webhook is missing refund id")

    order_id = _string_id(payload.get("order_id"))
    transactions = payload.get("transactions") if isinstance(payload.get("transactions"), list) else []
    refunded_amount = 0.0
    has_amount = False
    currency: str | None = None
    for transaction in transactions:
        if not isinstance(transaction, dict):
            continue
        amount = transaction.get("amount")
        if currency is None:
            currency = transaction.get("currency")
        try:
            if amount is not None:
                refunded_amount += float(amount)
                has_amount = True
        except (TypeError, ValueError):
            continue

    return {
        "event_id": _event_id(topic, headers, payload),
        "event_type": "refund",
        "schema_version": "1.0",
        "occurred_at": _occurred_at(headers, payload),
        "source": "shopify_webhook",
        "entity": {"type": "refund", "id": refund_id},
        "actor": None,
        "context": {
            "shop_domain": headers.get("x-shopify-shop-domain"),
            "shopify_topic": topic,
            "api_version": headers.get("x-shopify-api-version"),
            "webhook_id": headers.get("x-shopify-webhook-id"),
            "shopify_event_id": headers.get("x-shopify-event-id"),
            "order_id": order_id,
        },
        "properties": {
            "note": payload.get("note"),
            "refund_line_items": payload.get("refund_line_items", []),
            "transactions": transactions,
        },
        "outcome": "refund_created",
        "revenue_impact": -refunded_amount if has_amount else None,
        "currency": currency,
    }


def _customer_event(topic: str, headers: Any, payload: dict[str, Any]) -> dict[str, Any]:
    customer_id = _string_id(payload.get("admin_graphql_api_id") or payload.get("id"))
    if customer_id is None:
        raise HTTPException(status_code=400, detail="Customer webhook is missing customer id")

    return {
        "event_id": _event_id(topic, headers, payload),
        "event_type": "customer_updated",
        "schema_version": "1.0",
        "occurred_at": _occurred_at(headers, payload),
        "source": "shopify_webhook",
        "entity": {"type": "customer", "id": customer_id},
        "actor": {"customer_id": customer_id},
        "context": {
            "shop_domain": headers.get("x-shopify-shop-domain"),
            "shopify_topic": topic,
            "api_version": headers.get("x-shopify-api-version"),
            "webhook_id": headers.get("x-shopify-webhook-id"),
            "shopify_event_id": headers.get("x-shopify-event-id"),
        },
        "properties": {
            "orders_count": payload.get("orders_count"),
            "total_spent": payload.get("total_spent"),
            "tags": payload.get("tags"),
            "state": payload.get("state"),
            "verified_email": payload.get("verified_email"),
        },
        "outcome": "customer_updated",
        "revenue_impact": None,
        "currency": payload.get("currency"),
    }


def canonicalize_shopify_webhook(topic: str, headers: Any, payload: dict[str, Any]) -> dict[str, Any]:
    """Map a supported Shopify webhook into the canonical Sonic event envelope."""
    if topic not in _TOPIC_MAP:
        raise HTTPException(status_code=422, detail=f"Unsupported Shopify webhook topic: {topic}")
    if topic == "orders/create":
        return _order_event(topic, headers, payload)
    if topic == "refunds/create":
        return _refund_event(topic, headers, payload)
    return _customer_event(topic, headers, payload)


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def ingest_shopify_webhook(request: Request) -> dict[str, Any]:
    secret = os.getenv("SHOPIFY_WEBHOOK_SECRET", "")
    if not secret:
        raise HTTPException(status_code=503, detail="SHOPIFY_WEBHOOK_SECRET is not configured")

    raw_body = await request.body()
    provided_hmac = request.headers.get("x-shopify-hmac-sha256", "")
    if not verify_shopify_hmac(raw_body, provided_hmac, secret):
        raise HTTPException(status_code=401, detail="Invalid Shopify webhook signature")

    topic = request.headers.get("x-shopify-topic", "").lower().strip()
    if not topic:
        raise HTTPException(status_code=400, detail="Missing X-Shopify-Topic header")

    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid Shopify webhook JSON") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Shopify webhook payload must be an object")

    event = canonicalize_shopify_webhook(topic, request.headers, payload)
    inserted = store.append(event)
    return {
        "accepted": True,
        "duplicate": not inserted,
        "event_id": event["event_id"],
        "event_type": event["event_type"],
    }


@router.get("/health", include_in_schema=False)
def shopify_webhook_health() -> Response:
    """Receiver health without exposing webhook secret state."""
    return Response(status_code=status.HTTP_204_NO_CONTENT)
