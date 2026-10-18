"""Actual Sonic API paths, bounded synthetic audio, no paid/provider calls."""
import hashlib
import io
import json
import stat
import wave
import zipfile
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from apps.api.database import SessionLocal
from apps.api.main import app
from apps.api.repositories.forge_repository import ForgeArtifact, ForgeEvent, ForgePack
from apps.api.services import forge_service as module
from apps.api.workbench.forge_core import ArchiveRejected, inventory_pack

ROOT = "/workbench/api/forge"


def wav():
    stream = io.BytesIO()
    with wave.open(stream, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(8000)
        audio.writeframes(b"\0\0" * 800)
    return stream.getvalue()


def archive(files=None):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", zipfile.ZIP_DEFLATED) as z:
        for name, data in (files or {"Pack/Loops/test.wav": wav(), "Pack/LICENSE.txt": b"Synthetic fixture only"}).items():
            z.writestr(name, data)
    return stream.getvalue()


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setenv("SONIC_CONTROL_PLANE_TOKEN", "forge-test-operator")
    monkeypatch.delenv("SONIC_DESKTOP_TOKEN", raising=False)
    for key in ("SONIC_OAUTH_ISSUER", "SONIC_OAUTH_JWKS_URL", "SONIC_PUBLIC_MCP_URL"):
        monkeypatch.delenv(key, raising=False)
    # ASGI without lifespan avoids unrelated provider/MCP startup in focused tests.
    with TestClient(app, headers={"Authorization": "Bearer forge-test-operator"}) as client:
        yield client


def upload(client, content=None, request_id=None):
    return client.post(ROOT + "/packs", params={"request_id": request_id or str(uuid4()), "title": "Synthetic pack", "taxonomy": "test / drums"},
                       content=archive() if content is None else content, headers={"Content-Type": "application/zip"})


def mutate(client, pack, action, **extra):
    return client.request("PATCH" if action == "review" else "POST", ROOT + f"/packs/{pack['id']}/{action}",
        json={"request_id": str(uuid4()), "expected_revision": pack["manifest_revision"], **extra})


def reviewed(client, rights="cleared"):
    initial = upload(client).json()
    result = mutate(client, initial, "review", updates={a["asset_id"]: {"rights_state": rights,
        "proposed_path": "RELEASE/" + a["original_path"]} for a in initial["manifest"]["assets"]})
    assert result.status_code == 200, result.text
    return result.json()


def test_roundtrip_immutable_bytes_audit_download_and_retry(client):
    data = archive()
    original_sha = hashlib.sha256(data).hexdigest()
    request_id = str(uuid4())
    first = upload(client, data, request_id)
    assert first.status_code == 201, first.text
    assert upload(client, data, request_id).json() == first.json()
    pack = first.json()
    assert pack["manifest"]["source_zip_sha256"] == original_sha
    assert all(a["bpm"]["value"] is None and a["key"]["value"] is None for a in pack["manifest"]["assets"])
    review = mutate(client, pack, "review", updates={a["asset_id"]: {
        "rights_state": "cleared", "taxonomy": "test", "proposed_path": "Release/" + a["original_path"],
        **({"bpm_override": 120.0, "key_override": "C minor"} if a["asset_type"] == "audio" else {})
    } for a in pack["manifest"]["assets"]})
    assert review.status_code == 200, review.text
    pack = review.json()
    assert pack["manifest_revision"] == 2
    assert mutate(client, pack, "export").status_code == 400
    pack = mutate(client, pack, "approve").json()
    export_id = str(uuid4())
    payload = {"request_id": export_id, "expected_revision": 2}
    url = ROOT + f"/packs/{pack['id']}/export"
    export = client.post(url, json=payload)
    assert export.status_code == 200, export.text
    assert client.post(url, json=payload).json() == export.json()
    # New command ID also reuses the same immutable revision artifact.
    assert mutate(client, pack, "export").json()["artifact"]["id"] == export.json()["artifact"]["id"]
    artifact = export.json()["artifact"]
    download = client.get(ROOT + "/exports/" + artifact["id"])
    assert download.status_code == 200
    assert hashlib.sha256(download.content).hexdigest() == artifact["sha256"]
    with zipfile.ZipFile(io.BytesIO(download.content)) as z, zipfile.ZipFile(io.BytesIO(data)) as source:
        manifest = json.loads(z.read("manifest.json"))
        for asset in manifest["assets"]:
            assert z.read(asset["proposed_path"]) == source.read(asset["original_path"])
            assert hashlib.sha256(z.read(asset["proposed_path"])).hexdigest() == asset["sha256"]
        assert "manifest.csv" in z.namelist()
    draft = mutate(client, pack, "shopify-draft", price="5.00", sku="OH-TEST")
    assert draft.status_code == 200, draft.text
    assert b"FALSE" in client.get(ROOT + "/exports/" + draft.json()["artifact"]["id"]).content
    state = client.get(ROOT + "/packs/" + pack["id"]).json()
    assert state["events"][0]["action"] == "upload"
    assert all(e["actor"] == "local-producer:omega-house-studio" and e["correlation_id"] for e in state["events"])
    with SessionLocal() as session:
        stored = session.get(ForgePack, pack["id"])
        assert stored.source == data


def test_auth_fail_closed_and_hostile_origin(client, monkeypatch):
    assert client.get(ROOT + "/packs", headers={"Authorization": ""}).status_code == 401
    assert client.get(ROOT + "/packs", headers={"Authorization": "Bearer wrong"}).status_code == 401
    assert client.get(ROOT + "/packs", headers={"Origin": "https://evil.test"}).status_code == 403
    assert client.get(ROOT + "/packs", headers={"Origin": "http://localhost:3000"}).status_code == 200
    monkeypatch.delenv("SONIC_CONTROL_PLANE_TOKEN")
    assert client.get(ROOT + "/packs").status_code == 503


def test_owner_workspace_isolation(client):
    pack = reviewed(client)
    mutate(client, pack, "approve")
    artifact = mutate(client, pack, "export").json()["artifact"]
    with SessionLocal() as session:
        stored = session.get(ForgePack, pack["id"])
        stored.owner = "other-owner:other-workspace"
        stored_artifact = session.get(ForgeArtifact, artifact["id"])
        stored_artifact.owner = "other-owner:other-workspace"
        session.commit()
    assert pack["id"] not in [p["id"] for p in client.get(ROOT + "/packs").json()]
    assert client.get(ROOT + "/packs/" + pack["id"]).status_code == 404
    assert mutate(client, pack, "approve").status_code == 404
    assert client.get(ROOT + "/exports/" + artifact["id"]).status_code == 404


def test_stale_revision_and_approval_invalidation(client):
    pack = reviewed(client)
    approved = mutate(client, pack, "approve").json()
    asset_id = pack["manifest"]["assets"][0]["asset_id"]
    edited = mutate(client, pack, "review", updates={asset_id: {"tags": ["new"]}}).json()
    assert edited["manifest_revision"] == 3
    assert edited["approved_revision"] is None
    assert mutate(client, approved, "export").status_code == 409
    assert mutate(client, edited, "export").status_code == 400


def test_retry_conflict_and_concurrent_review(client):
    request_id = str(uuid4())
    pack = upload(client, request_id=request_id).json()
    assert upload(client, archive({"different.txt": b"different"}), request_id).status_code == 409
    asset_id = pack["manifest"]["assets"][0]["asset_id"]
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: mutate(client, pack, "review", updates={asset_id: {"tags": ["ok"]}}).status_code, range(2)))
    assert sorted(results) == [200, 409]


