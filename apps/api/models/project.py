from datetime import datetime

from schemas.project import Project, ProjectCreate


class InMemoryProjectStore:
    def __init__(self) -> None:
        self._projects: list[Project] = []
        self._next_id = 1

    def list_projects(self) -> list[Project]:
        return self._projects.copy()

    def create_project(self, payload: ProjectCreate) -> Project:
        now = datetime.utcnow().replace(microsecond=0)

        project = Project(
            id=self._next_id,
            name=payload.name,
            artist=payload.artist,
            genre=payload.genre,
            bpm=payload.bpm,
            key=payload.key,
            notes=payload.notes,
            status=payload.status,
            created_at=now,
            updated_at=now,
        )

        self._projects.append(project)
        self._next_id += 1

        return project


project_store = InMemoryProjectStore()