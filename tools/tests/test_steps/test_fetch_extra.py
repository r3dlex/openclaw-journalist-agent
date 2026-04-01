"""Additional tests for the fetch steps (FetchFeedsStep, _parse_single_feed)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pipeline_runner.config import FeedConfig, PipelineSettings
from pipeline_runner.steps.fetch import (
    FeedEntry,
    FetchFeedsStep,
    _parse_single_feed,
)


class TestFetchFeedsStep:
    def test_should_always_run(self) -> None:
        step = FetchFeedsStep()
        assert step.should_run({}) is True
        assert step.should_run({"anything": "here"}) is True

    @patch("pipeline_runner.steps.fetch.requests.get")
    def test_fetches_all_feeds_concurrently(
        self, mock_get: MagicMock, settings: PipelineSettings, feed_config: FeedConfig
    ) -> None:
        rss_xml = """<?xml version="1.0"?>
        <rss version="2.0">
          <channel>
            <item>
              <title>Test Story</title>
              <link>https://example.com/story</link>
              <description>A story.</description>
              <pubDate>Tue, 01 Apr 2026 10:00:00 GMT</pubDate>
            </item>
          </channel>
        </rss>"""
        mock_response = MagicMock()
        mock_response.content = rss_xml.encode()
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        step = FetchFeedsStep()
        ctx = {"settings": settings, "feeds_config": feed_config}
        result = step.execute(ctx)

        assert "entries" in result
        assert len(result["entries"]) >= 1
        assert result["entries"][0].title == "Test Story"

    @patch("pipeline_runner.steps.fetch.requests.get")
    def test_continues_on_single_feed_failure(
        self, mock_get: MagicMock, settings: PipelineSettings, feed_config: FeedConfig
    ) -> None:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("connection error")
        mock_get.return_value = mock_response

        step = FetchFeedsStep()
        ctx = {"settings": settings, "feeds_config": feed_config}
        # Should not raise even when feed fails
        result = step.execute(ctx)
        assert "entries" in result

    @patch("pipeline_runner.steps.fetch.requests.get")
    def test_uses_default_settings_when_not_in_context(self, mock_get: MagicMock) -> None:
        rss_xml = """<?xml version="1.0"?>
        <rss version="2.0"><channel></channel></rss>"""
        mock_response = MagicMock()
        mock_response.content = rss_xml.encode()
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        step = FetchFeedsStep()
        # No settings in context — should use defaults
        # We patch FeedConfig to avoid actual file reads
        with patch(
            "pipeline_runner.steps.fetch.FeedConfig"
        ) as mock_feed_config_cls:
            mock_fc = MagicMock()
            mock_fc.max_concurrent_fetchers = 2
            mock_fc.max_entries_per_feed = 3
            mock_fc.categories = {"TEST": ["https://example.com/feed.xml"]}
            mock_feed_config_cls.return_value = mock_fc
            result = step.execute({})

        assert "entries" in result


class TestParseSingleFeed:
    @patch("pipeline_runner.steps.fetch.requests.get")
    def test_parses_entries_correctly(self, mock_get: MagicMock) -> None:
        rss_xml = """<?xml version="1.0"?>
        <rss version="2.0">
          <channel>
            <item>
              <title>Story 1</title>
              <link>https://example.com/1</link>
              <description>Summary 1</description>
              <pubDate>Tue, 01 Apr 2026 10:00:00 GMT</pubDate>
            </item>
            <item>
              <title>Story 2</title>
              <link>https://example.com/2</link>
              <description>Summary 2</description>
              <pubDate>Tue, 01 Apr 2026 11:00:00 GMT</pubDate>
            </item>
          </channel>
        </rss>"""
        mock_response = MagicMock()
        mock_response.content = rss_xml.encode()
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        entries = _parse_single_feed("TEST", "https://example.com/feed.xml", 10, 15)

        assert len(entries) == 2
        assert entries[0].title == "Story 1"
        assert entries[0].category == "TEST"
        assert entries[0].source_feed == "https://example.com/feed.xml"

    @patch("pipeline_runner.steps.fetch.requests.get")
    def test_respects_max_entries(self, mock_get: MagicMock) -> None:
        items = "\n".join(
            f"<item><title>Story {i}</title><link>http://ex.com/{i}</link></item>"
            for i in range(10)
        )
        rss_xml = f"""<?xml version="1.0"?>
        <rss version="2.0"><channel>{items}</channel></rss>"""
        mock_response = MagicMock()
        mock_response.content = rss_xml.encode()
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        entries = _parse_single_feed("TEST", "https://example.com/feed.xml", 3, 15)
        assert len(entries) == 3

    @patch("pipeline_runner.steps.fetch.requests.get")
    def test_summary_truncated_to_500(self, mock_get: MagicMock) -> None:
        long_summary = "X" * 1000
        rss_xml = f"""<?xml version="1.0"?>
        <rss version="2.0">
          <channel>
            <item>
              <title>Story</title>
              <link>http://ex.com</link>
              <description>{long_summary}</description>
            </item>
          </channel>
        </rss>"""
        mock_response = MagicMock()
        mock_response.content = rss_xml.encode()
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        entries = _parse_single_feed("TEST", "https://example.com/feed.xml", 10, 15)
        assert len(entries[0].summary) == 500
