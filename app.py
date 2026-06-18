import json
import pickle

# Load model + vectorizer
with open("model.pkl", "rb") as f:
    model = pickle.load(f)

with open("vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)

with open("intents.json") as f:
    responses = json.load(f)

# Load knowledge base
try:
    with open("knowledge.json") as f:
        knowledge = json.load(f)
except FileNotFoundError:
    knowledge = {}

# Load memory
try:
    with open("memory.json") as f:
        memory = json.load(f)
except FileNotFoundError:
    memory = {}

CONFIDENCE_THRESHOLD = 0.5


def save_memory():
    with open("memory.json", "w") as f:
        json.dump(memory, f, indent=2)


def check_knowledge(message):
    """
    Simple keyword match against knowledge base
    """
    msg = message.lower()
    for key, value in knowledge.items():
        if key in msg:
            return value
    return None


while True:
    message = input("You: ")

    # ---- MEMORY UPDATE ----
    memory["last_message"] = message

    # ---- KNOWLEDGE CHECK FIRST (rule-based override) ----
    kb_answer = check_knowledge(message)
    if kb_answer:
        print("AI:", kb_answer)
        continue

    # ---- ML MODEL ----
    X = vectorizer.transform([message])
    probs = model.predict_proba(X)[0]

    max_confidence = max(probs)
    intent = model.classes_[probs.argmax()]

    if max_confidence >= CONFIDENCE_THRESHOLD:
        reply = responses.get(intent, "I don't have a response for that.")
        print("AI:", reply)

        # update memory
        memory["last_intent"] = intent
    else:
        print("AI: Sorry, I didn't understand that.")

    print(f"(confidence: {max_confidence:.2f})")

    # save memory after every turn
    save_memory()