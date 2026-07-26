import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from repositories.project_repository import SQLAlchemyProjectRepository, project_store
from schemas.project import ProjectCreate
from services.project_service import ProjectService, project_service


def test_create_project_persists_and_lists_project() -> None:
    project_store.clear()

    created = project_service.create_project(
        ProjectCreate(
            name="Midnight Echo",
            artist="Nova Lane",
            genre="Synthwave",
            bpm=124,
            key="A minor",
            notes="First pass",
            status="draft",
        )
    )

    assert created.name == "Midnight Echo"
    assert created.id == 1
    assert project_service.list_projects()[0].id == created.id


def test_project_repository_persists_across_instances() -> None:
    repository = SQLAlchemyProjectRepository()
    repository.clear()

    created = repository.create_project(
        ProjectCreate(
            name="Neon Harbor",
            artist="Kai Sol",
            genre="Ambient",
            bpm=98,
            key="C major",
            notes="Second pass",
            status="active",
        )
    )

    reloaded_repository = SQLAlchemyProjectRepository()
    projects = reloaded_repository.list_projects()

    assert created.id is not None
    assert len(projects) == 1
    assert projects[0].id == created.id
    assert projects[0].name == "Neon Harbor"
