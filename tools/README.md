# Pipeline Runner

Zero-install Python pipeline runner for the Journalist agent.

## Quick Start

```bash
# Build and start the scheduler (recommended)
docker compose up -d scheduler

# Run ad-hoc commands via the scheduler (instant, no startup delay)
docker compose exec scheduler pipeline news
docker compose exec scheduler pipeline article https://example.com/story
docker compose exec scheduler pipeline weather 6am
docker compose exec scheduler pipeline validate

# One-shot alternative (cli profile, cold start each time)
docker compose run --rm --profile cli pipeline news

# Build and test (zero-install)
docker compose run --rm --profile test pipeline-test
```

## Architecture

Pipelines are built from composable **steps**. Each step receives a context dict
and returns an updated context dict. Steps can be skipped, retried, or chained.

```
FetchFeeds → ScoreImportance → FormatBriefing → LibrarianHandoff
```

See `spec/PIPELINES.md` for the full specification and `spec/ARCHITECTURE.md`
for how pipelines fit into the overall system design.

## Module Structure

```
pipeline_runner/
├── __init__.py          # Package metadata
├── cli.py               # CLI entry point
├── config.py            # Configuration (from .env and feeds.json)
├── runner.py            # Core pipeline engine
├── scheduler.py         # Long-running scheduler service (ARCH-006)
├── pipelines/           # Pre-built pipeline definitions
│   ├── news.py          # News briefing pipeline
│   ├── article.py       # Article extraction pipeline
│   └── weather.py       # Weather briefing pipeline
└── steps/               # Composable pipeline steps
    ├── fetch.py          # RSS/HTTP fetch (Tier 1)
    ├── extract.py        # HTML content extraction
    ├── score.py          # Importance scoring
    ├── format.py         # Output formatting
    ├── handoff.py        # Librarian handoff
    └── notify.py         # Telegram notifications
```

## Testing

```bash
# Unit tests (in Docker)
docker compose run --rm --profile test pipeline-test

# Local development (requires Poetry)
cd tools
poetry install
poetry run pytest -v
poetry run ruff check pipeline_runner/
poetry run mypy pipeline_runner/
```

## Dependencies

Managed via Poetry (`pyproject.toml`). Key dependencies:
- `feedparser` — RSS parsing
- `requests` — HTTP client
- `beautifulsoup4` — HTML extraction
- `pydantic` / `pydantic-settings` — Configuration management
- `schedule` — Cron-like task scheduling (scheduler service)

Dev dependencies: `pytest`, `ruff`, `mypy`

## Logging

All pipeline output is logged to `log/pipeline.log` with rotation (5MB, 5 backups).
The `log/` folder is tracked in git via `.gitkeep` but file contents are gitignored.

## Telegram Notifications

When `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set in `.env`, every pipeline
automatically sends its generated content to the configured Telegram chat.
The `telegram_notify` step is the last step in each pipeline and is silently
skipped when Telegram is not configured.
