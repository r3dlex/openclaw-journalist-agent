"""Configuration management for pipelines.

Loads settings from environment variables and config files.
All sensitive values come from .env (never hardcoded).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

from pydantic import Field
from pydantic_settings import BaseSettings


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

    # Telegram notifications
    telegram_bot_token: str = Field(default="", alias="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: str = Field(default="", alias="TELEGRAM_CHAT_ID")

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
