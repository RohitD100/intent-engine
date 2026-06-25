"""Core chatbot logic – pure functions, no framework dependencies.
All persistence is delegated to the DB layer (see intent_engine.db).
"""

import random
import difflib
import re
import datetime
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
    return reply

def _check_knowledge(message: str) -> Optional[str]:
    msg = message.lower()
    for k, v in WITH_KNOWLEDGE.items():
        if k in msg:
            return v
    return None

def _approx_match(text: str, keywords: list) -> bool:
    """Return True if any keyword appears as a substring in the text.
    This uses simple exact substring matching to avoid false‑positive fuzzy matches.
    """
    lowered = text.lower()
    for kw in keywords:
        if kw in lowered:
            return True
    return False

def _available_slots(date_str: str) -> list:
    return ["10:00", "14:00", "16:00"]

def _parse_date(text: str) -> str:
    import re, datetime
    lowered = text.lower().strip()
    # Remove trailing time specifications like "at 10:00"
    lowered = re.sub(r"\s+at\s+.*$", "", lowered)
    # Expand tomorrow spellings to be more tolerant
    tomorrow_variants = [
        "tomorrow", "tomoerow", "tomoreow", "tomorow", "yomorrow",
        "tomorroq", "tomoreoq", "tomoroq", "tomroow", "tommorow", "tommorow",
        "tmorrow", "tommorrow", "tomorow", "tomorrw", "tomorow"
    ]
    if any(v in lowered for v in tomorrow_variants):
        return (datetime.date.today() + datetime.timedelta(days=1)).isoformat()
    # Recognize "next <weekday>" with fuzzy matching for misspelled weekdays
    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    m = re.search(r"next\s+([a-z]{3,9})", lowered)
    if m:
        cand = m.group(1)
        # Find closest weekday using difflib if exact prefix not found
        matches = difflib.get_close_matches(cand, weekdays, n=1, cutoff=0.5)
        day = matches[0] if matches else None
        if not day:
            for d in weekdays:
                if d.startswith(cand[:3]):
                    day = d
                    break
        if day:
            days_ahead = (weekdays.index(day) - datetime.date.today().weekday() + 7) % 7
            days_ahead = days_ahead or 7
            return (datetime.date.today() + datetime.timedelta(days=days_ahead)).isoformat()
    return text.strip()

def _is_valid_time(t: str) -> bool:
    import re
    stripped = t.strip()
    if re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", stripped):
        return True
    if re.fullmatch(r"(?:[01]\d|2[0-3])", stripped):
        return True
    return False

def _log_state(old_state: dict, new_state: dict, action: str) -> None:
    print(f"[STATE LOG] Action: {action}, before: {old_state}, after: {new_state}")

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------

