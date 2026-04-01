"""Tests for the Telegram notification step."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
import requests

from pipeline_runner.steps.notify import (
    MAX_MESSAGE_LENGTH,
    TelegramNotifyStep,
    _resolve_chat_id,
    _resolve_token,
)


class TestResolveToken:
    def test_env_var_takes_priority(self) -> None:
        with patch.dict(os.environ, {"TELEGRAM_BOT_TOKEN": "env_token_123"}):
            token = _resolve_token()
            assert token == "env_token_123"

    def test_returns_none_when_no_config(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            # Patch open to simulate missing openclaw config
            with patch("builtins.open", side_effect=FileNotFoundError):
                token = _resolve_token()
                assert token is None

    def test_reads_from_openclaw_config(self, tmp_path: Path) -> None:
        config = {
            "channels": {
                "telegram": {
                    "accounts": {
                        "default": {"botToken": "openclaw_token_456"}
                    }
                }
            }
        }
        config_file = tmp_path / "openclaw.json"
        config_file.write_text(json.dumps(config))

        with patch.dict(os.environ, {}, clear=True):
            with patch("os.path.expanduser", return_value=str(config_file)):
                token = _resolve_token()
                assert token == "openclaw_token_456"

    def test_returns_none_when_openclaw_config_missing_key(self, tmp_path: Path) -> None:
        config = {"channels": {}}
        config_file = tmp_path / "openclaw.json"
        config_file.write_text(json.dumps(config))

        with patch.dict(os.environ, {}, clear=True):
            with patch("os.path.expanduser", return_value=str(config_file)):
                token = _resolve_token()
                assert token is None

    def test_returns_none_on_invalid_json(self, tmp_path: Path) -> None:
        config_file = tmp_path / "openclaw.json"
        config_file.write_text("not valid json")

        with patch.dict(os.environ, {}, clear=True):
            with patch("os.path.expanduser", return_value=str(config_file)):
                token = _resolve_token()
                assert token is None


class TestResolveChatId:
    def test_returns_env_var(self) -> None:
        with patch.dict(os.environ, {"TELEGRAM_CHAT_ID": "123456"}):
            chat_id = _resolve_chat_id()
            assert chat_id == "123456"

    def test_returns_none_when_missing(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            chat_id = _resolve_chat_id()
            assert chat_id is None


class TestTelegramNotifyStep:
    def test_should_not_run_without_token(self) -> None:
        step = TelegramNotifyStep()
        with patch("pipeline_runner.steps.notify._resolve_token", return_value=None):
            with patch("pipeline_runner.steps.notify._resolve_chat_id", return_value="123"):
                assert step.should_run({}) is False

    def test_should_not_run_without_chat_id(self) -> None:
        step = TelegramNotifyStep()
        with patch("pipeline_runner.steps.notify._resolve_token", return_value="token"):
            with patch("pipeline_runner.steps.notify._resolve_chat_id", return_value=None):
                assert step.should_run({}) is False

    def test_should_run_with_both_credentials(self) -> None:
        step = TelegramNotifyStep()
        with patch("pipeline_runner.steps.notify._resolve_token", return_value="token"):
            with patch("pipeline_runner.steps.notify._resolve_chat_id", return_value="123"):
                assert step.should_run({}) is True

    @patch("pipeline_runner.steps.notify.requests.post")
    def test_sends_briefing(self, mock_post: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        step = TelegramNotifyStep()
        with patch("pipeline_runner.steps.notify._resolve_token", return_value="test_token"):
            with patch("pipeline_runner.steps.notify._resolve_chat_id", return_value="chat_999"):
                ctx = {"briefing": "# Test Briefing\nSome content"}
                result = step.execute(ctx)

        mock_post.assert_called_once()
        call_args = mock_post.call_args
        url = call_args[0][0]
        payload = call_args.kwargs.get("json") or call_args[1].get("json")
        assert "test_token" in url
        assert payload["chat_id"] == "chat_999"
        assert "Test Briefing" in payload["text"]
        assert payload["parse_mode"] == "Markdown"

    @patch("pipeline_runner.steps.notify.requests.post")
    def test_truncates_long_content(self, mock_post: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        step = TelegramNotifyStep()
        long_content = "x" * (MAX_MESSAGE_LENGTH + 500)

        with patch("pipeline_runner.steps.notify._resolve_token", return_value="tok"):
            with patch("pipeline_runner.steps.notify._resolve_chat_id", return_value="123"):
                step.execute({"briefing": long_content})

        call_args = mock_post.call_args
        payload = call_args.kwargs.get("json") or call_args[1].get("json")
        assert len(payload["text"]) <= MAX_MESSAGE_LENGTH
        assert "truncated" in payload["text"]

    @patch("pipeline_runner.steps.notify.requests.post")
    def test_returns_context_on_success(self, mock_post: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        step = TelegramNotifyStep()
        ctx = {"briefing": "Hello", "other_key": "preserved"}

        with patch("pipeline_runner.steps.notify._resolve_token", return_value="tok"):
            with patch("pipeline_runner.steps.notify._resolve_chat_id", return_value="123"):
                result = step.execute(ctx)

        assert result["other_key"] == "preserved"

    @patch("pipeline_runner.steps.notify.requests.post")
    def test_handles_http_error_gracefully(self, mock_post: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"
        http_error = requests.exceptions.HTTPError(response=mock_resp)
        mock_resp.raise_for_status.side_effect = http_error
        mock_post.return_value = mock_resp

        step = TelegramNotifyStep()
        ctx = {"briefing": "test"}

        with patch("pipeline_runner.steps.notify._resolve_token", return_value="bad_token"):
            with patch("pipeline_runner.steps.notify._resolve_chat_id", return_value="123"):
                result = step.execute(ctx)

        # Should not raise, just return context
        assert result is ctx

    @patch("pipeline_runner.steps.notify.requests.post")
    def test_handles_generic_exception_gracefully(self, mock_post: MagicMock) -> None:
        mock_post.side_effect = Exception("Network error")

        step = TelegramNotifyStep()
        ctx = {"briefing": "test content"}

        with patch("pipeline_runner.steps.notify._resolve_token", return_value="tok"):
            with patch("pipeline_runner.steps.notify._resolve_chat_id", return_value="123"):
                result = step.execute(ctx)

        # Should not raise
        assert result is ctx

    def test_returns_context_when_no_briefing(self) -> None:
        step = TelegramNotifyStep()
        ctx: dict = {}

        with patch("pipeline_runner.steps.notify._resolve_token", return_value="tok"):
            with patch("pipeline_runner.steps.notify._resolve_chat_id", return_value="123"):
                result = step.execute(ctx)

        assert result is ctx
