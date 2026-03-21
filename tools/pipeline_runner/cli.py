"""CLI entry point for the pipeline runner.

Usage:
    pipeline news              — Run the news briefing pipeline
    pipeline article <url>     — Extract article content from a URL
    pipeline weather <slot>    — Run weather briefing (6am|12pm|4pm|8pm|sunday_9pm)
    pipeline validate          — Validate configuration (feeds, env)
    pipeline scheduler         — Start the long-running scheduler service
"""

from __future__ import annotations

import argparse
import logging
import sys
from logging.handlers import RotatingFileHandler

from pipeline_runner.config import PipelineSettings
from pipeline_runner.pipelines.article import run_article_pipeline
from pipeline_runner.pipelines.news import run_news_pipeline
from pipeline_runner.pipelines.weather import run_weather_pipeline


def _setup_logging(settings: PipelineSettings, *, verbose: bool = False) -> None:
    """Configure logging to both console and log/ folder."""
    level = logging.DEBUG if verbose else logging.INFO
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

    # Console handler
    console = logging.StreamHandler()
    console.setLevel(level)
    console.setFormatter(logging.Formatter(fmt))

    # File handler — writes to log/ folder with rotation
    log_dir = settings.log_dir
    log_file = log_dir / "pipeline.log"
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(fmt))

    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    root.addHandler(console)
    root.addHandler(file_handler)


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="pipeline",
        description="Journalist Agent pipeline runner",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="Enable debug logging")

    subparsers = parser.add_subparsers(dest="command", required=True)

    # news
    subparsers.add_parser("news", help="Run news briefing pipeline")

    # article
    article_parser = subparsers.add_parser("article", help="Extract article from URL")
    article_parser.add_argument("url", help="URL to extract")

    # weather
    weather_parser = subparsers.add_parser("weather", help="Run weather briefing")
    weather_parser.add_argument(
        "slot",
        nargs="?",
        default="6am",
        choices=["6am", "12pm", "4pm", "8pm", "sunday_9pm"],
        help="Time slot (default: 6am)",
    )

    # validate
    subparsers.add_parser("validate", help="Validate configuration")

    # scheduler
    subparsers.add_parser("scheduler", help="Start the long-running scheduler (blocks)")

    args = parser.parse_args()

    settings = PipelineSettings()
    _setup_logging(settings, verbose=args.verbose)

    if args.command == "news":
        print(run_news_pipeline(settings))
    elif args.command == "article":
        print(run_article_pipeline(args.url, settings))
    elif args.command == "weather":
        print(run_weather_pipeline(args.slot, settings))
    elif args.command == "validate":
        _validate(settings)
    elif args.command == "scheduler":
        from pipeline_runner.scheduler import run_scheduler

        run_scheduler(settings)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()


def _validate(settings: PipelineSettings) -> None:
    """Validate configuration files and environment."""
    from pipeline_runner.config import FeedConfig

    errors: list[str] = []

    # Check feeds file
    try:
        fc = FeedConfig(settings.feeds_file)
        cat_count = len(fc.categories)
        feed_count = sum(len(v) for v in fc.categories.values())
        print(f"Feeds: {feed_count} feeds in {cat_count} categories")
    except Exception as e:
        errors.append(f"Feeds config: {e}")

    # Check paths
    if settings.journalist_data_dir.exists():
        print(f"Data dir: {settings.journalist_data_dir} (exists)")
    else:
        errors.append(f"Data dir does not exist: {settings.journalist_data_dir}")

    if settings.librarian_agent_workspace and settings.librarian_agent_workspace.exists():
        print(f"Librarian workspace: {settings.librarian_agent_workspace} (exists)")
    else:
        print(f"Librarian workspace: {settings.librarian_agent_workspace} (not found)")

    if errors:
        print(f"\nValidation FAILED with {len(errors)} errors:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print("\nValidation OK")
