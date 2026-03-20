"""
Dark pattern detection engine.

Implements a hybrid approach combining:
  1. Rule-based keyword/regex detection for known deceptive patterns
  2. ML-based classification using DistilBERT for nuanced detection
  3. HTML structural analysis for UI-level dark patterns

Detected pattern categories follow established dark-pattern taxonomies.
"""

import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

# Attempt to load transformer-based classifier
try:
    from transformers import pipeline as hf_pipeline
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False
    logger.warning("transformers not installed — ML-based detection disabled")


# ── Dark Pattern Taxonomy ───────────────────────────────────

DARK_PATTERN_RULES = {
    "confirmshaming": {
        "description": "Guilt-tripping the user into opting in by framing the decline option negatively.",
        "patterns": [
            r"no\s*,?\s*i\s*(don'?t|do\s*not)\s*(want|like|need|care)",
            r"i('?ll)?\s*(prefer|rather)\s*(to\s*)?(stay|remain|keep)\s*(stupid|uninformed|ignorant|broke|poor)",
            r"no\s*thanks?\s*,?\s*i\s*(hate|don'?t\s*(like|want))\s*(saving|money|deals|discounts)",
            r"i('?m)?\s*(not\s*interested\s*in)\s*(saving|improving|growing)",
        ],
        "keywords": [
            "no thanks, i prefer", "i don't want to save",
            "no, i hate saving money", "i don't need",
            "i prefer to stay", "i'll pass on this",
        ],
    },
    "urgency": {
        "description": "Creating false urgency to pressure immediate action.",
        "patterns": [
            r"(only|just)\s*\d+\s*(left|remaining|available)",
            r"(hurry|rush|act\s*now|don'?t\s*miss|last\s*chance)",
            r"(offer|sale|deal)\s*(ends?|expires?|closing)\s*(soon|today|tonight|now|in\s*\d+)",
            r"(limited\s*time|while\s*supplies?\s*last|going\s*fast)",
            r"\d+\s*(people|users?|customers?)\s*(are\s*)?(viewing|looking|watching)\s*(this)?\s*(right\s*now|now)",
        ],
        "keywords": [
            "act now", "hurry", "limited time", "offer ends",
            "last chance", "don't miss out", "going fast",
            "only a few left", "selling out", "almost gone",
            "expires soon", "today only", "flash sale",
        ],
    },
    "scarcity": {
        "description": "Displaying fake or exaggerated scarcity to push purchases.",
        "patterns": [
            r"(only|just)\s*\d+\s*(left|remaining|in\s*stock)",
            r"(low|limited)\s*stock",
            r"(selling|going)\s*(out\s*)?fast",
            r"(high|huge)\s*demand",
            r"\d+\s*(people|others?)\s*(have\s*)?bought\s*this\s*(today|recently)",
        ],
        "keywords": [
            "limited stock", "selling fast", "high demand",
            "almost sold out", "few remaining", "popular item",
        ],
    },
    "misdirection": {
        "description": "Drawing user attention toward one thing to distract from another.",
        "patterns": [
            r"(free|no\s*cost)\s*(trial|sign\s*up|account).*\$?\d+",
            r"(you('?re)?\s*(pre-?selected|automatically\s*enrolled|opted\s*in))",
            r"(by\s*(continuing|clicking|proceeding)\s*(you\s*)?(agree|accept|consent))",
        ],
        "keywords": [
            "pre-selected", "automatically enrolled",
            "by continuing you agree", "free trial",
            "no obligation", "cancel anytime",
        ],
    },
    "social_proof": {
        "description": "Using fake or misleading social proof to influence decisions.",
        "patterns": [
            r"\d+\s*(people|users?|customers?|buyers?)\s*(bought|purchased|signed\s*up|viewing)",
            r"(trending|popular|best\s*seller|most\s*popular)",
            r"\d+\s*(people|viewers?)\s*(are\s*)?(looking\s*at\s*this|watching|browsing)",
        ],
        "keywords": [
            "trending now", "best seller", "most popular",
            "people are viewing", "recently purchased",
            "join thousands", "millions trust us",
        ],
    },
    "hidden_costs": {
        "description": "Concealing additional charges until late in the checkout flow.",
        "patterns": [
            r"(service|processing|handling|convenience)\s*fee",
            r"(additional|extra)\s*(charges?|fees?|costs?)\s*(may\s*)?(apply|added)",
            r"(plus|excluding)\s*(tax(es)?|shipping|delivery|handling)",
        ],
        "keywords": [
            "service fee", "processing fee", "additional charges",
            "excluding tax", "plus shipping", "fees may apply",
            "convenience fee", "handling fee",
        ],
    },
    "trick_question": {
        "description": "Using confusing language to trick users into making unintended choices.",
        "patterns": [
            r"(un)?check\s*(this\s*box\s*)?(to\s*(not|opt\s*out))",
            r"(don'?t\s*)?unsubscribe\s*(from)?",
            r"(deselect|uncheck)\s*(if\s*you\s*(don'?t|do\s*not))",
        ],
        "keywords": [
            "uncheck to opt out", "deselect if you don't want",
            "check to not receive", "unsubscribe from not receiving",
        ],
    },
    "forced_continuity": {
        "description": "Making it difficult to cancel a subscription or free trial.",
        "patterns": [
            r"(auto\s*-?\s*renew(s|al|ed)?)",
            r"(will\s*be\s*charged\s*after)\s*(free\s*)?trial",
            r"(cancel\s*(before|by)\s*\w+\s*to\s*avoid\s*charges?)",
        ],
        "keywords": [
            "auto-renew", "automatically charged",
            "cancel before", "will be charged after trial",
            "recurring billing", "continuous subscription",
        ],
    },
    "nagging": {
        "description": "Repeatedly asking the user to do something they've already declined.",
        "patterns": [
            r"(remind\s*me\s*later|maybe\s*later|ask\s*me\s*(again|later))",
            r"(not\s*now|skip\s*for\s*now|later)",
            r"(we('?ll)?\s*(remind|ask|check\s*back)\s*(you\s*)?(later|again|tomorrow|next\s*time))",
        ],
        "keywords": [
            "remind me later", "not now", "ask me later",
            "maybe next time", "we'll check back",
        ],
    },
}


