from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
import pickle
import json

# Load intents
with open("intents.json", "r", encoding="utf-8") as f:
    intents = json.load(f)

texts = []
labels = []

# Extract patterns + intents
for intent_name, intent_data in intents.items():
    patterns = intent_data.get("patterns", [])

    for pattern in patterns:
        texts.append(pattern.lower())
        labels.append(intent_name)

# Safety check
if not texts:
    raise ValueError("No training data found in intents.json")

# Vectorizer
vectorizer = TfidfVectorizer(
    analyzer="char_wb",
    ngram_range=(3, 5)
)

X = vectorizer.fit_transform(texts)

# Model
model = SGDClassifier(loss="log_loss", max_iter=1000, tol=1e-3)
model.fit(X, labels)

# Save model
with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

with open("vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

print("Model trained successfully!")
print("Training samples:", len(texts))
print("Intents:", list(intents.keys()))