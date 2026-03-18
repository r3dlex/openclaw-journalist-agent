"""Librarian handoff step — write outputs and notify the Librarian agent.

Implements the inter-agent collaboration protocol defined in ARCH-004.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

from pipeline_runner.config import PipelineSettings

logger = logging.getLogger(__name__)


class LibrarianHandoffStep:
    """Write pipeline output to log directory and prepare handoff metadata.

    Context in:  briefing or weather_briefing (str), pipeline name
    Context out: handoff_path (Path), handoff_metadata (dict)
    """

    name = "librarian_handoff"

    def should_run(self, context: dict[str, Any]) -> bool:
        return "briefing" in context or "weather_briefing" in context

    def execute(self, context: dict[str, Any]) -> dict[str, Any]:
        settings: PipelineSettings = context.get("settings", PipelineSettings())
        now = datetime.now(tz=UTC)
        timestamp = now.strftime("%Y%m%d_%H%M%S")
        pipeline_name = context.get("pipeline_name", "unknown")

        # Determine content to hand off
        content = context.get("briefing") or context.get("weather_briefing", "")

        # Write to log directory
        log_dir = settings.log_dir
        filename = f"{timestamp}_{pipeline_name}.md"
        output_path = log_dir / filename
        output_path.write_text(content, encoding="utf-8")
        logger.info("Wrote output to %s", output_path)

        # Write handoff metadata
        metadata = {
            "source_agent": "journalist",
            "target_agent": "librarian",
            "pipeline": pipeline_name,
            "timestamp": now.isoformat(),
            "output_file": str(output_path),
            "output_size_bytes": len(content.encode("utf-8")),
        }

        metadata_path = log_dir / f"{timestamp}_{pipeline_name}.meta.json"
        metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")

        # If librarian workspace is configured, write a handoff signal
        librarian_ws = settings.librarian_agent_workspace
        if librarian_ws and librarian_ws.exists():
            inbox = librarian_ws / "inbox"
            inbox.mkdir(parents=True, exist_ok=True)
            signal_path = inbox / f"journalist_{timestamp}.json"
            signal_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
            logger.info("Handoff signal written to %s", signal_path)
        else:
            logger.warning(
                "Librarian workspace not configured or not found: %s", librarian_ws
            )

        context["handoff_path"] = output_path
        context["handoff_metadata"] = metadata
        return context
