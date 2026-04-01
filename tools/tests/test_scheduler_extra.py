"""Additional tests for scheduler internals to boost coverage."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

import schedule as schedule_lib

from pipeline_runner.config import PipelineSettings
from pipeline_runner.scheduler import (
    _STATE_FILE,
    _already_ran_today,
    _load_state,
    _mark_ran,
    _save_state,
)


class TestLoadState:
    def test_returns_empty_dict_when_file_missing(self, tmp_path: Path) -> None:
        non_existent = tmp_path / "nonexistent_state.json"
        with patch("pipeline_runner.scheduler._STATE_FILE", non_existent):
            state = _load_state()
        assert state == {}

    def test_returns_data_when_file_exists(self, tmp_path: Path) -> None:
        state_file = tmp_path / "scheduler_state.json"
        state_data = {"morning_briefing": "2026-04-01T06:00:00+00:00"}
        state_file.write_text(json.dumps(state_data))

        with patch("pipeline_runner.scheduler._STATE_FILE", state_file):
            state = _load_state()

        assert state == state_data

    def test_returns_empty_on_corrupt_file(self, tmp_path: Path) -> None:
        state_file = tmp_path / "scheduler_state.json"
        state_file.write_text("not valid json{{{{")

        with patch("pipeline_runner.scheduler._STATE_FILE", state_file):
            state = _load_state()

        assert state == {}


class TestSaveState:
    def test_creates_parent_directory(self, tmp_path: Path) -> None:
        state_file = tmp_path / "subdir" / "scheduler_state.json"
        state = {"task": "2026-04-01T06:00:00+00:00"}

        with patch("pipeline_runner.scheduler._STATE_FILE", state_file):
            _save_state(state)

        assert state_file.exists()
        saved = json.loads(state_file.read_text())
        assert saved == state

    def test_handles_write_error_gracefully(self, tmp_path: Path) -> None:
        state_file = tmp_path / "readonly_state.json"
        state = {"task": "2026-04-01T06:00:00"}

        with patch("pipeline_runner.scheduler._STATE_FILE", state_file):
            with patch("pathlib.Path.write_text", side_effect=PermissionError("read only")):
                # Should not raise
                _save_state(state)


class TestHandleSignal:
    def test_sets_shutdown_flag(self) -> None:
        import pipeline_runner.scheduler as sched

        old_shutdown = sched._shutdown
        try:
            sched._shutdown = False
            from pipeline_runner.scheduler import _handle_signal

            _handle_signal(15, None)
            assert sched._shutdown is True
        finally:
            sched._shutdown = old_shutdown


class TestRunWeatherHelper:
    @patch("pipeline_runner.scheduler.run_weather_pipeline")
    def test_run_weather_handles_exception(
        self, mock_weather: MagicMock, settings: PipelineSettings
    ) -> None:
        from pipeline_runner.scheduler import _run_weather

        mock_weather.side_effect = RuntimeError("API down")
        # Should not raise
        _run_weather("12pm", settings)

    @patch("pipeline_runner.scheduler.run_weather_pipeline")
    def test_run_weather_logs_lines(
        self, mock_weather: MagicMock, settings: PipelineSettings
    ) -> None:
        from pipeline_runner.scheduler import _run_weather

        mock_weather.return_value = "# Weather\nLine 1\nLine 2\nLine 3"
        _run_weather("6am", settings)
        mock_weather.assert_called_once_with("6am", settings)


class TestRunScheduler:
    @patch("pipeline_runner.scheduler.iamq_register")
    @patch("pipeline_runner.scheduler.iamq_heartbeat")
    @patch("pipeline_runner.scheduler.register_schedule")
    @patch("pipeline_runner.scheduler._load_state")
    @patch("pipeline_runner.scheduler.schedule.run_pending")
    @patch("pipeline_runner.scheduler.time.sleep")
    def test_scheduler_exits_on_shutdown(
        self,
        mock_sleep: MagicMock,
        mock_run_pending: MagicMock,
        mock_load_state: MagicMock,
        mock_register: MagicMock,
        mock_heartbeat: MagicMock,
        mock_iamq_register: MagicMock,
        settings: PipelineSettings,
    ) -> None:
        import pipeline_runner.scheduler as sched

        mock_load_state.return_value = {}
        mock_register.return_value = []

        # Set _shutdown to True after first run_pending so loop exits
        call_count = 0

        def set_shutdown(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count >= 1:
                sched._shutdown = True

        mock_run_pending.side_effect = set_shutdown

        old_shutdown = sched._shutdown
        try:
            sched._shutdown = False
            with pytest.raises(SystemExit):
                from pipeline_runner.scheduler import run_scheduler

                run_scheduler(settings)
        finally:
            sched._shutdown = old_shutdown
            schedule_lib.clear()

    @patch("pipeline_runner.scheduler.iamq_register")
    @patch("pipeline_runner.scheduler.register_schedule")
    @patch("pipeline_runner.scheduler._load_state")
    def test_scheduler_uses_default_settings_when_none(
        self,
        mock_load_state: MagicMock,
        mock_register: MagicMock,
        mock_iamq_register: MagicMock,
    ) -> None:
        import pipeline_runner.scheduler as sched

        mock_load_state.return_value = {}
        mock_register.return_value = []

        old_shutdown = sched._shutdown
        call_count = 0

        def set_shutdown():
            nonlocal call_count
            call_count += 1
            sched._shutdown = True

        try:
            sched._shutdown = False
            with patch("pipeline_runner.scheduler.schedule.run_pending", side_effect=set_shutdown):
                with patch("pipeline_runner.scheduler.time.sleep"):
                    with patch("pipeline_runner.scheduler.schedule.next_run", return_value="now"):
                        with pytest.raises(SystemExit):
                            from pipeline_runner.scheduler import run_scheduler

                            run_scheduler(None)  # Should use default PipelineSettings
        finally:
            sched._shutdown = old_shutdown
            schedule_lib.clear()
