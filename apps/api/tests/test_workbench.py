import asyncio
import csv
import hashlib
import io
import json
import math
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4
from zipfile import ZipFile

import httpx
import mido
import numpy as np
import pytest
import soundfile as sf
from fastapi.testclient import TestClient
from sqlalchemy import select

from apps.api.database import SessionLocal
from apps.api.main import app
from apps.api.workbench import midi, service
from apps.api.workbench.models import Run, WorkEvent
from apps.api.workbench.schemas import MidiCommand

TOKEN = "workbench-test-only-token"
AUTH = {"Authorization": "Bearer " + TOKEN}


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("SONIC_CONTROL_PLANE_TOKEN", TOKEN)
    monkeypatch.setenv("SONIC_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SONIC_EVENT_DB", str(tmp_path / "events.db"))
    with SessionLocal() as s:
        s.query(WorkEvent).delete()
        s.query(Run).delete()
        from apps.api.workbench.models import Asset
        s.query(Asset).delete()
        s.commit()
    with TestClient(app, base_url="http://localhost", headers=AUTH) as c:
        yield c


def post(client, kind, data):
    response = client.post("/workbench/api/" + kind, json=data)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["status"] == "succeeded", result
    return result


def fixture_wav(signal, subtype="PCM_24"):
    data = io.BytesIO()
    sf.write(data, signal, 48000, format="WAV", subtype=subtype)
    return data.getvalue()


def read_file(client, run, name):
    response = client.get(f"/workbench/api/runs/{run['id']}/files/{name}")
    assert response.status_code == 200, response.text
    return response.content


def test_midi_assets_parse_with_balanced_notes_and_exact_duration(client):
    run = post(client, "midi", {"title":"C minor session", "key":"C", "bpm":130, "bars":8})
    for artifact in run["result"]["artifacts"]:
        content = read_file(client, run, artifact["name"])
        assert hashlib.sha256(content).hexdigest() == artifact["sha256"]
        if artifact["name"].endswith(".mid"):
            song = mido.MidiFile(file=io.BytesIO(content))
            assert song.ticks_per_beat == 480
            assert math.isclose(song.length, 8 * 4 * 60 / 130, abs_tol=0.001)
            on_count = 0
            for track in song.tracks:
                held = set()
                for message in track:
                    assert message.time >= 0
                    if message.type == "note_on" and message.velocity > 0:
                        key = (message.channel, message.note)
                        assert key not in held, "Overlapping note of identical pitch can produce a stuck/retriggered voice"
                        held.add(key)
                        on_count += 1
                        if message.channel != 9:
                            assert message.note % 12 in midi.SCALES["minor"]
                    if message.type == "note_off" or (message.type == "note_on" and not message.velocity):
                        held.remove((message.channel, message.note))
                assert not held
            assert on_count > 0
    audio, sr = sf.read(io.BytesIO(read_file(client, run, "Audition.wav")))
    assert sr == 22050 and np.abs(audio).max() > .1 and np.abs(audio).max() < 1


@pytest.mark.parametrize("style", ["cloud", "trap", "soul"])
@pytest.mark.parametrize("scale", list(midi.SCALES))
def test_composition_reproducible_and_in_key_across_styles(scale, style):
    params = MidiCommand(key="F#", scale=scale, style=style, bars=16, seed=12345)
    notes = midi.compose(params)
    assert notes == midi.compose(params)
    assert notes != midi.compose(params.model_copy(update={"seed":54321}))
    for note in notes:
        assert 0 <= note["start"] < 64 and note["duration"] > 0
        assert note["start"] + note["duration"] <= 64.00001
        assert 0 <= note["pitch"] <= 127 and 1 <= note["velocity"] <= 127
        if note["track"] != "Drums":
            assert (note["pitch"] - 6) % 12 in midi.SCALES[scale]


def test_idempotent_retry_conflicting_request_and_restart(client):
    request_id = str(uuid4())
    first = post(client, "midi", {"request_id":request_id,"bars":4})
    second = post(client, "midi", {"request_id":request_id,"bars":4})
    assert first["id"] == second["id"]
    assert client.post("/workbench/api/midi",json={"request_id":request_id,"bars":8}).status_code == 422
    with SessionLocal() as s:
        assert len(s.scalars(select(Run).where(Run.request_id == request_id)).all()) == 1
        assert len(s.scalars(select(WorkEvent).where(WorkEvent.run_id == first["id"])).all()) == 1
    # Reload from a new application lifespan; the disk file and database record survive.
    with TestClient(app, base_url="http://localhost", headers=AUTH) as reopened:
        assert reopened.get(f"/workbench/api/runs/{first['id']}").json()["result"] == first["result"]
        assert read_file(reopened, first, "Melody.mid").startswith(b"MThd")


