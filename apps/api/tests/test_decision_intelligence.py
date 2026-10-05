import asyncio
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.api.intelligence_store import IntelligenceStore
from apps.api.integrations.gateway import build_mcp
from apps.api.main import app
from apps.api.workbench.decision_intelligence import DecisionIntelligence
from apps.api.workbench.decision_schemas import DecisionRankRequest

TOKEN = "tier2-decision-token"
AUTH = {"Authorization": "Bearer " + TOKEN}


def seed(path: Path) -> IntelligenceStore:
    store = IntelligenceStore(path)
    store.put_intent({
        "intent_id": "SI-DEC-001",
        "statement": "Generate verified revenue through the highest-value bounded action.",
        "priority": 100,
        "created_at": "2026-10-05T23:00:00Z",
    })
    for index, claim in enumerate([
        "Warm leads have already expressed direct product interest.",
        "Follow-up outreach is available without new advertising spend.",
        "The offer and delivery path already exist.",
    ], 1):
        store.append_evidence({
            "evidence_id": f"E-DEC-00{index}",
            "intent_id": "SI-DEC-001",
            "kind": "verified_operational_fact",
            "source": "operator",
            "observed_at": f"2026-10-05T23:0{index}:00Z",
            "confidence": 1.0,
            "claim": claim,
        })

    store.append_checkpoint({
        "checkpoint_id": "CHK-DEC-001",
        "intent_id": "SI-DEC-001",
        "source_event_id": "EV-DEC-001",
        "sequence": 1,
        "projection": {"evidenceIds": ["E-DEC-001", "E-DEC-002", "E-DEC-003"]},
        "created_at": "2026-10-05T23:04:00Z",
    })
    store.append_candidate({
        "candidate_id": "MEM-DEC-001",
        "intent_id": "SI-DEC-001",
        "candidate_type": "memory",
        "content": {"content": "Warm leads follow up revenue work should use the existing offer before new paid traffic."},
        "evidence_ids": ["E-DEC-001", "E-DEC-002", "E-DEC-003"],
        "confidence": 1.0,
        "source_checkpoint_id": "CHK-DEC-001",
        "created_at": "2026-10-05T23:05:00Z",
    })
    store.decide_candidate("MEM-DEC-001", {
        "decision_id": "DEC-MEM-001",
        "status": "accepted",
        "rationale": "Explicit operator approval.",
        "decided_at": "2026-10-05T23:06:00Z",
    })
    store.materialize_memory("MEM-DEC-001", {
        "materialization_event_id": "MAT-DEC-001",
        "rationale": "Explicit second-step activation.",
        "occurred_at": "2026-10-05T23:07:00Z",
    })
    return store


def request(memory_limit=5):
    return DecisionRankRequest.model_validate({
        "intent_id": "SI-DEC-001",
        "objective": "Generate revenue from warm leads follow up using the existing offer.",
        "memory_limit": memory_limit,
        "options": [
            {
                "option_id": "FOLLOW_UP_WARM_LEADS",
                "action": "Follow up qualified warm leads with the existing offer and direct CTA.",
                "alignment": 0.95,
                "expected_impact": 0.80,
                "urgency": 0.90,
                "reversibility": 1.00,
                "effort": 0.20,
                "resource_cost": 0.10,
                "risk": 0.10,
                "authority_level": "L2_EXTERNAL_REVERSIBLE",
                "evidence_ids": ["E-DEC-001", "E-DEC-002", "E-DEC-003"],
            },
            {
                "option_id": "BROAD_PAID_AD",
                "action": "Launch a broad paid acquisition campaign before more direct follow-up.",
                "alignment": 0.70,
                "expected_impact": 0.90,
                "urgency": 0.60,
                "reversibility": 0.70,
                "effort": 0.50,
                "resource_cost": 0.90,
                "risk": 0.60,
                "authority_level": "L3_BUSINESS_MUTATION",
                "evidence_ids": ["E-DEC-001"],
            },
        ],
    })


def test_ranker_selects_bounded_evidence_backed_action_and_explains_advantage(tmp_path):
    store = seed(tmp_path / "intelligence.sqlite3")
    result = DecisionIntelligence(store).rank(request())

    assert result["decision_status"] == "recommend"
    assert result["recommended_option_id"] == "FOLLOW_UP_WARM_LEADS"
    assert result["decision_confidence"] > 0.8
    assert result["authority"] == {
        "recommendation_only": True,
        "execution_exposed": False,
        "recommended_action_authority": "L2_EXTERNAL_REVERSIBLE",
        "explicit_approval_required": True,
    }
    assert result["why_this_beats_runner_up"]["runner_up_option_id"] == "BROAD_PAID_AD"
    assert result["ranked_options"][0]["score"] > result["ranked_options"][1]["score"]
    assert result["ranked_options"][0]["evidence_strength"] == 1.0
    assert result["ranking_method"]["id"] == "tier2_decision_score_v1"
    assert result["context_memories"][0]["candidate_id"] == "MEM-DEC-001"


def test_materialized_memory_is_context_only_and_cannot_secretly_change_score(tmp_path):
    store = seed(tmp_path / "intelligence.sqlite3")
    with_memory = DecisionIntelligence(store).rank(request(memory_limit=5))
    no_memory = DecisionIntelligence(store).rank(request(memory_limit=0))

    assert with_memory["context_memories"]
    assert no_memory["context_memories"] == []
    assert [
        (item["option_id"], item["score"]) for item in with_memory["ranked_options"]
    ] == [
        (item["option_id"], item["score"]) for item in no_memory["ranked_options"]
    ]


