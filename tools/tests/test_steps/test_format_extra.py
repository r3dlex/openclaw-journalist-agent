"""Additional tests for format steps (FormatWeatherStep gaps)."""

from __future__ import annotations

from typing import Any

import pytest

from pipeline_runner.steps.format import FormatWeatherStep


class TestFormatWeatherStep:
    def test_should_run_with_weather_data(self) -> None:
        step = FormatWeatherStep()
        assert step.should_run({"weather_data": {}}) is True

    def test_should_not_run_without_weather_data(self) -> None:
        step = FormatWeatherStep()
        assert step.should_run({}) is False

    def _make_weather_data(self) -> dict[str, Any]:
        return {
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
                    ]
                }
            ],
        }

    def test_formats_basic_weather(self) -> None:
        step = FormatWeatherStep()
        data = self._make_weather_data()
        ctx: dict[str, Any] = {"weather_data": data, "time_slot": "6am"}
        result = step.execute(ctx)

        briefing = result["weather_briefing"]
        assert "Stuttgart" in briefing
        assert "15C" in briefing
        assert "Partly cloudy" in briefing

    def test_uses_data_key_when_wrapped(self) -> None:
        step = FormatWeatherStep()
        wrapped = {"data": self._make_weather_data()}
        ctx: dict[str, Any] = {"weather_data": wrapped, "time_slot": "6am"}
        result = step.execute(ctx)
        assert "Stuttgart" in result["weather_briefing"]

    def test_uses_fallback_area_when_no_nearest_area(self) -> None:
        step = FormatWeatherStep()
        data: dict[str, Any] = {
            "current_condition": [
                {
                    "temp_C": "20",
                    "FeelsLikeC": "18",
                    "humidity": "40",
                    "weatherDesc": [{"value": "Sunny"}],
                }
            ],
            "nearest_area": [],
            "weather": [],
        }
        ctx: dict[str, Any] = {"weather_data": data, "time_slot": "12pm"}
        result = step.execute(ctx)
        briefing = result["weather_briefing"]
        # Fallback area is "Stuttgart"
        assert "Stuttgart" in briefing

    def test_includes_hourly_table(self) -> None:
        step = FormatWeatherStep()
        data = self._make_weather_data()
        ctx: dict[str, Any] = {"weather_data": data, "time_slot": "6am"}
        result = step.execute(ctx)
        briefing = result["weather_briefing"]
        assert "| Time |" in briefing
        assert "06:00" in briefing

    def test_default_time_slot_is_6am(self) -> None:
        step = FormatWeatherStep()
        data = self._make_weather_data()
        # No time_slot in context
        ctx: dict[str, Any] = {"weather_data": data}
        result = step.execute(ctx)
        assert "6am" in result["weather_briefing"]

    def test_handles_two_days_of_hourly_data(self) -> None:
        step = FormatWeatherStep()
        hourly = [
            {
                "time": "600",
                "tempC": "12",
                "FeelsLikeC": "10",
                "weatherDesc": [{"value": "Clear"}],
                "chanceofrain": "5",
            }
        ]
        data: dict[str, Any] = {
            "current_condition": [
                {
                    "temp_C": "15",
                    "FeelsLikeC": "13",
                    "humidity": "65",
                    "weatherDesc": [{"value": "Cloudy"}],
                }
            ],
            "nearest_area": [{"areaName": [{"value": "Berlin"}]}],
            "weather": [{"hourly": hourly}, {"hourly": hourly}],  # 2 days
        }
        ctx: dict[str, Any] = {"weather_data": data, "time_slot": "8pm"}
        result = step.execute(ctx)
        # Should not raise and should produce briefing
        assert "weather_briefing" in result
