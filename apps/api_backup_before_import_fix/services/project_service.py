from repositories.project_repository import project_store
from schemas.project import Project, ProjectCreate


class ProjectService:
    def list_projects(self) -> list[Project]:
        return project_store.list_projects()

    def create_project(self, payload: ProjectCreate) -> Project:
        self._validate_project(payload)
        return project_store.create_project(payload)

    def _validate_project(self, payload: ProjectCreate) -> None:
        if not payload.name.strip():
            raise ValueError("Project name is required.")

        if payload.bpm is not None:
            if payload.bpm < 40 or payload.bpm > 240:
                raise ValueError("BPM must be between 40 and 240.")


project_service = ProjectService()