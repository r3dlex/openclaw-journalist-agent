"""Pipeline scheduler — long-running service that executes pipelines on cron.

Reads the schedule from configuration and runs pipelines at specified times.
Stays running as a Docker service (`docker compose up -d scheduler`).

For ad-hoc commands while the scheduler is running:
    docker compose exec scheduler pipeline news
    docker compose exec scheduler pipeline article <url>

See spec/CRON.md for the schedule definition.
See ARCH-006 for the architectural decision.
"""

from __future__ import annotations

import logging
import signal
import sys
import time
from dataclasses import dataclass
from typing import Any

import schedule

from pipeline_runner.config import PipelineSettings
from pipeline_runner.pipelines.news import run_news_pipeline
from pipeline_runner.pipelines.weather import run_weather_pipeline

logger = logging.getLogger(__name__)

# Sentinel for graceful shutdown
_shutdown = False


@dataclass
class ScheduledTask:
    """A task registered with the scheduler."""

    name: str
    schedule_desc: str
    pipeline_fn: str


def _handle_signal(signum: int, frame: Any) -> None:
    """Handle SIGTERM/SIGINT for graceful shutdown."""
    global _shutdown
    logger.info("Received signal %d, shutting down gracefully...", signum)
    _shutdown = True


def _run_news(settings: PipelineSettings) -> None:
    """Run the news briefing pipeline, logging results."""
    logger.info("Scheduled: running news briefing pipeline")
    try:
        result = run_news_pipeline(settings)
        lines = result.split("\n")
        logger.info("News briefing completed: %d lines", len(lines))
    except Exception:
        logger.exception("News briefing pipeline failed")


def _run_weather(slot: str, settings: PipelineSettings) -> None:
    """Run the weather briefing pipeline for a specific time slot."""
    logger.info("Scheduled: running weather pipeline (slot=%s)", slot)
    try:
        result = run_weather_pipeline(slot, settings)
        lines = result.split("\n")
        logger.info("Weather briefing completed (slot=%s): %d lines", slot, len(lines))
    except Exception:
        logger.exception("Weather pipeline failed (slot=%s)", slot)


def _run_news_and_weather(slot: str, settings: PipelineSettings) -> None:
    """Run both news and weather pipelines (for combined schedule slots)."""
    _run_news(settings)
    _run_weather(slot, settings)


def register_schedule(settings: PipelineSettings) -> list[ScheduledTask]:
    """Register all scheduled tasks matching spec/CRON.md.

    Schedule (from spec/CRON.md):
        06:00  Morning briefing    news + weather 6am
        08:00  News update         news
        12:00  Midday weather      weather 12pm
        14:00  Afternoon briefing  news
        16:00  Afternoon weather   weather 4pm
        20:00  Evening briefing    news + weather 8pm
        Sun 21:00  Weekly weather  weather sunday_9pm
    """
    tasks: list[ScheduledTask] = []

    # 06:00 — Morning briefing (news + weather 6am)
    schedule.every().day.at("06:00").do(_run_news_and_weather, "6am", settings)
    tasks.append(ScheduledTask("Morning briefing", "daily 06:00", "news + weather 6am"))

    # 08:00 — News update
    schedule.every().day.at("08:00").do(_run_news, settings)
    tasks.append(ScheduledTask("News update", "daily 08:00", "news"))

    # 12:00 — Midday weather
    schedule.every().day.at("12:00").do(_run_weather, "12pm", settings)
    tasks.append(ScheduledTask("Midday weather", "daily 12:00", "weather 12pm"))

    # 14:00 — Afternoon briefing
    schedule.every().day.at("14:00").do(_run_news, settings)
    tasks.append(ScheduledTask("Afternoon briefing", "daily 14:00", "news"))

    # 16:00 — Afternoon weather
    schedule.every().day.at("16:00").do(_run_weather, "4pm", settings)
    tasks.append(ScheduledTask("Afternoon weather", "daily 16:00", "weather 4pm"))

    # 20:00 — Evening briefing (news + weather 8pm)
    schedule.every().day.at("20:00").do(_run_news_and_weather, "8pm", settings)
    tasks.append(ScheduledTask("Evening briefing", "daily 20:00", "news + weather 8pm"))

    # Sunday 21:00 — Weekly weather
    schedule.every().sunday.at("21:00").do(_run_weather, "sunday_9pm", settings)
    tasks.append(ScheduledTask("Weekly weather", "sunday 21:00", "weather sunday_9pm"))

    return tasks


def run_scheduler(settings: PipelineSettings | None = None) -> None:
    """Start the scheduler loop. Blocks until SIGTERM/SIGINT."""
    global _shutdown

    settings = settings or PipelineSettings()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    tasks = register_schedule(settings)

    logger.info("Scheduler started with %d tasks:", len(tasks))
    for t in tasks:
        logger.info("  [%s] %s -> %s", t.schedule_desc, t.name, t.pipeline_fn)

    logger.info("Next run: %s", schedule.next_run())

    while not _shutdown:
        schedule.run_pending()
        # Sleep in short intervals so we can respond to signals promptly
        for _ in range(10):
            if _shutdown:
                break
            time.sleep(1)

    logger.info("Scheduler stopped.")
    sys.exit(0)