def test_rights_gaps_and_changed_source_hash(client):
    pack = reviewed(client, "unverified")
    mutate(client, pack, "approve")
    assert mutate(client, pack, "shopify-draft", price="5.00", sku="OH-TEST").status_code == 400
    with SessionLocal() as session:
        row = session.get(ForgePack, pack["id"])
        row.source = archive({"changed.txt": b"changed"})
        session.commit()
    assert mutate(client, pack, "export").status_code == 409


@pytest.mark.parametrize("changes", [
    {"proposed_path": "../outside.wav"}, {"proposed_path": "bad.mp3"}, {"bpm_override": True},
    {"bpm_override": 999}, {"key_override": "totally fake"}, {"rights_state": "owned"},
    {"sha256": "fake"}, {"taxonomy": ""}, {"tags": ["x" * 41]}, {"taxonomy": None},
])
def test_bad_metadata_is_atomic(client, changes):
    pack = upload(client).json()
    before = client.get(ROOT + "/packs/" + pack["id"]).json()
    response = mutate(client, pack, "review", updates={pack["manifest"]["assets"][0]["asset_id"]: changes})
    assert response.status_code in {400, 422}, response.text
    after = client.get(ROOT + "/packs/" + pack["id"]).json()
    assert after["manifest"] == before["manifest"]
    assert after["manifest_revision"] == before["manifest_revision"]
    assert after["status"] == before["status"]


