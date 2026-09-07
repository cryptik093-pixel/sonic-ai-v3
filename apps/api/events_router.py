"""Versioned Tier 5 event ingestion API.

Mount this router from the existing FastAPI application at /api/v1.
"""
from __future__ import annotations

import os
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from event_store import EventStore


class EventEntity(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: str = Field(min_length=1)
    id: str = Field(min_length=1)


class EventActor(BaseModel):
    model_config = ConfigDict(extra="allow")
    user_id: str | None = None
    customer_id: str | None = None
    session_id: str | None = None


class BusinessEvent(BaseModel):
    model_config = ConfigDict(extra="allow")
    event_id: str = Field(min_length=1)
    event_type: str = Field(min_length=1)
    schema_version: str = "1.0"
    occurred_at: str = Field(min_length=1)
    source: str = Field(min_length=1)
    entity: EventEntity
    actor: EventActor | None = None
    context: dict[str, Any] | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
    outcome: str | None = None
    revenue_impact: float | None = None
    currency: str | None = None


router = APIRouter(prefix="/api/v1/events", tags=["events"])
store = EventStore(os.getenv("SONIC_EVENT_DB", "data/sonic_events.sqlite3"))


@router.post("", status_code=202)
def ingest_event(event: BusinessEvent) -> dict[str, Any]:
    if event.schema_version != "1.0":
        raise HTTPException(status_code=400, detail="Unsupported event schema version")

    inserted = store.append(event.model_dump(mode="json"))
    return {
        "accepted": True,
        "duplicate": not inserted,
        "event_id": event.event_id,
    }


@router.get("/{event_id}")
def get_event(event_id: str) -> dict[str, Any]:
    event = store.get(event_id)
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event
