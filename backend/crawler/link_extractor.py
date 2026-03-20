"""
Link extraction module.

Extracts and filters internal links from parsed HTML,
avoiding navigation noise, external domains, and non-page resources.
"""

from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import List
import logging

logger = logging.getLogger(__name__)

# File extensions to skip
SKIP_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".ico",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".zip", ".rar", ".tar", ".gz", ".mp3", ".mp4", ".avi",
    ".css", ".js", ".json", ".xml", ".rss",
}

# URL path fragments to skip
SKIP_PATHS = {
    "/login", "/logout", "/signup", "/register", "/cart",
    "/checkout", "/admin", "/wp-admin", "/feed", "/rss",
    "#", "javascript:", "mailto:", "tel:",
}


class LinkExtractor:
    """
    Extracts clean, internal hyperlinks from a BeautifulSoup document.

    Filters out external links, binary resources, navigation noise,
    and enforces same-domain crawling.
    """

    def extract(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """
        Extract all valid internal links from the page.

        Args:
            soup: Parsed HTML document.
            base_url: The URL of the page being parsed (used to resolve relative links).

        Returns:
            Deduplicated list of absolute internal URLs.
        """
        base_domain = urlparse(base_url).netloc
        links = set()

        for anchor in soup.find_all("a", href=True):
            href = anchor["href"].strip()

            # Skip empty or javascript links
            if not href or any(href.lower().startswith(s) for s in ["javascript:", "mailto:", "tel:", "#"]):
                continue

            # Resolve relative URLs
            absolute = urljoin(base_url, href)

            # Parse and validate
            parsed = urlparse(absolute)
            if parsed.scheme not in ("http", "https"):
                continue

            # Same domain only
            if parsed.netloc != base_domain:
                continue

            # Skip binary / resource files
            path_lower = parsed.path.lower()
            if any(path_lower.endswith(ext) for ext in SKIP_EXTENSIONS):
                continue

            # Skip known non-content paths
            if any(skip in path_lower for skip in SKIP_PATHS):
                continue

            # Normalize: strip fragment, trailing slash
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")
            links.add(clean_url)

        # Don't return the base URL itself
        links.discard(base_url.rstrip("/"))

        return list(links)
