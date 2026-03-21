"""Tests for the weather briefing pipeline."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pipeline_runner.config import PipelineSettings
from pipeline_runner.pipelines.weather import build_weather_pipeline


class TestWeatherPipeline:
    def test_pipeline_has_five_steps(self) -> None:
        pipeline = build_weather_pipeline()
        assert len(pipeline._steps) == 5

    def test_pipeline_step_names(self) -> None:
        pipeline = build_weather_pipeline()
        names = [s.name for s in pipeline._steps]
        assert names == [
            "fetch_weather",
            "format_weather",
            "librarian_handoff",
            "telegram_notify",
            "iamq_announce",
        ]

    @patch("pipeline_runner.pipelines.weather.requests.get")
    def test_end_to_end_with_mock_api(
        self, mock_get: MagicMock, settings: PipelineSettings
    ) -> None:
        """Integration test: full weather pipeline with mocked API."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "current_condition": [
                {
                    "temp_C": "15",
                    "FeelsLikeC": "13",
                    "humidity": "65",
                    "weatherDesc": [{"value": "Partly cloudy"}],
                }
            ],
            "nearest_area": [{"areaName": [{"value": "Stuttgart"}]}],
            "weather": [
                {
                    "hourly": [
                        {
                            "time": "600",
                            "tempC": "12",
                            "FeelsLikeC": "10",
                            "weatherDesc": [{"value": "Clear"}],
                            "chanceofrain": "5",
                        },
                        {
                            "time": "900",
                            "tempC": "16",
                            "FeelsLikeC": "14",
                            "weatherDesc": [{"value": "Sunny"}],
                            "chanceofrain": "0",
                        },
                    ]
                }
            ],
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        pipeline = build_weather_pipeline(settings)
        result = pipeline.run(
            {
                "settings": settings,
                "time_slot": "6am",
                "pipeline_name": "weather_briefing",
            }
        )

        assert result.success
        briefing = result.context.get("weather_briefing", "")
        assert "Stuttgart" in briefing
        assert "15" in briefing  # current temp
