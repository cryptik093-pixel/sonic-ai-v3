from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.api.intelligence_store import IntelligenceStore
from apps.api.main import app

TOKEN = "tier2-materialization-token"
AUTH = {"Authorization": "Bearer " + TOKEN}


def seeded_store(path: Path) -> IntelligenceStore:
    store = IntelligenceStore(path)
    store.put_intent({
        "intent_id": "SI-MAT-001",
        "statement": "Validate controlled memory materialization.",
        "priority": 100,
        "created_at": "2026-10-05T20:00:00Z",
    })
    store.append_evidence({
        "evidence_id": "E-MAT-001",
        "intent_id": "SI-MAT-001",
        "kind": "deterministic_fact",
        "source": "test",
        "observed_at": "2026-10-05T20:01:00Z",
        "confidence": 1.0,
        "claim": "Materialization test evidence.",
    })
    store.append_checkpoint({
        "checkpoint_id": "CHK-MAT-001",
        "intent_id": "SI-MAT-001",
        "source_event_id": "EV-MAT-001",
        "sequence": 1,
        "escalation": "standard",
        "projection": {"evidenceIds": ["E-MAT-001"]},
        "created_at": "2026-10-05T20:02:00Z",
    })
    store.append_candidate({
        "candidate_id": "MEM-MAT-001",
        "intent_id": "SI-MAT-001",
        "candidate_type": "memory",
        "content": {"claim": "The creator explicitly prefers deterministic evidence over inference."},
        "evidence_ids": ["E-MAT-001"],
        "confidence": 0.95,
        "source_checkpoint_id": "CHK-MAT-001",
        "created_at": "2026-10-05T20:03:00Z",
    })
    return store


def accept(store: IntelligenceStore, candidate_id="MEM-MAT-001"):
    return store.decide_candidate(candidate_id, {
        "decision_id": "DEC-" + candidate_id,
        "status": "accepted",
        "rationale": "Explicit operator approval.",
        "decided_at": "2026-10-05T20:04:00Z",
    })


def activation(event_id="MAT-001"):
    return {
        "materialization_event_id": event_id,
        "rationale": "Explicit second-step activation.",
        "occurred_at": "2026-10-05T20:05:00Z",
    }


def test_candidate_requires_acceptance_before_materialization(tmp_path):
    store = seeded_store(tmp_path / "intelligence.sqlite3")
    with pytest.raises(ValueError, match="explicitly accepted"):
        store.materialize_memory("MEM-MAT-001", activation())
    assert store.list_materialized_memories() == []


def test_materialization_is_idempotent_reversible_and_auditable(tmp_path):
    store = seeded_store(tmp_path / "intelligence.sqlite3")
    accept(store)

    first = store.materialize_memory("MEM-MAT-001", activation())
    retry = store.materialize_memory("MEM-MAT-001", activation())
    assert first["recorded"] is True
    assert retry["recorded"] is False
    assert first["active"] is True

    with pytest.raises(ValueError, match="already active"):
        store.materialize_memory("MEM-MAT-001", activation("MAT-002"))

    active = store.list_materialized_memories()
    assert [row["candidate_id"] for row in active] == ["MEM-MAT-001"]
    assert active[0]["content"].startswith("The creator explicitly prefers")

    retired = store.retire_materialized_memory("MEM-MAT-001", {
        "materialization_event_id": "MAT-RETIRE-001",
        "rationale": "Operator retired this memory view.",
        "occurred_at": "2026-10-05T20:06:00Z",
    })
    retired_retry = store.retire_materialized_memory("MEM-MAT-001", {
        "materialization_event_id": "MAT-RETIRE-001",
        "rationale": "Operator retired this memory view.",
        "occurred_at": "2026-10-05T20:06:00Z",
    })
    assert retired["active"] is False
    assert retired_retry["recorded"] is False
    assert store.list_materialized_memories() == []
    assert len(store.materialization_state("MEM-MAT-001")["events"]) == 2


def test_materialization_event_id_collision_fails_closed(tmp_path):
    store = seeded_store(tmp_path / "intelligence.sqlite3")
    accept(store)
    store.materialize_memory("MEM-MAT-001", activation())
    with pytest.raises(ValueError, match="event ID collision"):
        store.materialize_memory("MEM-MAT-001", {
            "materialization_event_id": "MAT-001",
            "rationale": "Different content under the same immutable event ID.",
            "occurred_at": "2026-10-05T20:05:00Z",
        })


