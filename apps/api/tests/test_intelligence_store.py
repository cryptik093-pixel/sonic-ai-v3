from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.api.intelligence_store import IntelligenceStore
from apps.api.main import app

TOKEN = "tier2-intelligence-test-token"
AUTH = {"Authorization": "Bearer " + TOKEN}


def intent(intent_id="SI-TEST-001"):
    return {
        "intent_id": intent_id,
        "statement": "Build an evidence-backed intelligence loop.",
        "status": "active",
        "priority": 90,
        "horizon": "medium_term",
        "payload": {"owner": "creator", "automation": False},
        "created_at": "2026-10-05T19:10:00Z",
    }


def evidence(evidence_id="E-001", intent_id="SI-TEST-001"):
    return {
        "evidence_id": evidence_id,
        "intent_id": intent_id,
        "kind": "deterministic_fact",
        "source": "test",
        "observed_at": "2026-10-05T19:11:00Z",
        "confidence": 1.0,
        "claim": "A deterministic validation passed.",
        "value": {"passed": True},
        "provenance": ["ci:test"],
        "created_at": "2026-10-05T19:11:01Z",
    }


def checkpoint(checkpoint_id="CHK-001", sequence=1, source_event_id="EV-001"):
    return {
        "checkpoint_id": checkpoint_id,
        "intent_id": "SI-TEST-001",
        "source_event_id": source_event_id,
        "sequence": sequence,
        "escalation": "standard",
        "projection": {
            "openObstacles": 0,
            "completedActions": 1,
            "evidenceIds": ["E-001"],
        },
        "created_at": "2026-10-05T19:12:00Z",
    }


def candidate(candidate_id="MEM-001", **overrides):
    value = {
        "candidate_id": candidate_id,
        "intent_id": "SI-TEST-001",
        "candidate_type": "memory",
        "content": {"claim": "Validated behavior should be retained."},
        "evidence_ids": ["E-001"],
        "confidence": 0.9,
        "source_checkpoint_id": "CHK-001",
        "created_at": "2026-10-05T19:13:00Z",
    }
    value.update(overrides)
    return value


@pytest.fixture
def store(tmp_path: Path):
    return IntelligenceStore(tmp_path / "intelligence.sqlite3")


def seed(store: IntelligenceStore):
    store.put_intent(intent())
    store.append_evidence(evidence())
    store.append_checkpoint(checkpoint())


def test_intent_is_idempotent_but_cannot_be_silently_rewritten(store):
    first = store.put_intent(intent())
    second = store.put_intent(intent())
    assert first["recorded"] is True and second["recorded"] is False

    changed = intent()
    changed["statement"] = "Rewrite history without a new intent ID."
    with pytest.raises(ValueError, match="explicit new intent/revision ID"):
        store.put_intent(changed)


def test_evidence_is_immutable_and_workspace_scoped(store, tmp_path):
    store.put_intent(intent())
    first = store.append_evidence(evidence())
    retry = store.append_evidence(evidence())
    assert first["recorded"] is True and retry["recorded"] is False

    conflict = evidence()
    conflict["claim"] = "Different claim under same evidence ID."
    with pytest.raises(ValueError, match="immutable evidence"):
        store.append_evidence(conflict)

    other = IntelligenceStore(
        tmp_path / "intelligence.sqlite3",
        owner_id="other-owner",
        workspace_id="other-workspace",
    )
    with pytest.raises(ValueError, match="Intent not found"):
        other.get_intent("SI-TEST-001")


def test_checkpoint_stream_rejects_sequence_and_source_event_collisions(store):
    store.put_intent(intent())
    first = store.append_checkpoint(checkpoint())
    retry = store.append_checkpoint(checkpoint())
    assert first["recorded"] is True and retry["recorded"] is False

    with pytest.raises(ValueError, match="sequence or source event"):
        store.append_checkpoint(checkpoint("CHK-002", 1, "EV-002"))

    with pytest.raises(ValueError, match="sequence or source event"):
        store.append_checkpoint(checkpoint("CHK-003", 2, "EV-001"))


