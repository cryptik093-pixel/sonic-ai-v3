from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class ProjectStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    artist: str = Field(..., min_length=1, max_length=120)
    genre: str = Field(..., min_length=1, max_length=80)
    bpm: int = Field(..., ge=40, le=240)
    key: str = Field(..., min_length=1, max_length=20)
    notes: str = Field(default="", max_length=2000)
    status: ProjectStatus = ProjectStatus.DRAFT


class ProjectCreate(ProjectBase):
    pass


class Project(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
