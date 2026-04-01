"""Tests for the pipeline convenience runner functions (run_*_pipeline)."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pipeline_runner.config import FeedConfig, PipelineSettings


class TestRunNewsPipeline:
    @patch("pipeline_runner.steps.fetch.requests.get")
    def test_returns_briefing_string_on_success(
        self, mock_get: MagicMock, settings: PipelineSettings, feed_config: FeedConfig
    ) -> None:
        from pipeline_runner.pipelines.news import run_news_pipeline

        rss_xml = """<?xml version="1.0"?>
        <rss version="2.0">
          <channel>
            <item>
              <title>Test Story</title>
              <link>https://example.com/story</link>
              <description>A test story.</description>
              <pubDate>Tue, 18 Mar 2026 10:00:00 GMT</pubDate>
            </item>
          </channel>
        </rss>"""
        mock_response = MagicMock()
        mock_response.content = rss_xml.encode()
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = run_news_pipeline(settings)

        assert isinstance(result, str)
        assert "Test Story" in result

    @patch("pipeline_runner.pipelines.news.build_news_pipeline")
    def test_returns_failure_message_on_pipeline_fail(
        self, mock_build: MagicMock, settings: PipelineSettings
    ) -> None:
        from pipeline_runner.pipelines.news import run_news_pipeline

        mock_pipeline = MagicMock()
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.summary.return_value = "Step fetch_feeds failed"
        mock_pipeline.run.return_value = mock_result
        mock_build.return_value = mock_pipeline

        result = run_news_pipeline(settings)

        assert "Pipeline failed" in result
        assert "fetch_feeds" in result


class TestRunArticlePipeline:
    @patch("pipeline_runner.steps.fetch.requests.get")
    def test_returns_content_string_on_success(
        self, mock_get: MagicMock, settings: PipelineSettings
    ) -> None:
        from pipeline_runner.pipelines.article import run_article_pipeline

        mock_response = MagicMock()
        mock_response.text = """
        <html>
        <head><title>Test Article</title></head>
        <body>
            <article>
                <p>This is the main article content for our test. It has enough text to pass
                the 100 char threshold for content selector detection in the step.</p>
            </article>
        </body>
        </html>
        """
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = run_article_pipeline("https://example.com/article", settings)

        assert isinstance(result, str)
        assert "Test Article" in result
        assert "Tier 1" in result

    @patch("pipeline_runner.pipelines.article.build_article_pipeline")
    def test_returns_failure_message_on_pipeline_fail(
        self, mock_build: MagicMock, settings: PipelineSettings
    ) -> None:
        from pipeline_runner.pipelines.article import run_article_pipeline

        mock_pipeline = MagicMock()
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.summary.return_value = "fetch_url failed"
        mock_pipeline.run.return_value = mock_result
        mock_build.return_value = mock_pipeline

        result = run_article_pipeline("https://example.com", settings)

        assert "Article extraction failed" in result

    @patch("pipeline_runner.steps.fetch.requests.get")
    def test_no_title_header_when_title_empty(
        self, mock_get: MagicMock, settings: PipelineSettings
    ) -> None:
        from pipeline_runner.pipelines.article import run_article_pipeline

        mock_response = MagicMock()
        # No <title> tag
        mock_response.text = "<html><body><p>Just content no title here at all and it is long.</p></body></html>"
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = run_article_pipeline("https://example.com", settings)

        assert isinstance(result, str)
        # Without a title tag, no # header prefix
        assert result.startswith("(Fetched via Tier")


class TestRunWeatherPipeline:
    @patch("pipeline_runner.pipelines.weather.requests.get")
    def test_returns_weather_string_on_success(
        self, mock_get: MagicMock, settings: PipelineSettings
    ) -> None:
        from pipeline_runner.pipelines.weather import run_weather_pipeline

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "current_condition": [
                {
                    "temp_C": "20",
                    "FeelsLikeC": "18",
                    "humidity": "50",
                    "weatherDesc": [{"value": "Sunny"}],
                }
            ],
            "nearest_area": [{"areaName": [{"value": "Stuttgart"}]}],
            "weather": [],
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        result = run_weather_pipeline("6am", settings)

        assert isinstance(result, str)
        assert "Stuttgart" in result or "Weather" in result

    @patch("pipeline_runner.pipelines.weather.build_weather_pipeline")
    def test_returns_failure_message_on_pipeline_fail(
        self, mock_build: MagicMock, settings: PipelineSettings
    ) -> None:
        from pipeline_runner.pipelines.weather import run_weather_pipeline

        mock_pipeline = MagicMock()
        mock_result = MagicMock()
        mock_result.success = False
        mock_result.summary.return_value = "fetch_weather failed"
        mock_pipeline.run.return_value = mock_result
        mock_build.return_value = mock_pipeline

        result = run_weather_pipeline("6am", settings)

        assert "Weather pipeline failed" in result

    @patch("pipeline_runner.pipelines.weather.requests.get")
    def test_uses_default_settings_when_none(self, mock_get: MagicMock) -> None:
        from pipeline_runner.pipelines.weather import run_weather_pipeline

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "current_condition": [
                {
                    "temp_C": "10",
                    "FeelsLikeC": "8",
                    "humidity": "70",
                    "weatherDesc": [{"value": "Cloudy"}],
                }
            ],
            "nearest_area": [],
            "weather": [],
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        # Should use default settings without crashing
        with patch("pipeline_runner.steps.handoff.LibrarianHandoffStep.execute") as mock_handoff:
            mock_handoff.side_effect = lambda ctx: ctx  # passthrough
            with patch("pipeline_runner.steps.notify.TelegramNotifyStep.should_run", return_value=False):
                with patch("pipeline_runner.steps.iamq.IAMQAnnounceStep.should_run", return_value=False):
                    result = run_weather_pipeline("12pm")

        assert isinstance(result, str)
