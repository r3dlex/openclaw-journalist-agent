"""Telegram notification step — send pipeline output to a Telegram chat.

Sends the generated content (briefing, weather, article) to a configured
Telegram bot chat. Credentials are resolved from ~/.openclaw/openclaw.json
via the agent's binding (agentId → accountId → botToken + chatId).
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from pipeline_runner.config import PipelineSettings

logger = logging.getLogger(__name__)

# Telegram message length limit
MAX_MESSAGE_LENGTH = 4096


class TelegramNotifyStep:
    """Send pipeline output to Telegram.

    Context in:  briefing or weather_briefing or content (str)
    Context out: telegram_sent (bool), telegram_message_id (int | None)
    """

    name = "telegram_notify"

    def should_run(self, context: dict[str, Any]) -> bool:
        settings: PipelineSettings = context.get("settings", PipelineSettings())
        if not settings.telegram_bot_token or not settings.telegram_chat_id:
            logger.debug("Telegram not configured, skipping notification")
            return False
        return "briefing" in context or "weather_briefing" in context or "content" in context

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        settings: PipelineSettings = context.get("settings", PipelineSettings())

        # Determine content to send
        content = (
            context.get("briefing") or context.get("weather_briefing") or context.get("content", "")
        )

        if not content:
            logger.warning("No content to send to Telegram")
            context["telegram_sent"] = False
            context["telegram_message_id"] = None
            return context

        pipeline_name = context.get("pipeline_name", "unknown")

        # Truncate if needed (Telegram limit is 4096 chars)
        if len(content) > MAX_MESSAGE_LENGTH:
            truncated = content[: MAX_MESSAGE_LENGTH - 100]
            content = truncated + f"\n\n... (truncated, full report in log/{pipeline_name})"

        url = f"https://api.telegram.org/bot{settings.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": settings.telegram_chat_id,
            "text": content,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        }

        try:
            response = requests.post(url, json=payload, timeout=settings.request_timeout)
            response.raise_for_status()
            result = response.json()

            if result.get("ok"):
                message_id = result.get("result", {}).get("message_id")
                context["telegram_sent"] = True
                context["telegram_message_id"] = message_id
                logger.info(
                    "Telegram notification sent for %s (message_id=%s)",
                    pipeline_name,
                    message_id,
                )
            else:
                context["telegram_sent"] = False
                context["telegram_message_id"] = None
                logger.error("Telegram API error: %s", result.get("description", "unknown"))
        except Exception:
            context["telegram_sent"] = False
            context["telegram_message_id"] = None
            logger.exception("Failed to send Telegram notification")

        return context
