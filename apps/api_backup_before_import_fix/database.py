from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "data"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "sonic_ai.db"
DB_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class ProjectORM(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    artist: Mapped[str] = mapped_column(String(120), nullable=False)
    genre: Mapped[str] = mapped_column(String(80), nullable=False)
    bpm: Mapped[int] = mapped_column(nullable=False)
    key: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[str] = mapped_column(Text, nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class ChatSessionORM(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, default="Studio Session")
    project_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("projects.id"), nullable=True)
    focus: Mapped[str] = mapped_column(String(40), nullable=False, default="general")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class ChatMessageORM(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey("chat_sessions.id"), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class MemoryORM(Base):
    __tablename__ = "memories"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    memory_type: Mapped[str] = mapped_column(String(40), nullable=False, default="studio")
    category: Mapped[str] = mapped_column(String(60), nullable=False, default="general")
    content: Mapped[str] = mapped_column(Text, nullable=False)
    project_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("projects.id"), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    source: Mapped[str] = mapped_column(String(60), nullable=False, default="user")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class SessionSnapshotORM(Base):
    __tablename__ = "session_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("projects.id"), nullable=True)
    snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


class DecisionORM(Base):
    __tablename__ = "decisions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("projects.id"), nullable=True)
    asset_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    observation: Mapped[str] = mapped_column(Text, nullable=False)
    evidence: Mapped[str] = mapped_column(Text, nullable=True)
    interpretation: Mapped[str] = mapped_column(Text, nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    recommendation: Mapped[str] = mapped_column(Text, nullable=True)
    selected_option: Mapped[str] = mapped_column(Text, nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=True)
    action: Mapped[str] = mapped_column(Text, nullable=True)
    outcome: Mapped[str] = mapped_column(Text, nullable=True)
    producer_response: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


Base.metadata.create_all(bind=engine)
