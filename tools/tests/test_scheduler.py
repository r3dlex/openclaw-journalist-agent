"""Tests for the pipeline scheduler."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import schedule as schedule_lib

from pipeline_runner.config import PipelineSettings
from pipeline_runner.scheduler import register_schedule


class TestRegisterSchedule:
    def setup_method(self) -> None:
        """Clear the schedule before each test."""
        schedule_lib.clear()

    def teardown_method(self) -> None:
        """Clear the schedule after each test."""
        schedule_lib.clear()

    def test_registers_seven_tasks(self, settings: PipelineSettings) -> None:
        tasks = register_schedule(settings)
        assert len(tasks) == 7

    def test_task_names(self, settings: PipelineSettings) -> None:
        tasks = register_schedule(settings)
        names = [t.name for t in tasks]
        assert "Morning briefing" in names
        assert "News update" in names
        assert "Midday weather" in names
        assert "Afternoon briefing" in names
        assert "Afternoon weather" in names
        assert "Evening briefing" in names
        assert "Weekly weather" in names

    def test_schedule_jobs_registered(self, settings: PipelineSettings) -> None:
        register_schedule(settings)
        # schedule library should have 7 jobs
        assert len(schedule_lib.get_jobs()) == 7

    def test_task_schedule_descriptions(self, settings: PipelineSettings) -> None:
        tasks = register_schedule(settings)
        descs = {t.name: t.schedule_desc for t in tasks}
        assert descs["Morning briefing"] == "daily 06:00"
        assert descs["Weekly weather"] == "sunday 21:00"

    def test_task_pipeline_functions(self, settings: PipelineSettings) -> None:
        tasks = register_schedule(settings)
        fns = {t.name: t.pipeline_fn for t in tasks}
        assert fns["Morning briefing"] == "news + weather 6am"
        assert fns["News update"] == "news"
        assert fns["Midday weather"] == "weather 12pm"


class TestSchedulerHelpers:
    @patch("pipeline_runner.scheduler.run_news_pipeline")
    def test_run_news_calls_pipeline(
        self, mock_news: MagicMock, settings: PipelineSettings
    ) -> None:
        from pipeline_runner.scheduler import _run_news

        mock_news.return_value = "# Briefing\nLine 1\nLine 2"
        _run_news(settings)
        mock_news.assert_called_once_with(settings)

    @patch("pipeline_runner.scheduler.run_weather_pipeline")
    def test_run_weather_calls_pipeline(
        self, mock_weather: MagicMock, settings: PipelineSettings
    ) -> None:
        from pipeline_runner.scheduler import _run_weather

        mock_weather.return_value = "# Weather\nLine 1"
        _run_weather("6am", settings)
        mock_weather.assert_called_once_with("6am", settings)

    @patch("pipeline_runner.scheduler.run_news_pipeline")
    def test_run_news_handles_exception(
        self, mock_news: MagicMock, settings: PipelineSettings
    ) -> None:
        from pipeline_runner.scheduler import _run_news

        mock_news.side_effect = RuntimeError("feed timeout")
        # Should not raise — exceptions are logged, not propagated
        _run_news(settings)

    @patch("pipeline_runner.scheduler.run_weather_pipeline")
    @patch("pipeline_runner.scheduler.run_news_pipeline")
    def test_run_news_and_weather(
        self,
        mock_news: MagicMock,
        mock_weather: MagicMock,
        settings: PipelineSettings,
    ) -> None:
        from pipeline_runner.scheduler import _run_news_and_weather

        mock_news.return_value = "news"
        mock_weather.return_value = "weather"
        _run_news_and_weather("6am", settings)
        mock_news.assert_called_once_with(settings)
        mock_weather.assert_called_once_with("6am", settings)
