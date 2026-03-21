"""Pipeline scheduler — long-running service that executes pipelines on cron.

Reads the schedule from configuration and runs pipelines at specified times.
Stays running as a Docker service (`docker compose up -d scheduler`).

For ad-hoc commands while the scheduler is running:
    docker compose exec scheduler pipeline news
    docker compose exec scheduler pipeline article <url>

See spec/CRON.md for the schedule definition.
See ARCH-006 for the architectural decision.

IMPORTANT: The `schedule` library fires "overdue" jobs immediately on the
first `run_pending()` call. To prevent every restart from re-running all
past-time jobs, we track last-run timestamps in a state file and skip
jobs that already ran today.
"""

from __future__ import annotations

import json
import logging
import signal
import sys
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import schedule

from pipeline_runner.config import PipelineSettings
from pipeline_runner.pipelines.news import run_news_pipeline
from pipeline_runner.pipelines.weather import run_weather_pipeline
from pipeline_runner.steps.iamq import iamq_heartbeat, iamq_register

logger = logging.getLogger(__name__)

# Sentinel for graceful shutdown
_shutdown = False

# State file to track last run times (survives restarts via Docker volume)
_STATE_FILE = Path("log/scheduler_state.json")

# Shared state dict — loaded once at startup, updated on each run
_run_state: dict[str, str] = {}


@dataclass
class ScheduledTask:
    """A task registered with the scheduler."""

    name: str
    schedule_desc: str
    pipeline_fn: str


def _load_state() -> dict[str, str]:
    """Load last-run timestamps from state file."""
    try:
        if _STATE_FILE.exists():
            data: dict[str, str] = json.loads(_STATE_FILE.read_text(encoding="utf-8"))
            return data
    except Exception:
        logger.warning("Could not load scheduler state, starting fresh")
    return {}


def _save_state(state: dict[str, str]) -> None:
    """Persist last-run timestamps to state file."""
    try:
        _STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception:
        logger.warning("Could not save scheduler state", exc_info=True)


def _already_ran_today(task_name: str, state: dict[str, str]) -> bool:
    """Check if a task already ran today (by date string comparison)."""
    today = datetime.now(tz=UTC).strftime("%Y-%m-%d")
    last_run = state.get(task_name, "")
    return last_run.startswith(today)


def _mark_ran(task_name: str, state: dict[str, str]) -> None:
    """Record that a task ran now."""
    state[task_name] = datetime.now(tz=UTC).isoformat()
    _save_state(state)


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


def _guarded_run(task_name: str, fn: Any, *args: Any) -> None:
    """Run a task only if it hasn't already run today. Tracks state.

    This prevents the schedule library's "overdue job" behavior from
    re-running all past-time tasks on every container restart.
    """
    if _already_ran_today(task_name, _run_state):
        logger.info("Skipping '%s' — already ran today (restart protection)", task_name)
        return
    fn(*args)
    _mark_ran(task_name, _run_state)


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

    Each task is wrapped in _guarded_run to prevent re-execution on
    container restart (the schedule library fires overdue jobs immediately).
    """
    tasks: list[ScheduledTask] = []

    # 06:00 — Morning briefing (news + weather 6am)
    schedule.every().day.at("06:00").do(
        _guarded_run, "morning_briefing", _run_news_and_weather, "6am", settings
    )
    tasks.append(ScheduledTask("Morning briefing", "daily 06:00", "news + weather 6am"))

    # 08:00 — News update
    schedule.every().day.at("08:00").do(_guarded_run, "news_08", _run_news, settings)
    tasks.append(ScheduledTask("News update", "daily 08:00", "news"))

    # 12:00 — Midday weather
    schedule.every().day.at("12:00").do(_guarded_run, "weather_12", _run_weather, "12pm", settings)
    tasks.append(ScheduledTask("Midday weather", "daily 12:00", "weather 12pm"))

    # 14:00 — Afternoon briefing
    schedule.every().day.at("14:00").do(_guarded_run, "news_14", _run_news, settings)
    tasks.append(ScheduledTask("Afternoon briefing", "daily 14:00", "news"))

    # 16:00 — Afternoon weather
    schedule.every().day.at("16:00").do(_guarded_run, "weather_16", _run_weather, "4pm", settings)
    tasks.append(ScheduledTask("Afternoon weather", "daily 16:00", "weather 4pm"))

    # 20:00 — Evening briefing (news + weather 8pm)
    schedule.every().day.at("20:00").do(
        _guarded_run, "evening_briefing", _run_news_and_weather, "8pm", settings
    )
    tasks.append(ScheduledTask("Evening briefing", "daily 20:00", "news + weather 8pm"))

    # Sunday 21:00 — Weekly weather
    schedule.every().sunday.at("21:00").do(
        _guarded_run, "weekly_weather", _run_weather, "sunday_9pm", settings
    )
    tasks.append(ScheduledTask("Weekly weather", "sunday 21:00", "weather sunday_9pm"))

    # IAMQ heartbeat — every 2 minutes (TTL is 5 min on the MQ side)
    schedule.every(2).minutes.do(iamq_heartbeat, settings)
    tasks.append(ScheduledTask("IAMQ heartbeat", "every 2 min", "iamq_heartbeat"))

    return tasks


def run_scheduler(settings: PipelineSettings | None = None) -> None:
    """Start the scheduler loop. Blocks until SIGTERM/SIGINT."""
    global _shutdown, _run_state

    settings = settings or PipelineSettings()

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    # Load persisted state so we know which tasks already ran today
    _run_state = _load_state()
    logger.info("Loaded scheduler state: %d tasks previously ran", len(_run_state))

    # Register with IAMQ on startup
    iamq_register(settings)

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
