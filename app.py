"""Thin wrapper that delegates all logic to the new package.
Keeps the original CLI behaviour (session‑ID generation) while the FastAPI app is now
exposed as `intent_engine.main.app`.
"""

import uuid
from intent_engine.main import app as api_app
from intent_engine.core.chatbot import process_message
from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional

# Re‑export the FastAPI app under the name `api` for backward compatibility
api = api_app

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500)

class ChatResponse(BaseModel):
    reply: str
    confidence: Optional[float] = None
    intent: Optional[str] = None

def run_cli() -> None:
    try:
        """Interactive console – generates a fresh UUID for the session."""
        session_id = str(uuid.uuid4())
        print(f"Session ID: {session_id}")
        while True:
            message = input("You: ")
            result = process_message(message, session_id)
            print("AI:", result["reply"])
            # if result["confidence"] is not None:
            #     print(f"(confidence: {result['confidence']:.2f})")
            #     if result["confidence"] < 0.6:
            #         print("Note: low confidence")
    except KeyboardInterrupt:
        print("\nExiting…")
        # clean‑up or simply exit

if __name__ == "__main__":
    run_cli()



# pip install --upgrade pip
# source venv/bin/activate    


# /home/user/coding/intent-engine/app.py

# could you please test it by running replay_via_http.py file and read its output if uvicorn server is already running then use exisitng server, after that rate accuracy and then tell me key gaps