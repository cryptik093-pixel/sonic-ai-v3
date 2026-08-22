from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any

from config import settings
from schemas.agent_protocol import (
    AgentId,
    AgentMessage,
    AgentMessageType,
    AgentRun,
    AgentRunStatus,
    AgentTask,
    AgentTaskStatus,
    OrchestrationResult,
)
from schemas.chat import StudioFocus
from schemas.context import ContextPackage
from services.agent_registry import AgentRegistry, agent_registry
from services.context_engine import ContextEngine, context_engine
from services.evidence_validator import EvidenceValidator, evidence_validator
from services.llm_service import LLMService, LLMServiceError, llm_service
from services.producer_intelligence import build_agent_system_prompt, build_context_block


class AgentOrchestrationError(ValueError):
    pass


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


class AgentOrchestrator:
    def __init__(
        self,
        registry: AgentRegistry | None = None,
        context_service: ContextEngine | None = None,
        llm: LLMService | None = None,
        evidence_service: EvidenceValidator | None = None,
    ) -> None:
        self.registry = registry or agent_registry
        self.context_service = context_service or context_engine
        self.llm = llm or llm_service
        self.evidence_service = evidence_service or evidence_validator

    def execute(
        self,
        task: AgentTask,
        focus: StudioFocus = StudioFocus.GENERAL,
    ) -> OrchestrationResult:
        manifest = self.registry.get(task.target_agent_id)
        if task.task_type not in manifest.accepted_task_types and task.target_agent_id != AgentId.OMEGA:
            raise AgentOrchestrationError(
                f"Agent {manifest.agent_id.value} does not accept task type {task.task_type!r}."
            )

        started_at = utc_now()
        task.status = AgentTaskStatus.RUNNING
        task.started_at = started_at
        input_hash = self._hash_payload(task.model_dump(mode="json"))
        context_package = task.context_package
        if context_package is None and hasattr(self.context_service, "build_context_package"):
            context_package = self.context_service.build_context_package(
                user_message=task.objective,
                project_id=task.project_id,
                session_id=task.session_id,
            )
            task.context_package = context_package

        if context_package is not None:
            context_text = self.context_service.render_context_package(context_package)
            context_labels = context_package.context_labels
        else:
            try:
                context_text, context_labels = self.context_service.build_context(
                    user_message=task.objective,
                    project_id=task.project_id,
                    session_id=task.session_id,
                )
            except TypeError:
                context_text, context_labels = self.context_service.build_context(
                    user_message=task.objective,
                    project_id=task.project_id,
                )
        system_prompt = build_agent_system_prompt(manifest.agent_id, focus)
        if context_text:
            system_prompt = f"{system_prompt}\n\n{build_context_block([context_text])}"

        messages = [
            {"role": "system", "content": system_prompt},
        ]
        history = task.input_data.get("history", [])
        if context_package is not None and context_package.chat is not None:
            history = [
                {"role": message.role.value, "content": message.content}
                for message in context_package.chat.messages
            ]
        messages.extend(
            message
            for message in history
            if isinstance(message, dict)
            and message.get("role") in ("user", "assistant")
            and isinstance(message.get("content"), str)
        )
        messages.append({"role": "user", "content": task.objective})

        try:
            reply = self.llm.generate(messages)
        except LLMServiceError as exc:
            task.status = AgentTaskStatus.FAILED
            task.completed_at = utc_now()
            run = AgentRun(
                task_id=task.task_id,
                agent_id=manifest.agent_id,
                model=settings.openai_model,
                status=AgentRunStatus.FAILED,
                input_hash=input_hash,
                error_code="llm_request_failed",
                started_at=started_at,
                completed_at=task.completed_at,
            )
            raise AgentOrchestrationError(str(exc)) from exc

        completed_at = utc_now()
        task.status = AgentTaskStatus.COMPLETED
        task.completed_at = completed_at
        output_hash = self._hash_payload({"reply": reply})
        run = AgentRun(
            task_id=task.task_id,
            agent_id=manifest.agent_id,
            model=settings.openai_model,
            status=AgentRunStatus.COMPLETED,
            input_hash=input_hash,
            output_hash=output_hash,
            started_at=started_at,
            completed_at=completed_at,
        )
        message = AgentMessage(
            task_id=task.task_id,
            correlation_id=task.correlation_id,
            sender_agent_id=manifest.agent_id,
            recipient_agent_id=task.requesting_agent_id,
            message_type=AgentMessageType.TASK_COMPLETED,
            payload={"content": reply},
        )
        if context_package is not None:
            self.evidence_service.validate(message.evidence_refs, context_package)
        return OrchestrationResult(
            agent_message=message,
            agent_run=run,
            context_labels=context_labels,
        )

    def _hash_payload(self, payload: dict[str, Any]) -> str:
        serialized = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()


agent_orchestrator = AgentOrchestrator()
