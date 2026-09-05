from fastapi import APIRouter, HTTPException, Query, status

from ..schemas.decision import Decision, DecisionCreate
from ..schemas.session_snapshot import SessionSnapshot, SessionSnapshotCreate
from ..services.asset_intelligence_service import asset_intelligence_service
from ..services.decision_service import decision_service
from ..services.session_snapshot_service import snapshot_service

router = APIRouter(
    prefix="/intelligence",
    tags=["Intelligence"],
)


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


@router.get("/snapshot")
def get_project_intelligence_snapshot(
    project_id: int | None = Query(default=None),
    asset_id: int | None = Query(default=None),
):
    return asset_intelligence_service.build_context_snapshot(project_id, asset_id)
