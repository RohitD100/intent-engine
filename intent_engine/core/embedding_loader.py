"""Placeholder for Sentence‑Transformers embedding loader.

The production version should load a pre‑trained SentenceTransformer model
(e.g., `all-MiniLM-L6-v2`) and expose a `transform` method compatible with
the existing TF‑IDF vectorizer interface.

For now this module provides a minimal stub that raises a clear error if
used, reminding the maintainer to install `sentence_transformers` and add
the serialized model files.
"""

import os
from pathlib import Path

# Expected path for the serialized SentenceTransformer model (to be added by the developer)
MODEL_DIR = Path(__file__).parents[2] / "embedding_model"

class EmbeddingVectorizer:
    """Thin wrapper mimicking the TF‑IDF vectorizer API.

    The real implementation should load the SentenceTransformer model and
    provide a `transform` method that returns a dense embedding matrix.
    """

    def __init__(self):
        if not MODEL_DIR.exists():
            raise FileNotFoundError(
                "Embedding model directory not found. Please add the SentenceTransformer model files to 'embedding_model/'."
            )
        # Placeholder – in a full implementation you would load the model here.
        # from sentence_transformers import SentenceTransformer
        # self.model = SentenceTransformer(str(MODEL_DIR / 'model'))
        raise NotImplementedError(
            "Embedding vectorizer not implemented. Install 'sentence_transformers' and load a model."
        )

    def transform(self, texts):
        """Return embeddings for a list of strings.

        The real method would return a NumPy array (n_samples, embedding_dim).
        """
        raise NotImplementedError("Embedding transform not implemented.")

def get_embedding_vectorizer():
    """Factory function returning an EmbeddingVectorizer instance.
    """
    return EmbeddingVectorizer()
