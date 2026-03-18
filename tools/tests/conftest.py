"""Shared test fixtures for pipeline_runner tests."""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline_runner.config import FeedConfig, PipelineSettings
from pipeline_runner.steps.fetch import FeedEntry


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Path:
    """Create a temporary data directory with log and reports subdirs."""
    log_dir = tmp_path / "log"
    log_dir.mkdir()
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    return tmp_path


@pytest.fixture
def feeds_json(tmp_path: Path) -> Path:
    """Create a minimal feeds.json for testing."""
    import json

    config = {
        "categories": {
            "TEST": ["https://example.com/feed.xml"],
        },
        "important_keywords": ["breaking", "ai", "test"],
        "settings": {
            "max_entries_per_feed": 3,
            "importance_threshold_for_detail": 2,
            "max_concurrent_fetchers": 2,
            "article_max_chars": 1000,
            "request_timeout_seconds": 5,
        },
    }
    path = tmp_path / "feeds.json"
    path.write_text(json.dumps(config))
    return path


@pytest.fixture
def settings(tmp_data_dir: Path, feeds_json: Path) -> PipelineSettings:
    """Create PipelineSettings pointing to temp directories."""
    return PipelineSettings(
        JOURNALIST_DATA_DIR=str(tmp_data_dir),
        FEEDS_FILE=str(feeds_json),
        LIBRARIAN_AGENT_WORKSPACE="",
        WEATHER_LOCATION="Stuttgart",
        WEATHER_COUNTRY="DE",
    )


@pytest.fixture
def feed_config(feeds_json: Path) -> FeedConfig:
    """Create a FeedConfig from the test feeds.json."""
    return FeedConfig(feeds_json)


@pytest.fixture
def sample_entries() -> list[FeedEntry]:
    """Create sample FeedEntry objects for testing."""
    return [
        FeedEntry(
            title="Breaking: AI Model Released",
            link="https://example.com/1",
            summary="A new AI model was released today with breaking benchmarks.",
            published="2026-03-18",
            category="AI & MODELS",
            source_feed="https://example.com/feed.xml",
        ),
        FeedEntry(
            title="Local Weather Update",
            link="https://example.com/2",
            summary="Weather conditions are normal today.",
            published="2026-03-18",
            category="LOCAL",
            source_feed="https://example.com/feed.xml",
        ),
        FeedEntry(
            title="Urgent: War Escalation in Region",
            link="https://example.com/3",
            summary="Urgent reports of war escalation and crisis in the region.",
            published="2026-03-18",
            category="BREAKING / HIGH PRIORITY",
            source_feed="https://example.com/feed.xml",
        ),
    ]
