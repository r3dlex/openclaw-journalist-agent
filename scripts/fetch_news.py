#!/usr/bin/env python3
"""RSS news fetcher with importance scoring.

Reads feed configuration from config/feeds.json (or $FEEDS_FILE),
scores stories by relevance, and outputs a structured briefing.
"""
import datetime
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import feedparser
import requests
from bs4 import BeautifulSoup

# --- Configuration ---

FEEDS_FILE = os.environ.get("FEEDS_FILE", "config/feeds.json")
USER_AGENT = "Mozilla/5.0 (compatible; JournalistAgent/1.0)"


def load_config():
    """Load feed configuration from JSON file."""
    config_path = Path(FEEDS_FILE)
    if not config_path.exists():
        print(f"Error: feeds config not found at {config_path}", file=sys.stderr)
        sys.exit(1)
    with open(config_path) as f:
        return json.load(f)


def score_importance(title, summary, keywords):
    """Score importance of a story (0-10) based on keyword matches."""
    text = f"{title} {summary}".lower()
    score = sum(1 for kw in keywords if kw in text)

    # Boost for high-urgency signals
    if any(w in text for w in ("breaking", "exclusive")):
        score += 3
    if any(w in text for w in ("urgent", "war", "crisis")):
        score += 2
    if any(w in text for w in ("russia", "ukraine", "trump", "eu ", "european", "election")):
        score += 1

    return min(score, 10)


def parse_feed(category, url, keywords, max_entries):
    """Parse a single feed and return entries with importance scores."""
    try:
        feed = feedparser.parse(url)
        entries = []
        for entry in feed.entries[:max_entries]:
            title = entry.title.replace("\n", " ").strip()
            summary = getattr(entry, "summary", "")[:200]
            link = entry.link
            importance = score_importance(title, summary, keywords)
            entries.append({
                "category": category,
                "title": title,
                "summary": summary,
                "link": link,
                "importance": importance,
                "source": feed.feed.get("title", url[:40]),
            })
        return entries
    except Exception:
        return []


def fetch_article_details(url, max_chars):
    """Fetch and extract article content from a URL."""
    try:
        resp = requests.get(
            url, headers={"User-Agent": USER_AGENT}, timeout=15
        )
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "aside"]):
            tag.decompose()
        article = (
            soup.find("article")
            or soup.find("main")
            or soup.find("div", class_="content")
            or soup.body
        )
        if article:
            text = article.get_text(separator="\n", strip=True)
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            return "\n".join(lines[:50])[:max_chars]
        return "Could not extract content"
    except Exception as e:
        return f"Error: {e}"


def main():
    config = load_config()
    categories = config["categories"]
    keywords = config.get("important_keywords", [])
    settings = config.get("settings", {})
    max_entries = settings.get("max_entries_per_feed", 5)
    max_workers = settings.get("max_concurrent_fetchers", 10)
    importance_threshold = settings.get("importance_threshold_for_detail", 3)
    article_max_chars = settings.get("article_max_chars", 2000)

    today = datetime.date.today().strftime("%B %d, %Y")
    print(f"NEWS BRIEFING -- {today}")
    print("=" * 60)

    # Fetch all feeds concurrently
    all_news = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for category, urls in categories.items():
            for url in urls:
                futures.append(
                    executor.submit(parse_feed, category, url, keywords, max_entries)
                )
        for future in futures:
            all_news.extend(future.result())

    all_news.sort(key=lambda x: x["importance"], reverse=True)

    # Top stories
    ai_cats = {"AI & MODELS", "TECH & DEV", "LINUX & OPEN SOURCE"}
    breaking_cats = {"BREAKING / HIGH PRIORITY", "GLOBAL & ECON"}

    print("\n## AI & TECH TOP STORIES")
    print("-" * 40)
    for item in [n for n in all_news if n["category"] in ai_cats][:5]:
        print(f"[{item['importance']}] {item['title'][:80]}")
        print(f"  Source: {item['source']}")
        print()

    print("\n## BREAKING & WORLD NEWS")
    print("-" * 40)
    for item in [n for n in all_news if n["category"] in breaking_cats][:5]:
        print(f"[{item['importance']}] {item['title'][:80]}")
        print(f"  Source: {item['source']}")
        print()

    # All stories by category
    print("\n## ALL STORIES BY CATEGORY")
    print("-" * 40)
    for category in categories:
        cat_items = [n for n in all_news if n["category"] == category]
        if cat_items:
            print(f"\n### {category}")
            for item in cat_items[:5]:
                flag = " **" if item["importance"] >= importance_threshold else ""
                print(f"  [{item['importance']}]{flag} {item['title'][:70]}")
                if item["importance"] >= 5:
                    print(f"      {item['link']}")

    # Stories worth fetching in detail
    important = [n for n in all_news if n["importance"] >= importance_threshold]
    print("\n" + "=" * 60)
    print(f"## STORIES FOR DETAILED FETCH (importance >= {importance_threshold})")
    print("-" * 40)
    for item in important:
        print(f"TITLE: {item['title'][:80]}")
        print(f"URL: {item['link']}")
        print(f"SUMMARY: {item['summary'][:150]}...")
        print()

    print(f"\nTotal stories: {len(all_news)}")
    print(f"High importance ({importance_threshold}+): {len(important)}")


if __name__ == "__main__":
    main()
