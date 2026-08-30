from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from ..database import SessionSnapshotORM, SessionLocal
from schemas.session_snapshot import SessionSnapshot, SessionSnapshotCreate


class SQLAlchemySessionSnapshotRepository:
    def __init__(self, session: Session | None = None) -> None:
        self._session = session or SessionLocal()

    def list_snapshots(self, project_id: int | None = None, limit: int = 50) -> list[SessionSnapshot]:
        query = self._session.query(SessionSnapshotORM).order_by(SessionSnapshotORM.created_at.desc())
        if project_id is not None:
            query = query.filter(SessionSnapshotORM.project_id == project_id)
        records = query.limit(limit).all()
        return [self._to_schema(record) for record in records]

    def create_snapshot(self, payload: SessionSnapshotCreate) -> SessionSnapshot:
        now = datetime.utcnow().replace(microsecond=0)
        record = SessionSnapshotORM(
            project_id=payload.project_id,
            snapshot=payload.snapshot,
            created_at=now,
        )
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        return self._to_schema(record)

    def _to_schema(self, record: SessionSnapshotORM) -> SessionSnapshot:
        return SessionSnapshot(
            id=record.id,
            project_id=record.project_id,
            snapshot=record.snapshot,
            created_at=record.created_at,
        )


snapshot_store = SQLAlchemySessionSnapshotRepository()
