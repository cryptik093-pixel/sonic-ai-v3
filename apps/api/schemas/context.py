from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from schemas.chat import ChatMessage
from schemas.memory import MemoryCategory, MemoryType


class ContextSourceType(str, Enum):
    PROJECT = "project"
    ASSET = "asset"
    MEMORY = "memory"
    CHAT_SESSION = "chat_session"
    CHAT_MESSAGE = "chat_message"
    AUDIO_ANALYSIS = "audio_analysis"
    EXTERNAL = "external"


class ContextArea(str, Enum):
    PROJECT = "project"
    ASSET = "asset"
    MEMORY = "memory"
    CHAT = "chat"


def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


class SourceRef(BaseModel):
    source_type: ContextSourceType
    source_id: str = Field(..., min_length=1, max_length=200)
    field: str = Field(..., min_length=1, max_length=200)
    provenance: str = Field(..., min_length=1, max_length=500)
    observed_at: datetime
    reliability: float = Field(default=1.0, ge=0.0, le=1.0)


class ContextObservation(BaseModel):
    observation_id: UUID = Field(default_factory=uuid4)
    context_area: ContextArea
    field: str = Field(..., min_length=1, max_length=200)
    value: Any
    source: SourceRef
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    is_inference: bool = False

    def model_post_init(self, __context: Any) -> None:
        if self.is_inference:
            raise ValueError("Context observations cannot represent inference.")


class ProjectContext(BaseModel):
    project_id: int
    observations: list[ContextObservation] = Field(default_factory=list)


class AssetContext(BaseModel):
    asset_id: int
    observations: list[ContextObservation] = Field(default_factory=list)


class MemoryContext(BaseModel):
    memory_id: int
    observations: list[ContextObservation] = Field(default_factory=list)
    memory_type: MemoryType
    category: MemoryCategory
    source: str
    confidence: float = Field(ge=0.0, le=1.0)


class ChatContext(BaseModel):
    session_id: int
    messages: list[ChatMessage] = Field(default_factory=list)


class ContextPackage(BaseModel):
    package_id: UUID = Field(default_factory=uuid4)
    task_query: str = Field(..., min_length=1, max_length=16000)
    project: ProjectContext | None = None
    assets: list[AssetContext] = Field(default_factory=list)
    memories: list[MemoryContext] = Field(default_factory=list)
    chat: ChatContext | None = None
    observations: list[ContextObservation] = Field(default_factory=list)
    context_labels: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utc_now)
    retrieved_at: datetime = Field(default_factory=utc_now)
