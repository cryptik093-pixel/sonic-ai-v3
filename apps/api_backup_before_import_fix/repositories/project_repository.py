from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from ..database import ProjectORM, SessionLocal
from schemas.project import Project, ProjectCreate, ProjectStatus


class SQLAlchemyProjectRepository:
    def __init__(self, session: Session | None = None) -> None:
        self._session = session or SessionLocal()

    def clear(self) -> None:
        with SessionLocal() as session:
            session.query(ProjectORM).delete()
            session.commit()

    def list_projects(self) -> list[Project]:
        records = self._session.query(ProjectORM).order_by(ProjectORM.id.asc()).all()
        return [self._to_schema(record) for record in records]

    def create_project(self, payload: ProjectCreate) -> Project:
        now = datetime.utcnow().replace(microsecond=0)
        record = ProjectORM(
            name=payload.name,
            artist=payload.artist,
            genre=payload.genre,
            bpm=payload.bpm,
            key=payload.key,
            notes=payload.notes,
            status=payload.status.value if isinstance(payload.status, ProjectStatus) else str(payload.status),
            created_at=now,
            updated_at=now,
        )
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        return self._to_schema(record)

    def _to_schema(self, record: ProjectORM) -> Project:
        return Project(
            id=record.id,
            name=record.name,
            artist=record.artist,
            genre=record.genre,
            bpm=record.bpm,
            key=record.key,
            notes=record.notes,
            status=ProjectStatus(record.status),
            created_at=record.created_at,
            updated_at=record.updated_at,
        )


project_store = SQLAlchemyProjectRepository()