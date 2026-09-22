from sqlalchemy import ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base, engine

OWNER = "local-producer"
WORKSPACE = "omega-house-studio"


class Run(Base):
    __tablename__ = "workbench_runs"
    __table_args__ = (UniqueConstraint("owner_id", "request_id"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(80), default=OWNER)
    workspace_id: Mapped[str] = mapped_column(String(80), default=WORKSPACE)
    project_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("projects.id"), nullable=True)
    request_id: Mapped[str] = mapped_column(String(36))
    request_hash: Mapped[str] = mapped_column(String(64))
    kind: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[str] = mapped_column(String(40))
    completed_at: Mapped[str | None] = mapped_column(String(40), nullable=True)
    request_json: Mapped[str] = mapped_column(Text)
    result_json: Mapped[str] = mapped_column(Text, default="{}")
    error: Mapped[str | None] = mapped_column(Text, nullable=True)


class Asset(Base):
    __tablename__ = "workbench_assets"
    __table_args__ = (UniqueConstraint("owner_id", "sha256"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(80), default=OWNER)
    workspace_id: Mapped[str] = mapped_column(String(80), default=WORKSPACE)
    name: Mapped[str] = mapped_column(String(180))
    sha256: Mapped[str] = mapped_column(String(64))
    category: Mapped[str] = mapped_column(String(30))
    bytes: Mapped[int] = mapped_column(Integer)
    metadata_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[str] = mapped_column(String(40))


class WorkEvent(Base):
    __tablename__ = "workbench_events"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(80), default=OWNER)
    workspace_id: Mapped[str] = mapped_column(String(80), default=WORKSPACE)
    run_id: Mapped[str] = mapped_column(ForeignKey("workbench_runs.id"))
    type: Mapped[str] = mapped_column(String(80))
    occurred_at: Mapped[str] = mapped_column(String(40))
    payload: Mapped[str] = mapped_column(Text)


Base.metadata.create_all(engine)
