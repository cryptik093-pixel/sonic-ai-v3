import asyncio
import base64
import hashlib
import hmac
import json
from dataclasses import replace
from uuid import uuid4

import httpx
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from apps.api.config import Settings
from apps.api.integrations.config import ControlConfig
from apps.api.integrations.models import IntegrationStatus
from apps.api.integrations.providers import OpenAIAdapter, ShopifyAdapter, compare_scopes
from apps.api.integrations.store import EventStore
from apps.api.main import app


def check(adapter, handler):
    async def run():
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            return await adapter.check(client)
    return asyncio.run(run())


def openai(key="test-provider-secret"):
    return OpenAIAdapter(Settings(key, "test-model", "https://api.openai.com/v1"))


def shopify(**kwargs):
    return ShopifyAdapter(ControlConfig(shop_domain="fixture.myshopify.com", shop_token="test-provider-secret", **kwargs))


def test_model_does_not_equate_configuration_with_connectivity():
    s = IntegrationStatus(provider="test", configured=True)
    assert s.authenticated is None and s.reachable is None
    with pytest.raises(ValidationError):
        IntegrationStatus(provider="test", configured=True, validation_status="CONNECTED")


@pytest.mark.parametrize("adapter", [openai(None), ShopifyAdapter(ControlConfig())])
def test_missing_config_performs_no_request(adapter):
    result = check(adapter, lambda r: pytest.fail("network must not run"))
    assert result.validation_status == "NOT_CONFIGURED"
    assert result.authenticated is None


@pytest.mark.parametrize("adapter", [openai(), shopify()])
@pytest.mark.parametrize("code", [401, 403, 429, 500])
def test_provider_http_failures_are_sanitized(adapter, code):
    result = check(adapter, lambda r: httpx.Response(code, text="test-provider-secret"))
    assert result.reachable is True
    assert result.validation_status == "FAILED"
    assert result.authenticated is (False if code == 401 else None)
    assert "test-provider-secret" not in result.model_dump_json()


@pytest.mark.parametrize("adapter", [openai(), shopify()])
def test_network_failure(adapter):
    def fail(request):
        raise httpx.ConnectError("test-provider-secret", request=request)
    result = check(adapter, fail)
    assert result.reachable is False
    assert result.last_error == "provider_transport_error"


@pytest.mark.parametrize("adapter", [openai(), shopify()])
@pytest.mark.parametrize("payload", [{}, [], {"errors": [{"message": "test-provider-secret"}]}])
def test_malformed_provider_responses(adapter, payload):
    result = check(adapter, lambda r: httpx.Response(200, json=payload))
    assert result.validation_status == "FAILED"
    assert "test-provider-secret" not in result.model_dump_json()


def test_openai_auth_and_model_metadata_are_not_inference():
    def handle(request):
        assert request.method == "GET"
        return httpx.Response(200, json={"data": []} if request.url.path == "/v1/models" else {"id": "test-model"})
    result = check(openai(), handle)
    assert result.authenticated and result.model_available
    assert result.runtime_available is None
    assert result.last_successful_check


def test_openai_model_unavailable_preserves_auth():
    result = check(openai(), lambda r: httpx.Response(200, json={"data": []}) if r.url.path == "/v1/models" else httpx.Response(404))
    assert result.authenticated is True and result.model_available is False
    assert result.validation_status == "DEGRADED"


def test_openai_custom_base_does_not_send_key():
    result = check(OpenAIAdapter(Settings("secret", "model", "https://untrusted.invalid")), lambda r: pytest.fail("network must not run"))
    assert result.last_error == "non_official_base_url_not_validated"


def shop_response(granted, version="2026-07"):
    return httpx.Response(200, headers={"X-Shopify-API-Version": version}, json={"data": {
        "shop": {"id": "gid://shopify/Shop/1", "myshopifyDomain": "fixture.myshopify.com"},
        "currentAppInstallation": {"accessScopes": [{"handle": x} for x in granted]}}})


def test_scope_comparison():
    assert compare_scopes(["write_orders"], ["write_products"], ["read_products"]) == ([], ["write_orders"])
    assert compare_scopes([], [], ["read_products"]) == (["read_products"], [])


def test_shopify_read_and_scopes():
    def handle(request):
        query = json.loads(request.content)["query"]
        assert "mutation" not in query
        assert "/2026-07/" in request.url.path
        if "currentAppInstallation" in query:
            return shop_response(["read_products"])
        return httpx.Response(200, json={"data": {"products": {"nodes": []}}})
    result = check(shopify(requested_scopes=("read_products",)), handle)
    assert result.validation_status == "VALIDATED" and result.permissions_proven
    assert result.granted_scopes == ["read_products"]


def test_shopify_missing_scopes_and_version_drift():
    result = check(shopify(), lambda r: shop_response([]))
    assert result.authenticated and not result.permissions_proven
    assert result.missing_scopes == ["read_products"]
    drift = check(shopify(), lambda r: shop_response(["read_products"], "2026-04"))
    assert drift.last_error == "api_version_not_confirmed"


