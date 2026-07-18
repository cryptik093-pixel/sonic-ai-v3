from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    artist: str = Field(..., min_length=1, max_length=120)
    genre: str = Field(..., min_length=1, max_length=80)
    bpm: int = Field(..., ge=40, le=240)
    key: str = Field(..., min_length=1, max_length=20)
    notes: str = Field(..., min_length=1, max_length=2000)
    status: str = Field(default="draft", max_length=40)


class ProjectCreate(ProjectBase):
    pass


class Project(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
