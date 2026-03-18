"""Tests for the fetch steps."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pipeline_runner.config import PipelineSettings
from pipeline_runner.steps.fetch import FetchUrlStep


class TestFetchUrlStep:
    def test_should_run_with_url(self) -> None:
        step = FetchUrlStep()
        assert step.should_run({"url": "https://example.com"})

    def test_should_not_run_without_url(self) -> None:
        step = FetchUrlStep()
        assert not step.should_run({})

    @patch("pipeline_runner.steps.fetch.requests.get")
    def test_fetches_url(self, mock_get: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.text = "<html><body>Test</body></html>"
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        step = FetchUrlStep()
        result = step.execute(
            {
                "url": "https://example.com",
                "settings": PipelineSettings(
                    JOURNALIST_DATA_DIR=".",
                    FEEDS_FILE="config/feeds.json",
                ),
            }
        )

        assert result["raw_html"] == "<html><body>Test</body></html>"
        assert result["fetch_tier"] == 1
        assert result["fetch_status"] == 200

    @patch("pipeline_runner.steps.fetch.requests.get")
    def test_raises_on_http_error(self, mock_get: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = Exception("404")
        mock_get.return_value = mock_response

        step = FetchUrlStep()
        with pytest.raises(Exception, match="404"):
            step.execute(
                {
                    "url": "https://example.com/notfound",
                    "settings": PipelineSettings(
                        JOURNALIST_DATA_DIR=".",
                        FEEDS_FILE="config/feeds.json",
                    ),
                }
            )
