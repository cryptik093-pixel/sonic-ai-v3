from fastapi import APIRouter, HTTPException, Query, status

from ..schemas.memory import Memory, MemoryCreate
from ..services.memory_service import memory_service

router = APIRouter(
    prefix="/memory",
    tags=["Memory"],
)


@router.get(
    "",
    response_model=list[Memory],
    summary="List studio memories",
)
def list_memories(project_id: int | None = Query(default=None)) -> list[Memory]:
    return memory_service.list_memories(project_id=project_id)


@router.post(
    "",
    response_model=Memory,
    status_code=status.HTTP_201_CREATED,
    summary="Create studio memory",
)
def create_memory(payload: MemoryCreate) -> Memory:
    try:
        return memory_service.create_memory(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
