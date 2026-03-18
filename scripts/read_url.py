#!/usr/bin/env python3
"""Article content extractor.

Fetches a URL and extracts the main article text using BeautifulSoup.
Falls back gracefully if content cannot be extracted.

Usage:
    python scripts/read_url.py <url> [max_chars]
"""
import os
import sys

import requests
from bs4 import BeautifulSoup

USER_AGENT = "Mozilla/5.0 (compatible; JournalistAgent/1.0)"
DEFAULT_MAX_CHARS = 3000


def read_article(url, max_chars=DEFAULT_MAX_CHARS):
    """Extract main content from a URL."""
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=int(os.environ.get("REQUEST_TIMEOUT", "15")),
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove non-content elements
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()

        # Find main content area
        article = (
            soup.find("article")
            or soup.find("main")
            or soup.find("div", class_="content")
            or soup.body
        )

        if not article:
            return "Error: could not find content on page"

        text = article.get_text(separator="\n", strip=True)
        return text[:max_chars]

    except requests.exceptions.Timeout:
        return "Error: request timed out"
    except requests.exceptions.HTTPError as e:
        return f"Error: HTTP {e.response.status_code}"
    except Exception as e:
        return f"Error: {e}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: read_url.py <url> [max_chars]", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    max_chars = int(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_MAX_CHARS
    print(read_article(url, max_chars))
