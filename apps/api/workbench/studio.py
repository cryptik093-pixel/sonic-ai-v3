"""Local-only browser studio prototype: authenticated previews and read-only audio metadata.

No timeline mutation, provider invocation or audio processing is performed over this socket.
"""
import asyncio
import hmac
import os
from uuid import UUID

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from . import service
from .audio_analyzer import extract_musical_metadata
from .schemas import MidiCommand

router = APIRouter(tags=["Experimental Browser Studio"])


@router.get("/workbench/api/studio/assets/{asset_id}/metadata")
def audio_metadata(asset_id: UUID):
    try:
        asset, path = service.get_asset(asset_id)  # Validates workspace and SHA-256 before read.
        if asset["category"] == "MIDI":
            raise ValueError("Musical audio metadata requires an imported audio sample.")
        return {"asset_id": asset["id"], "source_sha256": asset["sha256"],
                "filename": asset["name"], "metadata": extract_musical_metadata(path)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from None


@router.websocket("/workbench/ws/studio")
async def studio_chat_socket(ws: WebSocket):
    # WorkbenchAuth protects HTTP only; WebSockets require their own fail-closed gate.
    host = ws.headers.get("host", "").split(":")[0].lower()
    origin = ws.headers.get("origin")
    permitted = {"http://localhost:3000", "http://127.0.0.1:3000"}
    if host not in {"localhost", "127.0.0.1", "testserver"} or (origin and origin not in permitted):
        await ws.close(code=1008)
        return
    expected = os.getenv("SONIC_DESKTOP_TOKEN") or os.getenv("SONIC_CONTROL_PLANE_TOKEN", "")
    if not expected:
        await ws.close(code=1008)
        return

    await ws.accept()
    try:
        first = await asyncio.wait_for(ws.receive_json(), timeout=5)
        provided = first.get("token", "") if isinstance(first, dict) and first.get("type") == "AUTH" else ""
        if not isinstance(provided, str) or not hmac.compare_digest(provided.encode(), expected.encode()):
            await ws.send_json({"type": "ERROR", "message": "Studio authorization failed."})
            await ws.close(code=1008)
            return
        await ws.send_json({"type": "READY", "message": "Local studio connected (preview only)."})
        while True:
            data = await ws.receive_json()
            if not isinstance(data, dict) or data.get("type") != "PROMPT":
                await ws.send_json({"type": "ERROR", "message": "Unsupported studio request."})
                continue
            prompt = data.get("text")
            request_id = data.get("request_id")
            if (not isinstance(prompt, str) or not 0 < len(prompt.strip()) <= 2000
                    or not isinstance(request_id, str) or len(request_id) > 80):
                await ws.send_json({"type": "ERROR", "message": "Provide a prompt of 1–2000 characters."})
                continue
            await ws.send_json({"type": "STATUS_UPDATE", "request_id": request_id,
                                "message": "Reading production brief; no session changes."})
            try:
                # Existing deterministic compiler, no audio/track modification.
                preview = await asyncio.to_thread(service.preview_midi, MidiCommand(prompt=prompt.strip()))
                await ws.send_json({"type": "SUCCESS", "request_id": request_id,
                                    "message": preview["summary"] + " — preview only; nothing was changed.",
                                    "preview": preview})
            except (ValueError, ValidationError):
                await ws.send_json({"type": "ERROR", "request_id": request_id,
                                    "message": "That production brief could not be previewed."})
    except (WebSocketDisconnect, asyncio.TimeoutError, ValueError, TypeError):
        await ws.close(code=1000)
