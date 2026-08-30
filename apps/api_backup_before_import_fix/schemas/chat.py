from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ChatRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class StudioFocus(str, Enum):
    GENERAL = "general"
    PRODUCTION = "production"
    MIXING = "mixing"
    MASTERING = "mastering"
    SOUND_DESIGN = "sound_design"
    ARRANGEMENT = "arrangement"
    THEORY = "theory"
    WORKFLOW = "workflow"


class ChatMessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=16000)


class ChatMessage(BaseModel):
    id: int
    session_id: int
    role: ChatRole
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatSessionCreate(BaseModel):
    title: str = Field(default="Studio Session", max_length=200)
    project_id: int | None = None
    focus: StudioFocus = StudioFocus.GENERAL


class ChatSession(BaseModel):
    id: int
    title: str
    project_id: int | None
    focus: StudioFocus
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatSessionDetail(ChatSession):
    messages: list[ChatMessage] = Field(default_factory=list)


class ChatSendRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=16000)
    project_id: int | None = None
    focus: StudioFocus = StudioFocus.GENERAL


class ChatSendResponse(BaseModel):
    session_id: int
    message: ChatMessage
    reply: ChatMessage
    context_used: list[str] = Field(default_factory=list)
