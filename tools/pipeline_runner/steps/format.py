"""Formatting steps — transform pipeline data into output documents.

Produces structured Markdown briefings and weather reports.
Uses the two-level domain→category hierarchy from feeds.json for
structured output grouping.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from pipeline_runner.config import FeedConfig
from pipeline_runner.steps.score import ScoredEntry

logger = logging.getLogger(__name__)


class FormatBriefingStep:
    """Format scored entries into a structured Markdown briefing.

    Uses the domain hierarchy from ``feeds_config`` to group entries:
    Domain (H2) → Category (H3) → entries.  Falls back to flat category
    headings when domains are not configured.

    Context in:  scored_entries (list[ScoredEntry]), feeds_config (FeedConfig)
    Context out: briefing (str), briefing_date (str)
    """

    name = "format_briefing"

    def __init__(self, max_per_category: int = 5, top_stories: int = 10) -> None:
        self.max_per_category = max_per_category
        self.top_stories = top_stories

    def should_run(self, context: dict[str, Any]) -> bool:
        return "scored_entries" in context

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        scored: list[ScoredEntry] = context["scored_entries"]
        feed_config: FeedConfig | None = context.get("feeds_config")
        now = datetime.now(tz=UTC)
        date_str = now.strftime("%Y-%m-%d %H:%M UTC")

        lines: list[str] = [f"# News Briefing — {date_str}", ""]

        # ── Top Stories ─────────────────────────────────────────
        top = scored[: self.top_stories]
        if top:
            lines.append("## ⚡ Top Stories")
            lines.append("")
            for i, s in enumerate(top, 1):
                score_bar = "+" * min(s.score, 10)
                lines.append(f"{i}. [{score_bar}] **{s.entry.title}**")
                if s.entry.summary:
                    lines.append(f"   {s.entry.summary[:200]}")
                lines.append(f"   Source: {s.entry.link}")
                lines.append("")

        # ── Group entries by category ──────────────────────────
        by_category: dict[str, list[ScoredEntry]] = {}
        for s in scored:
            by_category.setdefault(s.entry.category, []).append(s)

        # ── Domain-grouped output ──────────────────────────────
        if feed_config and feed_config.domains:
            lines.extend(self._format_by_domain(feed_config, by_category))
        else:
            # Flat fallback (no domains configured)
            lines.extend(self._format_flat(by_category))

        # ── Summary ────────────────────────────────────────────
        domain_count = len(feed_config.domains) if feed_config and feed_config.domains else 0
        lines.append("---")
        summary = f"Total: {len(scored)} stories across " f"{len(by_category)} categories"
        if domain_count:
            summary += f" in {domain_count} domains"
        summary += f". Generated: {date_str}"
        lines.append(summary)

        briefing = "\n".join(lines)
        context["briefing"] = briefing
        context["briefing_date"] = now.isoformat()
        logger.info("Formatted briefing: %d lines, %d chars", len(lines), len(briefing))
        return context

    # ── Private helpers ────────────────────────────────────────

    def _format_by_domain(
        self,
        feed_config: FeedConfig,
        by_category: dict[str, list[ScoredEntry]],
    ) -> list[str]:
        """Render entries grouped by domain (H2) → category (H3)."""
        lines: list[str] = []
        domain_prio = feed_config.domain_priority

        # Sort domains by priority (highest first)
        sorted_domains = sorted(
            feed_config.domains.items(),
            key=lambda kv: domain_prio.get(kv[0], 5),
            reverse=True,
        )

        assigned_categories: set[str] = set()

        for domain_key, domain_info in sorted_domains:
            domain_label = domain_info.get("label", domain_key)
            domain_cats = domain_info.get("categories", [])

            # Collect categories that actually have entries
            active_cats = [c for c in domain_cats if c in by_category]
            if not active_cats:
                continue

            lines.append(f"## {domain_label}")
            lines.append("")

            for cat in active_cats:
                assigned_categories.add(cat)
                entries = by_category[cat]
                lines.append(f"### {cat}")
                lines.append("")
                for s in entries[: self.max_per_category]:
                    lines.append(f"- **{s.entry.title}** (score: {s.score})")
                    lines.append(f"  {s.entry.link}")
                lines.append("")

        # Any categories not assigned to a domain (orphans)
        orphans = {k: v for k, v in by_category.items() if k not in assigned_categories}
        if orphans:
            lines.append("## Other")
            lines.append("")
            for cat, entries in orphans.items():
                lines.append(f"### {cat}")
                lines.append("")
                for s in entries[: self.max_per_category]:
                    lines.append(f"- **{s.entry.title}** (score: {s.score})")
                    lines.append(f"  {s.entry.link}")
                lines.append("")

        return lines

    def _format_flat(self, by_category: dict[str, list[ScoredEntry]]) -> list[str]:
        """Render entries as flat category sections (legacy fallback)."""
        lines: list[str] = []
        for cat, entries in by_category.items():
            lines.append(f"## {cat}")
            lines.append("")
            for s in entries[: self.max_per_category]:
                lines.append(f"- **{s.entry.title}** (score: {s.score})")
                lines.append(f"  {s.entry.link}")
            lines.append("")
        return lines


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
