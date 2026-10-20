"""OMEGA SIGNAL-001: signed commerce receipts -> immutable intelligence evidence.

No inference of settled revenue, customer identity, or campaign causation.
"""
from __future__ import annotations

import os
from decimal import Decimal, InvalidOperation
from typing import Any

from ..event_store import EventStore
from ..intelligence_store import IntelligenceStore


def _amount(value: Any) -> Decimal | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = Decimal(str(value))
        return number if number.is_finite() and number >= 0 else None
    except (ValueError, InvalidOperation):
        return None


def _order_number(identifier: Any) -> str:
    return str(identifier or "").rsplit("/", 1)[-1]


class CommerceEvidenceService:
    """Project only HMAC-verified receipts; generic events cannot enter this ledger."""

    def __init__(self, events: EventStore, intelligence: IntelligenceStore, shop_domain: str):
        if not shop_domain:
            raise ValueError("Configured shop domain is required")
        self.events, self.intelligence, self.shop_domain = events, intelligence, shop_domain.lower()

    @classmethod
    def from_env(cls) -> "CommerceEvidenceService":
        return cls(
            EventStore(os.getenv("SONIC_EVENT_DB", "apps/api/data/sonic_events.sqlite3")),
            IntelligenceStore(),
            os.getenv("SONIC_SHOPIFY_SHOP_DOMAIN", "").strip().lower(),
        )

    def project(self, event: dict[str, Any]) -> bool:
        """Create stable, redacted, immutable evidence after signed receipt persistence."""
        if event.get("source") != "shopify_webhook" or (event.get("context") or {}).get("shop_domain") != self.shop_domain:
            raise ValueError("Event is outside the configured Shopify evidence scope")
        if not self.events.has_verified_shopify_receipt(event["event_id"], self.shop_domain):
            raise ValueError("Missing verified Shopify receipt")
        props = event.get("properties") or {}
        evidence = {
            "evidence_id": "commerce:" + event["event_id"],
            "intent_id": None,
            "kind": "deterministic_fact",
            "source": "signed_shopify_webhook",
            "observed_at": event["occurred_at"],
            "confidence": 1.0,
            "claim": "Authenticated commerce event observed; settlement, economics, and campaign causation are not independently verified.",
            "value": {
                "event_type": event["event_type"],
                "entity": event["entity"],
                "currency": event.get("currency"),
                "reported_amount": props.get("reported_total_amount") if event["event_type"] in {"order_created", "order_updated"} else event.get("revenue_impact"),
                "financial_status": props.get("financial_status"),
                "acquisition": props.get("acquisition") or {},
                "line_items": props.get("line_items") or [],
                "variants": props.get("variants") or [],
            },
            "scope": {"shop_domain": self.shop_domain},
            "provenance": [event["event_id"]],
        }
        return self.intelligence.append_evidence(evidence)["recorded"]

    def replay(self) -> dict[str, int]:
        """Idempotent repair after a crash between event commit and projection."""
        repaired, existing = 0, 0
        for event in self.events.verified_shopify_events(self.shop_domain):
            if self.project(event):
                repaired += 1
            else:
                existing += 1
        return {"projected": repaired, "already_projected": existing}

    def report(self) -> dict[str, Any]:
        """Diagnostic snapshot, never a settled-revenue or attribution claim."""
        events = self.events.verified_shopify_events(self.shop_domain)
        orders: dict[str, dict[str, Any]] = {}
        products: dict[str, dict[str, Any]] = {}
        refunds: dict[str, dict[str, Any]] = {}
        for event in events:
            typ, eid = event["event_type"], event["entity"]["id"]
            if typ in {"order_created", "order_updated"}:
                previous = orders.get(eid)
                props = event.get("properties") or {}
                timestamp = props.get("updated_at") or event["occurred_at"]
                priority = 1 if typ == "order_updated" else 0
                if previous is None or (timestamp, priority, event["event_id"]) > previous["_sort"]:
                    orders[eid] = {**event, "_sort": (timestamp, priority, event["event_id"])}
            elif typ in {"product_created", "product_updated"}:
                previous = products.get(eid)
                timestamp = (event.get("properties") or {}).get("updated_at") or event["occurred_at"]
                if previous is None or (timestamp, event["event_id"]) > previous["_sort"]:
                    products[eid] = {**event, "_sort": (timestamp, event["event_id"])}
            elif typ == "refund":
                refunds[eid] = event

        amounts: dict[str, Decimal] = {}
        paid_orders = 0
        attributed = 0
        invalid_amounts = 0
        for order in orders.values():
            props = order.get("properties") or {}
            if props.get("financial_status") != "paid":
                continue
            paid_orders += 1
            currency = order.get("currency")
            value = _amount(props.get("reported_total_amount", order.get("revenue_impact")))

            if not currency or value is None:
                invalid_amounts += 1
                continue
            amounts[currency] = amounts.get(currency, Decimal(0)) + value
            if props.get("acquisition"):
                attributed += 1

        known_order_numbers = {_order_number(x) for x in orders}
        unmatched_refunds = sum(
            1 for r in refunds.values()
            if _order_number((r.get("context") or {}).get("order_id")) not in known_order_numbers
        )
        return {
            "status": "signed_evidence_only" if events else "no_signed_evidence",
            "shop_domain": self.shop_domain,
            "signed_event_count": len(events),
            "unique_order_count": len(orders),
            "reported_paid_order_count": paid_orders,
            "reported_paid_order_totals_by_currency": {k: str(v) for k, v in sorted(amounts.items())},
            "reported_paid_orders_with_campaign_parameters": attributed,
            "invalid_or_missing_paid_amount_count": invalid_amounts,
            "unique_product_count": len(products),
            "unique_refund_count": len(refunds),
            "unmatched_refund_count": unmatched_refunds,
            "settled_net_revenue": None,
            "reconciliation_status": "incomplete_needs_shopify_admin_order_refund_reconciliation",
            "limitations": [
                "Webhook deliveries alone are not a complete order or settlement ledger.",
                "Reported paid status and total are not independently settled revenue.",
                "Campaign parameters are observed identifiers, not proven attribution.",
                "No conversion rate without qualified session denominator.",
            ],
        }