def test_candidate_requires_real_scoped_provenance_and_has_explicit_lifecycle(store):
    seed(store)

    with pytest.raises(ValueError, match="missing or cross-intent evidence"):
        store.append_candidate(candidate("MEM-BAD", evidence_ids=["E-NOT-REAL"]))

    first = store.append_candidate(candidate())
    assert first["recorded"] is True
    assert first["status"] == "proposed"

    accepted = store.decide_candidate("MEM-001", {
        "decision_id": "DEC-001",
        "status": "accepted",
        "rationale": "Creator explicitly approved this candidate.",
        "decided_at": "2026-10-05T19:14:00Z",
    })
    assert accepted["status"] == "accepted"
    assert accepted["decision_recorded"] is True

    replacement = store.append_candidate(candidate(
        "MEM-002",
        content={"claim": "New evidence supersedes the prior memory candidate."},
        supersedes_candidate_id="MEM-001",
        created_at="2026-10-05T19:15:00Z",
    ))
    assert replacement["supersedes_candidate_id"] == "MEM-001"

    superseded = store.decide_candidate("MEM-001", {
        "decision_id": "DEC-002",
        "status": "superseded",
        "rationale": "Replaced by MEM-002 with newer evidence.",
        "decided_at": "2026-10-05T19:16:00Z",
    })
    assert superseded["status"] == "superseded"

    with pytest.raises(ValueError, match="already terminal"):
        store.decide_candidate("MEM-001", {
            "decision_id": "DEC-003",
            "status": "accepted",
            "rationale": "Illegal resurrection.",
        })


def test_candidate_cannot_cross_intent_or_type_during_supersession(store):
    seed(store)
    store.append_candidate(candidate())
    store.put_intent(intent("SI-OTHER-001"))
    store.append_evidence(evidence("E-OTHER", "SI-OTHER-001"))

    with pytest.raises(ValueError, match="same type within the same intent"):
        store.append_candidate(candidate(
            "MEM-OTHER",
            intent_id="SI-OTHER-001",
            evidence_ids=["E-OTHER"],
            source_checkpoint_id=None,
            supersedes_candidate_id="MEM-001",
        ))

    with pytest.raises(ValueError, match="same type within the same intent"):
        store.append_candidate(candidate(
            "DNA-001",
            candidate_type="creator_dna",
            supersedes_candidate_id="MEM-001",
        ))


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("SONIC_CONTROL_PLANE_TOKEN", TOKEN)
    monkeypatch.setenv("SONIC_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SONIC_INTELLIGENCE_DB", str(tmp_path / "intelligence.sqlite3"))
    monkeypatch.setenv("SONIC_EVENT_DB", str(tmp_path / "events.sqlite3"))
    with TestClient(app, base_url="http://localhost") as c:
        yield c


def test_intelligence_api_is_authenticated_and_candidate_only(client):
    assert client.get("/workbench/api/intelligence/status").status_code == 401

    created = client.post("/workbench/api/intelligence/intents", headers=AUTH, json=intent())
    assert created.status_code == 200, created.text
    assert created.json()["recorded"] is True

    ev = client.post("/workbench/api/intelligence/evidence", headers=AUTH, json=evidence())
    assert ev.status_code == 200, ev.text

    cp = client.post("/workbench/api/intelligence/checkpoints", headers=AUTH, json=checkpoint())
    assert cp.status_code == 200, cp.text

    memory = client.post("/workbench/api/intelligence/candidates", headers=AUTH, json=candidate())
    assert memory.status_code == 200, memory.text
    assert memory.json()["status"] == "proposed"

    accepted = client.post(
        "/workbench/api/intelligence/candidates/MEM-001/decision",
        headers=AUTH,
        json={
            "decision_id": "DEC-API-001",
            "status": "accepted",
            "rationale": "Explicit operator approval.",
            "decided_at": "2026-10-05T19:20:00Z",
        },
    )
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["status"] == "accepted"

    status = client.get("/workbench/api/intelligence/status", headers=AUTH)
    assert status.status_code == 200
    assert status.json() == {
        "status": "ready",
        "authority": "candidate-ledger-only",
        "counts": {"intents": 1, "evidence": 1, "checkpoints": 1, "candidates": 1, "decisions": 1},
    }

    listed = client.get(
        "/workbench/api/intelligence/candidates",
        headers=AUTH,
        params={"intent_id": "SI-TEST-001", "candidate_type": "memory"},
    )
    assert listed.status_code == 200
    assert [item["candidate_id"] for item in listed.json()] == ["MEM-001"]
