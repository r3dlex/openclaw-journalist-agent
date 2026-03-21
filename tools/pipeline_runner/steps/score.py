"""Importance scoring step — rank entries by relevance.

Scores stories 0-10 based on keyword matching and domain priority.
Higher scores indicate stories the user is more likely to care about.
See ARCH-001 for how scoring feeds into the tiered research pipeline.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from pipeline_runner.config import FeedConfig
from pipeline_runner.steps.fetch import FeedEntry

logger = logging.getLogger(__name__)

# Boost values for keyword tiers
BOOST_CRITICAL = 3  # breaking, exclusive
BOOST_HIGH = 2  # urgent, war, crisis
BOOST_NORMAL = 1  # standard keyword match

# Domain priority adds a fractional boost (0.0-1.0) used only for sorting.
# This doesn't inflate keyword scores but ensures high-priority domains
# sort above equal-keyword-score entries from lower-priority domains.
DOMAIN_PRIORITY_WEIGHT = 0.1


@dataclass
class ScoredEntry:
    """A feed entry with an importance score."""

    entry: FeedEntry
    score: int
    matched_keywords: list[str]
    domain_priority: int = 5


class ScoreImportanceStep:
    """Score feed entries by importance using keyword matching + domain priority.

    Context in:  entries (list[FeedEntry]), feeds_config (FeedConfig)
    Context out: scored_entries (list[ScoredEntry])
    """

    name = "score_importance"

    def should_run(self, context: dict[str, Any]) -> bool:
        return "entries" in context and len(context["entries"]) > 0

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        entries: list[FeedEntry] = context["entries"]
        feed_config: FeedConfig = context["feeds_config"]
        keywords = feed_config.important_keywords

        # Build category → domain priority lookup
        cat_domain = feed_config.domain_for_category
        domain_prio = feed_config.domain_priority

        scored: list[ScoredEntry] = []
        for entry in entries:
            score, matched = _score_entry(entry, keywords)
            dp = _domain_priority_for(entry.category, cat_domain, domain_prio)
            scored.append(
                ScoredEntry(
                    entry=entry,
                    score=score,
                    matched_keywords=matched,
                    domain_priority=dp,
                )
            )

        # Sort by keyword score (primary), then domain priority (secondary)
        scored.sort(
            key=lambda s: (s.score, s.domain_priority * DOMAIN_PRIORITY_WEIGHT),
            reverse=True,
        )
        context["scored_entries"] = scored

        high_count = sum(1 for s in scored if s.score >= feed_config.importance_threshold)
        logger.info(
            "Scored %d entries: %d above threshold (%d)",
            len(scored),
            high_count,
            feed_config.importance_threshold,
        )
        return context


def _score_entry(entry: FeedEntry, keywords: list[str]) -> tuple[int, list[str]]:
    """Score a single entry against keywords. Returns (score, matched_keywords)."""
    text = f"{entry.title} {entry.summary}".lower()
    score = 0
    matched: list[str] = []

    for keyword in keywords:
        kw = keyword.lower()
        if kw in text:
            matched.append(keyword)
            if kw in ("breaking", "exclusive"):
                score += BOOST_CRITICAL
            elif kw in ("urgent", "war", "crisis", "attack"):
                score += BOOST_HIGH
            else:
                score += BOOST_NORMAL

    return min(score, 10), matched


def _domain_priority_for(
    category: str,
    cat_domain: dict[str, str],
    domain_prio: dict[str, int],
) -> int:
    """Look up domain priority for a category. Default 5 (mid)."""
    domain_key = cat_domain.get(category, "")
    return domain_prio.get(domain_key, 5)
