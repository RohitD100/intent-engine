#!/usr/bin/env python3
"""Replay generated dialogs by calling the FastAPI /api/chat endpoint."""

import json
import requests
from pathlib import Path

API_URL = "http://localhost:8000/api/chat"
DATA_FILE = Path(__file__).parent / "generated_conversations.json"

def chat(payload, session_id):
    headers = {"session-id": session_id}
    r = requests.post(API_URL, json=payload, headers=headers)
    r.raise_for_status()
    return r.json()["reply"]

def main():
    data = json.loads(DATA_FILE.read_text())
    print(f"\nReplaying {len(data)} conversations via HTTP …\n")

    for conv in data:
        cid = conv["customer_id"]
        sess = conv.get("session_id") or f"http-replay-{cid}"
        print(f"--- Customer {cid} (session {sess}) ---")

        if "error" in conv:
            err = conv["error"]
            print("⚡  Generation error:", err["error"])
            continue

        for turn in conv["conversation"]:
            if turn["role"] == "user":
                user_msg = turn["message"]
                print(f"> You: {user_msg}")
                try:
                    bot_reply = chat({"message": user_msg}, sess)
                except Exception as exc:
                    bot_reply = f"[ERROR] {type(exc).__name__}: {exc}"
                print(f"< Bot: {bot_reply}")
        print()

if __name__ == "__main__":
    main()