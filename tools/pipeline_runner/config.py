"""Configuration management for pipelines.

Loads settings from environment variables and config files.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, cast

from pydantic import Field
from pydantic_settings import BaseSettings

_log = logging.getLogger(__name__)


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
