"""Inter-Agent Message Queue (IAMQ) step — announce pipeline results to other agents.

Integrates with the OpenClaw IAMQ service (Elixir/OTP) for agent-to-agent
communication. Sends pipeline completion announcements and checks the
journalist's inbox for pending tasks from other agents.

The IAMQ runs at IAMQ_HTTP_URL (default: http://127.0.0.1:18790).
See openclaw-inter-agent-message-queue/spec/API.md for the full protocol.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from pipeline_runner.config import PipelineSettings

logger = logging.getLogger(__name__)

AGENT_ID = "journalist_agent"


class IAMQAnnounceStep:
    """Announce pipeline completion to the IAMQ.

    Sends a message to ``broadcast`` (all agents) summarising the pipeline
    output.  Gracefully degrades when the IAMQ service is unreachable —
    a pipeline should never fail because the message queue is down.

    Context in:  briefing | weather_briefing | content (str), pipeline_name
    Context out: iamq_announced (bool), iamq_message_id (str | None)
    """

    name = "iamq_announce"

    def should_run(self, context: dict[str, Any]) -> bool:
        settings: PipelineSettings = context.get("settings", PipelineSettings())
        if not settings.iamq_http_url:
            return False
        return "briefing" in context or "weather_briefing" in context or "content" in context

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        settings: PipelineSettings = context.get("settings", PipelineSettings())
        pipeline_name = context.get("pipeline_name", "unknown")
        content = (
            context.get("briefing") or context.get("weather_briefing") or context.get("content", "")
        )

        if not content:
            context["iamq_announced"] = False
            context["iamq_message_id"] = None
            return context

        # Truncate for MQ — full content goes via handoff files
        summary = content[:500]
        if len(content) > 500:
            summary += "\n\n... (truncated, full output in log/)"

        payload = {
            "from": AGENT_ID,
            "to": "broadcast",
            "type": "info",
            "priority": "NORMAL",
            "subject": f"Pipeline completed: {pipeline_name}",
            "body": summary,
        }

        try:
            url = f"{settings.iamq_http_url}/send"
            resp = requests.post(url, json=payload, timeout=5)
            resp.raise_for_status()
            data = resp.json()
            msg_id = data.get("id", data.get("message_id"))
            context["iamq_announced"] = True
            context["iamq_message_id"] = msg_id
            logger.info("IAMQ: announced '%s' (id=%s)", pipeline_name, msg_id)
        except requests.ConnectionError:
            logger.warning("IAMQ: service unreachable at %s — skipping", settings.iamq_http_url)
            context["iamq_announced"] = False
            context["iamq_message_id"] = None
        except Exception:
            logger.warning("IAMQ: announce failed", exc_info=True)
            context["iamq_announced"] = False
            context["iamq_message_id"] = None

        return context


def iamq_register(settings: PipelineSettings) -> bool:
    """Register the journalist agent with the IAMQ service."""
    if not settings.iamq_http_url:
        return False
    try:
        url = f"{settings.iamq_http_url}/register"
        resp = requests.post(url, json={"agent_id": AGENT_ID}, timeout=5)
        resp.raise_for_status()
        logger.info("IAMQ: registered as '%s'", AGENT_ID)
        return True
    except Exception:
        logger.warning("IAMQ: registration failed", exc_info=True)
        return False


def iamq_heartbeat(settings: PipelineSettings) -> bool:
    """Send a heartbeat to the IAMQ service."""
    if not settings.iamq_http_url:
        return False
    try:
        url = f"{settings.iamq_http_url}/heartbeat"
        resp = requests.post(url, json={"agent_id": AGENT_ID}, timeout=5)
        resp.raise_for_status()
        return True
    except Exception:
        logger.debug("IAMQ: heartbeat failed", exc_info=True)
        return False


def iamq_check_inbox(settings: PipelineSettings) -> list[dict[str, Any]]:
    """Fetch unread messages from the journalist's IAMQ inbox."""
    if not settings.iamq_http_url:
        return []
    try:
        url = f"{settings.iamq_http_url}/inbox/{AGENT_ID}?status=unread"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        messages: list[dict[str, Any]] = resp.json().get("messages", resp.json())
        if isinstance(messages, list):
            return messages
        return []
    except Exception:
        logger.debug("IAMQ: inbox check failed", exc_info=True)
        return []


def iamq_list_agents(settings: PipelineSettings) -> list[dict[str, Any]]:
    """List all agents registered with the IAMQ service."""
    if not settings.iamq_http_url:
        return []
    try:
        url = f"{settings.iamq_http_url}/agents"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        agents: list[dict[str, Any]] = resp.json().get("agents", resp.json())
        if isinstance(agents, list):
            return agents
        return []
    except Exception:
        logger.debug("IAMQ: agent list failed", exc_info=True)
        return []


def iamq_send_message(
    settings: PipelineSettings,
    *,
    to: str,
    subject: str,
    body: str,
    priority: str = "NORMAL",
    msg_type: str = "info",
) -> str | None:
    """Send a direct message to another agent via IAMQ. Returns message ID."""
    if not settings.iamq_http_url:
        return None
    try:
        url = f"{settings.iamq_http_url}/send"
        payload = {
            "from": AGENT_ID,
            "to": to,
            "type": msg_type,
            "priority": priority,
            "subject": subject,
            "body": body,
        }
        resp = requests.post(url, json=payload, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        msg_id: str | None = data.get("id", data.get("message_id"))
        logger.info("IAMQ: sent message to '%s' (id=%s)", to, msg_id)
        return msg_id
    except Exception:
        logger.warning("IAMQ: send to '%s' failed", to, exc_info=True)
        return None
