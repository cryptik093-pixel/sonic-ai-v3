from __future__ import annotations

from ..repositories.chat_repository import chat_store
from ..schemas.chat import (
    ChatMessage,
    ChatRole,
    ChatSendRequest,
    ChatSendResponse,
    ChatSession,
    ChatSessionCreate,
    ChatSessionDetail,
    StudioFocus,
)
from ..services.context_engine import context_engine
from ..services.llm_service import LLMServiceError, llm_service
from ..services.producer_intelligence import build_context_block, build_system_prompt


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

        context_text, context_labels = context_engine.build_context(
            user_message=payload.message,
            project_id=project_id,
        )

        system_prompt = build_system_prompt(focus)
        if context_text:
            system_prompt = f"{system_prompt}\n\n{build_context_block([context_text])}"

        history = chat_store.get_recent_messages(session_id, limit=20)
        llm_messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

        for message in history:
            if message.role in (ChatRole.USER, ChatRole.ASSISTANT):
                llm_messages.append({"role": message.role.value, "content": message.content})

        try:
            reply_content = llm_service.generate(llm_messages)
        except LLMServiceError as exc:
            raise ValueError(str(exc)) from exc

        reply_message = chat_store.add_message(session_id, ChatRole.ASSISTANT, reply_content)

        return ChatSendResponse(
            session_id=session_id,
            message=user_message,
            reply=reply_message,
            context_used=context_labels,
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
