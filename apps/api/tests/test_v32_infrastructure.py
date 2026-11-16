"""Regression checks for legacy modules at the canonical runtime boundary."""
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.session_integrity import IntegrityLedger


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("SONIC_CONTROL_PLANE_TOKEN", "local-infrastructure-test")
    monkeypatch.setenv("SONIC_INTEGRITY_DB", str(tmp_path / "ledger.db"))
    monkeypatch.delenv("SONIC_DESKTOP_TOKEN", raising=False)
    monkeypatch.delenv("SONIC_DESKTOP_MODE", raising=False)
    with TestClient(app) as test:
        yield test


AUTH = {"Authorization": "Bearer local-infrastructure-test"}
ROOT = "/session-integrity/sessions"
STATE = {"project_id": "fixture.flp", "host": "FL Studio", "tracks": [], "assets": []}


def test_legacy_and_canonical_tests_share_one_database_module():
    from apps.api import database
    source = Path(database.__file__).resolve()
    loaded = [name for name, module in sys.modules.copy().items()
              if getattr(module, "__file__", None)
              and name.endswith(".database")
              and Path(module.__file__).resolve() == source]
    assert loaded == ["apps.api.database"], loaded


def test_integrity_fails_closed_outside_desktop_mode(client, monkeypatch):
    assert client.get(ROOT + "/unknown").status_code == 401
    assert client.post(ROOT, json={"state": STATE}).status_code == 401
    assert client.post(ROOT, json={"state": STATE}, headers={**AUTH, "Host": "remote.test"}).status_code == 403
    assert client.post(ROOT, json={"state": STATE}, headers={**AUTH, "Origin": "https://remote.test"}).status_code == 403
    monkeypatch.delenv("SONIC_CONTROL_PLANE_TOKEN")
    assert client.post(ROOT, json={"state": STATE}, headers=AUTH).status_code == 503


def test_integrity_revision_restore_and_restart_through_http(client, monkeypatch):
    created = client.post(ROOT, json={"state": STATE}, headers=AUTH)
    assert created.status_code == 201
    first = created.json()
    url = ROOT + "/" + first["session_id"]
    changed = {**STATE, "tempo": 140}
    assert client.post(url + "/checkpoints", json={"expected_revision": 0, "state": changed}, headers=AUTH).status_code == 200
    assert client.post(url + "/checkpoints", json={"expected_revision": 0, "state": STATE}, headers=AUTH).status_code == 409
    restored = client.post(url + "/restores", json={"expected_revision": 1, "target_revision": 0}, headers=AUTH)
    assert restored.status_code == 200
    assert restored.json()["state"] == STATE
    assert IntegrityLedger().get(first["session_id"])["revision"] == 2
    assert len(client.get(url + "/history", headers=AUTH).json()) == 3
    assert [r["kind"] for r in client.get(url + "/operations", headers=AUTH).json()] == ["checkpoint", "restore"]


def test_integrity_uses_desktop_data_root_and_explicit_override(monkeypatch, tmp_path):
    monkeypatch.delenv("SONIC_INTEGRITY_DB", raising=False)
    monkeypatch.setenv("SONIC_DATA_DIR", str(tmp_path / "desktop"))
    ledger = IntegrityLedger()
    assert ledger.path == tmp_path / "desktop" / "session_integrity.sqlite3"
    sid = ledger.create(STATE)["session_id"]
    assert IntegrityLedger().get(sid)["state"] == STATE
    override = tmp_path / "isolated" / "other.db"
    monkeypatch.setenv("SONIC_INTEGRITY_DB", str(override))
    assert IntegrityLedger().path == override
    assert not (Path(__file__).parents[1] / "data" / "session_integrity.sqlite3").exists()
