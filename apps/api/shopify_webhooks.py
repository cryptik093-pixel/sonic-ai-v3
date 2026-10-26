"""Authenticated Shopify webhook adapter for Sonic AI V3."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import re
from urllib.parse import parse_qs, urlsplit
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request, Response, status

from .event_store import EventStore


router = APIRouter(prefix="/api/v1/webhooks/shopify", tags=["shopify-webhooks"])

_SUPPORTED_TOPICS = {"orders/create", "orders/updated", "refunds/create", "customers/update", "products/create", "products/update"}


def verify_shopify_hmac(raw_body: bytes, provided_hmac: str, secret: str) -> bool:
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
    stable_id = (
        headers.get("x-shopify-event-id")
        or headers.get("x-shopify-webhook-id")
        or _string_id(payload.get("id"))
    )
    if stable_id is None:
        raise HTTPException(status_code=400, detail="Shopify webhook has no stable event identifier")
    return f"shopify:{topic}:{stable_id}"


def _acquisition(landing_site: Any) -> dict[str, str]:
    if not isinstance(landing_site, str):
        return {}
    params = parse_qs(urlsplit(landing_site).query)
    allowed = {"utm_source", "utm_medium", "utm_campaign", "utm_content", "campaign_id", "creative_id", "placement"}
    return {key: params[key][0] for key in allowed if key in params and re.fullmatch(r"[a-zA-Z0-9_.-]{1,120}", params[key][0])}


def canonicalize_shopify_webhook(topic: str, headers: Any, payload: dict[str, Any]) -> dict[str, Any]:
    if topic not in _SUPPORTED_TOPICS:
        raise HTTPException(status_code=422, detail=f"Unsupported Shopify webhook topic: {topic}")

    context = {
        "shop_domain": headers.get("x-shopify-shop-domain"),
        "shopify_topic": topic,
        "api_version": headers.get("x-shopify-api-version"),
        "shopify_event_id": headers.get("x-shopify-event-id"),
    }

    if topic in {"orders/create", "orders/updated"}:
        order_id = _string_id(payload.get("admin_graphql_api_id") or payload.get("id"))
        if order_id is None:
            raise HTTPException(status_code=400, detail="Order webhook is missing order id")
        customer = payload.get("customer") if isinstance(payload.get("customer"), dict) else {}
        customer_id = _string_id(customer.get("admin_graphql_api_id") or customer.get("id"))
        total = payload.get("current_total_price") or payload.get("total_price")
        revenue_impact = None
        try:
            if total is not None:
                revenue_impact = float(total)
        except (TypeError, ValueError):
            pass
        return {
            "event_id": _event_id(topic, headers, payload),
            "event_type": "order_created" if topic == "orders/create" else "order_updated",
            "schema_version": "1.0",
            "occurred_at": _occurred_at(headers, payload),
            "source": "shopify_webhook",
            "entity": {"type": "order", "id": order_id},
            "actor": {"customer_id": customer_id} if customer_id else None,
            "context": context,
            "properties": {
                "name": payload.get("name"),
                "financial_status": payload.get("financial_status"),
                "test": payload.get("test") is True,
                "reported_total_amount": str(total) if total is not None else None,
                "fulfillment_status": payload.get("fulfillment_status"),
                "source_name": payload.get("source_name"),
                "line_items": [{"sku": x.get("sku"), "product_id": str(x.get("product_id")), "quantity": x.get("quantity")} for x in payload.get("line_items", []) if isinstance(x, dict)],
                "acquisition": _acquisition(payload.get("landing_site")),
                "updated_at": payload.get("updated_at"),
            },
            "outcome": "order_created",
            "revenue_impact": revenue_impact,
            "currency": payload.get("currency") or payload.get("presentment_currency"),
        }

    if topic == "refunds/create":
        refund_id = _string_id(payload.get("admin_graphql_api_id") or payload.get("id"))
        if refund_id is None:
            raise HTTPException(status_code=400, detail="Refund webhook is missing refund id")
        transactions = payload.get("transactions") if isinstance(payload.get("transactions"), list) else []
        refunded_amount = 0.0
        has_amount = False
        currency = None
        for transaction in transactions:
            if not isinstance(transaction, dict):
                continue
            if currency is None:
                currency = transaction.get("currency")
            try:
                amount = transaction.get("amount")
                if amount is not None:
                    refunded_amount += float(amount)
                    has_amount = True
            except (TypeError, ValueError):
                continue
        context["order_id"] = _string_id(payload.get("order_id"))
        return {
            "event_id": _event_id(topic, headers, payload),
            "event_type": "refund",
            "schema_version": "1.0",
            "occurred_at": _occurred_at(headers, payload),
            "source": "shopify_webhook",
            "entity": {"type": "refund", "id": refund_id},
            "actor": None,
            "context": context,
            "properties": {
                "note": payload.get("note"),
                "refund_line_items": payload.get("refund_line_items", []),
                "transactions": [{"amount": x.get("amount"), "currency": x.get("currency"), "status": x.get("status")} for x in transactions if isinstance(x, dict)],
            },
            "outcome": "refund_created",
            "revenue_impact": -refunded_amount if has_amount else None,
            "currency": currency,
        }

    if topic in {"products/create", "products/update"}:
        product_id = _string_id(payload.get("admin_graphql_api_id") or payload.get("id"))
        if product_id is None:
            raise HTTPException(status_code=400, detail="Product webhook is missing product id")
        return {
            "event_id": _event_id(topic, headers, payload),
            "event_type": "product_created" if topic == "products/create" else "product_updated",
            "schema_version": "1.0",
            "occurred_at": _occurred_at(headers, payload),
            "source": "shopify_webhook",
            "entity": {"type": "product", "id": product_id},
            "actor": None,
            "context": context,
            "properties": {
                "handle": payload.get("handle"),
                "status": payload.get("status"),
                "updated_at": payload.get("updated_at"),
                "variants": [
                    {"id": _string_id(x.get("admin_graphql_api_id") or x.get("id")),
                     "sku": x.get("sku"), "price": x.get("price")}
                    for x in payload.get("variants", []) if isinstance(x, dict)
                ],
            },
            "outcome": "catalog_change",
            "revenue_impact": None,
            "currency": None,
        }

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
        "context": context,
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


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def ingest_shopify_webhook(request: Request) -> dict[str, Any]:
    from .integrations.config import ControlConfig
    from .services.commerce_evidence import CommerceEvidenceService

    config = ControlConfig.from_env()
    secret = config.webhook_secret or os.getenv("SHOPIFY_WEBHOOK_SECRET", "")
    if not secret or not config.valid_shop:
        raise HTTPException(status_code=503, detail="Shopify webhook not configured")

    raw_body = await request.body()
    if len(raw_body) > 1_048_576:
        raise HTTPException(status_code=413, detail="Shopify webhook too large")
    if not verify_shopify_hmac(raw_body, request.headers.get("x-shopify-hmac-sha256", ""), secret):
        raise HTTPException(status_code=401, detail="Invalid Shopify webhook signature")
    if request.headers.get("x-shopify-shop-domain", "").strip().lower() != config.shop_domain:
        raise HTTPException(status_code=403, detail="Unexpected Shopify shop")

    topic = request.headers.get("x-shopify-topic", "").lower().strip()
    try:
        payload = json.loads(raw_body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid Shopify webhook JSON") from exc
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Shopify webhook payload must be an object")

    event = canonicalize_shopify_webhook(topic, request.headers, payload)
    evidence = CommerceEvidenceService.from_env()
    try:
        inserted = evidence.events.append_verified_shopify(event, hashlib.sha256(raw_body).hexdigest())
        evidence.project(event)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
    except Exception as exc:
        # Durable receipt survives projection errors; a retry or replay repairs it.
        raise HTTPException(status_code=503, detail="Commerce projection unavailable; retry delivery") from exc
    return {"accepted": True, "duplicate": not inserted,
            "event_id": event["event_id"], "event_type": event["event_type"]}


@router.get("/health", include_in_schema=False)
def shopify_webhook_health() -> Response:
    return Response(status_code=status.HTTP_204_NO_CONTENT)
