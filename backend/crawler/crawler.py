"""
Semantic web crawler using Selenium and BeautifulSoup.

Uses a headless Chrome browser to render JavaScript-heavy pages,
extracts text content and links, and captures screenshots.
Implements priority-queue-based focused crawling.
"""

import heapq
import hashlib
import os
import logging
from urllib.parse import urljoin, urlparse
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

from backend.crawler.link_extractor import LinkExtractor

logger = logging.getLogger(__name__)

SCREENSHOT_DIR = os.path.join(os.path.dirname(__file__), "..", "screenshots")
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


class SemanticCrawler:
    """
    Priority-based web crawler with real-browser rendering.

    Maintains a priority queue of URLs scored by semantic relevance
    and a visited set to avoid duplicates.
    """

    def __init__(self, max_pages: int = 20):
        self.max_pages = max_pages
        self.visited: set = set()
        self.queue: list = []  # heapq — min-heap, so we negate priorities
        self.counter = 0       # tie-breaker for equal priorities
        self.driver = self._init_driver()
        self.link_extractor = LinkExtractor()

    def _init_driver(self) -> webdriver.Chrome:
        """Initialize a headless Chrome WebDriver."""
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-notifications")
        options.add_argument(
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )

        try:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=options)
        except Exception:
            # Fallback: assume chromedriver is in PATH
            driver = webdriver.Chrome(options=options)

        driver.set_page_load_timeout(30)
        return driver

    def add_to_queue(self, url: str, priority: float = 0.5):
        """
        Add a URL to the crawl priority queue.

        Higher priority values are crawled first (heap uses negated values).
        """
        normalized = self._normalize_url(url)
        if normalized and normalized not in self.visited:
            self.counter += 1
            heapq.heappush(self.queue, (-priority, self.counter, normalized))

    def has_next(self) -> bool:
        """Check whether there are still URLs to crawl."""
        return len(self.queue) > 0

    def get_next(self) -> Optional[str]:
        """Pop the highest-priority URL that hasn't been visited yet."""
        while self.queue:
            _, _, url = heapq.heappop(self.queue)
            if url not in self.visited:
                return url
        return None

    def fetch_page(self, url: str) -> Optional[dict]:
        """
        Load a page in the browser, extract content, and capture a screenshot.

        Returns a dict with title, html, text, links, screenshot_path,
        or None if the page fails to load.
        """
        if url in self.visited:
            return None
        self.visited.add(url)

        try:
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            html = self.driver.page_source
            title = self.driver.title or ""

            # Parse and extract
            soup = BeautifulSoup(html, "html.parser")
            text = self._extract_main_content(soup)
            links = self.link_extractor.extract(soup, url)

            # Screenshot
            screenshot_path = self._capture_screenshot(url)

            return {
                "title": title,
                "html": html,
                "text": text,
                "links": links,
                "screenshot_path": screenshot_path,
            }

        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """
        Structure-aware content extraction.

        Removes navigation, ads, scripts, footers, and sidebars
        to isolate the main article or page content.
        """
        # Remove non-content elements
        for tag in soup.find_all(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            tag.decompose()

        # Remove elements by common class/id patterns
        noise_patterns = [
            "sidebar", "navigation", "nav-", "menu", "footer",
            "cookie", "popup", "modal", "advertisement", "ad-",
            "social-share", "comment",
        ]
        for element in soup.find_all(True):
            element_classes = " ".join(element.get("class", []))
            element_id = element.get("id", "")
            combined = f"{element_classes} {element_id}".lower()
            if any(pat in combined for pat in noise_patterns):
                element.decompose()

        # Prefer <main> or <article> if available
        main = soup.find("main") or soup.find("article")
        if main:
            text = main.get_text(separator=" ", strip=True)
        else:
            text = soup.get_text(separator=" ", strip=True)

        # Clean up whitespace
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        return " ".join(lines)

    def _capture_screenshot(self, url: str) -> Optional[str]:
        """Save a full-page screenshot and return the file path."""
        try:
            url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
            filename = f"screenshot_{url_hash}.png"
            filepath = os.path.join(SCREENSHOT_DIR, filename)
            self.driver.save_screenshot(filepath)
            return filepath
        except Exception as e:
            logger.warning(f"Screenshot failed for {url}: {e}")
            return None

    def _normalize_url(self, url: str) -> Optional[str]:
        """Normalize a URL by removing fragments and trailing slashes."""
        try:
            parsed = urlparse(url)
            if parsed.scheme not in ("http", "https"):
                return None
            normalized = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
            return normalized
        except Exception:
            return None

    def close(self):
        """Shut down the browser driver."""
        try:
            self.driver.quit()
        except Exception:
            pass