def test_authentication_host_origin_and_download_boundaries(client, monkeypatch):
    assert client.get("/workbench/api/status", headers={"Authorization":""}).status_code == 401
    assert client.post("/workbench/api/midi",json={},headers={"Origin":"https://evil.invalid"}).status_code == 403
    assert client.get("/workbench/api/status",headers={"Host":"evil.invalid"}).status_code == 403
    run = post(client,"midi",{"bars":4})
    assert client.get(f"/workbench/api/runs/{run['id']}/files/sonic_ai.db").status_code == 404
    monkeypatch.delenv("SONIC_CONTROL_PLANE_TOKEN")
    assert client.get("/workbench/api/status").status_code == 503


def test_validation_invalid_scope_and_missing_asset(client):
    for payload in [{"bpm":0},{"key":"Z"},{"bars":100},{"surprise":"instruction"},{"seed":-1}]:
        assert client.post("/workbench/api/midi",json=payload).status_code == 422
    assert client.post("/workbench/api/midi",json={"project_id":999999}).status_code == 422
    response=client.post("/workbench/api/analysis",json={"asset_id":str(uuid4())}).json()
    assert response["status"] == "failed" and "not found" in response["error"]


def test_audio_numerical_evidence_duplicate_import_and_pack_lineage(client):
    signal = .5*np.sin(2*np.pi*440*np.arange(48000)/48000)
    data = fixture_wav(np.column_stack([signal,-signal]))
    first = client.post("/workbench/api/imports",files={"file":("../../kick.wav",data,"audio/wav")}).json()
    assert first["name"] == "kick.wav"
    duplicate=client.post("/workbench/api/imports",files={"file":("other.wav",data,"audio/wav")}).json()
    assert first["id"]==duplicate["id"] and duplicate["duplicate"]
    analysis=post(client,"analysis",{"asset_id":first["id"]})
    m=analysis["result"]["measurements"]
    assert abs(m["sample_peak_dbfs"] - (-6.02)) < .02
    assert abs(m["rms_dbfs"] - (-9.03)) < .02
    assert m["stereo_correlation"] == -1
    assert m["subtype"] == "PCM_24" and m["bpm"] is None and m["key"] is None
    pack=post(client,"pack",{"title":"Proof Pack","asset_ids":[first["id"],first["id"]]})
    assert pack["result"]["manifest"]["asset_count"] == 1
    assert pack["result"]["manifest"]["license_status"] == "missing"
    z=ZipFile(io.BytesIO(read_file(client,pack,"Proof_Pack.zip")))
    manifest=json.loads(z.read("Manifest.json"))
    asset=manifest["assets"][0]
    assert hashlib.sha256(z.read(asset["archive_path"])).hexdigest() == first["sha256"]
    assert "LICENSE.txt" not in z.namelist()


def test_silence_does_not_become_nan_or_fake_tempo(client):
    asset=client.post("/workbench/api/imports",files={"file":("silence.wav",fixture_wav(np.zeros(4800)),"audio/wav")}).json()
    run=post(client,"analysis",{"asset_id":asset["id"]})
    m=run["result"]["measurements"]
    assert m["rms_dbfs"] is None and m["sample_peak_dbfs"] is None
    assert m["silence_fraction"]==1 and "silent" in m["observations"][0]["fact"]
    json.dumps(run,allow_nan=False)


def test_corrupt_oversized_and_nonfinite_audio_are_rejected(client,monkeypatch):
    assert client.post("/workbench/api/imports",files={"file":("fake.wav",b"not audio")}).status_code == 422
    assert client.post("/workbench/api/imports",files={"file":("shell.exe",b"MZ")}).status_code == 422
    monkeypatch.setattr(service,"MAX_UPLOAD",10)
    assert client.post("/workbench/api/imports",files={"file":("large.wav",b"0"*11)}).status_code == 422
    monkeypatch.setattr(service,"MAX_UPLOAD",100*1024*1024)
    asset=client.post("/workbench/api/imports",files={"file":("nan.wav",fixture_wav(np.array([float("nan")]*200),"FLOAT"))}).json()
    run=client.post("/workbench/api/analysis",json={"asset_id":asset["id"]}).json()
    assert run["status"]=="failed" and "non-finite" in run["error"]


