from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class SessionSnapshotCreate(BaseModel):
    project_id: int | None = None
    snapshot: str = Field(..., min_length=1)


class SessionSnapshot(BaseModel):
    id: int
    project_id: int | None
    snapshot: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
