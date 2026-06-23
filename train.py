from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
import pickle

texts = [
    "hello",
    "hi",
    "hey",
    "good morning",
    "bye",
    "goodbye",
    "see you",
    "thanks",
    "thank you"
]

labels = [
    "greeting",
    "greeting",
    "greeting",
    "greeting",
    "goodbye",
    "goodbye",
    "goodbye",
    "thanks",
    "thanks"
]

vectorizer =  TfidfVectorizer(
    analyzer="char_wb",
    ngram_range=(3, 5)
)
X = vectorizer.fit_transform(texts)

model = SGDClassifier(loss='log_loss', max_iter=1000, tol=1e-3)
model.fit(X, labels)

with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

with open("vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

print("Model trained successfully")