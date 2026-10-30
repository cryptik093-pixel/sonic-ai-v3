"""Browser-studio protocol and sample metadata smoke contracts."""
import io

import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.workbench.audio_analyzer import extract_musical_metadata

TOKEN = "local-studio-test-only"


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("SONIC_CONTROL_PLANE_TOKEN", TOKEN)
    monkeypatch.setenv("SONIC_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SONIC_EVENT_DB", str(tmp_path / "events.db"))
    with TestClient(app, base_url="http://localhost") as c:
        yield c


def test_chat_rejects_wrong_token(client):
    with client.websocket_connect("/workbench/ws/studio") as socket:
        socket.send_json({"type": "AUTH", "token": "incorrect"})
        result = socket.receive_json()
        assert result["type"] == "ERROR"
        assert "authorization" in result["message"].lower()


def test_chat_previews_without_claiming_state_mutation(client):
    with client.websocket_connect("/workbench/ws/studio") as socket:
        socket.send_json({"type": "AUTH", "token": TOKEN})
        assert socket.receive_json()["type"] == "READY"
        socket.send_json({"type": "PROMPT", "request_id": "preview-001",
                          "text": "A dark F minor trap beat, 130 BPM, 8 bars."})
        status = socket.receive_json()
        result = socket.receive_json()
        assert status["type"] == "STATUS_UPDATE"
        assert result["type"] == "SUCCESS"
        assert result["request_id"] == "preview-001"
        assert "preview only" in result["message"]
        assert result["preview"]["status"] == "previewed"


def test_metadata_uses_existing_protected_import(client, monkeypatch):
    audio = io.BytesIO()
    sf.write(audio, np.zeros(22050), 22050, format="WAV")
    unauthorized = client.get("/workbench/api/studio/assets/00000000-0000-0000-0000-000000000000/metadata")
    assert unauthorized.status_code == 401
    headers = {"Authorization": f"Bearer {TOKEN}"}
    imported = client.post("/workbench/api/imports", files={
        "file": ("silent-stem.wav", audio.getvalue(), "audio/wav")
    }, headers=headers)
    assert imported.status_code == 200, imported.text
    asset_id = imported.json()["id"]
    # Keep baseline CI independent of the optional librosa wheel.
    monkeypatch.setattr("apps.api.workbench.studio.extract_musical_metadata",
                        lambda path: {"bpm_estimate": None, "key_estimate": None})
    response = client.get(f"/workbench/api/studio/assets/{asset_id}/metadata", headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["asset_id"] == asset_id
    assert response.json()["metadata"]["bpm_estimate"] is None


def test_silent_audio_does_not_invent_bpm_or_key(tmp_path):
    pytest.importorskip("librosa")
    path = tmp_path / "silence.wav"
    sf.write(path, np.zeros(22050), 22050)
    result = extract_musical_metadata(path)
    assert result["bpm_estimate"] is None
    assert result["key_estimate"] is None
    assert result["timbre_hint"] == "silent"
    assert result["semantic_embedding"] is None
