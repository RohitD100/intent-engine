"""Core chatbot logic – pure functions, no framework dependencies.
All persistence is delegated to the DB layer (see intent_engine.db).
"""

import random
from typing import Optional

from .model_loader import get_model, get_vectorizer

# Load static data (intents & knowledge) once at import time – they live in the project root.
import json
from pathlib import Path

BASE_DIR = Path(__file__).parents[2]
WITH_INTENTS = json.load(open(BASE_DIR / "intents.json"))
WITH_KNOWLEDGE = json.load(open(BASE_DIR / "knowledge.json")) if (BASE_DIR / "knowledge.json").exists() else {}

CONFIDENCE_THRESHOLD = 0.5

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------

def _apply_personality(reply: str) -> str:
    # prefixes = [
    #     "Sure thing!",
    #     "Here's what I think:",
    #     "Absolutely:",
    #     "Let me tell you:",
    #     "Interesting question!",
    # ]
    # return random.choice(prefixes) + " " + reply
    return reply

def _check_knowledge(message: str) -> Optional[str]:
    msg = message.lower()
    for k, v in WITH_KNOWLEDGE.items():
        if k in msg:
            return v
    return None

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------

def process_message(message: str, session_id: str) -> dict:
    """Take a raw user message and return a dict with reply, confidence and intent.
    Side‑effects: persists the turn and any fallback entry via the DB layer.
    """
    # Knowledge‑base shortcut
    kb_answer = _check_knowledge(message)
    if kb_answer:
        reply = _apply_personality(kb_answer)
        confidence = None
        intent = None
    else:
        vec = get_vectorizer().transform([message])
        probs = get_model().predict_proba(vec)[0]
        max_confidence = max(probs)
        intent_pred = get_model().classes_[probs.argmax()]
        if max_confidence >= CONFIDENCE_THRESHOLD:
            reply = _apply_personality(WITH_INTENTS.get(intent_pred, {"response": "I don't have a response."}).get("response"))
            confidence = max_confidence
            intent = intent_pred
        else:
            reply = _apply_personality("Sorry, I didn't understand that.")
            confidence = max_confidence
            intent = None
            # Record fallback for later self‑learning
            from ..db import log_fallback
            log_fallback(session_id, message)
    # Persist conversation turn
    from ..db import save_history
    save_history(session_id, message, reply, confidence, intent)
    return {"reply": reply, "confidence": confidence, "intent": intent}