def _process_message_impl(message: str, session_id: str) -> dict:
    reply = ""
    confidence = None
    from ..db import get_state, set_state, save_history
    state = get_state(session_id)
    # Ensure intent persistence across turns
    current_intent = state.get("current_intent")
    # If we are in the middle of a flow, prioritize that over new intent detection
    if "booking" in state:
        current_intent = "booking"
    elif "cancellation" in state:
        current_intent = "cancellation"
    # Store back for later steps
    if current_intent:
        state["current_intent"] = current_intent

    kb_answer = _check_knowledge(message)
    if kb_answer:
        reply = _apply_personality(kb_answer)
        confidence = None
        intent = None
        set_state(session_id, state)
        save_history(session_id, message, reply, confidence, intent)
        return {"reply": reply, "confidence": confidence, "intent": intent}

    greeting_keywords = [
        "hello", "hi", "hey", "good morning", "good afternoon", "good evening",
        "greetings", "gud morning", "gud afternoon", "gud evening",
        "gud morninh", "gud mornibg", "gud moening",
        "gello", "gi", "hrllo", "hry there", "gey there", "hood morning",
        "good morninh", "goof morning", "gello", "gi", "hrllo"
    ]
    if current_intent is None and _approx_match(message.lower(), greeting_keywords):
        old_state = state.copy()
        state.pop("booking", None)
        state.pop("cancellation", None)
        _log_state(old_state, state, "greeting_reset_state")
        reply = _apply_personality(WITH_INTENTS.get("greeting", {"response": "Hi! How can I help?"})["response"])
        confidence = None
        intent = "greeting"
        set_state(session_id, state)
        save_history(session_id, message, reply, confidence, intent)
        return {"reply": reply, "confidence": confidence, "intent": intent}

    lowered = message.lower()
    intent = None
    cancel_keywords = [
        "cancel", "cance", "delete", "remove", "cancelling", "canc", "cancle",
        "abort", "stop", "terminate", "call off", "calloff", "drop"
    ]
    if _approx_match(lowered, cancel_keywords):
        intent = "cancel_appointment"
    if intent is None:
        booking_keywords = [
            "appointment", "appoin", "book", "schedule", "reserve", "meeting",
            "booki", "bookin", "appoibtment", "sppoibtment", "appointmebt",
            "nook an appointment", "make an appointment", "set up appointment"
        ]
        if _approx_match(lowered, booking_keywords):
            intent = "book_appointment"
    if intent is None:
        handoff_keywords = [
            "human", "person", "staff", "agent", "operator", "hum an", "humman",
            "peason", "real persob", "humab", "staff membrr", "hand over",
            "hand me over", "transfer", "human handoff", "talk to a person"
        ]
        if _approx_match(lowered, handoff_keywords):
            intent = "handoff"
    if intent is None:
        price_keywords = [
            "price", "cost", "fee", "discount", "how much", "pricing",
            "how much does", "what is the cost", "what's the price", "charge",
            "cleaning", "cleaning cost", "cleaning price", "procedure fee", "cleaning fee",
            "cleaning cost", "cleaning price", "fee for braces", "discounts", "discount"
        ]
        if _approx_match(lowered, price_keywords):
            intent = "price"
    if intent is None:
        small_talk_keywords = [
            "how are you", "how's it going", "what's up", "sup", "how are things",
            "what are you doing", "how's life", "how's your day"
        ]
        if _approx_match(lowered, small_talk_keywords):
            intent = "small_talk"

    if intent == "handoff":
        state["handoff_requested"] = True
        reply = _apply_personality("Human handoff has been requested. A support agent will contact you shortly.")
        confidence = None
        intent = None
    elif intent == "price":
        # Provide static pricing for known services and handle discounts/fees
        if "cleaning" in lowered:
            reply = _apply_personality("A standard cleaning costs $75.")
        elif "root canal" in lowered:
            reply = _apply_personality("Root canal treatment starts at $250.")
        elif "discount" in lowered or "discounts" in lowered:
            reply = _apply_personality("We currently have no discounts.")
        elif "braces" in lowered or "fee for braces" in lowered:
            reply = _apply_personality("Braces fee starts at $200.")
        else:
            reply = _apply_personality(WITH_INTENTS.get("price", {"response": "I don't have pricing info."})["response"])
        confidence = 1.0
    elif intent == "small_talk":
        reply = _apply_personality(WITH_INTENTS.get("small_talk", {"response": "I'm just a bot, but I'm doing fine!"})["response"])
        confidence = 1.0
        set_state(session_id, state)
        save_history(session_id, message, reply, confidence, intent)
        return {"reply": reply, "confidence": confidence, "intent": intent}
    if intent is None and "booking" not in state and "cancellation" not in state:
        # Detect time‑like input (e.g., "14:00" or "9") even if invalid, and suggest slots
        if re.search(r"^\s*\d{1,2}(?::\d{2})?\s*$", lowered):
            slots = _available_slots(datetime.date.today().isoformat())
            slots_str = ", ".join(slots)
            reply = _apply_personality(f"Available times: {slots_str}. Please let me know which one works for you.")
            confidence = None
            intent = None
            set_state(session_id, state)
            save_history(session_id, message, reply, confidence, intent)
            return {"reply": reply, "confidence": confidence, "intent": intent}
        # Date parsing for natural language dates like "tomorrow" or "next monday"
        parsed_date = _parse_date(lowered)
        if parsed_date != lowered:
            slots = _available_slots(parsed_date)
            slots_str = ", ".join(slots)
            reply = _apply_personality(f"Available times for {parsed_date}: {slots_str}. Please let me know which one works for you.")
            confidence = None
            intent = None
            set_state(session_id, state)
            save_history(session_id, message, reply, confidence, intent)
            return {"reply": reply, "confidence": confidence, "intent": intent}
    elif intent == "book_appointment":
        state["booking"] = {"step": "await_date"}
        reply = _apply_personality("Sure! What date would you like to book?")
        confidence = None
        intent = None
        set_state(session_id, state)
        save_history(session_id, message, reply, confidence, intent)
        return {"reply": reply, "confidence": confidence, "intent": intent}
    elif intent == "cancel_appointment":
        state["cancellation"] = {"step": "await_details"}
        reply = _apply_personality("Sure, please provide the appointment details you want to cancel.")
        confidence = None
        intent = None
        set_state(session_id, state)
        save_history(session_id, message, reply, confidence, intent)
        return {"reply": reply, "confidence": confidence, "intent": intent}
    else:
        reply = _apply_personality("I couldn't understand that. You can ask about booking, cancellation, price, discounts, or say 'help' for a list of supported commands.")
        confidence = 0.0
        intent = None

    if "booking" in state:
        booking = state["booking"]
        step = booking.get("step")
        if step == "await_date":
            raw_date = message.strip()
            parsed_date = _parse_date(raw_date)
            if parsed_date == raw_date:
                reply = _apply_personality("I couldn't understand the date. Please provide a clear date like 'tomorrow' or 'next Monday'.")
                confidence = None
            else:
                old_state = state.copy()
                booking["date"] = parsed_date
                booking["available"] = _available_slots(parsed_date)
                booking["step"] = "await_time"
                state["booking"] = booking
                _log_state(old_state, state, "await_date_parsed")
                slots_str = ", ".join(booking["available"])
                reply = _apply_personality(f"Available times for {parsed_date}: {slots_str}. Which one works for you?")
                confidence = None
        elif step == "await_time":
            chosen_raw = message.strip()
            if re.fullmatch(r"(?:[01]\d|2[0-3])", chosen_raw):
                chosen = f"{chosen_raw}:00"
            else:
                chosen = chosen_raw
            if not _is_valid_time(chosen):
                # Suggest available times when user provides an invalid time format
                available = booking.get("available", [])
                suggestion = f" Available times are: {', '.join(available)}." if available else ""
                reply = _apply_personality(f"'{chosen}' is not a valid time. Please provide a time in HH:MM (24‑hour) format.{suggestion}")
                confidence = None
            elif chosen not in booking.get("available", []):
                slots_str = ", ".join(booking.get("available", []))
                reply = _apply_personality(f"Sorry, {chosen} is not available. Available times: {slots_str}. Please choose one.")
                confidence = None
            else:
                booking["time"] = chosen
                date = booking.get("date", "[date]")
                reply = _apply_personality(f"Your appointment is booked for {date} at {chosen}.")
                state.pop("booking", None)
                confidence = None
        else:
            state.pop("booking", None)

    if "cancellation" in state:
        cancel = state["cancellation"]
        step = cancel.get("step")
        if step == "await_details":
            raw_details = message.strip()
            lower = raw_details.lower()
            time_match = None
            if " at " in lower:
                parts = lower.split(" at ")
                if len(parts) > 1:
                    time_candidate = parts[1].split()[0]
                    if _is_valid_time(time_candidate):
                        time_match = time_candidate
            date_part = lower.split(" at ")[0]
            parsed_date = _parse_date(date_part.strip())
            if parsed_date != date_part.strip():
                if time_match:
                    reply = _apply_personality(f"Your appointment on {parsed_date} at {time_match} has been cancelled.")
                else:
                    reply = _apply_personality(f"Your appointment on {parsed_date} has been cancelled.")
                state.pop("cancellation", None)
                _log_state(state, state, "cancellation_confirmed")
                confidence = None
                intent = None
            else:
                reply = _apply_personality("I couldn't understand the appointment you want to cancel. Please provide a clear date (e.g., 'tomorrow') and time if known.")
                confidence = None
                intent = None
                _log_state(state, state, "cancellation_invalid")
        else:
            state.pop("cancellation", None)

    set_state(session_id, state)
    save_history(session_id, message, reply, confidence, intent)
    return {"reply": reply, "confidence": confidence, "intent": intent}

# Exported name for FastAPI routing
process_message = _process_message_impl
