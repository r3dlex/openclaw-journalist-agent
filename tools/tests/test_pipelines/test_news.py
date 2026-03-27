"""Tests for the news briefing pipeline."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pipeline_runner.config import FeedConfig, PipelineSettings
from pipeline_runner.pipelines.news import build_news_pipeline


class TestNewsPipeline:
    def test_pipeline_has_six_steps(self) -> None:
        pipeline = build_news_pipeline()
        assert len(pipeline._steps) == 6

    def test_pipeline_step_names(self) -> None:
        pipeline = build_news_pipeline()
        names = [s.name for s in pipeline._steps]
        assert names == [
            "fetch_feeds",
            "score_importance",
            "format_briefing",
            "librarian_handoff",
            "iamq_announce",
            "telegram_notify",
        ]

    @patch("pipeline_runner.steps.fetch.requests.get")
    def test_end_to_end_with_mock_feeds(
        self, mock_get: MagicMock, settings: PipelineSettings, feed_config: FeedConfig
    ) -> None:
        """Integration test: full pipeline with mocked HTTP."""
        # Mock RSS response
        rss_xml = """<?xml version="1.0"?>
        <rss version="2.0">
          <channel>
            <item>
              <title>Breaking: AI Test Story</title>
              <link>https://example.com/story</link>
              <description>A test story about breaking AI news.</description>
              <pubDate>Tue, 18 Mar 2026 10:00:00 GMT</pubDate>
            </item>
          </channel>
        </rss>"""
        mock_response = MagicMock()
        mock_response.content = rss_xml.encode()
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        pipeline = build_news_pipeline(settings)
        result = pipeline.run(
            {
                "settings": settings,
                "feeds_config": feed_config,
                "pipeline_name": "news_briefing",
            }
        )

        assert result.success
        assert "briefing" in result.context
        assert "Breaking: AI Test Story" in result.context["briefing"]