@pytest.mark.parametrize("name,data", [("bad.wav", b"not audio"), ("bad.wav", wav()[:-20]),
    ("bad.mid", b"not midi"), ("bad.json", b"{invalid"), ("../escape.txt", b"x"),
    ("COM9.txt", b"x"), ("folder/CON.wav", wav()), ("bad.exe", b"MZ"),
    ("bad.flac", b"wrong"), ("bad.pdf", b"wrong")])
def test_unsafe_upload_rejected(client, name, data):
    assert upload(client, archive({name: data})).status_code == 400


def test_zip_limits_duplicates_symlink_and_invalid_data(client, monkeypatch):
    assert upload(client, b"not zip").status_code == 400
    assert upload(client, archive({"a.txt": b"1", "A.txt": b"2"})).status_code == 400
    assert upload(client, archive({"bomb.txt": b"0" * 2_000_000})).status_code == 400
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as z:
        item = zipfile.ZipInfo("link.txt")
        item.create_system = 3
        item.external_attr = (stat.S_IFLNK | 0o777) << 16
        z.writestr(item, b"target")
    assert upload(client, stream.getvalue()).status_code == 400
    from apps.api.routers import forge
    monkeypatch.setattr(forge, "MAX_UPLOAD_BYTES", 20)
    assert upload(client).status_code == 413


def test_normalized_unicode_paths_roundtrip(client):
    original = "Cafe\u0301/license.txt"
    pack = upload(client, archive({original: b"licensed fixture"})).json()
    assert pack["manifest"]["assets"][0]["original_path"] == "Caf\u00e9/license.txt"
    pack = mutate(client, pack, "review", updates={pack["manifest"]["assets"][0]["asset_id"]: {"tags": ["reviewed"]}}).json()
    assert mutate(client, pack, "approve").status_code == 200
    assert mutate(client, pack, "export").status_code == 200


def test_transaction_rollback_leaves_no_partial_artifact(client, monkeypatch):
    pack = reviewed(client)
    mutate(client, pack, "approve")
    def fail(*args, **kwargs):
        raise OSError("simulated disk failure")
    monkeypatch.setattr(module, "export_reviewed_pack", fail)
    assert mutate(client, pack, "export").status_code == 503
    with SessionLocal() as session:
        assert not list(session.scalars(select(ForgeArtifact).where(ForgeArtifact.pack_id == pack["id"])))
        assert session.get(ForgePack, pack["id"]).status == "approved"
        assert "export" not in [e.action for e in session.scalars(select(ForgeEvent).where(ForgeEvent.pack_id == pack["id"]))]
