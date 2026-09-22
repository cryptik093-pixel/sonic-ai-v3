from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from ..database import MemoryORM, SessionLocal
from ..schemas.memory import Memory, MemoryCreate, MemoryCategory, MemoryType


class SQLAlchemyMemoryRepository:
    def __init__(self, session: Session | None = None) -> None:
        self._session = session or SessionLocal()

    def clear(self) -> None:
        with SessionLocal() as session:
            session.query(MemoryORM).delete()
            session.commit()

    def list_memories(
        self,
        project_id: int | None = None,
        limit: int = 50,
    ) -> list[Memory]:
        query = self._session.query(MemoryORM).order_by(MemoryORM.updated_at.desc())
        if project_id is not None:
            query = query.filter(
                (MemoryORM.project_id == project_id) | (MemoryORM.project_id.is_(None))
            )
        records = query.limit(limit).all()
        return [self._to_schema(record) for record in records]

    def create_memory(self, payload: MemoryCreate) -> Memory:
        now = datetime.utcnow().replace(microsecond=0)
        record = MemoryORM(
            memory_type=payload.memory_type.value,
            category=payload.category.value,
            content=payload.content,
            project_id=payload.project_id,
            confidence=payload.confidence,
            source=payload.source,
            created_at=now,
            updated_at=now,
        )
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        return self._to_schema(record)

    def search_relevant(self, query_text: str, project_id: int | None = None, limit: int = 8) -> list[Memory]:
        lowered = query_text.lower()
        tokens = [token for token in lowered.split() if len(token) > 3]
        records = self.list_memories(project_id=project_id, limit=100)

        scored: list[tuple[int, Memory]] = []
        for memory in records:
            content_lower = memory.content.lower()
            score = sum(1 for token in tokens if token in content_lower)
            if score > 0:
                scored.append((score, memory))

        scored.sort(key=lambda item: (item[0], item[1].confidence), reverse=True)
        return [memory for _, memory in scored[:limit]]

    def _to_schema(self, record: MemoryORM) -> Memory:
        return Memory(
            id=record.id,
            memory_type=MemoryType(record.memory_type),
            category=MemoryCategory(record.category),
            content=record.content,
            project_id=record.project_id,
            confidence=record.confidence,
            source=record.source,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )


memory_store = SQLAlchemyMemoryRepository()
