import sys
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from schemas.asset import Asset
from schemas.chat import ChatMessage, ChatRole
from schemas.memory import Memory, MemoryCategory, MemoryType
from schemas.project import Project, ProjectStatus
from services.context_engine import ContextEngine


OBSERVED_AT = datetime.now(timezone.utc)


def test_build_context_package_contains_typed_provenance_and_legacy_rendering() -> None:
    project = Project(
        id=7,
        name="Neon Harbor",
        artist="Kai Sol",
        genre="Synthwave",
        bpm=124,
        key="A minor",
        notes="Dark synth layers",
        status=ProjectStatus.ACTIVE,
        created_at=OBSERVED_AT,
        updated_at=OBSERVED_AT,
    )
    asset = Asset(
        id=11,
        project_id=7,
        filename="pad.wav",
        filepath="uploads/pad.wav",
        file_type="audio/wav",
        duration=8.0,
        bpm=124,
        key="A minor",
        created_at=OBSERVED_AT,
    )
    memory = Memory(
        id=19,
        memory_type=MemoryType.STUDIO,
        category=MemoryCategory.PREFERENCE,
        content="Keep the pads wide.",
        project_id=7,
        confidence=0.8,
        source="user",
        created_at=OBSERVED_AT,
        updated_at=OBSERVED_AT,
    )
    message = ChatMessage(
        id=23,
        session_id=31,
        role=ChatRole.USER,
        content="Review the pad.",
        created_at=OBSERVED_AT,
    )

    with patch("services.context_engine.project_store.list_projects", return_value=[project]), patch(
        "services.context_engine.asset_service.list_assets", return_value=[asset]
    ), patch(
        "services.context_engine.memory_store.search_relevant", return_value=[memory]
    ), patch(
        "services.context_engine.chat_store.get_recent_messages", return_value=[message]
    ):
        engine = ContextEngine()
        package = engine.build_context_package("Review the pad.", project_id=7, session_id=31)
        rendered, labels = engine.build_context("Review the pad.", project_id=7, session_id=31)

    assert package.context_labels == ["project", "assets", "memory"]
    assert {item.source.source_type.value for item in package.observations} == {"project", "asset", "memory", "chat_message"}
    assert any(item.source.source_id == "7" and item.field == "genre" for item in package.observations)
    assert any(item.source.source_id == "11" and item.field == "filename" for item in package.observations)
    assert any(item.source.source_id == "19" and item.field == "content" for item in package.observations)
    assert package.chat is not None
    assert package.chat.messages[0].id == 23
    assert labels == ["project", "assets", "memory"]
    assert "Neon Harbor" in rendered
    assert "pad.wav" in rendered
    assert "Keep the pads wide." in rendered
