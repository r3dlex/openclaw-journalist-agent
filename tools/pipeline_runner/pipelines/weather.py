"""Weather briefing pipeline — fetch forecast, format, hand off.

Uses wttr.in API (free, no API key required).
See spec/CRON.md for the weather schedule.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from pipeline_runner.config import PipelineSettings
from pipeline_runner.runner import Pipeline
from pipeline_runner.steps.format import FormatWeatherStep
from pipeline_runner.steps.handoff import LibrarianHandoffStep

logger = logging.getLogger(__name__)


class FetchWeatherStep:
    """Fetch weather data from wttr.in API.

    Context in:  time_slot (str), settings (PipelineSettings)
    Context out: weather_data (dict)
    """

    name = "fetch_weather"

    def should_run(self, context: dict[str, Any]) -> bool:
        return True

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        settings: PipelineSettings = context.get("settings", PipelineSettings())
        location = settings.weather_location

        url = f"https://wttr.in/{location}?format=j1"
        logger.info("Fetching weather for %s", location)

        response = requests.get(url, timeout=settings.request_timeout)
        response.raise_for_status()

        context["weather_data"] = response.json()
        return context


def build_weather_pipeline(settings: PipelineSettings | None = None) -> Pipeline:
    """Build the weather briefing pipeline.

    Steps:
        1. fetch_weather — Get forecast from wttr.in
        2. format_weather — Produce readable Markdown
        3. librarian_handoff — Write to log and notify Librarian
    """
    pipeline = Pipeline("weather_briefing")
    pipeline.add_step(FetchWeatherStep())
    pipeline.add_step(FormatWeatherStep())
    pipeline.add_step(LibrarianHandoffStep())
    return pipeline


def run_weather_pipeline(time_slot: str = "6am", settings: PipelineSettings | None = None) -> str:
    """Convenience function: fetch and format weather for a time slot."""
    settings = settings or PipelineSettings()

    pipeline = build_weather_pipeline(settings)
    result = pipeline.run(
        {
            "settings": settings,
            "time_slot": time_slot,
            "pipeline_name": "weather_briefing",
        }
    )

    if result.success:
        briefing: str = result.context.get("weather_briefing", "No weather data.")
        return briefing
    else:
        return f"Weather pipeline failed:\n{result.summary()}"