class DarkPatternDetector:
    """
    Hybrid dark-pattern detector combining rules and ML inference.

    The detect() method runs both engines and merges results,
    deduplicating overlapping detections.
    """

    def __init__(self):
        self.classifier = None
        if HF_AVAILABLE:
            try:
                self.classifier = hf_pipeline(
                    "text-classification",
                    model="distilbert-base-uncased",
                    top_k=None,
                    truncation=True,
                )
                logger.info("DistilBERT classifier loaded for ML-based detection")
            except Exception as e:
                logger.warning(f"Could not load DistilBERT: {e}")

    def detect(self, text: str, html: str = "") -> List[Dict]:
        """
        Run all detection methods on the given text and HTML.

        Args:
            text: Extracted page text content.
            html: Raw HTML source (used for structural analysis).

        Returns:
            List of detected patterns, each as a dict with:
              type, description, confidence, evidence, method
        """
        results = []

        # Rule-based detection
        results.extend(self._rule_based_detect(text))

        # HTML structural detection
        if html:
            results.extend(self._structural_detect(html))

        # ML-based detection (on suspicious text segments)
        if self.classifier and text:
            results.extend(self._ml_detect(text))

        # Deduplicate by (type, evidence)
        seen = set()
        unique = []
        for r in results:
            key = (r["type"], r.get("evidence", "")[:100])
            if key not in seen:
                seen.add(key)
                unique.append(r)

        return unique

    def _rule_based_detect(self, text: str) -> List[Dict]:
        """Apply regex patterns and keyword matching against the text."""
        results = []
        text_lower = text.lower()

        for pattern_type, config in DARK_PATTERN_RULES.items():
            # Keyword detection
            for keyword in config["keywords"]:
                if keyword.lower() in text_lower:
                    # Extract surrounding context
                    idx = text_lower.find(keyword.lower())
                    start = max(0, idx - 40)
                    end = min(len(text), idx + len(keyword) + 40)
                    context = text[start:end].strip()

                    results.append({
                        "type": pattern_type,
                        "description": config["description"],
                        "confidence": 0.75,
                        "evidence": context,
                        "method": "rule-based",
                    })

            # Regex detection
            for pattern in config["patterns"]:
                matches = re.finditer(pattern, text_lower)
                for match in matches:
                    start = max(0, match.start() - 30)
                    end = min(len(text), match.end() + 30)
                    context = text[start:end].strip()

                    results.append({
                        "type": pattern_type,
                        "description": config["description"],
                        "confidence": 0.85,
                        "evidence": context,
                        "method": "rule-based",
                    })

        return results

    def _structural_detect(self, html: str) -> List[Dict]:
        """Detect dark patterns in HTML structure (hidden inputs, pre-checked boxes, etc.)."""
        from bs4 import BeautifulSoup

        results = []
        soup = BeautifulSoup(html, "html.parser")

        # Pre-checked checkboxes (potential opt-in dark patterns)
        for checkbox in soup.find_all("input", {"type": "checkbox", "checked": True}):
            label = ""
            parent = checkbox.parent
            if parent:
                label = parent.get_text(strip=True)[:100]
            results.append({
                "type": "misdirection",
                "description": "Pre-checked checkbox found — user may unknowingly agree.",
                "confidence": 0.70,
                "evidence": f"Pre-checked: {label}",
                "method": "structural",
            })

        # Hidden inputs with suspicious names
        suspicious_names = ["newsletter", "subscribe", "marketing", "optin", "consent"]
        for hidden in soup.find_all("input", {"type": "hidden"}):
            name = (hidden.get("name", "") or "").lower()
            value = (hidden.get("value", "") or "").lower()
            if any(s in name for s in suspicious_names) and value in ("1", "true", "yes"):
                results.append({
                    "type": "misdirection",
                    "description": "Hidden form input auto-enrolling user.",
                    "confidence": 0.80,
                    "evidence": f"Hidden input: name='{hidden.get('name')}' value='{hidden.get('value')}'",
                    "method": "structural",
                })

        # Countdown timers
        timer_indicators = ["countdown", "timer", "clock", "expire", "remaining-time"]
        for el in soup.find_all(True):
            classes = " ".join(el.get("class", [])).lower()
            el_id = (el.get("id") or "").lower()
            if any(t in classes or t in el_id for t in timer_indicators):
                results.append({
                    "type": "urgency",
                    "description": "Countdown timer element detected in page.",
                    "confidence": 0.80,
                    "evidence": f"Timer element: class='{classes}' id='{el_id}'",
                    "method": "structural",
                })

        return results

    def _ml_detect(self, text: str) -> List[Dict]:
        """
        Run ML-based classification on text segments.

        Splits text into sentence-sized chunks and classifies each
        for potential deceptive language patterns.
        """
        results = []

        # Split into manageable chunks
        sentences = [s.strip() for s in re.split(r"[.!?]+", text) if len(s.strip()) > 20]
        # Sample up to 50 sentences
        sample = sentences[:50]

        if not sample:
            return results

        try:
            predictions = self.classifier(sample, batch_size=8)

            for sentence, pred_list in zip(sample, predictions):
                # DistilBERT base outputs POSITIVE/NEGATIVE labels
                # High NEGATIVE confidence on commercial text may indicate manipulation
                for pred in pred_list:
                    if pred["label"] == "NEGATIVE" and pred["score"] > 0.85:
                        # Cross-check with dark pattern keywords
                        sentence_lower = sentence.lower()
                        for pattern_type, config in DARK_PATTERN_RULES.items():
                            if any(kw in sentence_lower for kw in config["keywords"]):
                                results.append({
                                    "type": pattern_type,
                                    "description": f"ML-detected: {config['description']}",
                                    "confidence": round(pred["score"], 3),
                                    "evidence": sentence[:200],
                                    "method": "ml-classifier",
                                })
                                break

        except Exception as e:
            logger.warning(f"ML detection failed: {e}")

        return results
