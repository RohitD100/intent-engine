"""Pydantic request/response models for the FastAPI endpoints."""

from pydantic import BaseModel, Field
from typing import Optional


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)


class ChatResponse(BaseModel):
    reply: str
    confidence: Optional[float] = None
    intent: Optional[str] = None
