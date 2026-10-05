from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


AuthorityLevel = Literal[
    "L0_READ_ONLY",
    "L1_LOCAL_REVERSIBLE",
    "L2_EXTERNAL_REVERSIBLE",
    "L3_BUSINESS_MUTATION",
    "L4_IRREVERSIBLE",
]


class DecisionOption(BaseModel):
    option_id: str = Field(min_length=1, max_length=160)
    action: str = Field(min_length=1, max_length=4000)
    alignment: float = Field(ge=0, le=1)
    expected_impact: float = Field(ge=0, le=1)
    urgency: float = Field(ge=0, le=1)
    reversibility: float = Field(ge=0, le=1)
    effort: float = Field(ge=0, le=1)
    resource_cost: float = Field(ge=0, le=1)
    risk: float = Field(ge=0, le=1)
    authority_level: AuthorityLevel
    evidence_ids: list[str] = Field(default_factory=list, max_length=100)
    dependencies: list[str] = Field(default_factory=list, max_length=100)


class DecisionRankRequest(BaseModel):
    intent_id: str = Field(min_length=1, max_length=160)
    objective: str = Field(min_length=1, max_length=4000)
    options: list[DecisionOption] = Field(min_length=2, max_length=20)
    memory_limit: int = Field(default=5, ge=0, le=10)
