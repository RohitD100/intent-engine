import uuid
import pytest
import sys

# Ensure the intent_engine package is on the import path
sys.path.append('intent_engine')
from intent_engine.core.chatbot import process_message

@pytest.mark.parametrize('msg', [
    "Hi",
    "Hello there",
    "I need to cancel my appointment",
    "I want to book an appointment",
    "Good morninh",
    "Could you handoff me to a human?",
    "What is the cleaning cost?",
    "Tell me the root canal price",
    "What is the braces fee?",
    "Do you have discounts?",
    "Tomorrow",
    "Next Monday",
    "Tomorrow at 2pm",
    "How are you?",
])
def test_intent(msg):
    """Run a quick sanity check for each sample message."""
    sess = str(uuid.uuid4())
    res = process_message(msg, sess)
    # Basic sanity: response dict contains expected keys
    assert isinstance(res, dict)
    assert "reply" in res
    # Ensure we get a non‑empty reply string
    assert isinstance(res["reply"], str)
    # Optional: print for debugging (pytest captures stdout)
    print(f'Input: {msg!r} => Intent: {res.get("intent")}, Reply: {res.get("reply")}')
