from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AssetEdit(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    proposed_path: str | None = Field(default=None, min_length=1, max_length=240)
    taxonomy: str | None = Field(default=None, min_length=1, max_length=120)
    tags: list[str] | None = Field(default=None, max_length=25)
    rights_state: Literal["unverified", "cleared", "restricted"] | None = None
    bpm_override: float | None = Field(default=None, ge=30, le=300, allow_inf_nan=False)
    key_override: str | None = Field(default=None, max_length=20)


class ForgeMutation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    request_id: UUID
    expected_revision: int = Field(ge=1, strict=True)


class ForgeReview(ForgeMutation):
    updates: dict[str, AssetEdit] = Field(min_length=1, max_length=500)


class ForgeDraft(ForgeMutation):
    price: str = Field(min_length=1, max_length=20)
    sku: str = Field(min_length=2, max_length=64)
