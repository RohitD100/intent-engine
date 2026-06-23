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

@router.post("/handoff", response_model=ChatResponse)
def handoff_endpoint(
    session_id: str = Header(..., description="Unique client identifier"),
):
    """Mark the conversation as needing human handoff.
    The chatbot will set a `handoff_requested` flag in the session state.
    """
    from ..db import get_state, set_state
    state = get_state(session_id)
    state["handoff_requested"] = True
    set_state(session_id, state)
    # Simple acknowledgment response; no confidence/intent needed.
    return ChatResponse(reply="Human handoff has been requested. A support agent will contact you shortly.", confidence=None, intent=None)
