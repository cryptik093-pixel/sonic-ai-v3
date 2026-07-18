from models.project import project_store
from schemas.project import Project, ProjectCreate


class ProjectService:
    def list_projects(self) -> list[Project]:
        return project_store.list_projects()

    def create_project(self, payload: ProjectCreate) -> Project:
        return project_store.create_project(payload)


project_service = ProjectService()
