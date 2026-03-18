"""Fetch steps — RSS feed aggregation and URL content retrieval.

Implements Tier 1 (RSS/HTTP) of the three-tier research pipeline.
See ARCH-001 for the tiered research decision.
"""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any

import feedparser
import requests

from pipeline_runner.config import FeedConfig, PipelineSettings

logger = logging.getLogger(__name__)

USER_AGENT = "JournalistAgent/0.1 (OpenClaw; +https://github.com/your-org/openclaw-journalist-agent)"


@dataclass
class FeedEntry:
    """A single entry from an RSS feed."""

    title: str
    link: str
    summary: str
    published: str
    category: str
    source_feed: str


class FetchFeedsStep:
    """Fetch and parse all configured RSS feeds concurrently.

    Context in:  feeds_config (FeedConfig)
    Context out: entries (list[FeedEntry])
    """

    name = "fetch_feeds"

    def should_run(self, context: dict[str, Any]) -> bool:
        return True

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        settings: PipelineSettings = context.get("settings", PipelineSettings())
        feed_config: FeedConfig = context.get(
            "feeds_config", FeedConfig(settings.feeds_file)
        )

        entries: list[FeedEntry] = []
        max_workers = feed_config.max_concurrent_fetchers
        max_per_feed = feed_config.max_entries_per_feed
        timeout = settings.request_timeout

        all_feeds: list[tuple[str, str]] = []
        for category, urls in feed_config.categories.items():
            for url in urls:
                all_feeds.append((category, url))

        logger.info("Fetching %d feeds with %d workers", len(all_feeds), max_workers)

        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = {
                pool.submit(_parse_single_feed, cat, url, max_per_feed, timeout): (cat, url)
                for cat, url in all_feeds
            }
            for future in as_completed(futures):
                cat, url = futures[future]
                try:
                    result = future.result()
                    entries.extend(result)
                except Exception as exc:
                    logger.warning("Feed %s failed: %s", url, exc)

        logger.info("Fetched %d entries from %d feeds", len(entries), len(all_feeds))
        context["entries"] = entries
        context["feeds_config"] = feed_config
        return context


def _parse_single_feed(
    category: str, url: str, max_entries: int, timeout: int
) -> list[FeedEntry]:
    """Parse a single RSS feed URL."""
    response = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    feed = feedparser.parse(response.content)
    entries = []
    for entry in feed.entries[:max_entries]:
        entries.append(
            FeedEntry(
                title=entry.get("title", "Untitled"),
                link=entry.get("link", ""),
                summary=entry.get("summary", "")[:500],
                published=entry.get("published", ""),
                category=category,
                source_feed=url,
            )
        )
    return entries


class FetchUrlStep:
    """Fetch content from a single URL (Tier 1 HTTP fetch).

    Context in:  url (str)
    Context out: raw_html (str), fetch_tier (int)
    """

    name = "fetch_url"

    def should_run(self, context: dict[str, Any]) -> bool:
        return "url" in context

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        settings: PipelineSettings = context.get("settings", PipelineSettings())
        url: str = context["url"]

        logger.info("Fetching URL: %s", url)
        response = requests.get(
            url,
            timeout=settings.request_timeout,
            headers={"User-Agent": USER_AGENT},
        )
        response.raise_for_status()

        context["raw_html"] = response.text
        context["fetch_tier"] = 1
        context["fetch_status"] = response.status_code
        return context
