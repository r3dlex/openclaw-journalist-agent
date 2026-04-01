"""Additional IAMQ tests to cover remaining gaps."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from pipeline_runner.config import PipelineSettings
from pipeline_runner.steps.iamq import (
    IAMQAnnounceStep,
    iamq_check_inbox,
    iamq_heartbeat,
    iamq_list_agents,
    iamq_mark_message,
    iamq_register,
    iamq_send_message,
)


class TestIAMQAnnounceStepExtra:
    @patch("pipeline_runner.steps.iamq.requests.post")
    def test_announce_uses_weather_briefing_when_no_briefing(self, mock_post: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"id": "msg-w1"}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        step = IAMQAnnounceStep()
        settings = PipelineSettings(IAMQ_HTTP_URL="http://localhost:18790")  # type: ignore[call-arg]
        ctx = {
            "weather_briefing": "# Weather\nSunny",
            "pipeline_name": "weather_briefing",
            "settings": settings,
        }
        result = step.execute(ctx)
        assert result["iamq_announced"] is True

    @patch("pipeline_runner.steps.iamq.requests.post")
    def test_announce_uses_content_as_fallback(self, mock_post: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"message_id": "msg-c1"}
        mock_resp.raise_for_status = MagicMock()
        mock_post.return_value = mock_resp

        step = IAMQAnnounceStep()
        settings = PipelineSettings(IAMQ_HTTP_URL="http://localhost:18790")  # type: ignore[call-arg]
        ctx = {
            "content": "Article content here",
            "pipeline_name": "article_extraction",
            "settings": settings,
        }
        result = step.execute(ctx)
        assert result["iamq_announced"] is True
        # message_id key fallback
        assert result["iamq_message_id"] == "msg-c1"

    @patch("pipeline_runner.steps.iamq.requests.post")
    def test_announce_handles_general_exception(self, mock_post: MagicMock) -> None:
        mock_post.side_effect = Exception("Unexpected error")

        step = IAMQAnnounceStep()
        settings = PipelineSettings(IAMQ_HTTP_URL="http://localhost:18790")  # type: ignore[call-arg]
        ctx = {
            "briefing": "content",
            "pipeline_name": "test",
            "settings": settings,
        }
        result = step.execute(ctx)

        # Should not raise; graceful degradation
        assert result["iamq_announced"] is False
        assert result["iamq_message_id"] is None


class TestIAMQHelperEdgeCases:
    def test_heartbeat_no_url(self) -> None:
        settings = PipelineSettings(IAMQ_HTTP_URL="")  # type: ignore[call-arg]
        assert iamq_heartbeat(settings) is False

    @patch("pipeline_runner.steps.iamq.requests.post")
    def test_heartbeat_handles_exception(self, mock_post: MagicMock) -> None:
        mock_post.side_effect = Exception("timeout")
        settings = PipelineSettings(IAMQ_HTTP_URL="http://localhost:18790")  # type: ignore[call-arg]
        # Should not raise
        result = iamq_heartbeat(settings)
        assert result is False

    def test_check_inbox_no_url(self) -> None:
        settings = PipelineSettings(IAMQ_HTTP_URL="")  # type: ignore[call-arg]
        result = iamq_check_inbox(settings)
        assert result == []

    @patch("pipeline_runner.steps.iamq.requests.get")
    def test_check_inbox_handles_exception(self, mock_get: MagicMock) -> None:
        mock_get.side_effect = Exception("conn refused")
        settings = PipelineSettings(IAMQ_HTTP_URL="http://localhost:18790")  # type: ignore[call-arg]
        result = iamq_check_inbox(settings)
        assert result == []

    @patch("pipeline_runner.steps.iamq.requests.get")
    def test_check_inbox_returns_empty_on_malformed_response(self, mock_get: MagicMock) -> None:
        # API returns something unexpected — should degrade gracefully
        mock_resp = MagicMock()
        # Simulate a response that raises when .get() is called (returns a list)
        mock_resp.json.return_value = {"messages": [{"id": "m1"}]}
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        settings = PipelineSettings(IAMQ_HTTP_URL="http://localhost:18790")  # type: ignore[call-arg]
        messages = iamq_check_inbox(settings)
        # Should parse the "messages" key correctly
        assert messages == [{"id": "m1"}]

    def test_list_agents_no_url(self) -> None:
        settings = PipelineSettings(IAMQ_HTTP_URL="")  # type: ignore[call-arg]
        result = iamq_list_agents(settings)
        assert result == []

    @patch("pipeline_runner.steps.iamq.requests.get")
    def test_list_agents_handles_exception(self, mock_get: MagicMock) -> None:
        mock_get.side_effect = Exception("timeout")
        settings = PipelineSettings(IAMQ_HTTP_URL="http://localhost:18790")  # type: ignore[call-arg]
        result = iamq_list_agents(settings)
        assert result == []

    @patch("pipeline_runner.steps.iamq.requests.get")
    def test_list_agents_returns_from_agents_key(self, mock_get: MagicMock) -> None:
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "agents": [{"agent_id": "a1"}, {"agent_id": "a2"}]
        }
        mock_resp.raise_for_status = MagicMock()
        mock_get.return_value = mock_resp

        settings = PipelineSettings(IAMQ_HTTP_URL="http://localhost:18790")  # type: ignore[call-arg]
        agents = iamq_list_agents(settings)
        assert len(agents) == 2

    @patch("pipeline_runner.steps.iamq.requests.post")
    def test_register_handles_exception(self, mock_post: MagicMock) -> None:
        mock_post.side_effect = Exception("connection error")
        settings = PipelineSettings(IAMQ_HTTP_URL="http://localhost:18790")  # type: ignore[call-arg]
        result = iamq_register(settings)
        assert result is False

    def test_register_no_url_returns_false(self) -> None:
        settings = PipelineSettings(IAMQ_HTTP_URL="")  # type: ignore[call-arg]
        assert iamq_register(settings) is False

    @patch("pipeline_runner.steps.iamq.requests.post")
    def test_send_message_handles_exception(self, mock_post: MagicMock) -> None:
        mock_post.side_effect = Exception("timeout")
        settings = PipelineSettings(IAMQ_HTTP_URL="http://localhost:18790")  # type: ignore[call-arg]
        result = iamq_send_message(
            settings, to="librarian_agent", subject="test", body="hello"
        )
        assert result is None

    @patch("pipeline_runner.steps.iamq.requests.patch")
    def test_mark_message_handles_exception(self, mock_patch: MagicMock) -> None:
        mock_patch.side_effect = Exception("timeout")
        settings = PipelineSettings(IAMQ_HTTP_URL="http://localhost:18790")  # type: ignore[call-arg]
        result = iamq_mark_message(settings, "msg-123")
        assert result is False
