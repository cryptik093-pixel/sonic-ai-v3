from fastapi import APIRouter, HTTPException, status

from ..schemas.chat import ChatSendRequest, ChatSendResponse, ChatSession, ChatSessionCreate, ChatSessionDetail
from ..services.chat_service import chat_service

router = APIRouter(
    prefix="/chat",
    tags=["Studio AI"],
)


@router.get(
    "/sessions",
    response_model=list[ChatSession],
    summary="List chat sessions",
)
def list_sessions() -> list[ChatSession]:
    return chat_service.list_sessions()


@router.post(
    "/sessions",
    response_model=ChatSession,
    status_code=status.HTTP_201_CREATED,
    summary="Create chat session",
)
def create_session(payload: ChatSessionCreate) -> ChatSession:
    return chat_service.create_session(payload)


@router.get(
    "/sessions/{session_id}",
    response_model=ChatSessionDetail,
    summary="Get chat session with messages",
)
def get_session(session_id: int) -> ChatSessionDetail:
    session = chat_service.get_session(session_id)
    if session is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")
    return session


@router.post(
    "/sessions/{session_id}/messages",
    response_model=ChatSendResponse,
    summary="Send message in session",
)
def send_message(session_id: int, payload: ChatSendRequest) -> ChatSendResponse:
    try:
        return chat_service.send_message(session_id, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.post(
    "/messages",
    response_model=ChatSendResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Start new session and send message",
)
def start_and_send(payload: ChatSendRequest) -> ChatSendResponse:
    try:
        return chat_service.start_and_send(payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
