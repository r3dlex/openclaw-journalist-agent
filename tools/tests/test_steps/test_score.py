"""Tests for the importance scoring step."""

from __future__ import annotations

from pipeline_runner.steps.fetch import FeedEntry
from pipeline_runner.steps.score import ScoreImportanceStep, _score_entry


class TestScoreEntry:
    def test_no_keywords_match(self) -> None:
        entry = FeedEntry(
            title="Normal headline",
            link="",
            summary="Nothing special here.",
            published="",
            category="TEST",
            source_feed="",
        )
        score, matched = _score_entry(entry, ["breaking", "ai"])
        assert score == 0
        assert matched == []

    def test_single_keyword_match(self) -> None:
        entry = FeedEntry(
            title="New AI model released",
            link="",
            summary="",
            published="",
            category="TEST",
            source_feed="",
        )
        score, matched = _score_entry(entry, ["ai", "war"])
        assert score == 1
        assert "ai" in matched

    def test_breaking_boost(self) -> None:
        entry = FeedEntry(
            title="Breaking news about AI",
            link="",
            summary="",
            published="",
            category="TEST",
            source_feed="",
        )
        score, matched = _score_entry(entry, ["breaking", "ai"])
        assert score == 4  # breaking=3 + ai=1
        assert "breaking" in matched
        assert "ai" in matched

    def test_urgent_war_boost(self) -> None:
        entry = FeedEntry(
            title="Urgent: War crisis update",
            link="",
            summary="",
            published="",
            category="TEST",
            source_feed="",
        )
        score, matched = _score_entry(entry, ["urgent", "war", "crisis"])
        assert score == 6  # urgent=2 + war=2 + crisis=2

    def test_score_capped_at_10(self) -> None:
        entry = FeedEntry(
            title="Breaking exclusive urgent war crisis attack",
            link="",
            summary="",
            published="",
            category="TEST",
            source_feed="",
        )
        keywords = ["breaking", "exclusive", "urgent", "war", "crisis", "attack"]
        score, _ = _score_entry(entry, keywords)
        assert score == 10

    def test_case_insensitive(self) -> None:
        entry = FeedEntry(
            title="AI Breaking NEWS",
            link="",
            summary="",
            published="",
            category="TEST",
            source_feed="",
        )
        score, matched = _score_entry(entry, ["ai", "breaking"])
        assert score == 4
        assert len(matched) == 2


class TestScoreImportanceStep:
    def test_sorts_by_score_descending(self, sample_entries, feed_config) -> None:
        step = ScoreImportanceStep()
        context = {"entries": sample_entries, "feeds_config": feed_config}
        result = step.execute(context)

        scored = result["scored_entries"]
        scores = [s.score for s in scored]
        assert scores == sorted(scores, reverse=True)

    def test_should_run_with_entries(self, sample_entries) -> None:
        step = ScoreImportanceStep()
        assert step.should_run({"entries": sample_entries})

    def test_should_not_run_without_entries(self) -> None:
        step = ScoreImportanceStep()
        assert not step.should_run({})
        assert not step.should_run({"entries": []})
