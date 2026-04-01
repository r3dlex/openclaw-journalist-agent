"""Tests for the librarian handoff step."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

from pipeline_runner.config import PipelineSettings
from pipeline_runner.steps.handoff import LibrarianHandoffStep


class TestLibrarianHandoffStep:
    def test_should_run_with_briefing(self) -> None:
        step = LibrarianHandoffStep()
        assert step.should_run({"briefing": "content"}) is True

    def test_should_run_with_weather_briefing(self) -> None:
        step = LibrarianHandoffStep()
        assert step.should_run({"weather_briefing": "weather"}) is True

    def test_should_not_run_without_content(self) -> None:
        step = LibrarianHandoffStep()
        assert step.should_run({}) is False

    def test_writes_output_file(self, tmp_data_dir: Path) -> None:
        step = LibrarianHandoffStep()
        settings = PipelineSettings(JOURNALIST_DATA_DIR=str(tmp_data_dir))
        ctx = {
            "briefing": "# Test Briefing\nContent here",
            "settings": settings,
            "pipeline_name": "news_briefing",
        }
        result = step.execute(ctx)

        assert "handoff_path" in result
        output_path: Path = result["handoff_path"]
        assert output_path.exists()
        assert "# Test Briefing" in output_path.read_text()

    def test_writes_metadata_file(self, tmp_data_dir: Path) -> None:
        step = LibrarianHandoffStep()
        settings = PipelineSettings(JOURNALIST_DATA_DIR=str(tmp_data_dir))
        ctx = {
            "briefing": "Content",
            "settings": settings,
            "pipeline_name": "news_briefing",
        }
        result = step.execute(ctx)

        import json

        metadata = result["handoff_metadata"]
        assert metadata["source_agent"] == "journalist"
        assert metadata["target_agent"] == "librarian"
        assert metadata["pipeline"] == "news_briefing"
        assert "output_file" in metadata
        assert "output_size_bytes" in metadata

    def test_uses_weather_briefing_when_no_briefing(self, tmp_data_dir: Path) -> None:
        step = LibrarianHandoffStep()
        settings = PipelineSettings(JOURNALIST_DATA_DIR=str(tmp_data_dir))
        ctx = {
            "weather_briefing": "# Weather Report\nSunny",
            "settings": settings,
            "pipeline_name": "weather_briefing",
        }
        result = step.execute(ctx)

        output_path: Path = result["handoff_path"]
        assert "Weather Report" in output_path.read_text()

    def test_writes_signal_to_librarian_workspace(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        librarian_ws = tmp_path / "librarian"
        librarian_ws.mkdir()

        step = LibrarianHandoffStep()
        # Set LIBRARIAN_WORKSPACE_MOUNT to librarian_ws so it takes precedence
        settings = PipelineSettings(
            JOURNALIST_DATA_DIR=str(data_dir),
            LIBRARIAN_AGENT_WORKSPACE=str(librarian_ws),
            LIBRARIAN_WORKSPACE_MOUNT=str(librarian_ws),
        )
        ctx = {
            "briefing": "Content",
            "settings": settings,
            "pipeline_name": "news_briefing",
        }
        result = step.execute(ctx)

        inbox = librarian_ws / "inbox"
        assert inbox.exists()
        signal_files = list(inbox.glob("journalist_*.json"))
        assert len(signal_files) == 1

    def test_logs_warning_when_no_librarian_workspace(self, tmp_data_dir: Path) -> None:
        step = LibrarianHandoffStep()
        settings = PipelineSettings(
            JOURNALIST_DATA_DIR=str(tmp_data_dir),
            LIBRARIAN_AGENT_WORKSPACE="",
        )
        ctx = {
            "briefing": "Content",
            "settings": settings,
            "pipeline_name": "news_briefing",
        }
        # Should not raise even without librarian workspace
        result = step.execute(ctx)
        assert "handoff_path" in result

    def test_uses_unknown_pipeline_name_when_missing(self, tmp_data_dir: Path) -> None:
        step = LibrarianHandoffStep()
        settings = PipelineSettings(JOURNALIST_DATA_DIR=str(tmp_data_dir))
        ctx = {
            "briefing": "Content",
            "settings": settings,
        }
        result = step.execute(ctx)
        metadata = result["handoff_metadata"]
        assert metadata["pipeline"] == "unknown"

    def test_uses_mounted_librarian_workspace_over_host(self, tmp_path: Path) -> None:
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        mounted_ws = tmp_path / "mounted_librarian"
        mounted_ws.mkdir()

        step = LibrarianHandoffStep()
        # When LIBRARIAN_WORKSPACE_MOUNT is set and exists, it is used
        settings = PipelineSettings(
            JOURNALIST_DATA_DIR=str(data_dir),
            LIBRARIAN_WORKSPACE_MOUNT=str(mounted_ws),
        )
        ctx = {
            "briefing": "Content",
            "settings": settings,
            "pipeline_name": "news_briefing",
        }
        result = step.execute(ctx)

        # Mounted workspace inbox should be used
        mounted_inbox = mounted_ws / "inbox"
        assert mounted_inbox.exists()
