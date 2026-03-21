"""Tests for the formatting steps."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pipeline_runner.config import FeedConfig
from pipeline_runner.steps.fetch import FeedEntry
from pipeline_runner.steps.format import FormatBriefingStep
from pipeline_runner.steps.score import ScoredEntry


def _make_scored(
    title: str, category: str, score: int, *, link: str = "", summary: str = ""
) -> ScoredEntry:
    return ScoredEntry(
        entry=FeedEntry(
            title=title,
            link=link or f"https://example.com/{title.lower().replace(' ', '-')}",
            summary=summary,
            published="2026-03-19",
            category=category,
            source_feed="https://example.com/feed",
        ),
        score=score,
        matched_keywords=[],
    )


def _make_config(tmp_path: Path, *, with_domains: bool = True) -> FeedConfig:
    data: dict[str, Any] = {
        "categories": {
            "BREAKING": ["https://example.com/feed1"],
            "AI & MODELS": ["https://example.com/feed2"],
            "AEC INDUSTRY": ["https://example.com/feed3"],
        },
        "important_keywords": ["ai"],
        "settings": {
            "max_entries_per_feed": 3,
            "importance_threshold_for_detail": 2,
            "max_concurrent_fetchers": 2,
        },
    }
    if with_domains:
        data["domains"] = {
            "CORE": {
                "label": "Core Intelligence",
                "priority": 10,
                "categories": ["BREAKING"],
            },
            "TECH & AI": {
                "label": "Technology & AI",
                "priority": 9,
                "categories": ["AI & MODELS"],
            },
            "INDUSTRIES": {
                "label": "Industry Watch",
                "priority": 7,
                "categories": ["AEC INDUSTRY"],
            },
        }
    path = tmp_path / "feeds.json"
    path.write_text(json.dumps(data))
    return FeedConfig(path)


class TestFormatBriefingDomains:
    """Test domain-grouped briefing formatting."""

    def test_domain_sections_appear_as_h2(self, tmp_path: Path) -> None:
        config = _make_config(tmp_path, with_domains=True)
        entries = [
            _make_scored("Breaking event", "BREAKING", 8),
            _make_scored("New AI model", "AI & MODELS", 5),
        ]
        step = FormatBriefingStep()
        ctx: dict[str, Any] = {
            "scored_entries": entries,
            "feeds_config": config,
        }
        result = step.execute(ctx)
        briefing = result["briefing"]
        assert "## Core Intelligence" in briefing
        assert "## Technology & AI" in briefing

    def test_categories_appear_as_h3_under_domain(self, tmp_path: Path) -> None:
        config = _make_config(tmp_path, with_domains=True)
        entries = [
            _make_scored("Breaking event", "BREAKING", 8),
            _make_scored("Construction news", "AEC INDUSTRY", 3),
        ]
        step = FormatBriefingStep()
        ctx: dict[str, Any] = {
            "scored_entries": entries,
            "feeds_config": config,
        }
        result = step.execute(ctx)
        briefing = result["briefing"]
        assert "### BREAKING" in briefing
        assert "### AEC INDUSTRY" in briefing

    def test_domains_sorted_by_priority(self, tmp_path: Path) -> None:
        config = _make_config(tmp_path, with_domains=True)
        entries = [
            _make_scored("Construction news", "AEC INDUSTRY", 3),
            _make_scored("Breaking event", "BREAKING", 8),
            _make_scored("New AI model", "AI & MODELS", 5),
        ]
        step = FormatBriefingStep()
        ctx: dict[str, Any] = {
            "scored_entries": entries,
            "feeds_config": config,
        }
        result = step.execute(ctx)
        briefing = result["briefing"]
        core_pos = briefing.index("Core Intelligence")
        tech_pos = briefing.index("Technology & AI")
        industry_pos = briefing.index("Industry Watch")
        assert core_pos < tech_pos < industry_pos

    def test_empty_domains_skipped(self, tmp_path: Path) -> None:
        config = _make_config(tmp_path, with_domains=True)
        # Only BREAKING has entries; AI & MODELS and AEC INDUSTRY are empty
        entries = [_make_scored("Breaking event", "BREAKING", 8)]
        step = FormatBriefingStep()
        ctx: dict[str, Any] = {
            "scored_entries": entries,
            "feeds_config": config,
        }
        result = step.execute(ctx)
        briefing = result["briefing"]
        assert "## Core Intelligence" in briefing
        assert "Technology & AI" not in briefing
        assert "Industry Watch" not in briefing

    def test_orphan_categories_in_other_section(self, tmp_path: Path) -> None:
        config = _make_config(tmp_path, with_domains=True)
        entries = [
            _make_scored("Some news", "UNKNOWN_CATEGORY", 2),
        ]
        step = FormatBriefingStep()
        ctx: dict[str, Any] = {
            "scored_entries": entries,
            "feeds_config": config,
        }
        result = step.execute(ctx)
        briefing = result["briefing"]
        assert "## Other" in briefing
        assert "### UNKNOWN_CATEGORY" in briefing

    def test_summary_includes_domain_count(self, tmp_path: Path) -> None:
        config = _make_config(tmp_path, with_domains=True)
        entries = [_make_scored("Breaking event", "BREAKING", 8)]
        step = FormatBriefingStep()
        ctx: dict[str, Any] = {
            "scored_entries": entries,
            "feeds_config": config,
        }
        result = step.execute(ctx)
        briefing = result["briefing"]
        assert "3 domains" in briefing


class TestFormatBriefingFlatFallback:
    """Test flat formatting when no domains are configured."""

    def test_flat_categories_when_no_domains(self, tmp_path: Path) -> None:
        config = _make_config(tmp_path, with_domains=False)
        entries = [
            _make_scored("Breaking event", "BREAKING", 8),
            _make_scored("AI news", "AI & MODELS", 5),
        ]
        step = FormatBriefingStep()
        ctx: dict[str, Any] = {
            "scored_entries": entries,
            "feeds_config": config,
        }
        result = step.execute(ctx)
        briefing = result["briefing"]
        # Flat: categories appear as H2 (no H3)
        assert "## BREAKING" in briefing
        assert "## AI & MODELS" in briefing
        # No domain labels
        assert "Core Intelligence" not in briefing

    def test_flat_fallback_when_no_feeds_config(self) -> None:
        entries = [_make_scored("Some story", "TEST", 3)]
        step = FormatBriefingStep()
        ctx: dict[str, Any] = {"scored_entries": entries}
        result = step.execute(ctx)
        briefing = result["briefing"]
        assert "## TEST" in briefing

    def test_top_stories_always_present(self, tmp_path: Path) -> None:
        entries = [_make_scored("Important story", "BREAKING", 8)]
        step = FormatBriefingStep()
        ctx: dict[str, Any] = {"scored_entries": entries}
        result = step.execute(ctx)
        assert "Top Stories" in result["briefing"]

    def test_max_per_category_respected(self, tmp_path: Path) -> None:
        entries = [
            _make_scored(f"Story {i}", "BREAKING", 5 - i) for i in range(10)
        ]
        step = FormatBriefingStep(max_per_category=3)
        ctx: dict[str, Any] = {"scored_entries": entries}
        result = step.execute(ctx)
        briefing = result["briefing"]
        # Count "**Story" occurrences in the BREAKING section (not top stories)
        # Top stories shows up to 10, BREAKING section limited to 3
        breaking_section = briefing.split("## BREAKING")[1] if "## BREAKING" in briefing else ""
        story_count = breaking_section.count("**Story")
        assert story_count == 3
