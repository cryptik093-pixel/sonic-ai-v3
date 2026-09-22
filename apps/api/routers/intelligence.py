from fastapi import APIRouter, HTTPException, status

from ..schemas.session_snapshot import SessionSnapshot, SessionSnapshotCreate
from ..schemas.decision import Decision, DecisionCreate
from ..services.session_snapshot_service import snapshot_service
from ..services.decision_service import decision_service
from ..services.asset_service import asset_service

router = APIRouter(
    prefix="/intelligence",
    tags=["Intelligence"],
)


@router.get("/snapshot")
def get_asset_snapshot(project_id: int | None = None, asset_id: int | None = None):
    asset = asset_service.get_asset(asset_id) if asset_id is not None else None
    if asset is not None and project_id is not None and asset.project_id != project_id:
        raise HTTPException(404, "Asset not found in the selected project.")
    analysis = asset_service.get_latest_analysis(asset_id) if asset else None
    fields = ("file_type", "duration", "sample_rate", "channels", "confidence", "provenance")
    return {"asset": asset.model_dump() if asset else None,
            "analysis": {k: getattr(analysis, k) for k in fields} if analysis else None,
            "summary": "Stored asset metadata; no model inference has been performed."}


@router.get("/snapshots", response_model=list[SessionSnapshot])
def list_snapshots(project_id: int | None = None):
    return snapshot_service.list_snapshots(project_id=project_id)


@router.post("/snapshots", response_model=SessionSnapshot, status_code=status.HTTP_201_CREATED)
def create_snapshot(payload: SessionSnapshotCreate):
    try:
        return snapshot_service.create_snapshot(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/decisions", response_model=list[Decision])
def list_decisions(project_id: int | None = None):
    return decision_service.list_decisions(project_id=project_id)


@router.post("/decisions", response_model=Decision, status_code=status.HTTP_201_CREATED)
def create_decision(payload: DecisionCreate):
    try:
        return decision_service.create_decision(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
