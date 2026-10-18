"""Forge records share Sonic's database and transactional persistence boundary.

Original ZIPs and derived artifacts are bounded BLOBs: a committed artifact and
its audit/idempotency record are atomic, including across process crashes.
"""
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, LargeBinary, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base, engine
from ..workbench.models import Run  # Register the existing workbench run table.


class ForgePack(Base):
    __tablename__ = "forge_packs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner: Mapped[str] = mapped_column(String(80), index=True)
    run_id: Mapped[str] = mapped_column(ForeignKey("workbench_runs.id"))
    revision: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(30))
    manifest: Mapped[str] = mapped_column(Text)
    source: Mapped[bytes] = mapped_column(LargeBinary)
    approved_revision: Mapped[int | None] = mapped_column(Integer, nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class ForgeArtifact(Base):
    __tablename__ = "forge_artifacts"
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    owner: Mapped[str] = mapped_column(String(80), index=True)
    pack_id: Mapped[str] = mapped_column(String(36), index=True)
    revision: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String(20))
    sha256: Mapped[str] = mapped_column(String(64))
    content: Mapped[bytes] = mapped_column(LargeBinary)


class ForgeCommand(Base):
    __tablename__ = "forge_commands"
    __table_args__ = (UniqueConstraint("owner", "request_id"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    owner: Mapped[str] = mapped_column(String(80), index=True)
    request_id: Mapped[str] = mapped_column(String(36))
    fingerprint: Mapped[str] = mapped_column(String(64))
    response: Mapped[str] = mapped_column(Text)


class ForgeEvent(Base):
    __tablename__ = "forge_events"
    id: Mapped[int] = mapped_column(primary_key=True)
    owner: Mapped[str] = mapped_column(String(80), index=True)
    pack_id: Mapped[str] = mapped_column(String(36), index=True)
    request_id: Mapped[str] = mapped_column(String(36))
    action: Mapped[str] = mapped_column(String(30))
    revision: Mapped[int] = mapped_column(Integer)
    evidence: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


Base.metadata.create_all(engine, tables=[ForgePack.__table__, ForgeArtifact.__table__,
                                       ForgeCommand.__table__, ForgeEvent.__table__])
