"""News briefing pipeline — fetch, score, format, hand off.

This is the primary scheduled pipeline. It runs on cron (see spec/CRON.md)
and produces structured briefings from RSS feeds.
"""

from __future__ import annotations

from pipeline_runner.config import FeedConfig, PipelineSettings
from pipeline_runner.runner import Pipeline
from pipeline_runner.steps.fetch import FetchFeedsStep
from pipeline_runner.steps.format import FormatBriefingStep
from pipeline_runner.steps.handoff import LibrarianHandoffStep
from pipeline_runner.steps.iamq import IAMQAnnounceStep
from pipeline_runner.steps.score import ScoreImportanceStep


def build_news_pipeline(settings: PipelineSettings | None = None) -> Pipeline:
    """Build the news briefing pipeline.

    Steps:
        1. fetch_feeds — Aggregate RSS feeds concurrently
        2. score_importance — Rank by keyword matching
        3. format_briefing — Produce structured Markdown
        4. librarian_handoff — Write to log and notify Librarian
        5. iamq_announce — Announce completion to IAMQ
    """
    pipeline = Pipeline("news_briefing")
    pipeline.add_step(FetchFeedsStep())
    pipeline.add_step(ScoreImportanceStep())
    pipeline.add_step(FormatBriefingStep())
    pipeline.add_step(LibrarianHandoffStep())
    pipeline.add_step(IAMQAnnounceStep())
    return pipeline


def run_news_pipeline(settings: PipelineSettings | None = None) -> str:
    """Convenience function: build and run the news pipeline, return the briefing."""
    settings = settings or PipelineSettings()
    feed_config = FeedConfig(settings.feeds_file)

    pipeline = build_news_pipeline(settings)
    result = pipeline.run(
        {
            "settings": settings,
            "feeds_config": feed_config,
            "pipeline_name": "news_briefing",
        }
    )

    if result.success:
        briefing: str = result.context.get("briefing", "No briefing generated.")
        return briefing
    else:
        return f"Pipeline failed:\n{result.summary()}"
