import asyncio
import sqlite3
from time import monotonic
from uuid import uuid4

import httpx
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from ..config import settings
from ..database import engine
from .config import ControlConfig
from .models import DecisionRecord, IntegrationStatus, now
from .providers import OpenAIAdapter, ShopifyAdapter
from .store import EventStore


class ControlPlane:
    def __init__(self, config: ControlConfig, store: EventStore, *, api_serving: bool = False):
        self.config, self.store = config, store
        self.api_serving = api_serving
        self.openai, self.shopify = OpenAIAdapter(settings), ShopifyAdapter(config)
        self._latest: list[IntegrationStatus] = []
        self._checked = 0.0
        self._lock = asyncio.Lock()
        self.trace_ids: list[str] = []

    def status(self):
        database = IntegrationStatus(provider="database", configured=True, checked_at=now())
        try:
            with engine.connect() as connection:
                connection.execute(text("SELECT 1"))
            database.reachable = True
            database.validation_status = "VALIDATED"
            database.last_successful_check = database.checked_at
            database.evidence = ["Application SQLite SELECT 1 succeeded; authentication not applicable"]
        except SQLAlchemyError:
            database.reachable = False
            database.validation_status = "FAILED"
            database.last_error = "database_query_failed"
        events = IntegrationStatus(provider="event_ingestion", configured=bool(self.config.webhook_secret and self.config.valid_shop),
            validation_status="CONFIGURED" if self.config.webhook_secret and self.config.valid_shop else "NOT_CONFIGURED",
            degraded_capabilities=["live_delivery_not_tested", "automatic_actions_disabled"])
        try:
            self.store.count()
            events.evidence = ["Durable event store query succeeded"]
        except sqlite3.Error:
            events.validation_status = "FAILED"
            events.last_error = "event_store_query_failed"
        fresh = bool(self._latest) and monotonic() - self._checked < 60
        providers = self._latest if fresh else [self.openai.configuration(), self.shopify.configuration()]
        if not fresh:
            previous = {s.provider: s for s in self._latest}
            for item in providers:
                old = previous.get(item.provider)
                if old is not None:
                    item.checked_at = old.checked_at
                    item.last_successful_check = old.last_successful_check
                    item.last_error = old.last_error
                    item.evidence = ["Previous check expired; run POST /integrations/check for current connectivity"]
        return {
            "checked_at": now().isoformat(), "provider_checks_fresh": fresh,
            "provider_check_ttl_seconds": 60, "trace_ids": self.trace_ids,
            "integrations": [s.model_dump(mode="json") for s in [
                IntegrationStatus(provider="api", configured=True, reachable=True if self.api_serving else None, checked_at=now(),
                    validation_status="VALIDATED" if self.api_serving else "NOT_TESTED",
                    evidence=["API handler executing" if self.api_serving else "Local service probe; HTTP API not probed"]),
                database, *providers,
                IntegrationStatus(provider="mcp", configured=self.config.auth_configured,
                    validation_status="CONFIGURED" if self.config.auth_configured else "NOT_CONFIGURED",
                    evidence=["MCP transport requires a separate client initialization probe"],
                    degraded_capabilities=["public_endpoint_not_validated", "chatgpt_connection_not_validated", "mutations_disabled"]),
                events]],
        }

    async def check(self, client: httpx.AsyncClient | None = None):
        async with self._lock:
            if self._latest and monotonic() - self._checked < 30:
                return self.status()
            if client is None:
                async with httpx.AsyncClient(timeout=8.0, follow_redirects=False) as owned:
                    results = await asyncio.gather(self.openai.check(owned), self.shopify.check(owned))
            else:
                results = await asyncio.gather(self.openai.check(client), self.shopify.check(client))
            trace_ids = []
            previous = {s.provider: s for s in self._latest}
            for result in results:
                if result.last_successful_check is None and result.provider in previous:
                    result.last_successful_check = previous[result.provider].last_successful_check
                record = DecisionRecord(trace_id=str(uuid4()), provider=result.provider,
                    requested_operation="integration_health_check",
                    evidence=result.evidence + ([result.last_error] if result.last_error else []),
                    validation_status=result.validation_status, resulting_state=result.validation_status,
                    integration_status=result)
                self.store.record(record.model_dump(mode="json"))
                trace_ids.append(record.trace_id)
            self._latest, self._checked, self.trace_ids = results, monotonic(), trace_ids
            return self.status()
