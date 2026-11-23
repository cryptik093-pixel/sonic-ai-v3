"""Read-only signed commerce evidence status and authorized idempotent replay."""
from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .services.commerce_evidence import CommerceEvidenceService

# Inherits the existing WorkbenchAuth operator/loopback boundary.
router = APIRouter(prefix="/workbench/api/intelligence/commerce", tags=["Commerce Evidence"])


def _service() -> CommerceEvidenceService:
    try:
        return CommerceEvidenceService.from_env()
    except ValueError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from None


@router.get("/status")
def commerce_evidence_status():
    return _service().report()


@router.post("/replay")
def replay_signed_commerce_evidence():
    try:
        return _service().replay()
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from None
