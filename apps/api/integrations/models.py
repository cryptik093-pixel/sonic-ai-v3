from datetime import datetime, timezone
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


def now() -> datetime:
    return datetime.now(timezone.utc)


class IntegrationStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: str
    configured: bool
    authenticated: bool | None = None
    reachable: bool | None = None
    permissions_proven: bool | None = None
    requested_scopes: list[str] = Field(default_factory=list)
    granted_scopes: list[str] = Field(default_factory=list)
    required_scopes: list[str] = Field(default_factory=list)
    missing_scopes: list[str] = Field(default_factory=list)
    ungranted_requested_scopes: list[str] = Field(default_factory=list)
    api_version: str | None = None
    model_available: bool | None = None
    runtime_available: bool | None = None
    checked_at: datetime | None = None
    last_successful_check: datetime | None = None
    last_error: str | None = None
    latency_ms: float | None = None
    degraded_capabilities: list[str] = Field(default_factory=list)
    validation_status: Literal["NOT_CONFIGURED", "CONFIGURED", "VALIDATED", "DEGRADED", "FAILED", "NOT_TESTED"] = "NOT_TESTED"
    evidence: list[str] = Field(default_factory=list)


class DecisionRecord(BaseModel):
    trace_id: str
    timestamp: datetime = Field(default_factory=now)
    provider: str
    requested_operation: str
    evidence: list[str]
    validation_status: str
    agent_service: str = "integration_control_plane"
    actor: str = "operator"
    resulting_state: str
    external_side_effect: str = "none"
    integration_status: IntegrationStatus | None = None
