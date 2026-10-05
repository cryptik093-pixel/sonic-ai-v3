import asyncio
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from apps.api.intelligence_store import IntelligenceStore
from apps.api.integrations.gateway import build_mcp
from apps.api.main import app

TOKEN = "tier2-retrieval-token"
AUTH = {"Authorization": "Bearer " + TOKEN}


def setup_store(path: Path) -> IntelligenceStore:
    store = IntelligenceStore(path)
    store.put_intent({
        "intent_id": "SI-RET-001",
        "statement": "Retrieve only active evidence-backed memory.",
        "priority": 100,
        "created_at": "2026-10-05T22:00:00Z",
    })
    for i, claim in enumerate([
        "Parallel compression was validated in the mix workflow.",
        "The creator prefers sparse melody arrangements.",
    ], 1):
        store.append_evidence({
            "evidence_id": f"E-RET-00{i}",
            "intent_id": "SI-RET-001",
            "kind": "creator_statement",
            "source": "operator",
            "observed_at": f"2026-10-05T22:0{i}:00Z",
            "confidence": 1.0,
            "claim": claim,
        })
    store.append_checkpoint({
        "checkpoint_id": "CHK-RET-001",
        "intent_id": "SI-RET-001",
        "source_event_id": "EV-RET-001",
        "sequence": 1,
        "projection": {"evidenceIds": ["E-RET-001", "E-RET-002"]},
        "created_at": "2026-10-05T22:03:00Z",
    })

    candidates = [
        {
            "candidate_id": "MEM-MIX",
            "content": {"content": "Mix workflow: use parallel compression to preserve punch while increasing density."},
            "evidence_ids": ["E-RET-001", "E-RET-002"],
            "confidence": 0.90,
        },
        {
            "candidate_id": "MEM-MELODY",
            "content": {"content": "Creative workflow: sparse melody arrangements leave room for the vocal."},
            "evidence_ids": ["E-RET-002"],
            "confidence": 0.95,
        },
        {
            "candidate_id": "MEM-INACTIVE",
            "content": {"content": "Mix workflow inactive candidate should never appear in retrieval."},
            "evidence_ids": ["E-RET-001"],
            "confidence": 1.0,
        },
    ]
    for item in candidates:
        store.append_candidate({
            "candidate_id": item["candidate_id"],
            "intent_id": "SI-RET-001",
            "candidate_type": "memory",
            "content": item["content"],
            "evidence_ids": item["evidence_ids"],
            "confidence": item["confidence"],
            "source_checkpoint_id": "CHK-RET-001",
            "created_at": "2026-10-05T22:04:00Z",
        })
        store.decide_candidate(item["candidate_id"], {
            "decision_id": "DEC-" + item["candidate_id"],
            "status": "accepted",
            "rationale": "Explicit operator approval.",
            "decided_at": "2026-10-05T22:05:00Z",
        })

    for candidate_id in ("MEM-MIX", "MEM-MELODY"):
        store.materialize_memory(candidate_id, {
            "materialization_event_id": "MAT-" + candidate_id,
            "rationale": "Explicit activation.",
            "occurred_at": "2026-10-05T22:06:00Z",
        })
    return store


def test_retrieval_ranks_active_memory_with_explainable_score(tmp_path):
    store = setup_store(tmp_path / "intelligence.sqlite3")
    results = store.retrieve_materialized_memories("mix workflow parallel compression", limit=8)
    assert [item["candidate_id"] for item in results] == ["MEM-MIX"]
    score = results[0]["retrieval"]
    assert score["method"] == "tier2_lexical_evidence_v1"
    assert score["matched_tokens"] == ["compression", "mix", "parallel", "workflow"]
    assert score["token_coverage"] == 1.0
    assert 0 < score["score"] <= 1


def test_retrieval_excludes_nonmaterialized_candidates_and_is_bounded(tmp_path):
    store = setup_store(tmp_path / "intelligence.sqlite3")
    results = store.retrieve_materialized_memories("workflow", limit=1)
    assert len(results) == 1
    assert results[0]["candidate_id"] in {"MEM-MIX", "MEM-MELODY"}
    assert all(item["candidate_id"] != "MEM-INACTIVE" for item in results)

    with pytest.raises(ValueError, match="query_text is required"):
        store.retrieve_materialized_memories(" ")
    with pytest.raises(ValueError, match="between 1 and 20"):
        store.retrieve_materialized_memories("workflow", limit=21)


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setenv("SONIC_CONTROL_PLANE_TOKEN", TOKEN)
    monkeypatch.setenv("SONIC_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("SONIC_INTELLIGENCE_DB", str(tmp_path / "intelligence.sqlite3"))
    monkeypatch.setenv("SONIC_EVENT_DB", str(tmp_path / "events.sqlite3"))
    setup_store(tmp_path / "intelligence.sqlite3")
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


def test_local_http_and_mcp_retrieval_are_read_only_and_scored(client):
    denied = client.get("/workbench/api/intelligence/retrieve", params={"query": "mix workflow"})
    assert denied.status_code == 401

    response = client.get(
        "/workbench/api/intelligence/retrieve",
        headers=AUTH,
        params={"query": "parallel compression", "intent_id": "SI-RET-001"},
    )
    assert response.status_code == 200, response.text
    assert response.json()[0]["candidate_id"] == "MEM-MIX"

    result = rpc(client, "sonic_intelligence_retrieve", {
        "query": "parallel compression",
        "intent_id": "SI-RET-001",
        "limit": 8,
    })
    assert not result["isError"]
    payload = json.loads(result["content"][0]["text"])
    assert payload["authority"] == "materialized_memory_read_only"
    assert payload["memories"][0]["candidate_id"] == "MEM-MIX"


def test_public_oauth_mode_denies_intelligence_memory_tool(client, monkeypatch):
    monkeypatch.setenv("SONIC_PUBLIC_MCP_URL", "https://sonic.example/mcp")
    monkeypatch.setenv("SONIC_OAUTH_ISSUER", "https://issuer.example")
    monkeypatch.setenv("SONIC_OAUTH_JWKS_URL", "https://issuer.example/jwks")
    server = build_mcp(lambda: app.state.control_plane)
    with pytest.raises(Exception, match="local-operator-only"):
        asyncio.run(server.call_tool("sonic_intelligence_retrieve", {
            "query": "parallel compression",
            "intent_id": "SI-RET-001",
            "limit": 8,
        }))
