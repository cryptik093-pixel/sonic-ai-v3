"""Manifest-only session integrity API. This router never operates a DAW."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Any

from .session_integrity import IntegrityError, IntegrityLedger

router = APIRouter(prefix="/session-integrity", tags=["session-integrity"])

class InitialState(BaseModel):
    state: dict[str, Any]
    session_id: str | None = None

class Checkpoint(BaseModel):
    expected_revision: int = Field(ge=0)
    state: dict[str, Any]

class Restore(BaseModel):
    expected_revision: int = Field(ge=0)
    target_revision: int = Field(ge=0)

def _run(fn, *args):
    try:
        return fn(*args)
    except IntegrityError as exc:
        status = {"not_found": 404, "conflict": 409, "corrupt": 500}.get(exc.code, 422)
        raise HTTPException(status_code=status, detail={"code": exc.code, "message": str(exc)}) from exc

@router.post("/sessions", status_code=201)
def create_session(request: InitialState):
    return _run(IntegrityLedger().create, request.state, request.session_id)

@router.get("/sessions/{session_id}")
def get_session(session_id: str):
    return _run(IntegrityLedger().get, session_id)

@router.get("/sessions/{session_id}/history")
def get_history(session_id: str):
    return _run(IntegrityLedger().history, session_id)

@router.get("/sessions/{session_id}/operations")
def get_operations(session_id: str):
    return _run(IntegrityLedger().operations, session_id)

@router.post("/sessions/{session_id}/checkpoints")
def checkpoint(session_id: str, request: Checkpoint):
    return _run(IntegrityLedger().checkpoint, session_id, request.expected_revision, request.state)

@router.post("/sessions/{session_id}/restores")
def restore(session_id: str, request: Restore):
    return _run(IntegrityLedger().restore, session_id, request.expected_revision, request.target_revision)
