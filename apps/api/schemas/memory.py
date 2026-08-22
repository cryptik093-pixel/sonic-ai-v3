from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class MemoryType(str, Enum):
    PROJECT = "project"
    STUDIO = "studio"
    PRODUCER = "producer"


class MemoryCategory(str, Enum):
    GENERAL = "general"
    CREATIVE = "creative"
    ENGINEERING = "engineering"
    MIX = "mix"
    MASTER = "master"
    WORKFLOW = "workflow"
    PREFERENCE = "preference"
    LESSON = "lesson"


class MemoryCreate(BaseModel):
    memory_type: MemoryType = MemoryType.STUDIO
    category: MemoryCategory = MemoryCategory.GENERAL
    content: str = Field(..., min_length=1, max_length=4000)
    project_id: int | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    source: str = Field(default="user", max_length=60)


class Memory(BaseModel):
    id: int
    memory_type: MemoryType
    category: MemoryCategory
    content: str
    project_id: int | None
    confidence: float
    source: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
