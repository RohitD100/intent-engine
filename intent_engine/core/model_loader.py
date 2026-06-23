"""Lazy, thread‑safe loading of the serialized model and vectorizer.
We keep the original pickle files in the project root (model.pkl, vectorizer.pkl).
"""

import pickle
from pathlib import Path
from threading import Lock

_model = None
_vectorizer = None
_lock = Lock()

BASE_DIR = Path(__file__).parents[2]  # project root (../.. from core)
MODEL_PATH = BASE_DIR / "model.pkl"
VEC_PATH = BASE_DIR / "vectorizer.pkl"


def get_model():
    """Return the trained SGDClassifier instance, loading it once on first call."""
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                with open(MODEL_PATH, "rb") as f:
                    _model = pickle.load(f)
    return _model


def get_vectorizer():
    """Return the fitted TfidfVectorizer, loading it once on first call."""
    global _vectorizer
    if _vectorizer is None:
        with _lock:
            if _vectorizer is None:
                with open(VEC_PATH, "rb") as f:
                    _vectorizer = pickle.load(f)
    return _vectorizer
