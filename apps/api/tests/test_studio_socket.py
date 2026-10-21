"""Socket proof: authorization, revision checks, bounded changes and safety rejections."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect
from apps.api.studio.router import router
from apps.api.studio.commands import apply_command, CommandError
from apps.api.studio.state import starter_session, StudioState

app = FastAPI()
app.include_router(router)

def test_schema_and_reversible_copy():
    original = starter_session()
    changed, _ = apply_command(original, "make drums quieter and pan left")
    assert original.tracks[0].volume == .6 and original.revision == 0
    assert changed.revision == 1 and changed.tracks[0].volume == .4 and changed.tracks[0].pan == -.5
    assert StudioState.model_validate(changed.model_dump()) == changed
    with pytest.raises(CommandError):
        apply_command(original, "move bass 9 seconds earlier")
    with pytest.raises(CommandError):
        apply_command(original, "publish my Shopify products")

def test_requires_token(monkeypatch):
    monkeypatch.setenv("SONIC_CONTROL_PLANE_TOKEN", "local-test-token")
    with TestClient(app) as c:
        with pytest.raises(WebSocketDisconnect) as info:
            with c.websocket_connect("/ws/studio") as ws:
                ws.send_json({"type": "AUTH", "token": "wrong"})
                ws.receive_json()
        assert info.value.code == 4401

def test_origin_gate(monkeypatch):
    monkeypatch.setenv("SONIC_CONTROL_PLANE_TOKEN", "local-test-token")
    with TestClient(app) as c:
        with pytest.raises(WebSocketDisconnect) as info:
            with c.websocket_connect("/ws/studio", headers={"origin": "https://evil.example"}) as ws:
                ws.receive_json()
        assert info.value.code == 1008

def test_state_change_revision_conflict_and_errors(monkeypatch):
    monkeypatch.setenv("SONIC_CONTROL_PLANE_TOKEN", "local-test-token")
    with TestClient(app) as c, c.websocket_connect("/ws/studio") as ws:
        ws.send_json({"type": "AUTH", "token": "local-test-token"})
        initial = ws.receive_json()
        assert initial["type"] == "SESSION_STATE" and initial["studio_state"]["revision"] == 0
        ws.send_json({"type": "COMMAND", "prompt": "crush drums hard", "request_id": "one", "expected_revision": 0})
        assert ws.receive_json()["type"] == "STATUS_UPDATE"
        good = ws.receive_json()
        assert good["type"] == "STATE_MUTATION_SUCCESS"
        assert good["studio_state"]["revision"] == 1
        assert good["studio_state"]["tracks"][0]["pluginChain"][0]["bits"] == 4
        ws.send_json({"type": "COMMAND", "prompt": "mute drums", "request_id": "stale", "expected_revision": 0})
        assert ws.receive_json()["type"] == "REVISION_CONFLICT"
        ws.send_json({"type": "COMMAND", "prompt": "delete entire song", "request_id": "bad", "expected_revision": 1})
        assert ws.receive_json()["type"] == "STATUS_UPDATE"
        err = ws.receive_json()
        assert err["type"] == "ENGINE_ERROR" and err["studio_state"]["revision"] == 1
        ws.send_json({"type": "COMMAND", "prompt": "mute drums", "request_id": "two", "expected_revision": 1})
        assert ws.receive_json()["type"] == "STATUS_UPDATE"
        assert ws.receive_json()["studio_state"]["tracks"][0]["isMuted"] is True

def test_no_token_configured(monkeypatch):
    monkeypatch.delenv("SONIC_DESKTOP_TOKEN", raising=False)
    monkeypatch.delenv("SONIC_CONTROL_PLANE_TOKEN", raising=False)
    with TestClient(app) as c:
        with pytest.raises(WebSocketDisconnect) as info:
            with c.websocket_connect("/ws/studio") as ws:
                ws.receive_json()
        assert info.value.code == 1013
