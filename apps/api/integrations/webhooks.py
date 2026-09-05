"""Authenticated Admin webhooks -> existing canonical event envelope."""
import base64
import hashlib
import hmac
import json
import sqlite3
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException, Request
from .models import DecisionRecord, now

router = APIRouter()
TOPICS = {"products/create": "product_created", "products/update": "product_updated"}


@router.post("/integrations/shopify/webhooks", include_in_schema=False)
async def receive_webhook(request: Request):
    plane = request.app.state.control_plane
    config = plane.config
    if not config.webhook_secret or not config.valid_shop:
        raise HTTPException(503, "webhook_not_configured")
    raw = bytearray()
    async for chunk in request.stream():
        raw.extend(chunk)
        if len(raw) > 1_048_576:
            raise HTTPException(413, "webhook_too_large")
    expected = base64.b64encode(hmac.new(config.webhook_secret.encode(), raw, hashlib.sha256).digest())
    if not hmac.compare_digest(expected, request.headers.get("x-shopify-hmac-sha256", "").encode()):
        raise HTTPException(401, "invalid_webhook_signature")
    if request.headers.get("x-shopify-shop-domain", "").lower() != config.shop_domain:
        raise HTTPException(403, "unexpected_shop")
    topic = request.headers.get("x-shopify-topic", "")
    if topic not in TOPICS:
        raise HTTPException(422, "unsupported_webhook_topic")
    if request.headers.get("x-shopify-api-version") != config.shop_version:
        raise HTTPException(422, "unsupported_webhook_version")
    try:
        provider_id = str(UUID(request.headers.get("x-shopify-event-id", "")))
        payload = json.loads(raw)
        product_id = payload["id"]
        if type(product_id) is not int or product_id <= 0:
            raise ValueError()
    except (ValueError, TypeError, KeyError):
        raise HTTPException(422, "invalid_webhook_payload_or_event_id") from None
    trace_id = str(uuid4())
    record = DecisionRecord(trace_id=trace_id, provider="shopify", actor="shopify_webhook",
        requested_operation="ingest_product_event",
        evidence=["Raw-body HMAC verified", "Configured shop, topic, version and product ID validated",
                  "Proposed catalog review; external mutation disabled"],
        validation_status="VALIDATED", resulting_state="PROPOSED")
    # Do not retain arbitrary product descriptions, secrets, or customer data.
    event = {"event_id": f"shopify:{config.shop_domain}:{topic}:{provider_id}",
        "event_type": TOPICS[topic], "schema_version": "1.0", "occurred_at": now().isoformat(),
        "source": "shopify", "entity": {"type": "product", "id": str(product_id)},
        "context": {"correlation_id": trace_id, "provider_event_id": provider_id,
                    "body_sha256": hashlib.sha256(raw).hexdigest(), "timestamp_basis": "received_at"},
        "properties": {"proposal": "review_catalog_change", "status": "PROPOSED"}, "outcome": "success"}
    try:
        inserted, trace_id = plane.store.ingest(event, record.model_dump(mode="json"))
    except ValueError:
        raise HTTPException(409, "event_id_payload_conflict") from None
    except sqlite3.Error:
        raise HTTPException(503, "durable_ingestion_failed_retry_delivery") from None
    return {"accepted": True, "duplicate": not inserted, "event_id": event["event_id"], "trace_id": trace_id}
