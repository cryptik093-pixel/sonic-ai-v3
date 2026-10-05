from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


class IntentCreate(BaseModel):
    intent_id: str = Field(min_length=1, max_length=160)
    statement: str = Field(min_length=1, max_length=4000)
    status: str = Field(default="active", min_length=1, max_length=80)
    priority: int = Field(default=50, ge=0, le=100)
    horizon: str | None = Field(default=None, max_length=80)
    payload: dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=utc_now)


class EvidenceCreate(BaseModel):
    evidence_id: str = Field(min_length=1, max_length=160)
    intent_id: str | None = Field(default=None, max_length=160)
    kind: str = Field(min_length=1, max_length=80)
    source: str = Field(min_length=1, max_length=200)
    observed_at: str = Field(default_factory=utc_now)
    confidence: float = Field(ge=0, le=1)
    claim: str | None = Field(default=None, max_length=8000)
    value: Any = None
    scope: str | None = Field(default=None, max_length=200)
    provenance: list[str] = Field(default_factory=list, max_length=100)
    supersedes: str | None = Field(default=None, max_length=160)


class CheckpointCreate(BaseModel):
    checkpoint_id: str = Field(min_length=1, max_length=160)
    intent_id: str = Field(min_length=1, max_length=160)
    source_event_id: str = Field(min_length=1, max_length=160)
    sequence: int = Field(ge=1)
    escalation: Literal["none", "standard", "deep"] = "none"
    projection: dict[str, Any]
    created_at: str = Field(default_factory=utc_now)


class CandidateCreate(BaseModel):
    candidate_id: str = Field(min_length=1, max_length=160)
    intent_id: str = Field(min_length=1, max_length=160)
    candidate_type: Literal["memory", "creator_dna", "foresight"]
    content: dict[str, Any]
    evidence_ids: list[str] = Field(default_factory=list, max_length=200)
    confidence: float = Field(ge=0, le=1)
    source_checkpoint_id: str | None = Field(default=None, max_length=160)
    supersedes_candidate_id: str | None = Field(default=None, max_length=160)
    created_at: str = Field(default_factory=utc_now)


class CandidateDecisionCreate(BaseModel):
    decision_id: str = Field(min_length=1, max_length=160)
    status: Literal["accepted", "rejected", "superseded"]
    rationale: str = Field(default="", max_length=8000)
    decided_at: str = Field(default_factory=utc_now)
