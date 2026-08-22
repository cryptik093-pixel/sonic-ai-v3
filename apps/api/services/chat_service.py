from __future__ import annotations

from repositories.chat_repository import chat_store
from schemas.agent_protocol import AgentId, AgentTask
from schemas.chat import (
    ChatMessage,
    ChatRole,
    ChatSendRequest,
    ChatSendResponse,
    ChatSession,
    ChatSessionCreate,
    ChatSessionDetail,
    StudioFocus,
)
from services.agent_orchestrator import AgentOrchestrationError, agent_orchestrator
from services.llm_service import llm_service


class ChatService:
    def list_sessions(self) -> list[ChatSession]:
        return chat_store.list_sessions()

    def get_session(self, session_id: int) -> ChatSessionDetail | None:
        return chat_store.get_session(session_id)

    def create_session(self, payload: ChatSessionCreate) -> ChatSession:
        return chat_store.create_session(payload)

    def send_message(self, session_id: int, payload: ChatSendRequest) -> ChatSendResponse:
        session = chat_store.get_session(session_id)
        if session is None:
            raise ValueError(f"Session {session_id} not found.")

        focus = payload.focus or session.focus
        project_id = payload.project_id if payload.project_id is not None else session.project_id

        user_message = chat_store.add_message(session_id, ChatRole.USER, payload.message.strip())

        try:
            history = chat_store.get_recent_messages(session_id, limit=20)
            result = agent_orchestrator.execute(
                AgentTask(
                    requesting_agent_id=AgentId.OMEGA,
                    target_agent_id=AgentId.OMEGA,
                    task_type="studio_assistance",
                    objective=payload.message.strip(),
                    project_id=project_id,
                    session_id=session_id,
                    input_data={
                        "focus": focus.value,
                        "history": [
                            {"role": message.role.value, "content": message.content}
                            for message in history
                        ],
                    },
                    context_requirements=["project", "assets", "memory"],
                ),
                focus=focus,
            )
            reply_content = result.agent_message.payload["content"]
        except AgentOrchestrationError as exc:
            raise ValueError(str(exc)) from exc

        reply_message = chat_store.add_message(session_id, ChatRole.ASSISTANT, reply_content)

        return ChatSendResponse(
            session_id=session_id,
            message=user_message,
            reply=reply_message,
            context_used=result.context_labels,
        )

    def start_and_send(self, payload: ChatSendRequest) -> ChatSendResponse:
        title = self._derive_session_title(payload.message)
        session = chat_store.create_session(
            ChatSessionCreate(
                title=title,
                project_id=payload.project_id,
                focus=payload.focus,
            )
        )
        return self.send_message(session.id, payload)

    def _derive_session_title(self, message: str) -> str:
        cleaned = " ".join(message.strip().split())
        if len(cleaned) <= 60:
            return cleaned or "Studio Session"
        return f"{cleaned[:57]}..."


chat_service = ChatService()
