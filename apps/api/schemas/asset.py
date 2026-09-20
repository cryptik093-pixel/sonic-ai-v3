from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class AssetCreate(BaseModel):
    project_id: int
    filename: str
    filepath: str
    file_type: str
    duration: Optional[float] = None
    bpm: Optional[int] = None
    key: Optional[str] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None


class Asset(BaseModel):
    id: int
    project_id: int
    filename: str
    filepath: str
    file_type: str
    duration: Optional[float] = None
    bpm: Optional[int] = None
    key: Optional[str] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    created_at: datetime