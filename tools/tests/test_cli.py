"""Tests for the CLI entry point."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from pipeline_runner.config import PipelineSettings


class TestSetupLogging:
    def test_setup_logging_creates_log_file(self, tmp_data_dir: Path) -> None:
        from pipeline_runner.cli import _setup_logging

        settings = PipelineSettings(JOURNALIST_DATA_DIR=str(tmp_data_dir))
        import logging

        root = logging.getLogger()
        old_handlers = root.handlers[:]
        try:
            _setup_logging(settings)
            log_file = settings.log_dir / "pipeline.log"
            assert log_file.exists()
        finally:
            # Restore handlers to avoid polluting other tests
            for h in root.handlers[:]:
                if h not in old_handlers:
                    h.close()
                    root.removeHandler(h)

    def test_setup_logging_verbose(self, tmp_data_dir: Path) -> None:
        from pipeline_runner.cli import _setup_logging

        import logging

        settings = PipelineSettings(JOURNALIST_DATA_DIR=str(tmp_data_dir))
        root = logging.getLogger()
        old_handlers = root.handlers[:]
        try:
            _setup_logging(settings, verbose=True)
            # Should not raise
        finally:
            for h in root.handlers[:]:
                if h not in old_handlers:
                    h.close()
                    root.removeHandler(h)


class TestValidate:
    def test_validate_ok(self, tmp_data_dir: Path, feeds_json: Path) -> None:
        from pipeline_runner.cli import _validate

        settings = PipelineSettings(
            JOURNALIST_DATA_DIR=str(tmp_data_dir),
            FEEDS_FILE=str(feeds_json),
        )
        # Should not raise or call sys.exit
        _validate(settings)

    def test_validate_bad_feeds_exits(self, tmp_data_dir: Path) -> None:
        from pipeline_runner.cli import _validate

        settings = PipelineSettings(
            JOURNALIST_DATA_DIR=str(tmp_data_dir),
            FEEDS_FILE=str(tmp_data_dir / "nonexistent.json"),
        )
        with pytest.raises(SystemExit) as exc_info:
            _validate(settings)
        assert exc_info.value.code == 1

    def test_validate_bad_data_dir_exits(self, feeds_json: Path) -> None:
        from pipeline_runner.cli import _validate

        settings = PipelineSettings(
            JOURNALIST_DATA_DIR="/nonexistent/path/that/does/not/exist",
            FEEDS_FILE=str(feeds_json),
        )
        with pytest.raises(SystemExit) as exc_info:
            _validate(settings)
        assert exc_info.value.code == 1

    def test_validate_prints_librarian_workspace(
        self, tmp_data_dir: Path, feeds_json: Path, capsys
    ) -> None:
        from pipeline_runner.cli import _validate

        settings = PipelineSettings(
            JOURNALIST_DATA_DIR=str(tmp_data_dir),
            FEEDS_FILE=str(feeds_json),
            LIBRARIAN_AGENT_WORKSPACE="",
        )
        _validate(settings)
        captured = capsys.readouterr()
        assert "Librarian workspace" in captured.out


class TestMainCLI:
    @patch("pipeline_runner.cli.run_news_pipeline")
    @patch("pipeline_runner.cli._setup_logging")
    def test_main_news_command(
        self, mock_logging: MagicMock, mock_news: MagicMock, tmp_data_dir: Path
    ) -> None:
        from pipeline_runner.cli import main

        mock_news.return_value = "# News Briefing\nContent here"

        with patch.object(sys, "argv", ["pipeline", "news"]):
            with patch("pipeline_runner.cli.PipelineSettings") as mock_settings_cls:
                mock_settings = MagicMock()
                mock_settings.log_dir = tmp_data_dir / "log"
                mock_settings.log_dir.mkdir(exist_ok=True)
                mock_settings_cls.return_value = mock_settings
                main()

        mock_news.assert_called_once()

    @patch("pipeline_runner.cli.run_article_pipeline")
    @patch("pipeline_runner.cli._setup_logging")
    def test_main_article_command(
        self, mock_logging: MagicMock, mock_article: MagicMock, tmp_data_dir: Path
    ) -> None:
        from pipeline_runner.cli import main

        mock_article.return_value = "# Article\nContent"

        with patch.object(sys, "argv", ["pipeline", "article", "https://example.com"]):
            with patch("pipeline_runner.cli.PipelineSettings") as mock_settings_cls:
                mock_settings = MagicMock()
                mock_settings.log_dir = tmp_data_dir / "log"
                mock_settings.log_dir.mkdir(exist_ok=True)
                mock_settings_cls.return_value = mock_settings
                main()

        mock_article.assert_called_once_with("https://example.com", mock_settings)

    @patch("pipeline_runner.cli.run_weather_pipeline")
    @patch("pipeline_runner.cli._setup_logging")
    def test_main_weather_command(
        self, mock_logging: MagicMock, mock_weather: MagicMock, tmp_data_dir: Path
    ) -> None:
        from pipeline_runner.cli import main

        mock_weather.return_value = "# Weather\nContent"

        with patch.object(sys, "argv", ["pipeline", "weather", "12pm"]):
            with patch("pipeline_runner.cli.PipelineSettings") as mock_settings_cls:
                mock_settings = MagicMock()
                mock_settings.log_dir = tmp_data_dir / "log"
                mock_settings.log_dir.mkdir(exist_ok=True)
                mock_settings_cls.return_value = mock_settings
                main()

        mock_weather.assert_called_once_with("12pm", mock_settings)

    @patch("pipeline_runner.cli._setup_logging")
    def test_main_validate_command(
        self, mock_logging: MagicMock, tmp_data_dir: Path, feeds_json: Path
    ) -> None:
        from pipeline_runner.cli import main

        with patch.object(sys, "argv", ["pipeline", "validate"]):
            with patch("pipeline_runner.cli.PipelineSettings") as mock_settings_cls:
                mock_settings = MagicMock()
                mock_settings.log_dir = tmp_data_dir / "log"
                mock_settings.log_dir.mkdir(exist_ok=True)
                mock_settings_cls.return_value = mock_settings
                with patch("pipeline_runner.cli._validate") as mock_validate:
                    main()
                    mock_validate.assert_called_once_with(mock_settings)

    @patch("pipeline_runner.cli._setup_logging")
    def test_main_scheduler_command(
        self, mock_logging: MagicMock, tmp_data_dir: Path
    ) -> None:
        from pipeline_runner.cli import main

        with patch.object(sys, "argv", ["pipeline", "scheduler"]):
            with patch("pipeline_runner.cli.PipelineSettings") as mock_settings_cls:
                mock_settings = MagicMock()
                mock_settings.log_dir = tmp_data_dir / "log"
                mock_settings.log_dir.mkdir(exist_ok=True)
                mock_settings_cls.return_value = mock_settings
                with patch("pipeline_runner.scheduler.run_scheduler") as mock_scheduler:
                    main()
                    mock_scheduler.assert_called_once_with(mock_settings)

    def test_main_no_args_exits(self) -> None:
        from pipeline_runner.cli import main

        with patch.object(sys, "argv", ["pipeline"]):
            with pytest.raises(SystemExit):
                main()

    @patch("pipeline_runner.cli.run_weather_pipeline")
    @patch("pipeline_runner.cli._setup_logging")
    def test_main_weather_default_slot(
        self, mock_logging: MagicMock, mock_weather: MagicMock, tmp_data_dir: Path
    ) -> None:
        from pipeline_runner.cli import main

        mock_weather.return_value = "# Weather"

        with patch.object(sys, "argv", ["pipeline", "weather"]):
            with patch("pipeline_runner.cli.PipelineSettings") as mock_settings_cls:
                mock_settings = MagicMock()
                mock_settings.log_dir = tmp_data_dir / "log"
                mock_settings.log_dir.mkdir(exist_ok=True)
                mock_settings_cls.return_value = mock_settings
                main()

        mock_weather.assert_called_once_with("6am", mock_settings)

    @patch("pipeline_runner.cli.run_news_pipeline")
    @patch("pipeline_runner.cli._setup_logging")
    def test_main_verbose_flag(
        self, mock_logging: MagicMock, mock_news: MagicMock, tmp_data_dir: Path
    ) -> None:
        from pipeline_runner.cli import main

        mock_news.return_value = "# News"

        with patch.object(sys, "argv", ["pipeline", "-v", "news"]):
            with patch("pipeline_runner.cli.PipelineSettings") as mock_settings_cls:
                mock_settings = MagicMock()
                mock_settings.log_dir = tmp_data_dir / "log"
                mock_settings.log_dir.mkdir(exist_ok=True)
                mock_settings_cls.return_value = mock_settings
                main()

        # _setup_logging should be called with verbose=True
        mock_logging.assert_called_once_with(mock_settings, verbose=True)
