"""Tests for the Telegram notification step."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pipeline_runner.config import PipelineSettings
from pipeline_runner.steps.notify import TelegramNotifyStep

# Patch _resolve_telegram so tests don't depend on ~/.openclaw/openclaw.json
_PATCH_RESOLVE = "pipeline_runner.config._resolve_telegram"


class TestTelegramNotifyStep:
    def _settings_with_telegram(self) -> PipelineSettings:
        """Return settings whose Telegram properties resolve to test values."""
        with patch(_PATCH_RESOLVE, return_value=("test-token", "12345")):
            return PipelineSettings()

    @patch(_PATCH_RESOLVE, return_value=("", ""))
    def test_should_not_run_without_config(self, _mock: MagicMock) -> None:
        step = TelegramNotifyStep()
        settings = PipelineSettings()
        ctx: dict[str, object] = {"briefing": "hello", "settings": settings}
        assert step.should_run(ctx) is False

    def test_should_run_with_config_and_briefing(self) -> None:
        step = TelegramNotifyStep()
        ctx: dict[str, object] = {
            "briefing": "hello",
            "settings": self._settings_with_telegram(),
        }
        with patch(_PATCH_RESOLVE, return_value=("test-token", "12345")):
            assert step.should_run(ctx) is True

    def test_should_run_with_weather_briefing(self) -> None:
        step = TelegramNotifyStep()
        ctx: dict[str, object] = {
            "weather_briefing": "sunny",
            "settings": self._settings_with_telegram(),
        }
        with patch(_PATCH_RESOLVE, return_value=("test-token", "12345")):
            assert step.should_run(ctx) is True

    def test_should_run_with_content(self) -> None:
        step = TelegramNotifyStep()
        ctx: dict[str, object] = {
            "content": "article text",
            "settings": self._settings_with_telegram(),
        }
        with patch(_PATCH_RESOLVE, return_value=("test-token", "12345")):
            assert step.should_run(ctx) is True

    def test_should_not_run_without_content(self) -> None:
        step = TelegramNotifyStep()
        ctx: dict[str, object] = {"settings": self._settings_with_telegram()}
        with patch(_PATCH_RESOLVE, return_value=("test-token", "12345")):
            assert step.should_run(ctx) is False

    @patch("pipeline_runner.steps.notify.requests.post")
    def test_sends_briefing(self, mock_post: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": True, "result": {"message_id": 42}}
        mock_post.return_value = mock_response

        step = TelegramNotifyStep()
        ctx: dict[str, object] = {
            "briefing": "Test briefing content",
            "settings": self._settings_with_telegram(),
            "pipeline_name": "news_briefing",
        }
        with patch(_PATCH_RESOLVE, return_value=("test-token", "12345")):
            result = step.execute(ctx)

        assert result["telegram_sent"] is True
        assert result["telegram_message_id"] == 42
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert "test-token" in call_kwargs.args[0]
        assert call_kwargs.kwargs["json"]["chat_id"] == "12345"
        assert call_kwargs.kwargs["json"]["text"] == "Test briefing content"

    @patch("pipeline_runner.steps.notify.requests.post")
    def test_handles_api_error(self, mock_post: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": False, "description": "Bad Request"}
        mock_post.return_value = mock_response

        step = TelegramNotifyStep()
        ctx: dict[str, object] = {
            "briefing": "Test",
            "settings": self._settings_with_telegram(),
        }
        with patch(_PATCH_RESOLVE, return_value=("test-token", "12345")):
            result = step.execute(ctx)

        assert result["telegram_sent"] is False
        assert result["telegram_message_id"] is None

    @patch("pipeline_runner.steps.notify.requests.post")
    def test_handles_network_error(self, mock_post: MagicMock) -> None:
        mock_post.side_effect = ConnectionError("network down")

        step = TelegramNotifyStep()
        ctx: dict[str, object] = {
            "briefing": "Test",
            "settings": self._settings_with_telegram(),
        }
        with patch(_PATCH_RESOLVE, return_value=("test-token", "12345")):
            result = step.execute(ctx)

        assert result["telegram_sent"] is False

    @patch("pipeline_runner.steps.notify.requests.post")
    def test_truncates_long_messages(self, mock_post: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = {"ok": True, "result": {"message_id": 99}}
        mock_post.return_value = mock_response

        step = TelegramNotifyStep()
        long_content = "x" * 5000
        ctx: dict[str, object] = {
            "briefing": long_content,
            "settings": self._settings_with_telegram(),
        }
        with patch(_PATCH_RESOLVE, return_value=("test-token", "12345")):
            step.execute(ctx)

        sent_text = mock_post.call_args.kwargs["json"]["text"]
        assert len(sent_text) <= 4096

    @patch(_PATCH_RESOLVE, return_value=("test-token", "12345"))
    def test_empty_content_sets_sent_false(self, _mock: MagicMock) -> None:
        step = TelegramNotifyStep()
        ctx: dict[str, object] = {
            "briefing": "",
            "weather_briefing": "",
            "content": "",
            "settings": PipelineSettings(),
        }
        result = step.execute(ctx)
        assert result["telegram_sent"] is False
