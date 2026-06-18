from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
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

model = MultinomialNB()
model.fit(X, labels)

with open("model.pkl", "wb") as f:
    pickle.dump(model, f)

with open("vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

print("Model trained successfully")