def test_midi_to_pack_to_release_no_invented_licensing_or_live_mutation(client):
    midi_run=post(client,"midi",{"bars":4})
    pack=post(client,"pack",{"title":"Local Set","source_run_id":midi_run["id"],"license_text":"Fixture license supplied by operator."})
    assert pack["result"]["manifest"]["asset_count"]==4
    zip_data=read_file(client,pack,"Local_Set.zip")
    assert ZipFile(io.BytesIO(zip_data)).read("LICENSE.txt")==b"Fixture license supplied by operator."
    draft=post(client,"release",{"pack_run_id":pack["id"],"audience":"Trap producers","product_url":"https://omega-house.online/products/test"})
    csv_text=read_file(client,draft,"Shopify_Draft.csv").decode("utf-8-sig")
    row=next(csv.DictReader(io.StringIO(csv_text)))
    assert row["Status"]=="draft" and row["Published"]=="FALSE"
    assert row["Variant Requires Shipping"]=="FALSE"
    assert "4 midi files" in draft["result"]["copy"]
    assert "certificate" not in draft["result"]["copy"].lower()
    assert "utm_source=social" in draft["result"]["product_url"]


def test_failure_is_durable_and_never_succeeded(client):
    with patch("apps.api.workbench.midi.generate",side_effect=OSError("private-path secret")):
        run=client.post("/workbench/api/midi",json={"bars":4}).json()
    assert run["status"]=="failed" and "secret" not in run["error"]
    assert client.get(f"/workbench/api/runs/{run['id']}").json()["status"]=="failed"
    assert not run["result"].get("artifacts")


def test_low_energy_plan_uses_a_bounded_action_and_retains_evidence(client):
    generated=post(client,"midi",{"bars":4})
    run=post(client,"focus",{"energy":"low","minutes":60,"goal":"finish"})
    assert run["result"]["minutes"]==15
    assert run["result"]["completion"]=="proposed"
    assert {"kind":"completed_run","ref":generated["id"]} in run["result"]["evidence"]


def test_coach_provider_quota_failure_preserves_useful_local_output(client,monkeypatch):
    from apps.api.services.llm_service import LLMServiceError
    generated=post(client,"midi",{"bars":4})
    monkeypatch.setenv("SONIC_OPENAI_API_KEY","fixture-key")
    with patch("apps.api.services.llm_service.LLMService.generate",side_effect=LLMServiceError("AI usage limit reached.")):
        insight=post(client,"coach",{"run_id":generated["id"],"question":"How can I finish this?"})
    assert insight["result"]["engine"]=="local_workflow_rules_v1"
    assert insight["result"]["next_action"]==generated["result"]["next_action"]
    assert "usage limit" in insight["result"]["warnings"][0]


def test_provider_raw_error_is_not_exposed(monkeypatch):
    from apps.api.services.llm_service import LLMService, LLMServiceError
    monkeypatch.setenv("SONIC_OPENAI_API_KEY","fixture-key")
    request=httpx.Request("POST","https://api.openai.com/v1/chat/completions")
    response=httpx.Response(429,text="super-secret provider body",request=request)
    with patch("httpx.Client.post",return_value=response),pytest.raises(LLMServiceError) as exc:
        LLMService().generate([{"role":"user","content":"hi"}])
    assert "secret" not in str(exc.value) and "usage limit" in str(exc.value)


def test_mcp_creation_is_idempotent_and_oauth_read_cannot_write(client,monkeypatch):
    from apps.api.tests.test_integrations import rpc
    # rpc uses its own test token; use the local helper here instead.
    def call(params):
        r=client.post("/mcp",headers={"Accept":"application/json, text/event-stream"},json={"jsonrpc":"2.0","id":1,"method":"tools/call","params":params})
        assert r.status_code==200,r.text
        return r.json()["result"]
    args={"name":"sonic_generate_midi","arguments":{"command":{"request_id":str(uuid4()),"bars":4}}}
    first=call(args);second=call(args)
    assert not first["isError"]
    one=json.loads(first["content"][0]["text"])
    two=json.loads(second["content"][0]["text"])
    assert one["id"]==two["id"] and one["result"]["artifacts"]
    # Direct tool execution keeps the OAuth guard even if a future transport grants read access.
    from apps.api.integrations.gateway import build_mcp
    from apps.api.integrations.service import ControlPlane
    server=build_mcp(lambda:app.state.control_plane)
    monkeypatch.setenv("SONIC_PUBLIC_MCP_URL","https://sonic.example/mcp")
    with pytest.raises(Exception,match="OAuth read scopes"):
        asyncio.run(server.call_tool("sonic_generate_midi",{"command":{"bars":4}}))
