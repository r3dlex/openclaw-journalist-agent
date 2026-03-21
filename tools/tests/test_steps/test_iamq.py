"""Tests for the IAMQ (Inter-Agent Message Queue) step."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pipeline_runner.config import PipelineSettings
from pipeline_runner.steps.iamq import (
    IAMQAnnounceStep,
    iamq_check_inbox,
    iamq_heartbeat,
    iamq_list_agents,
    iamq_register,
    iamq_send_message,
)


class TestIAMQAnnounceStep:
    def test_should_not_run_without_url(self) -> None:
        step = IAMQAnnounceStep()
        settings = PipelineSettings(IAMQ_HTTP_URL="")  # type: ignore[call-arg]
        ctx: dict[str, object] = {"briefing": "hello", "settings": settings}
        assert step.should_run(ctx) is False

    def test_should_not_run_without_content(self) -> None:
        step = IAMQAnnounceStep()
        settings = PipelineSettings(IAMQ_HTTP_URL="http://localhost:18790")  # type: ignore[call-arg]
        ctx: dict[str, object] = {"settings": settings}
        assert step.should_run(ctx) is False

    def test_should_run_with_briefing(self) -> None:
        step = IAMQAnnounceStep()
        settings = PipelineSettings(IAMQ_HTTP_URL="http://localhost:18790")  # type: ignore[call-arg]
        ctx: dict[str, object] = {"briefing": "hello", "settings": settings}
        assert step.should_run(ctx) is True

    def test_should_run_with_weather_briefing(self) -> None:
        step = IAMQAnnounceStep()
        settings = PipelineSettings(IAMQ_HTTP_URL="http://localhost:18790")  # type: ignore[call-arg]
        ctx: dict[str, object] = {"weather_briefing": "sunny", "settings": settings}
        assert step.should_run(ctx) is True

    def test_should_run_with_content(self) -> None:
        step = IAMQAnnounceStep()
        settings = PipelineSettings(IAMQ_HTTP_URL="http://localhost:18790")  # type: ignore[call-arg]
        ctx: dict[str, object] = {"content": "article text", "settings": settings}
        assert step.should_run(ctx) is True

    @patch("pipeline_runner.steps.iamq.requests.post")
    def test_announces_briefing(self, mock_post: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "msg-123"}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        step = IAMQAnnounceStep()
        settings = PipelineSettings(IAMQ_HTTP_URL="http://localhost:18790")  # type: ignore[call-arg]
        ctx: dict[str, object] = {
            "briefing": "Test briefing content",
            "pipeline_name": "news_briefing",
            "settings": settings,
        }
        result = step.execute(ctx)

        assert result["iamq_announced"] is True
        assert result["iamq_message_id"] == "msg-123"
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert payload["from"] == "journalist_agent"
        assert payload["to"] == "broadcast"
        assert "news_briefing" in payload["subject"]

    @patch("pipeline_runner.steps.iamq.requests.post")
    def test_handles_connection_error(self, mock_post: MagicMock) -> None:
        import requests

        mock_post.side_effect = requests.ConnectionError("refused")

        step = IAMQAnnounceStep()
        settings = PipelineSettings(IAMQ_HTTP_URL="http://localhost:18790")  # type: ignore[call-arg]
        ctx: dict[str, object] = {
            "briefing": "content",
            "pipeline_name": "test",
            "settings": settings,
        }
        result = step.execute(ctx)

        assert result["iamq_announced"] is False
        assert result["iamq_message_id"] is None

    @patch("pipeline_runner.steps.iamq.requests.post")
    def test_truncates_long_content(self, mock_post: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "msg-456"}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        step = IAMQAnnounceStep()
        settings = PipelineSettings(IAMQ_HTTP_URL="http://localhost:18790")  # type: ignore[call-arg]
        long_content = "x" * 1000
        ctx: dict[str, object] = {
            "briefing": long_content,
            "pipeline_name": "test",
            "settings": settings,
        }
        step.execute(ctx)

        call_kwargs = mock_post.call_args
        payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert len(payload["body"]) < 600  # 500 + truncation notice

    def test_empty_content_sets_announced_false(self) -> None:
        step = IAMQAnnounceStep()
        settings = PipelineSettings(IAMQ_HTTP_URL="http://localhost:18790")  # type: ignore[call-arg]
        ctx: dict[str, object] = {
            "briefing": "",
            "pipeline_name": "test",
            "settings": settings,
        }
        result = step.execute(ctx)
        assert result["iamq_announced"] is False


class TestIAMQHelpers:
    @patch("pipeline_runner.steps.iamq.requests.post")
    def test_register(self, mock_post: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        settings = PipelineSettings(IAMQ_HTTP_URL="http://localhost:18790")  # type: ignore[call-arg]
        assert iamq_register(settings) is True
        mock_post.assert_called_once()

    def test_register_no_url(self) -> None:
        settings = PipelineSettings(IAMQ_HTTP_URL="")  # type: ignore[call-arg]
        assert iamq_register(settings) is False

    @patch("pipeline_runner.steps.iamq.requests.post")
    def test_heartbeat(self, mock_post: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        settings = PipelineSettings(IAMQ_HTTP_URL="http://localhost:18790")  # type: ignore[call-arg]
        assert iamq_heartbeat(settings) is True

    @patch("pipeline_runner.steps.iamq.requests.get")
    def test_check_inbox(self, mock_get: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"messages": [{"id": "m1", "subject": "test"}]}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        settings = PipelineSettings(IAMQ_HTTP_URL="http://localhost:18790")  # type: ignore[call-arg]
        messages = iamq_check_inbox(settings)
        assert len(messages) == 1
        assert messages[0]["id"] == "m1"

    @patch("pipeline_runner.steps.iamq.requests.get")
    def test_list_agents(self, mock_get: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "agents": [
                {"agent_id": "journalist_agent"},
                {"agent_id": "librarian_agent"},
            ]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        settings = PipelineSettings(IAMQ_HTTP_URL="http://localhost:18790")  # type: ignore[call-arg]
        agents = iamq_list_agents(settings)
        assert len(agents) == 2

    @patch("pipeline_runner.steps.iamq.requests.post")
    def test_send_message(self, mock_post: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "msg-789"}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        settings = PipelineSettings(IAMQ_HTTP_URL="http://localhost:18790")  # type: ignore[call-arg]
        msg_id = iamq_send_message(
            settings,
            to="librarian_agent",
            subject="Handoff ready",
            body="News briefing completed",
        )
        assert msg_id == "msg-789"

    def test_send_message_no_url(self) -> None:
        settings = PipelineSettings(IAMQ_HTTP_URL="")  # type: ignore[call-arg]
        msg_id = iamq_send_message(
            settings, to="librarian_agent", subject="test", body="test"
        )
        assert msg_id is None
