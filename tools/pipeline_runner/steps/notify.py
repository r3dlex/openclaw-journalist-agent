"""Telegram notification step — sends briefing to user via Telegram Bot API."""

from __future__ import annotations

import logging
import os

import requests

logger = logging.getLogger(__name__)

MAX_MESSAGE_LENGTH = 4000


def _resolve_token() -> str | None:
    """Resolve the Telegram bot token.

    Priority:
    1. TELEGRAM_BOT_TOKEN env var (for explicit configuration)
    2. OpenClaw config at ~/.openclaw/openclaw.json (host machine only)

    Returns None if no token is found.
    """
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if token:
        return token

    # Try to read from OpenClaw config on the host machine
    openclaw_config_path = os.path.expanduser("~/.openclaw/openclaw.json")
    if openclaw_config_path:
        try:
            import json

            with open(openclaw_config_path) as f:
                config = json.load(f)
            channels = config.get("channels", {})
            default_telegram = channels.get("telegram", {}).get("accounts", {}).get("default", {})
            return default_telegram.get("botToken")
        except Exception:
            pass

    return None


def _resolve_chat_id() -> str | None:
    """Resolve the Telegram chat ID.

    Priority:
    1. TELEGRAM_CHAT_ID env var

    Returns None if no chat ID is found.
    """
    return os.environ.get("TELEGRAM_CHAT_ID")


class TelegramNotifyStep:
    """Sends the generated briefing to the user via the Telegram Bot API.

    Uses the OpenClaw-configured default Telegram bot if no explicit
    credentials are provided via environment variables.
    """

    name = "telegram_notify"

    def should_run(self, context: dict) -> bool:
        """Run if we have both a token and chat ID."""
        token = _resolve_token()
        chat_id = _resolve_chat_id()
        if not token:
            logger.warning("Step 'telegram_notify' skipped: no bot token found")
            return False
        if not chat_id:
            logger.warning("Step 'telegram_notify' skipped: no chat_id found")
            return False
        return True

    def execute(self, context: dict) -> dict:
        """Send the briefing to Telegram. Returns context for pipeline continuity."""
        token = _resolve_token()
        chat_id = _resolve_chat_id()

        content: str = context.get("briefing", "")
        if not content:
            return context

        # Truncate if needed (Telegram message limit is ~4096 chars)
        if len(content) > MAX_MESSAGE_LENGTH:
            content = content[:MAX_MESSAGE_LENGTH - 50] + "\n\n[...] (truncated)"

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        try:
            resp = requests.post(
                url,
                json={"chat_id": chat_id, "text": content, "parse_mode": "Markdown"},
                timeout=30,
            )
            resp.raise_for_status()
            logger.info("Briefing sent to Telegram successfully")
            return context
        except requests.exceptions.HTTPError as e:
            logger.error(f"Telegram API error: {e.response.status_code} {e.response.text}")
            return context
        except Exception as e:
            logger.error(f"Telegram notification failed: {e}")
            return context