def test_superseded_candidate_stops_qualifying_as_active_memory(tmp_path):
    store = seeded_store(tmp_path / "intelligence.sqlite3")
    accept(store)
    store.materialize_memory("MEM-MAT-001", activation())

    store.append_candidate({
        "candidate_id": "MEM-MAT-002",
        "intent_id": "SI-MAT-001",
        "candidate_type": "memory",
        "content": {"claim": "Newer evidence replaces the old candidate."},
        "evidence_ids": ["E-MAT-001"],
        "confidence": 0.97,
        "source_checkpoint_id": "CHK-MAT-001",
        "supersedes_candidate_id": "MEM-MAT-001",
        "created_at": "2026-10-05T20:07:00Z",
    })
    store.decide_candidate("MEM-MAT-001", {
        "decision_id": "DEC-SUPERSEDE-001",
        "status": "superseded",
        "rationale": "Replaced by MEM-MAT-002.",
        "decided_at": "2026-10-05T20:08:00Z",
    })

    state = store.materialization_state("MEM-MAT-001")
    assert state["requested_active"] is True
    assert state["active"] is False
    assert state["blocked_reason"] == "candidate_not_accepted"
    assert store.list_materialized_memories() == []


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("SONIC_CONTROL_PLANE_TOKEN", TOKEN)
    monkeypatch.setenv("SONIC_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SONIC_INTELLIGENCE_DB", str(tmp_path / "intelligence.sqlite3"))
    monkeypatch.setenv("SONIC_EVENT_DB", str(tmp_path / "events.sqlite3"))
    with TestClient(app, base_url="http://localhost") as c:
        yield c


def test_materialization_api_requires_second_explicit_authenticated_action(client):
    intent_payload = {
        "intent_id": "SI-API-MAT-001",
        "statement": "API materialization contract.",
        "priority": 90,
        "created_at": "2026-10-05T21:00:00Z",
    }
    assert client.post("/workbench/api/intelligence/intents", headers=AUTH, json=intent_payload).status_code == 200

    evidence_payload = {
        "evidence_id": "E-API-MAT-001",
        "intent_id": "SI-API-MAT-001",
        "kind": "creator_statement",
        "source": "operator",
        "observed_at": "2026-10-05T21:01:00Z",
        "confidence": 1.0,
        "claim": "Explicit materialization fixture.",
    }
    assert client.post("/workbench/api/intelligence/evidence", headers=AUTH, json=evidence_payload).status_code == 200

    checkpoint_payload = {
        "checkpoint_id": "CHK-API-MAT-001",
        "intent_id": "SI-API-MAT-001",
        "source_event_id": "EV-API-MAT-001",
        "sequence": 1,
        "projection": {"evidenceIds": ["E-API-MAT-001"]},
        "created_at": "2026-10-05T21:02:00Z",
    }
    assert client.post("/workbench/api/intelligence/checkpoints", headers=AUTH, json=checkpoint_payload).status_code == 200

    candidate_payload = {
        "candidate_id": "MEM-API-MAT-001",
        "intent_id": "SI-API-MAT-001",
        "candidate_type": "memory",
        "content": {"content": "Only materialize after explicit approval."},
        "evidence_ids": ["E-API-MAT-001"],
        "confidence": 1.0,
        "source_checkpoint_id": "CHK-API-MAT-001",
        "created_at": "2026-10-05T21:03:00Z",
    }
    assert client.post("/workbench/api/intelligence/candidates", headers=AUTH, json=candidate_payload).status_code == 200

    materialize_url = "/workbench/api/intelligence/candidates/MEM-API-MAT-001/materialize"
    event = {
        "materialization_event_id": "MAT-API-001",
        "rationale": "Second explicit action.",
        "occurred_at": "2026-10-05T21:05:00Z",
    }
    assert client.post(materialize_url, headers=AUTH, json=event).status_code == 422
    assert client.post(materialize_url, json=event).status_code == 401

    decision = {
        "decision_id": "DEC-API-MAT-001",
        "status": "accepted",
        "rationale": "First explicit action: approve candidate.",
        "decided_at": "2026-10-05T21:04:00Z",
    }
    assert client.post(
        "/workbench/api/intelligence/candidates/MEM-API-MAT-001/decision",
        headers=AUTH,
        json=decision,
    ).status_code == 200

    activated = client.post(materialize_url, headers=AUTH, json=event)
    assert activated.status_code == 200, activated.text
    assert activated.json()["active"] is True

    memories = client.get("/workbench/api/intelligence/materialized-memories", headers=AUTH)
    assert memories.status_code == 200
    assert [item["candidate_id"] for item in memories.json()] == ["MEM-API-MAT-001"]
