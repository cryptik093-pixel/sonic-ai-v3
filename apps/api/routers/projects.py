from fastapi import APIRouter, HTTPException, status

from ..schemas.project import Project, ProjectCreate
from ..services.project_service import project_service

router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)


@router.get(
    "",
    response_model=list[Project],
    status_code=status.HTTP_200_OK,
    summary="List Projects",
    description="Returns every project currently stored.",
)
def get_projects() -> list[Project]:
    return project_service.list_projects()


@router.post(
    "",
    response_model=Project,
    status_code=status.HTTP_201_CREATED,
    summary="Create Project",
    description="Creates a new music production project.",
)
def create_project(payload: ProjectCreate) -> Project:
    try:
        return project_service.create_project(payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
