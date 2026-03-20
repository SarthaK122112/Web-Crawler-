"""
NLP preprocessing pipeline using spaCy.

Handles tokenization, lemmatization, stop-word removal,
and named entity recognition for crawled page content.
"""

import logging
from typing import List, Optional

logger = logging.getLogger(__name__)

try:
    import spacy
    _NLP_MODEL = None

    def _get_nlp():
        """Lazy-load the spaCy model (expensive to initialize)."""
        global _NLP_MODEL
        if _NLP_MODEL is None:
            try:
                _NLP_MODEL = spacy.load("en_core_web_md")
            except OSError:
                logger.warning("en_core_web_md not found, falling back to en_core_web_sm")
                try:
                    _NLP_MODEL = spacy.load("en_core_web_sm")
                except OSError:
                    logger.error("No spaCy model available. Run: python -m spacy download en_core_web_md")
                    _NLP_MODEL = None
        return _NLP_MODEL

    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logger.warning("spaCy not installed — preprocessing will use fallback tokenizer")


class NLPPreprocessor:
    """
    Text preprocessing pipeline for web page content.

    Uses spaCy for linguistic analysis when available,
    with a lightweight regex-based fallback otherwise.
    """

    def __init__(self):
        self.nlp = _get_nlp() if SPACY_AVAILABLE else None

    def process(self, text: str) -> str:
        """
        Clean and preprocess raw page text.

        Performs:
          - Whitespace normalization
          - Tokenization & lemmatization
          - Stop-word and punctuation removal

        Returns the cleaned, lemmatized text string.
        """
        if not text or len(text.strip()) < 20:
            return ""

        text = self._normalize_whitespace(text)

        if self.nlp:
            return self._spacy_process(text)
        return self._fallback_process(text)

    def _spacy_process(self, text: str) -> str:
        """Process text using the spaCy pipeline."""
        # Limit to first 100,000 chars to avoid OOM
        doc = self.nlp(text[:100_000])

        tokens = []
        for token in doc:
            if token.is_stop or token.is_punct or token.is_space:
                continue
            if len(token.lemma_) < 2:
                continue
            tokens.append(token.lemma_.lower())

        return " ".join(tokens)

    def _fallback_process(self, text: str) -> str:
        """Simple fallback tokenizer when spaCy is unavailable."""
        import re
        words = re.findall(r"\b[a-zA-Z]{2,}\b", text.lower())

        stop_words = {
            "the", "is", "in", "at", "of", "and", "or", "to", "a", "an",
            "for", "on", "with", "by", "from", "as", "it", "that", "this",
            "be", "are", "was", "were", "has", "have", "had", "not", "but",
            "what", "which", "who", "whom", "how", "when", "where", "why",
            "can", "will", "do", "does", "did", "may", "might", "should",
            "could", "would", "shall", "its", "they", "them", "their", "we",
            "our", "you", "your", "he", "she", "his", "her",
        }

        return " ".join(w for w in words if w not in stop_words)

    def extract_entities(self, text: str) -> List[dict]:
        """
        Extract named entities from text using spaCy NER.

        Returns a list of dicts with entity text, label, and character offsets.
        """
        if not self.nlp or not text:
            return []

        doc = self.nlp(text[:50_000])
        return [
            {"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char}
            for ent in doc.ents
        ]

    @staticmethod
    def _normalize_whitespace(text: str) -> str:
        """Collapse multiple whitespace characters into single spaces."""
        import re
        return re.sub(r"\s+", " ", text).strip()
