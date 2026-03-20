"""
Visual dark pattern detection using OpenCV.

Analyzes webpage screenshots for visual deceptive design elements
including countdown timers, aggressive banners, misleading button
patterns, and color-based urgency indicators.
"""

import os
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    logger.warning("OpenCV not installed — visual analysis disabled")


class ScreenshotAnalyzer:
    """
    Analyzes webpage screenshots for visual dark patterns.

    Uses OpenCV for image processing to detect:
      - Countdown timer elements (digit-heavy regions with clock-like layout)
      - Aggressive/urgent color banners (large red/orange regions)
      - Misleading button sizing and placement patterns
      - Modal overlays and popup-like structures
    """

    def __init__(self, task_id: str = ""):
        self.task_id = task_id

    def analyze(self, screenshot_path: str, page_url: str = "") -> List[Dict]:
        """
        Run all visual detection methods on a screenshot.

        Args:
            screenshot_path: File path to the PNG screenshot.
            page_url: URL of the page (for logging).

        Returns:
            List of detected visual dark patterns.
        """
        if not CV2_AVAILABLE:
            return []

        if not os.path.exists(screenshot_path):
            logger.warning(f"Screenshot not found: {screenshot_path}")
            return []

        try:
            image = cv2.imread(screenshot_path)
            if image is None:
                return []

            results = []
            results.extend(self._detect_urgency_colors(image))
            results.extend(self._detect_modal_overlay(image))
            results.extend(self._detect_countdown_timer(image))
            results.extend(self._detect_button_asymmetry(image))

            return results

        except Exception as e:
            logger.error(f"Visual analysis failed for {screenshot_path}: {e}")
            return []

    def _detect_urgency_colors(self, image: np.ndarray) -> List[Dict]:
        """
        Detect large regions of red/orange urgency colors.

        E-commerce dark patterns often use red banners, countdown backgrounds,
        or orange "limited time" bars to create false urgency.
        """
        results = []
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        h, w = image.shape[:2]
        total_pixels = h * w

        # Red range (two ranges in HSV since red wraps around 0/180)
        red_lower1 = np.array([0, 120, 100])
        red_upper1 = np.array([10, 255, 255])
        red_lower2 = np.array([170, 120, 100])
        red_upper2 = np.array([180, 255, 255])

        mask_red1 = cv2.inRange(hsv, red_lower1, red_upper1)
        mask_red2 = cv2.inRange(hsv, red_lower2, red_upper2)
        mask_red = cv2.bitwise_or(mask_red1, mask_red2)

        red_ratio = cv2.countNonZero(mask_red) / total_pixels

        if red_ratio > 0.05:  # More than 5% of screen is red
            results.append({
                "type": "urgency",
                "description": f"Aggressive red color usage detected ({red_ratio:.1%} of viewport).",
                "confidence": min(0.9, 0.5 + red_ratio * 5),
            })

        # Orange range
        orange_lower = np.array([10, 120, 100])
        orange_upper = np.array([25, 255, 255])
        mask_orange = cv2.inRange(hsv, orange_lower, orange_upper)
        orange_ratio = cv2.countNonZero(mask_orange) / total_pixels

        if orange_ratio > 0.05:
            results.append({
                "type": "urgency",
                "description": f"Prominent orange/warning color detected ({orange_ratio:.1%} of viewport).",
                "confidence": min(0.85, 0.4 + orange_ratio * 4),
            })

        return results

    def _detect_modal_overlay(self, image: np.ndarray) -> List[Dict]:
        """
        Detect dark overlay layers typical of modal popups.

        Many dark patterns use modal dialogs with dark semi-transparent
        backgrounds to force user attention.
        """
        results = []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        # Check for large dark semi-transparent regions
        dark_mask = cv2.inRange(gray, 0, 80)
        dark_ratio = cv2.countNonZero(dark_mask) / (h * w)

        if dark_ratio > 0.30:
            # Large dark overlay — likely a modal or popup
            # Check for a lighter rectangle in the center (the modal itself)
            center_region = gray[h // 4 : 3 * h // 4, w // 4 : 3 * w // 4]
            center_mean = np.mean(center_region)

            if center_mean > 100:  # Center is brighter than surroundings
                results.append({
                    "type": "nagging",
                    "description": "Modal overlay popup detected — may be blocking content to force action.",
                    "confidence": 0.70,
                })

        return results

    def _detect_countdown_timer(self, image: np.ndarray) -> List[Dict]:
        """
        Detect potential countdown timer elements using contour analysis.

        Looks for small, digit-sized rectangular contours arranged
        horizontally, which is characteristic of countdown displays.
        """
        results = []
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        # Focus on top portion where timers usually appear
        top_region = gray[0 : h // 3, :]

        # Edge detection
        edges = cv2.Canny(top_region, 50, 150)

        # Find contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Look for digit-like rectangular contours arranged in a row
        digit_rects = []
        for c in contours:
            x, y, cw, ch = cv2.boundingRect(c)
            aspect_ratio = ch / max(cw, 1)
            # Digit-like proportions: taller than wide, small-to-medium size
            if 1.2 < aspect_ratio < 3.0 and 15 < ch < 80 and 8 < cw < 50:
                digit_rects.append((x, y, cw, ch))

        # Check if multiple digit-like shapes are horizontally aligned
        if len(digit_rects) >= 4:
            digit_rects.sort(key=lambda r: r[0])
            # Check for horizontal alignment
            y_values = [r[1] for r in digit_rects[:8]]
            y_spread = max(y_values) - min(y_values)

            if y_spread < 20:  # Roughly aligned vertically
                results.append({
                    "type": "urgency",
                    "description": "Possible countdown timer detected in page header.",
                    "confidence": 0.65,
                })

        return results

    def _detect_button_asymmetry(self, image: np.ndarray) -> List[Dict]:
        """
        Detect asymmetric button sizing that may indicate misdirection.

        Dark patterns often make the "accept" or "subscribe" button
        much larger/more prominent than the "decline" button.
        """
        results = []
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

        # Detect bright, saturated button-like regions
        bright_mask = cv2.inRange(hsv, np.array([0, 80, 180]), np.array([180, 255, 255]))

        # Morphological operations to clean up
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        bright_mask = cv2.morphologyEx(bright_mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(bright_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        button_candidates = []
        for c in contours:
            x, y, cw, ch = cv2.boundingRect(c)
            area = cw * ch
            aspect = cw / max(ch, 1)
            # Button-like: wider than tall, moderate size
            if 1.5 < aspect < 8.0 and 500 < area < 50000 and ch > 20:
                button_candidates.append({"x": x, "y": y, "w": cw, "h": ch, "area": area})

        # Check for pairs of nearby buttons with very different sizes
        for i, b1 in enumerate(button_candidates):
            for b2 in button_candidates[i + 1:]:
                y_diff = abs(b1["y"] - b2["y"])
                if y_diff < 60:  # Vertically close
                    size_ratio = max(b1["area"], b2["area"]) / max(min(b1["area"], b2["area"]), 1)
                    if size_ratio > 2.5:  # One button is 2.5x+ larger
                        results.append({
                            "type": "misdirection",
                            "description": f"Asymmetric button sizes detected (ratio: {size_ratio:.1f}x) — may hide the decline option.",
                            "confidence": min(0.80, 0.5 + size_ratio * 0.1),
                        })
                        return results  # One detection is enough

        return results
