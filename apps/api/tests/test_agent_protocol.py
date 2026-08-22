import sys
from pathlib import Path
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from schemas.agent_protocol import (
    AgentId,
    AgentMessage,
    AgentMessageType,
    AgentRun,
    AgentRunStatus,
    AgentTask,
    AgentTaskStatus,
    EvidenceRef,
    EvidenceSourceType,
    Recommendation,
)


def test_protocol_contracts_create_with_safe_defaults() -> None:
    task = AgentTask(objective="Review the current studio context.")
    message = AgentMessage(
        task_id=task.task_id,
        correlation_id=task.correlation_id,
        sender_agent_id=AgentId.OMEGA,
        recipient_agent_id=AgentId.OMEGA,
        message_type=AgentMessageType.TASK_COMPLETED,
        payload={"content": "Review complete."},
    )
    recommendation = Recommendation(
        task_id=task.task_id,
        agent_id=AgentId.OMEGA,
        title="Review context",
        summary="Review the available context before acting.",
    )

    assert isinstance(task.task_id, UUID)
    assert task.status is AgentTaskStatus.CREATED
    assert message.evidence_refs == []
    assert recommendation.requires_approval is True
    assert recommendation.evidence_refs == []


def test_evidence_requires_provenance_and_valid_reliability() -> None:
    evidence = EvidenceRef(
        observation_id=uuid4(),
        source_type=EvidenceSourceType.PROJECT,
        source_id="project-1",
        field="genre",
        value="Synthwave",
        observed_at=task_timestamp(),
        provenance="project repository",
    )

    assert evidence.reliability == 1.0

    with pytest.raises(ValidationError):
        EvidenceRef(
            observation_id=uuid4(),
            source_type=EvidenceSourceType.PROJECT,
            source_id="project-1",
            field="genre",
            value="Synthwave",
            observed_at=task_timestamp(),
            provenance="project repository",
            reliability=1.5,
        )


def test_agent_run_requires_status_and_hashes() -> None:
    task = AgentTask(objective="Run a check.")
    run = AgentRun(
        task_id=task.task_id,
        agent_id=AgentId.OMEGA,
        model="test-model",
        status=AgentRunStatus.COMPLETED,
        input_hash="input-hash",
        started_at=datetime.now(timezone.utc),
    )

    assert run.output_hash is None
    assert run.error_code is None


def task_timestamp() -> datetime:
    return datetime.now(timezone.utc)
