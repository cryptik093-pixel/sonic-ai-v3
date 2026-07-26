from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel


class AnalysisStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETE = "complete"
    FAILED = "failed"


class AssetBase(BaseModel):
    filename: str
    original_filename: str
    content_type: str
    file_size: int


class AssetCreate(AssetBase):
    project_id: UUID


class AssetResponse(AssetBase):
    id: UUID
    project_id: UUID

    duration_seconds: float | None = None
    sample_rate: int | None = None
    channels: int | None = None

    analysis_status: AnalysisStatus = AnalysisStatus.PENDING

    uploaded_at: datetime

    class Config:
        from_attributes = True