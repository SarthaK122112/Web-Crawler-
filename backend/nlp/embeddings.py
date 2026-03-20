"""
Semantic relevance scoring using Sentence-BERT.

Encodes text into dense vector embeddings and computes
cosine similarity to measure topic relevance of crawled pages.
"""

import logging
import numpy as np
from typing import Union

logger = logging.getLogger(__name__)

try:
    from sentence_transformers import SentenceTransformer
    SBERT_AVAILABLE = True
except ImportError:
    SBERT_AVAILABLE = False
    logger.warning("sentence-transformers not installed — using TF-IDF fallback for scoring")


class SemanticScorer:
    """
    Computes semantic similarity between a search topic and page content.

    Uses the all-MiniLM-L6-v2 model from Sentence-Transformers for
    high-quality, fast embeddings. Falls back to TF-IDF cosine
    similarity when the model is unavailable.
    """

    MODEL_NAME = "all-MiniLM-L6-v2"

    def __init__(self):
        self.model = None
        if SBERT_AVAILABLE:
            try:
                self.model = SentenceTransformer(self.MODEL_NAME)
                logger.info(f"Loaded Sentence-BERT model: {self.MODEL_NAME}")
            except Exception as e:
                logger.error(f"Failed to load Sentence-BERT model: {e}")

    def encode(self, text: str) -> np.ndarray:
        """
        Encode text into a dense embedding vector.

        Args:
            text: Input text (topic query or page content).

        Returns:
            Numpy array representing the text embedding.
        """
        if not text:
            return np.zeros(384)

        # Truncate very long texts (model max ~256 tokens)
        truncated = text[:2000]

        if self.model:
            return self.model.encode(truncated, convert_to_numpy=True)

        # Fallback: character-level hash embedding
        return self._fallback_encode(truncated)

    def similarity(self, embedding_a: np.ndarray, embedding_b: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings.

        Returns a float between 0 (unrelated) and 1 (identical).
        """
        norm_a = np.linalg.norm(embedding_a)
        norm_b = np.linalg.norm(embedding_b)

        if norm_a == 0 or norm_b == 0:
            return 0.0

        cosine = np.dot(embedding_a, embedding_b) / (norm_a * norm_b)
        # Clamp to [0, 1] — negative cosines treated as no similarity
        return float(max(0.0, min(1.0, cosine)))

    def score_relevance(self, topic: str, content: str) -> float:
        """
        Convenience method: encode both texts and return similarity.

        Args:
            topic: Search topic or keyword.
            content: Page content text.

        Returns:
            Relevance score between 0.0 and 1.0.
        """
        topic_emb = self.encode(topic)
        content_emb = self.encode(content)
        return self.similarity(topic_emb, content_emb)

    @staticmethod
    def _fallback_encode(text: str) -> np.ndarray:
        """
        Simple fallback encoding using character n-gram hashing.

        Produces a 384-dimensional vector by hashing character trigrams
        into fixed bucket positions. Not semantically meaningful but
        provides basic keyword overlap detection.
        """
        vec = np.zeros(384)
        words = text.lower().split()
        for word in words:
            for i in range(len(word) - 2):
                trigram = word[i:i + 3]
                idx = hash(trigram) % 384
                vec[idx] += 1.0

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec
