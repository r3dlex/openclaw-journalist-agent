"""Content extraction step — parse HTML into clean text.

Strips navigation, scripts, and boilerplate from raw HTML to produce
readable article content. Part of the Tier 1/2 pipeline.
See ARCH-001 for tier definitions.
"""

from __future__ import annotations

import logging
from typing import Any

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Tags to remove before extraction
REMOVE_TAGS = ["script", "style", "nav", "header", "footer", "aside", "iframe", "noscript"]

# CSS selectors to try for main content, in priority order
CONTENT_SELECTORS = [
    "article",
    "main",
    "[role='main']",
    ".post-content",
    ".article-content",
    ".entry-content",
    ".content",
    "#content",
    "body",
]


class ExtractContentStep:
    """Extract readable text from raw HTML.

    Context in:  raw_html (str)
    Context out: content (str), title (str)
    """

    name = "extract_content"

    def __init__(self, max_chars: int = 3000) -> None:
        self.max_chars = max_chars

    def should_run(self, context: dict[str, Any]) -> bool:
        return "raw_html" in context

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        html = context["raw_html"]
        max_chars = context.get("max_chars", self.max_chars)

        soup = BeautifulSoup(html, "html.parser")

        # Extract title
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else ""

        # Remove noise tags
        for tag_name in REMOVE_TAGS:
            for tag in soup.find_all(tag_name):
                tag.decompose()

        # Find main content container
        content_text = ""
        for selector in CONTENT_SELECTORS:
            element = soup.select_one(selector)
            if element:
                content_text = element.get_text(separator="\n", strip=True)
                if len(content_text) > 100:
                    break

        if not content_text:
            content_text = soup.get_text(separator="\n", strip=True)

        # Truncate to max chars
        if len(content_text) > max_chars:
            content_text = content_text[:max_chars] + "\n\n[Truncated]"

        context["content"] = content_text
        context["title"] = title
        logger.info("Extracted %d chars (title: %s)", len(content_text), title[:60])
        return context