def test_missing_evidence_never_becomes_high_confidence_recommendation(tmp_path):
    store = seed(tmp_path / "intelligence.sqlite3")
    payload = request(memory_limit=0).model_dump()
    for option in payload["options"]:
        option["evidence_ids"] = []
    result = DecisionIntelligence(store).rank(DecisionRankRequest.model_validate(payload))
    assert result["decision_status"] == "needs_evidence"
    assert result["decision_confidence"] < 0.4


def test_cross_intent_evidence_fails_closed(tmp_path):
    store = seed(tmp_path / "intelligence.sqlite3")
    store.put_intent({
        "intent_id": "SI-OTHER",
        "statement": "Other intent.",
        "priority": 10,
        "created_at": "2026-10-05T23:10:00Z",
    })
    store.append_evidence({
        "evidence_id": "E-OTHER",
        "intent_id": "SI-OTHER",
        "kind": "fact",
        "source": "test",
        "observed_at": "2026-10-05T23:11:00Z",
        "confidence": 1.0,
        "claim": "Must not cross into another intent.",
    })
    payload = request(memory_limit=0).model_dump()
    payload["options"][0]["evidence_ids"] = ["E-OTHER"]
    with pytest.raises(ValueError, match="Evidence not found for this intent/workspace"):
        DecisionIntelligence(store).rank(DecisionRankRequest.model_validate(payload))


def test_irreversible_or_high_risk_winner_is_forced_to_manual_review(tmp_path):
    store = seed(tmp_path / "intelligence.sqlite3")
    payload = request(memory_limit=0).model_dump()
    payload["options"][0].update({
        "authority_level": "L4_IRREVERSIBLE",
        "risk": 0.85,
        "alignment": 1.0,
        "expected_impact": 1.0,
    })
    payload["options"][1].update({
        "alignment": 0.1,
        "expected_impact": 0.1,
        "risk": 0.9,
        "authority_level": "L4_IRREVERSIBLE",
    })
    result = DecisionIntelligence(store).rank(DecisionRankRequest.model_validate(payload))
    assert result["recommended_option_id"] == "FOLLOW_UP_WARM_LEADS"
    assert result["decision_status"] == "manual_review"
    assert result["authority"]["execution_exposed"] is False


def test_duplicate_option_ids_are_rejected(tmp_path):
    store = seed(tmp_path / "intelligence.sqlite3")
    payload = request(memory_limit=0).model_dump()
    payload["options"][1]["option_id"] = payload["options"][0]["option_id"]
    with pytest.raises(ValueError, match="option_id values must be unique"):
        DecisionIntelligence(store).rank(DecisionRankRequest.model_validate(payload))


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("SONIC_CONTROL_PLANE_TOKEN", TOKEN)
    monkeypatch.setenv("SONIC_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SONIC_INTELLIGENCE_DB", str(tmp_path / "intelligence.sqlite3"))
    monkeypatch.setenv("SONIC_EVENT_DB", str(tmp_path / "events.sqlite3"))
    seed(tmp_path / "intelligence.sqlite3")
    with TestClient(app, base_url="http://localhost") as c:
        yield c


def rpc(client, name, arguments):
    response = client.post(
        "/mcp",
        headers={**AUTH, "Accept": "application/json, text/event-stream"},
        json={"jsonrpc": "2.0", "id": 1, "method": "tools/call",
              "params": {"name": name, "arguments": arguments}},
    )
    assert response.status_code == 200, response.text
    return response.json()["result"]


def test_http_and_mcp_rank_read_only_without_state_mutation(client):
    before = client.get("/workbench/api/intelligence/status", headers=AUTH).json()["counts"]
    denied = client.post("/workbench/api/intelligence/decisions/rank", json=request().model_dump())
    assert denied.status_code == 401

    response = client.post(
        "/workbench/api/intelligence/decisions/rank",
        headers=AUTH,
        json=request().model_dump(),
    )
    assert response.status_code == 200, response.text
    assert response.json()["recommended_option_id"] == "FOLLOW_UP_WARM_LEADS"

    result = rpc(client, "sonic_rank_next_actions", request().model_dump())
    assert not result["isError"]
    payload = json.loads(result["content"][0]["text"])
    assert payload["recommended_option_id"] == "FOLLOW_UP_WARM_LEADS"
    assert payload["authority"]["execution_exposed"] is False

    after = client.get("/workbench/api/intelligence/status", headers=AUTH).json()["counts"]
    assert after == before


def test_public_oauth_mode_denies_decision_intelligence(client, monkeypatch):
    monkeypatch.setenv("SONIC_PUBLIC_MCP_URL", "https://sonic.example/mcp")
    monkeypatch.setenv("SONIC_OAUTH_ISSUER", "https://issuer.example")
    monkeypatch.setenv("SONIC_OAUTH_JWKS_URL", "https://issuer.example/jwks")
    server = build_mcp(lambda: app.state.control_plane)
    with pytest.raises(Exception, match="local-operator-only"):
        asyncio.run(server.call_tool("sonic_rank_next_actions", request().model_dump()))
