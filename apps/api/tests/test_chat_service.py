from unittest.mock import patch

from apps.api.repositories.chat_repository import chat_store
from apps.api.repositories.memory_repository import memory_store
from apps.api.repositories.project_repository import project_store
from apps.api.schemas.chat import ChatSendRequest, ChatSessionCreate, StudioFocus
from apps.api.schemas.memory import MemoryCategory, MemoryCreate, MemoryType
from apps.api.schemas.project import ProjectCreate
from apps.api.services.chat_service import chat_service


def test_start_and_send_creates_session_and_messages() -> None:
    chat_store.clear()

    with patch(
        "apps.api.services.chat_service.llm_service.generate",
        return_value="Try a high-pass at 30Hz on the 808 bus.",
    ):
        response = chat_service.start_and_send(
            ChatSendRequest(
                message="How do I clean up my 808?",
                focus=StudioFocus.MIXING,
            )
        )

    assert response.session_id == 1
    assert response.message.role.value == "user"
    assert response.reply.role.value == "assistant"
    assert "808" in response.reply.content

    session = chat_service.get_session(response.session_id)
    assert session is not None
    assert len(session.messages) == 2


def test_send_message_includes_project_context() -> None:
    project_store.clear()
    chat_store.clear()

    project = project_store.create_project(
        ProjectCreate(
            name="Neon Harbor",
            artist="Kai Sol",
            genre="Synthwave",
            bpm=124,
            key="A minor",
            notes="Dark synth layers",
            status="active",
        )
    )

    session = chat_service.create_session(
        ChatSessionCreate(
            title="Mix Session",
            project_id=project.id,
            focus=StudioFocus.MIXING,
        )
    )

    with patch(
        "apps.api.services.chat_service.llm_service.generate",
        return_value="Cut 300Hz on the pad.",
    ) as mock_generate:
        response = chat_service.send_message(
            session.id,
            ChatSendRequest(
                message="The pad is muddy in the low mids",
                project_id=project.id,
                focus=StudioFocus.MIXING,
            ),
        )

    assert "project" in response.context_used
    mock_generate.assert_called_once()
    system_message = mock_generate.call_args[0][0][0]["content"]
    assert "Neon Harbor" in system_message


def test_memory_create_and_search() -> None:
    memory_store.clear()

    memory_store.create_memory(
        MemoryCreate(
            memory_type=MemoryType.STUDIO,
            category=MemoryCategory.PREFERENCE,
            content="Always high-pass vocals at 80Hz",
            confidence=0.8,
        )
    )

    results = memory_store.search_relevant("vocals high-pass EQ", limit=5)
    assert len(results) == 1
    assert "80Hz" in results[0].content
