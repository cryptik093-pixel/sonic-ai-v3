from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class DecisionCreate(BaseModel):
    project_id: int | None = None
    asset_id: int | None = None
    observation: str = Field(..., min_length=1)
    evidence: str | None = None
    interpretation: str | None = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    recommendation: str | None = None
    selected_option: str | None = None
    reason: str | None = None
    action: str | None = None
    outcome: str | None = None
    producer_response: str | None = None


class Decision(BaseModel):
    id: int
    project_id: int | None
    asset_id: int | None
    timestamp: datetime
    observation: str
    evidence: str | None
    interpretation: str | None
    confidence: float
    recommendation: str | None
    selected_option: str | None
    reason: str | None
    action: str | None
    outcome: str | None
    producer_response: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
