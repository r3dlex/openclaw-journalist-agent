"""Article extraction pipeline — fetch URL, extract content, hand off.

Implements the tiered fetch strategy: HTTP first, then escalate.
See ARCH-001 for tier definitions.
"""

from __future__ import annotations

from pipeline_runner.config import PipelineSettings
from pipeline_runner.runner import Pipeline
from pipeline_runner.steps.extract import ExtractContentStep
from pipeline_runner.steps.fetch import FetchUrlStep
from pipeline_runner.steps.handoff import LibrarianHandoffStep
from pipeline_runner.steps.iamq import IAMQAnnounceStep


def build_article_pipeline(
    settings: PipelineSettings | None = None,
    *,
    max_chars: int = 3000,
    handoff: bool = True,
) -> Pipeline:
    """Build the article extraction pipeline.

    Steps:
        1. fetch_url — HTTP GET the target URL (Tier 1)
        2. extract_content — Parse HTML into clean text
        3. librarian_handoff — (optional) Write to log and notify Librarian
        4. iamq_announce — Announce completion to IAMQ
    """
    pipeline = Pipeline("article_extraction")
    pipeline.add_step(FetchUrlStep())
    pipeline.add_step(ExtractContentStep(max_chars=max_chars))
    if handoff:
        pipeline.add_step(LibrarianHandoffStep())
    pipeline.add_step(IAMQAnnounceStep())
    return pipeline


def run_article_pipeline(url: str, settings: PipelineSettings | None = None) -> str:
    """Convenience function: extract article content from a URL."""
    settings = settings or PipelineSettings()

    pipeline = build_article_pipeline(settings, handoff=False)
    result = pipeline.run(
        {
            "settings": settings,
            "url": url,
            "pipeline_name": "article_extraction",
        }
    )

    if result.success:
        title = result.context.get("title", "")
        content = result.context.get("content", "")
        tier = result.context.get("fetch_tier", "?")
        header = f"# {title}\n\n" if title else ""
        return f"{header}(Fetched via Tier {tier})\n\n{content}"
    else:
        return f"Article extraction failed:\n{result.summary()}"
