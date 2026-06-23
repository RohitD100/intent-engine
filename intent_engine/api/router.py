"""FastAPI router – thin glue between HTTP and the core chatbot logic."""

from fastapi import APIRouter, Header, HTTPException
from ..core.chatbot import process_message
from .schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/api")

@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(
    payload: ChatRequest,
    session_id: str = Header(..., description="Unique client identifier"),
):
    """Receive a user message, forward to `process_message`, and return the reply.
    The caller must provide a `session_id` header (e.g. a UUID) so each user gets its own history.
    """
    result = process_message(payload.message, session_id)
    return ChatResponse(**result)
