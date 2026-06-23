"""Generate synthetic WhatsApp conversations with the Intent Engine.

The script simulates 100 different dental‑clinic customers.  Each customer gets a
unique session UUID and a short conversation that exercises the various chatbot
features:

* spelling mistakes
* incomplete answers
* interruptions (multiple messages in quick succession)
* changing requirements (switching intents mid‑conversation)
* price questions
* appointment booking and cancellation
* human‑hand‑off requests

If any exception is raised while calling ``process_message`` the script catches the
error, prints a concise description together with the traceback, and continues
with the next simulated customer.

The output is written to ``generated_conversations.json`` in the project root.
"""

import uuid
import random
import json
import traceback
from pathlib import Path

# Import the chatbot entry point
from intent_engine.core.chatbot import process_message

# ---------------------------------------------------------------------------
# Helpers to introduce variability
# ---------------------------------------------------------------------------

def typo(text: str, prob: float = 0.15) -> str:
    """Introduce random typographical errors with probability *prob* per character.
    Simple implementation: replace a character with a nearby keyboard key.
    """
    if not text:
        return text
    keys = {
        "a": "s", "s": "a", "d": "f", "f": "d",
        "q": "w", "w": "q", "e": "r", "r": "e",
        "t": "y", "y": "t", "g": "h", "h": "g",
        "z": "x", "x": "z", "c": "v", "v": "c",
        "b": "n", "n": "b",
        "1": "2", "2": "1", "3": "4", "4": "3",
        "5": "6", "6": "5",
    }
    chars = list(text)
    for i, ch in enumerate(chars):
        if random.random() < prob and ch.lower() in keys:
            replacement = keys[ch.lower()]
            # Preserve original case
            chars[i] = replacement.upper() if ch.isupper() else replacement
    return "".join(chars)


def truncate(text: str, prob: float = 0.1) -> str:
    """Randomly cut the message short to simulate an incomplete answer.
    With probability *prob* returns only the first half of the string.
    """
    if random.random() < prob:
        return text[: len(text) // 2]
    return text


def random_price_question() -> str:
    return random.choice([
        "How much does a cleaning cost?",
        "Price for a root canal?",
        "What is the fee for braces?",
        "Do you have any discounts?",
    ])


def random_booking_flow() -> list:
    """Return a list of messages that guide a booking scenario.
    The flow may change requirements mid‑way (e.g. ask for a different date).
    """
    steps = [
        "I would like to book an appointment.",
        "Tomorrow",  # date
        random.choice(["10:00", "14:00", "16:00", "09:30"]),  # time (some invalid)
    ]
    # Occasionally insert a change of mind
    if random.random() < 0.2:
        steps.insert(1, "Actually, can I do it next Monday?")
    return steps


def random_cancellation_flow() -> list:
    return [
        "I need to cancel my appointment.",
        "Tomorrow at 14:00",
    ]


def random_handoff() -> str:
    return random.choice([
        "I want to talk to a human.",
        "Can I speak with a real person?",
        "Please hand me over to a staff member.",
    ])


def random_greeting() -> str:
    return random.choice([
        "Hi", "Hello", "Hey there", "Good morning",
    ])


# ---------------------------------------------------------------------------
# Conversation generator
# ---------------------------------------------------------------------------

def simulate_customer(customer_id: int) -> dict:
    session_id = str(uuid.uuid4())
    conversation = []
    try:
        # 1. Greeting
        user_msg = typo(random_greeting())
        conv = process_message(user_msg, session_id)
        conversation.append({"role": "user", "message": user_msg})
        conversation.append({"role": "bot",  "message": conv["reply"]})

        # 2. Randomly pick a primary scenario
        scenario = random.choice(["price", "booking", "cancellation", "handoff", "smalltalk"])
        if scenario == "price":
            user_msg = typo(random_price_question())
            conv = process_message(user_msg, session_id)
            conversation.append({"role": "user", "message": user_msg})
            conversation.append({"role": "bot",  "message": conv["reply"]})
        elif scenario == "booking":
            for step in random_booking_flow():
                # Occasionally send an incomplete message
                user_msg = truncate(typo(step))
                conv = process_message(user_msg, session_id)
                conversation.append({"role": "user", "message": user_msg})
                conversation.append({"role": "bot",  "message": conv["reply"]})
        elif scenario == "cancellation":
            for step in random_cancellation_flow():
                user_msg = typo(step)
                conv = process_message(user_msg, session_id)
                conversation.append({"role": "user", "message": user_msg})
                conversation.append({"role": "bot",  "message": conv["reply"]})
        elif scenario == "handoff":
            user_msg = typo(random_handoff())
            conv = process_message(user_msg, session_id)
            conversation.append({"role": "user", "message": user_msg})
            conversation.append({"role": "bot",  "message": conv["reply"]})
        else:  # smalltalk / random intent
            user_msg = typo("How are you?")
            conv = process_message(user_msg, session_id)
            conversation.append({"role": "user", "message": user_msg})
            conversation.append({"role": "bot",  "message": conv["reply"]})

    except Exception as e:
        # Capture the error details for this customer
        err = {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "session_id": session_id,
        }
        return {"customer_id": customer_id, "error": err, "conversation": conversation}

    return {"customer_id": customer_id, "session_id": session_id, "conversation": conversation}


def main():
    results = []
    for cid in range(1, 101):
        results.append(simulate_customer(cid))
    out_path = Path(__file__).parent / "generated_conversations.json"
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"Generated {len(results)} conversations → {out_path}")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate synthetic WhatsApp conversations.")
    parser.add_argument("-n", "--num", type=int, default=100,
                        help="Number of customers to simulate (default 100)")
    parser.add_argument("-o", "--output", type=str,
                        default=str(Path(__file__).parent / "generated_conversations.json"),
                        help="Output JSON file path")
    args = parser.parse_args()
    # Re‑use the existing main logic but with custom count / output
    results = []
    for cid in range(1, args.num + 1):
        results.append(simulate_customer(cid))
    out_path = Path(args.output)
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"Generated {len(results)} conversations → {out_path}")
