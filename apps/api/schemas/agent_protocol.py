from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from schemas.context import ContextPackage


class AgentId(str, Enum):
    OMEGA = "omega"
    SPECTRA = "spectra"
    HAVEN = "haven"
    NEBULA = "nebula"
    MERCURY = "mercury"
    ATLAS = "atlas"
    ORION = "orion"


class AgentTaskStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentMessageType(str, Enum):
    TASK_REQUESTED = "task.requested"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"


class RecommendationStatus(str, Enum):
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"


class AgentRunStatus(str, Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class EvidenceSourceType(str, Enum):
    PROJECT = "project"
    ASSET = "asset"
    MEMORY = "memory"
    CHAT_SESSION = "chat_session"
    CHAT_MESSAGE = "chat_message"
    AUDIO_ANALYSIS = "audio_analysis"
    EXTERNAL = "external"


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


class AgentManifest(BaseModel):
    agent_id: AgentId
    display_name: str = Field(..., min_length=1, max_length=120)
    version: str = Field(default="1.0", min_length=1, max_length=30)
    description: str = Field(..., min_length=1, max_length=500)
    capabilities: list[str] = Field(default_factory=list)
    accepted_task_types: list[str] = Field(default_factory=list)
    enabled: bool = True
    supports_external_actions: bool = False


class AgentTask(BaseModel):
    task_id: UUID = Field(default_factory=uuid4)
    correlation_id: UUID = Field(default_factory=uuid4)
    parent_task_id: UUID | None = None
    requesting_agent_id: AgentId = AgentId.OMEGA
    target_agent_id: AgentId = AgentId.OMEGA
    task_type: str = Field(default="studio_assistance", min_length=1, max_length=100)
    objective: str = Field(..., min_length=1, max_length=16000)
    project_id: int | None = None
    session_id: int | None = None
    status: AgentTaskStatus = AgentTaskStatus.CREATED
    input_data: dict[str, Any] = Field(default_factory=dict)
    context_requirements: list[str] = Field(default_factory=list)
    context_package: ContextPackage | None = None
    created_at: datetime = Field(default_factory=utc_now)
    started_at: datetime | None = None
    completed_at: datetime | None = None


class EvidenceRef(BaseModel):
    evidence_id: UUID = Field(default_factory=uuid4)
    observation_id: UUID
    source_type: EvidenceSourceType
    source_id: str = Field(..., min_length=1, max_length=200)
    field: str = Field(..., min_length=1, max_length=200)
    value: Any
    observed_at: datetime
    provenance: str = Field(..., min_length=1, max_length=500)
    reliability: float = Field(default=1.0, ge=0.0, le=1.0)


class AgentMessage(BaseModel):
    message_id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    correlation_id: UUID
    sender_agent_id: AgentId
    recipient_agent_id: AgentId
    message_type: AgentMessageType
    payload: dict[str, Any] = Field(default_factory=dict)
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    created_at: datetime = Field(default_factory=utc_now)
    schema_version: str = Field(default="1.0", min_length=1, max_length=30)


class Recommendation(BaseModel):
    recommendation_id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    agent_id: AgentId
    title: str = Field(..., min_length=1, max_length=200)
    summary: str = Field(..., min_length=1, max_length=4000)
    rationale: str = Field(default="", max_length=8000)
    evidence_refs: list[EvidenceRef] = Field(default_factory=list)
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    impact: str | None = Field(default=None, max_length=40)
    status: RecommendationStatus = RecommendationStatus.PROPOSED
    requires_approval: bool = True
    created_at: datetime = Field(default_factory=utc_now)


class AgentRun(BaseModel):
    run_id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    agent_id: AgentId
    model: str = Field(..., min_length=1, max_length=120)
    prompt_version: str = Field(default="1.0", min_length=1, max_length=30)
    status: AgentRunStatus
    input_hash: str = Field(..., min_length=1, max_length=128)
    output_hash: str | None = Field(default=None, max_length=128)
    error_code: str | None = Field(default=None, max_length=120)
    started_at: datetime
    completed_at: datetime | None = None


class OrchestrationResult(BaseModel):
    agent_message: AgentMessage
    recommendation: Recommendation | None = None
    agent_run: AgentRun
    context_labels: list[str] = Field(default_factory=list)

    model_config = ConfigDict(arbitrary_types_allowed=True)
