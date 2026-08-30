from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from ..database import ChatMessageORM, ChatSessionORM, SessionLocal
from schemas.chat import ChatMessage, ChatSession, ChatSessionCreate, ChatSessionDetail, ChatRole


class SQLAlchemyChatRepository:
    def __init__(self, session: Session | None = None) -> None:
        self._session = session or SessionLocal()

    def clear(self) -> None:
        with SessionLocal() as session:
            session.query(ChatMessageORM).delete()
            session.query(ChatSessionORM).delete()
            session.commit()

    def list_sessions(self) -> list[ChatSession]:
        records = (
            self._session.query(ChatSessionORM)
            .order_by(ChatSessionORM.updated_at.desc())
            .all()
        )
        return [self._session_to_schema(record) for record in records]

    def get_session(self, session_id: int) -> ChatSessionDetail | None:
        record = self._session.query(ChatSessionORM).filter(ChatSessionORM.id == session_id).first()
        if record is None:
            return None

        messages = (
            self._session.query(ChatMessageORM)
            .filter(ChatMessageORM.session_id == session_id)
            .order_by(ChatMessageORM.created_at.asc())
            .all()
        )

        detail = ChatSessionDetail(
            **self._session_to_schema(record).model_dump(),
            messages=[self._message_to_schema(message) for message in messages],
        )
        return detail

    def create_session(self, payload: ChatSessionCreate) -> ChatSession:
        now = datetime.utcnow().replace(microsecond=0)
        record = ChatSessionORM(
            title=payload.title,
            project_id=payload.project_id,
            focus=payload.focus.value,
            created_at=now,
            updated_at=now,
        )
        self._session.add(record)
        self._session.commit()
        self._session.refresh(record)
        return self._session_to_schema(record)

    def add_message(self, session_id: int, role: ChatRole, content: str) -> ChatMessage:
        now = datetime.utcnow().replace(microsecond=0)
        record = ChatMessageORM(
            session_id=session_id,
            role=role.value,
            content=content,
            created_at=now,
        )
        self._session.add(record)

        session_record = (
            self._session.query(ChatSessionORM).filter(ChatSessionORM.id == session_id).first()
        )
        if session_record is not None:
            session_record.updated_at = now

        self._session.commit()
        self._session.refresh(record)
        return self._message_to_schema(record)

    def get_recent_messages(self, session_id: int, limit: int = 20) -> list[ChatMessage]:
        records = (
            self._session.query(ChatMessageORM)
            .filter(ChatMessageORM.session_id == session_id)
            .order_by(ChatMessageORM.created_at.desc())
            .limit(limit)
            .all()
        )
        records.reverse()
        return [self._message_to_schema(record) for record in records]

    def _session_to_schema(self, record: ChatSessionORM) -> ChatSession:
        from schemas.chat import StudioFocus

        return ChatSession(
            id=record.id,
            title=record.title,
            project_id=record.project_id,
            focus=StudioFocus(record.focus),
            created_at=record.created_at,
            updated_at=record.updated_at,
        )

    def _message_to_schema(self, record: ChatMessageORM) -> ChatMessage:
        return ChatMessage(
            id=record.id,
            session_id=record.session_id,
            role=ChatRole(record.role),
            content=record.content,
            created_at=record.created_at,
        )


chat_store = SQLAlchemyChatRepository()