def test_mutations_fail_closed_even_with_approval_flag():
    with pytest.raises(PermissionError):
        shopify().apply(approved=True, mutation="productUpdate")


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("SONIC_CONTROL_PLANE_TOKEN", "test-operator-token")
    monkeypatch.setenv("SONIC_EVENT_DB", str(tmp_path / "events.db"))
    monkeypatch.setenv("SONIC_SHOPIFY_SHOP_DOMAIN", "fixture.myshopify.com")
    monkeypatch.setenv("SONIC_SHOPIFY_WEBHOOK_SECRET", "test-webhook-secret")
    with TestClient(app, base_url="http://localhost") as c:
        yield c


AUTH = {"Authorization": "Bearer test-operator-token"}


def rpc(client, method, params=None):
    response = client.post("/mcp", headers={**AUTH, "Accept": "application/json, text/event-stream"},
        json={"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}})
    assert response.status_code == 200, response.text
    return response.json()


def test_auth_all_control_surfaces_and_health_compatibility(client, monkeypatch):
    assert client.get("/health").json() == {"healthy": True}
    for path in ("/mcp", "/integrations/status", "/integrations/check"):
        assert client.post(path).status_code == 401
        assert client.post(path, headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert client.get("/integrations/status", headers={**AUTH, "Origin": "https://evil.invalid"}).status_code == 403
    monkeypatch.delenv("SONIC_CONTROL_PLANE_TOKEN")
    assert client.get("/integrations/status").status_code == 503
    assert client.post("/mcp").status_code == 503


def test_mcp_initialization_discovery_read_and_mutation_rejection(client):
    initialized = rpc(client, "initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "sonic-tests", "version": "1"}})
    assert initialized["result"]["serverInfo"]["name"] == "Sonic AI V3"
    tools = rpc(client, "tools/list")["result"]["tools"]
    readonly = {"sonic_system_status", "sonic_integration_status", "sonic_shopify_status", "sonic_project_get", "sonic_decision_trace_get", "sonic_workbench_runs", "sonic_workbench_assets", "sonic_workbench_run_get", "sonic_compile_production_brief"}
    local_writes = {"sonic_generate_midi", "sonic_record_workbench_feedback", "sonic_analyze_audio", "sonic_build_pack", "sonic_draft_release", "sonic_plan_session"}
    assert {t["name"] for t in tools} == readonly | local_writes
    assert all(t["annotations"]["readOnlyHint"] == (t["name"] in readonly) and not t["annotations"]["destructiveHint"] for t in tools)
    before = app.state.control_plane.store.count()
    for name in ("sonic_system_status", "sonic_integration_status", "sonic_shopify_status"):
        result = rpc(client, "tools/call", {"name": name, "arguments": {}})["result"]
        assert not result.get("isError", False)
    assert app.state.control_plane.store.count() == before
    denied = rpc(client, "tools/call", {"name": "sonic_shopify_product_update_apply", "arguments": {"approved": True}})
    assert denied.get("error") or denied["result"]["isError"]


def test_provider_check_records_and_trace_read(client):
    response = client.post("/integrations/check", headers=AUTH)
    assert response.status_code == 200
    trace_id = response.json()["trace_ids"][0]
    result = rpc(client, "tools/call", {"name": "sonic_decision_trace_get", "arguments": {"trace_id": trace_id}})["result"]
    assert not result["isError"]
    assert "integration_health_check" in json.dumps(result)
    assert client.post("/integrations/check", headers=AUTH).json()["trace_ids"][0] == trace_id


def delivery(body, event_id=None):
    return {"X-Shopify-Hmac-Sha256": base64.b64encode(hmac.new(b"test-webhook-secret", body, hashlib.sha256).digest()).decode(),
        "X-Shopify-Shop-Domain": "fixture.myshopify.com", "X-Shopify-Topic": "products/update",
        "X-Shopify-Api-Version": "2026-07", "X-Shopify-Event-Id": event_id or str(uuid4())}


def test_webhook_auth_idempotency_and_restart(client):
    body = b'{"id": 1, "body_html": "untrusted content excluded"}'
    headers = delivery(body)
    url = "/integrations/shopify/webhooks"
    assert client.post(url, content=body).status_code == 401
    first = client.post(url, content=body, headers=headers).json()
    second = client.post(url, content=body, headers=headers).json()
    assert first["accepted"] and second["duplicate"] and first["trace_id"] == second["trace_id"]
    reopened = EventStore(app.state.control_plane.config.event_db)
    assert reopened.count() == 1
    assert reopened.trace(first["trace_id"])["resulting_state"] == "PROPOSED"
    assert "untrusted content" not in json.dumps(reopened.get(first["event_id"]))
    conflict_body = b'{"id": 2}'
    assert client.post(url, content=conflict_body, headers=delivery(conflict_body, headers["X-Shopify-Event-Id"])).status_code == 409


@pytest.mark.parametrize("override,code", [({"X-Shopify-Topic": "page_viewed"}, 422),
    ({"X-Shopify-Shop-Domain": "other.myshopify.com"}, 403), ({"X-Shopify-Event-Id": "bad"}, 422),
    ({"X-Shopify-Api-Version": "2025-01"}, 422)])
def test_webhook_rejects_invalid_envelope(client, override, code):
    body = b'{"id": 1}'
    assert client.post("/integrations/shopify/webhooks", content=body, headers={**delivery(body), **override}).status_code == code


def test_oauth_metadata_and_fail_closed_partial_configuration(client, monkeypatch):
    monkeypatch.setenv("SONIC_PUBLIC_MCP_URL", "https://sonic.test/mcp")
    assert client.get("/integrations/status", headers=AUTH).status_code == 503
    monkeypatch.setenv("SONIC_OAUTH_ISSUER", "https://issuer.test")
    monkeypatch.setenv("SONIC_OAUTH_JWKS_URL", "https://issuer.test/jwks")
    metadata = client.get("/.well-known/oauth-protected-resource/mcp").json()
    assert metadata["resource"] == "https://sonic.test/mcp"
    unauthorized = client.post("/mcp")
    assert unauthorized.status_code == 401
    assert "resource_metadata" in unauthorized.headers["www-authenticate"]


def test_recovered_asset_persistence_and_snapshot(client):
    from apps.api.repositories.asset_repository import asset_store
    from apps.api.schemas.asset import AssetCreate
    asset = asset_store.create_asset(AssetCreate(project_id=1, filename="fixture.wav", filepath="fixture.wav", file_type="wav"))
    asset_store.save_analysis(asset.id, {"file_type": "wav", "sample_rate": 48000})
    assert asset_store.get_latest_analysis(asset.id).sample_rate == 48000
    response = client.get("/intelligence/snapshot", params={"project_id": 1, "asset_id": asset.id})
    assert response.status_code == 200
    assert response.json()["analysis"]["sample_rate"] == 48000


@pytest.mark.parametrize("change,code", [({}, 200), ({"aud": "wrong"}, 401),
    ({"iss": "wrong"}, 401), ({"exp": 1}, 401), ({"scope": "unrelated"}, 403)])
def test_oauth_signature_claims_and_scopes(client, monkeypatch, change, code):
    import time
    import jwt
    from types import SimpleNamespace
    from cryptography.hazmat.primitives.asymmetric import rsa
    from apps.api.integrations import auth
    monkeypatch.setenv("SONIC_PUBLIC_MCP_URL", "https://sonic.test/mcp")
    monkeypatch.setenv("SONIC_OAUTH_ISSUER", "https://issuer.test")
    monkeypatch.setenv("SONIC_OAUTH_JWKS_URL", "https://issuer.test/jwks")
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    monkeypatch.setattr(auth, "jwks_client", lambda url: SimpleNamespace(get_signing_key_from_jwt=lambda token: SimpleNamespace(key=key.public_key())))
    claims = {"iss": "https://issuer.test", "aud": "https://sonic.test/mcp", "sub": "operator",
        "iat": int(time.time()), "exp": int(time.time()) + 60, "scope": "sonic:read", **change}
    token = jwt.encode(claims, key, algorithm="RS256")
    assert client.get("/integrations/status", headers={"Authorization": "Bearer " + token}).status_code == code
    if code == 200:
        assert client.post("/integrations/check", headers={"Authorization": "Bearer " + token}).status_code == 403
        assert client.get("/integrations/status", headers=AUTH).status_code == 401


def test_webhook_durability_failure_is_retryable(client, monkeypatch):
    import sqlite3
    def fail(*args):
        raise sqlite3.OperationalError("test-secret must not leak")
    monkeypatch.setattr(app.state.control_plane.store, "ingest", fail)
    body = b'{"id":1}'
    response = client.post("/integrations/shopify/webhooks", content=body, headers=delivery(body))
    assert response.status_code == 503 and "test-secret" not in response.text


def test_mcp_rejects_untrusted_host(client):
    response = client.post("/mcp", headers={**AUTH, "Host": "evil.invalid", "Accept": "application/json, text/event-stream"},
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert response.status_code == 421


def test_expired_health_does_not_claim_current_connectivity(client):
    from apps.api.integrations.models import now
    plane = app.state.control_plane
    checked = now()
    plane._latest = [IntegrationStatus(provider="openai", configured=True, authenticated=True,
        reachable=True, checked_at=checked, last_successful_check=checked, validation_status="VALIDATED")]
    from time import monotonic
    plane._checked = monotonic() - 61
    status = client.get("/integrations/status", headers=AUTH).json()
    item = next(x for x in status["integrations"] if x["provider"] == "openai")
    assert not status["provider_checks_fresh"]
    assert item["authenticated"] is None and item["reachable"] is None
    assert item["last_successful_check"] is not None
