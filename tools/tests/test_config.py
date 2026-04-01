"""Tests for configuration management."""

from __future__ import annotations

from pathlib import Path

import pytest

from pipeline_runner.config import FeedConfig, PipelineSettings


class TestFeedConfig:
    def test_loads_categories(self, feeds_json: Path) -> None:
        config = FeedConfig(feeds_json)
        assert "TEST" in config.categories
        assert len(config.categories["TEST"]) == 1

    def test_loads_keywords(self, feeds_json: Path) -> None:
        config = FeedConfig(feeds_json)
        assert "breaking" in config.important_keywords
        assert "ai" in config.important_keywords

    def test_loads_domains(self, feeds_json: Path) -> None:
        config = FeedConfig(feeds_json)
        assert "CORE" in config.domains
        assert config.domains["CORE"]["label"] == "Core Intelligence"
        assert config.domains["CORE"]["priority"] == 10

    def test_domain_for_category(self, feeds_json: Path) -> None:
        config = FeedConfig(feeds_json)
        mapping = config.domain_for_category
        assert mapping["TEST"] == "CORE"

    def test_domain_priority(self, feeds_json: Path) -> None:
        config = FeedConfig(feeds_json)
        prio = config.domain_priority
        assert prio["CORE"] == 10

    def test_settings_defaults(self, feeds_json: Path) -> None:
        config = FeedConfig(feeds_json)
        assert config.max_entries_per_feed == 3
        assert config.importance_threshold == 2
        assert config.max_concurrent_fetchers == 2
        assert config.article_max_chars == 1000

    def test_reload(self, feeds_json: Path) -> None:
        config = FeedConfig(feeds_json)
        assert config.max_entries_per_feed == 3
        # Modify file
        import json

        data = json.loads(feeds_json.read_text())
        data["settings"]["max_entries_per_feed"] = 10
        feeds_json.write_text(json.dumps(data))
        config.reload()
        assert config.max_entries_per_feed == 10

    def test_invalid_file_raises(self, tmp_path: Path) -> None:
        bad_path = tmp_path / "nonexistent.json"
        with pytest.raises(FileNotFoundError):
            FeedConfig(bad_path)


class TestPipelineSettings:
    def test_log_dir_creation(self, tmp_data_dir: Path) -> None:
        settings = PipelineSettings(JOURNALIST_DATA_DIR=str(tmp_data_dir))
        log_dir = settings.log_dir
        assert log_dir.exists()
        assert log_dir.name == "log"

    def test_reports_dir_creation(self, tmp_data_dir: Path) -> None:
        settings = PipelineSettings(JOURNALIST_DATA_DIR=str(tmp_data_dir))
        reports_dir = settings.reports_dir
        assert reports_dir.exists()
        assert reports_dir.name == "reports"
