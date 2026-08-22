import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from schemas.agent_protocol import AgentId, AgentRunStatus, AgentTask
from schemas.chat import StudioFocus
from services.agent_orchestrator import AgentOrchestrationError, AgentOrchestrator
from services.agent_registry import AgentRegistry
from services.llm_service import LLMServiceError


class FakeContextEngine:
    def build_context(self, user_message: str, project_id: int | None = None):
        assert user_message == "Analyze the project."
        assert project_id == 7
        return "### Active Project\n- Name: Neon Harbor", ["project"]


class FakeLLM:
    def __init__(self, reply: str = "The project is ready for a focused review.") -> None:
        self.reply = reply
        self.messages = []

    def generate(self, messages):
        self.messages = messages
        return self.reply


class FailingLLM:
    def generate(self, messages):
        raise LLMServiceError("provider unavailable")


def make_registry() -> AgentRegistry:
    return AgentRegistry()


def test_orchestrator_executes_omega_with_context_and_advisory_result() -> None:
    llm = FakeLLM()
    orchestrator = AgentOrchestrator(
        registry=make_registry(),
        context_service=FakeContextEngine(),
        llm=llm,
    )
    task = AgentTask(
        target_agent_id=AgentId.OMEGA,
        objective="Analyze the project.",
        project_id=7,
        task_type="studio_assistance",
    )

    result = orchestrator.execute(task, focus=StudioFocus.MIXING)

    assert result.agent_message.sender_agent_id is AgentId.OMEGA
    assert result.agent_message.payload["content"] == "The project is ready for a focused review."
    assert result.agent_message.evidence_refs == []
    assert result.agent_run.status is AgentRunStatus.COMPLETED
    assert result.agent_run.input_hash
    assert result.agent_run.output_hash
    assert result.context_labels == ["project"]
    assert "Neon Harbor" in llm.messages[0]["content"]
    assert task.status.value == "completed"


def test_orchestrator_rejects_task_type_not_supported_by_specialist() -> None:
    orchestrator = AgentOrchestrator(
        registry=make_registry(),
        context_service=FakeContextEngine(),
        llm=FakeLLM(),
    )
    task = AgentTask(
        target_agent_id=AgentId.NEBULA,
        objective="Analyze the project.",
        task_type="customer_support",
    )

    with pytest.raises(AgentOrchestrationError, match="does not accept"):
        orchestrator.execute(task)


def test_orchestrator_returns_failure_without_exposing_hidden_reasoning() -> None:
    orchestrator = AgentOrchestrator(
        registry=make_registry(),
        context_service=FakeContextEngine(),
        llm=FailingLLM(),
    )
    task = AgentTask(
        target_agent_id=AgentId.OMEGA,
        objective="Analyze the project.",
        project_id=7,
        task_type="studio_assistance",
    )

    with pytest.raises(AgentOrchestrationError, match="provider unavailable"):
        orchestrator.execute(task)

    assert task.status.value == "failed"
    assert task.completed_at is not None
