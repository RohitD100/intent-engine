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

# Helper to mock doctor slot availability (replace with real logic later)
def _available_slots(date_str: str) -> list:
    """Return a list of available time slots for the given date.
    Currently a static stub – replace with a DB lookup or external API.
    """
    return ["10:00", "14:00", "16:00"]

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------

def process_message(message: str, session_id: str) -> dict:
    """Take a raw user message and return a dict with reply, confidence and intent.
    Side‑effects: persists the turn, any fallback entry via the DB layer,
    and maintains per‑session state.
    """
    # Load existing conversation state (or empty dict)
    from ..db import get_state, set_state, save_history
    state = get_state(session_id)

    # Knowledge‑base shortcut
    kb_answer = _check_knowledge(message)
    if kb_answer:
        reply = _apply_personality(kb_answer)
        confidence = None
        intent = None
    else:
        # If we are in the middle of a booking or cancellation flow, skip model inference.
        if "booking" in state or "cancellation" in state:
            reply = None
            confidence = None
            intent = None
        else:
            lowered = message.lower()
            if "appointment" in lowered:
                intent = "book_appointment"
                confidence = 1.0
                reply = _apply_personality(WITH_INTENTS.get(intent, {"response": "I don't have a response."}).get("response"))
            else:
                # Default fallback when no model is available.
                reply = _apply_personality("Sorry, I didn't understand that.")
                confidence = 0.0
                intent = None

    # ----- Booking flow -----
    if "booking" in state:
        booking = state["booking"]
        step = booking.get("step")
        if step == "await_date":
            booking["date"] = message.strip()
            booking["available"] = _available_slots(booking["date"])  # store for later verification
            booking["step"] = "await_time"
            state["booking"] = booking
            slots_str = ", ".join(booking["available"])
            reply = _apply_personality(f"Available times for {booking['date']}: {slots_str}. Which one works for you?")
            confidence = None
            intent = None
        elif step == "await_time":
            chosen = message.strip()
            if chosen not in booking.get("available", []):
                slots_str = ", ".join(booking.get("available", []))
                reply = _apply_personality(f"Sorry, {chosen} is not available. Available times: {slots_str}. Please choose one.")
                confidence = None
                intent = None
            else:
                booking["time"] = chosen
                date = booking.get("date", "[date]")
                time = booking["time"]
                reply = _apply_personality(f"Your appointment is booked for {date} at {time}.")
                state.pop("booking", None)
                confidence = None
                intent = None
        else:
            # Unknown step – reset booking state
            state.pop("booking", None)
    # Start a new booking if none is active and intent indicates booking
    if "booking" not in state and intent == "book_appointment":
        state["booking"] = {"step": "await_date"}
        reply = _apply_personality("Sure! What date would you like to book?")
        confidence = None
        intent = None

    # ----- Cancellation flow -----
    if "cancellation" in state:
        cancel = state["cancellation"]
        step = cancel.get("step")
        if step == "await_details":
            cancel["details"] = message.strip()
            reply = _apply_personality(f"Your appointment '{cancel['details']}' has been cancelled.")
            state.pop("cancellation", None)
            confidence = None
            intent = None
        else:
            state.pop("cancellation", None)
    elif intent == "cancel_appointment":
        state["cancellation"] = {"step": "await_details"}
        reply = _apply_personality("Sure, please provide the appointment details you want to cancel.")
        confidence = None
        intent = None

    # Fallback: store last intent if not part of a flow
    if "booking" not in state and "cancellation" not in state:
        if intent:
            state["last_intent"] = intent
        else:
            state.pop("last_intent", None)

    # Persist updated state and conversation turn
    set_state(session_id, state)
    save_history(session_id, message, reply, confidence, intent)
    return {"reply": reply, "confidence": confidence, "intent": intent}
