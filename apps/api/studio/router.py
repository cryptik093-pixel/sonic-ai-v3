"""Single-operator local WebSocket. Authenticates before exposing a synthetic session."""
import hmac
import json
import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from .commands import CommandError, apply_command
from .state import starter_session

router = APIRouter()
_ALLOWED_ORIGINS = {"http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:8000", "http://127.0.0.1:8000"}
_ALLOWED_HOSTS = {"localhost", "127.0.0.1", "testserver"}

@router.websocket("/ws/studio")
async def studio_socket(socket: WebSocket):
    host = (socket.headers.get("host") or "").split(":", 1)[0]
    origin = socket.headers.get("origin")
    if host not in _ALLOWED_HOSTS or (origin is not None and origin not in _ALLOWED_ORIGINS):
        await socket.close(code=1008)
        return
    expected = os.getenv("SONIC_DESKTOP_TOKEN") or os.getenv("SONIC_CONTROL_PLANE_TOKEN", "")
    if not expected:
        await socket.close(code=1013, reason="Local studio token not configured")
        return
    await socket.accept()
    try:
        first = await socket.receive_text()
        if len(first) > 8192:
            await socket.close(code=1009)
            return
        try:
            auth = json.loads(first)
        except json.JSONDecodeError:
            await socket.close(code=1008)
            return
        if not isinstance(auth, dict):
            await socket.close(code=1008)
            return
        token = auth.get("token")
        if auth.get("type") != "AUTH" or not isinstance(token, str) or not hmac.compare_digest(expected, token):
            await socket.close(code=4401)
            return
        state = starter_session()
        await socket.send_json({"type": "SESSION_STATE", "studio_state": state.model_dump()})
        while True:
            raw = await socket.receive_text()
            if len(raw) > 8192:
                await socket.send_json({"type": "ENGINE_ERROR", "errors": ["Message too large"]})
                continue
            try:
                data = json.loads(raw)
                if not isinstance(data, dict) or data.get("type") != "COMMAND":
                    raise CommandError("Expected a COMMAND message")
                prompt = data.get("prompt")
                revision = data.get("expected_revision")
                request_id = data.get("request_id")
                if not isinstance(request_id, str) or len(request_id) > 100:
                    raise CommandError("Invalid request ID")
                if type(revision) is not int or revision != state.revision:
                    await socket.send_json({"type": "REVISION_CONFLICT", "studio_state": state.model_dump(), "request_id": request_id})
                    continue
                if not isinstance(prompt, str):
                    raise CommandError("Prompt must be text")
                await socket.send_json({"type": "STATUS_UPDATE", "message": "Validating studio command", "request_id": request_id})
                changed, explanation = apply_command(state, prompt)
                state = changed
                await socket.send_json({"type": "STATE_MUTATION_SUCCESS", "studio_state": state.model_dump(), "message": explanation, "request_id": request_id})
            except (CommandError, ValidationError, json.JSONDecodeError) as exc:
                await socket.send_json({"type": "ENGINE_ERROR", "errors": [str(exc)[:500]], "studio_state": state.model_dump()})
    except WebSocketDisconnect:
        return
