"""Formatting steps — transform pipeline data into output documents.

Produces structured Markdown briefings and weather reports.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from pipeline_runner.steps.score import ScoredEntry

logger = logging.getLogger(__name__)


class FormatBriefingStep:
    """Format scored entries into a structured Markdown briefing.

    Context in:  scored_entries (list[ScoredEntry])
    Context out: briefing (str), briefing_date (str)
    """

    name = "format_briefing"

    def __init__(self, max_per_category: int = 5) -> None:
        self.max_per_category = max_per_category

    def should_run(self, context: dict[str, Any]) -> bool:
        return "scored_entries" in context

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        scored: list[ScoredEntry] = context["scored_entries"]
        now = datetime.now(tz=UTC)
        date_str = now.strftime("%Y-%m-%d %H:%M UTC")

        lines: list[str] = []
        lines.append(f"# News Briefing — {date_str}")
        lines.append("")

        # Top stories (highest scores)
        top = scored[:10]
        if top:
            lines.append("## Top Stories")
            lines.append("")
            for i, s in enumerate(top, 1):
                score_bar = "+" * min(s.score, 10)
                lines.append(f"{i}. [{score_bar}] **{s.entry.title}**")
                if s.entry.summary:
                    lines.append(f"   {s.entry.summary[:200]}")
                lines.append(f"   Source: {s.entry.link}")
                lines.append("")

        # By category
        categories: dict[str, list[ScoredEntry]] = {}
        for s in scored:
            cat = s.entry.category
            categories.setdefault(cat, []).append(s)

        for cat, entries in categories.items():
            lines.append(f"## {cat}")
            lines.append("")
            for s in entries[: self.max_per_category]:
                lines.append(f"- **{s.entry.title}** (score: {s.score})")
                lines.append(f"  {s.entry.link}")
            lines.append("")

        # Summary
        lines.append("---")
        lines.append(
            f"Total: {len(scored)} stories from {len(categories)} categories. "
            f"Generated: {date_str}"
        )

        briefing = "\n".join(lines)
        context["briefing"] = briefing
        context["briefing_date"] = now.isoformat()
        logger.info("Formatted briefing: %d lines, %d chars", len(lines), len(briefing))
        return context


class FormatWeatherStep:
    """Format weather API response into a readable briefing.

    Context in:  weather_data (dict), time_slot (str)
    Context out: weather_briefing (str)
    """

    name = "format_weather"

    def should_run(self, context: dict[str, Any]) -> bool:
        return "weather_data" in context

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        data = context["weather_data"]
        # API wraps response in 'data' key
        if "data" in data:
            data = data["data"]
        time_slot = context.get("time_slot", "6am")

        current = data.get("current_condition", [{}])[0]
        nearest = data.get("nearest_area") or []
        if nearest:
            location = nearest[0]
            area = location.get("areaName", [{}])[0].get("value", "Unknown")
        else:
            # Fallback: use request info or settings
            area = "Stuttgart"  # fallback
        temp_c = current.get("temp_C", "?")
        feels_like = current.get("FeelsLikeC", "?")
        humidity = current.get("humidity", "?")
        desc = current.get("weatherDesc", [{}])[0].get("value", "")

        lines = [
            f"# Weather — {area} ({time_slot})",
            "",
            f"**Current:** {desc}, {temp_c}C (feels like {feels_like}C), humidity {humidity}%",
            "",
        ]

        # Hourly forecast from weather data
        weather_days = data.get("weather", [])
        if weather_days:
            lines.append("| Time | Temp | Feels Like | Desc | Rain % |")
            lines.append("|------|------|-----------|------|--------|")
            for day in weather_days[:2]:
                for hour in day.get("hourly", []):
                    time_val = hour.get("time", "0").zfill(4)
                    h = f"{time_val[:2]}:{time_val[2:]}"
                    lines.append(
                        f"| {h} | {hour.get('tempC', '?')}C "
                        f"| {hour.get('FeelsLikeC', '?')}C "
                        f"| {hour.get('weatherDesc', [{}])[0].get('value', '')} "
                        f"| {hour.get('chanceofrain', '?')}% |"
                    )

        context["weather_briefing"] = "\n".join(lines)
        return context
