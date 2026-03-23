"""Configuration management for pipelines.

Loads settings from environment variables and config files.
Telegram credentials are resolved from ~/.openclaw/openclaw.json
(the central OpenClaw config) rather than per-agent .env files.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, cast

from pydantic import Field
from pydantic_settings import BaseSettings

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# OpenClaw config resolver — reads Telegram credentials from the central
# ~/.openclaw/openclaw.json instead of per-agent env vars.
# ---------------------------------------------------------------------------

_OPENCLAW_CONFIG = Path.home() / ".openclaw" / "openclaw.json"
_OPENCLAW_CREDENTIALS = Path.home() / ".openclaw" / "credentials"


def _resolve_telegram(agent_id: str) -> tuple[str, str]:
    """Resolve (bot_token, chat_id) for *agent_id* from ~/.openclaw/openclaw.json.

    Lookup chain:
      1. bindings[] → find entry where agentId == agent_id → accountId
      2. channels.telegram.accounts[accountId].botToken
      3. credentials/telegram-{accountId}-allowFrom.json → first allowFrom entry
    Returns ("", "") if anything is missing so callers degrade gracefully.
    """
    try:
        cfg = json.loads(_OPENCLAW_CONFIG.read_text())
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        _log.debug("openclaw config not found or invalid: %s", exc)
        return "", ""

    # 1. Resolve binding → telegram accountId
    account_id = ""
    for binding in cfg.get("bindings", []):
        match = binding.get("match", {})
        if (
            binding.get("agentId") == agent_id
            and match.get("channel") == "telegram"
        ):
            account_id = match.get("accountId", "")
            break
    if not account_id:
        _log.debug("no telegram binding for agent %s", agent_id)
        return "", ""

    # 2. Resolve botToken
    accounts = cfg.get("channels", {}).get("telegram", {}).get("accounts", {})
    bot_token = accounts.get(account_id, {}).get("botToken", "")
    if not bot_token:
        _log.debug("no botToken for account %s", account_id)
        return "", ""

    # 3. Resolve chatId from allowFrom credentials
    chat_id = ""
    allow_file = _OPENCLAW_CREDENTIALS / f"telegram-{account_id}-allowFrom.json"
    try:
        allow_data = json.loads(allow_file.read_text())
        allow_list = allow_data.get("allowFrom", [])
        if allow_list:
            chat_id = str(allow_list[0])
    except (FileNotFoundError, json.JSONDecodeError):
        _log.debug("no allowFrom file for %s", account_id)

    return bot_token, chat_id


class PipelineSettings(BaseSettings):
    """Pipeline configuration loaded from environment variables."""

    # Paths
    journalist_data_dir: Path = Field(default=Path("."), alias="JOURNALIST_DATA_DIR")
    librarian_agent_workspace: Path = Field(default=Path(""), alias="LIBRARIAN_AGENT_WORKSPACE")
    feeds_file: Path = Field(default=Path("config/feeds.json"), alias="FEEDS_FILE")
    workspace_dir: Path = Field(default=Path("."), alias="JOURNALIST_WORKSPACE_DIR")

    # Weather
    weather_location: str = Field(default="Stuttgart", alias="WEATHER_LOCATION")
    weather_country: str = Field(default="DE", alias="WEATHER_COUNTRY")

    # Network
    request_timeout: int = Field(default=15, alias="REQUEST_TIMEOUT")

    # Optional API keys
    news_api_key: str = Field(default="", alias="NEWS_API_KEY")

    # Inter-Agent Message Queue (IAMQ)
    iamq_http_url: str = Field(default="http://127.0.0.1:18790", alias="IAMQ_HTTP_URL")

    # Mounted path for librarian workspace (when running in Docker)
    librarian_workspace_mount: Path = Field(default=Path(""), alias="LIBRARIAN_WORKSPACE_MOUNT")
    iamq_agent_id: str = Field(default="journalist_agent", alias="IAMQ_AGENT_ID")

    @property
    def telegram_bot_token(self) -> str:
        """Resolved from ~/.openclaw/openclaw.json (not env vars)."""
        token, _ = _resolve_telegram(self.iamq_agent_id)
        return token

    @property
    def telegram_chat_id(self) -> str:
        """Resolved from ~/.openclaw/openclaw.json credentials."""
        _, chat_id = _resolve_telegram(self.iamq_agent_id)
        return chat_id

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def log_dir(self) -> Path:
        """Return the log directory, creating it if necessary."""
        path = self.journalist_data_dir / "log"
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def reports_dir(self) -> Path:
        """Return the reports directory, creating it if necessary."""
        path = self.journalist_data_dir / "reports"
        path.mkdir(parents=True, exist_ok=True)
        return path


class FeedConfig:
    """Feed configuration loaded from feeds.json."""

    def __init__(self, config_path: Path) -> None:
        self._path = config_path
        self._data: dict[str, Any] = {}
        self.reload()

    def reload(self) -> None:
        """Reload configuration from disk."""
        with open(self._path) as f:
            self._data = json.load(f)

    @property
    def categories(self) -> dict[str, list[str]]:
        """Return feed categories mapping."""
        result: dict[str, list[str]] = self._data.get("categories", {})
        return result

    @property
    def domains(self) -> dict[str, dict[str, Any]]:
        """Return domain groupings for categories.

        Each domain maps to:
            label (str): Human-readable name
            priority (int): Domain priority (1-10)
            categories (list[str]): Category keys belonging to this domain
        """
        result: dict[str, dict[str, Any]] = self._data.get("domains", {})
        return result

    @property
    def domain_for_category(self) -> dict[str, str]:
        """Return a reverse mapping: category -> domain key."""
        mapping: dict[str, str] = {}
        for domain_key, domain_info in self.domains.items():
            for cat in domain_info.get("categories", []):
                mapping[cat] = domain_key
        return mapping

    @property
    def domain_priority(self) -> dict[str, int]:
        """Return domain key -> priority mapping."""
        return {key: int(info.get("priority", 5)) for key, info in self.domains.items()}

    @property
    def important_keywords(self) -> list[str]:
        """Return importance scoring keywords."""
        result: list[str] = self._data.get("important_keywords", [])
        return result

    @property
    def settings(self) -> dict[str, Any]:
        """Return feed settings."""
        result: dict[str, Any] = self._data.get("settings", {})
        return result

    @property
    def max_entries_per_feed(self) -> int:
        return cast(int, self.settings.get("max_entries_per_feed", 5))

    @property
    def importance_threshold(self) -> int:
        return cast(int, self.settings.get("importance_threshold_for_detail", 3))

    @property
    def max_concurrent_fetchers(self) -> int:
        return cast(int, self.settings.get("max_concurrent_fetchers", 10))

    @property
    def article_max_chars(self) -> int:
        return cast(int, self.settings.get("article_max_chars", 2000))
