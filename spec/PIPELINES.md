# PIPELINES.md - Pipeline Architecture

## Overview

Pipelines are the execution backbone of the Journalist agent. Each pipeline is a
sequence of composable **steps** that transform an input context into structured output.

**Location:** `tools/pipeline_runner/`
**ADR:** `ARCH-003` (Pipeline Architecture)

## Core Concepts

### Pipeline

An ordered sequence of steps with:
- **Context passing:** Each step receives and returns a `dict[str, Any]`
- **Fail-fast mode:** Stops on first failure (default) or continues through errors
- **Duration tracking:** Every step is timed for cost analysis
- **Summary reporting:** Human-readable run report

### Step Protocol

Every step implements:

```python
class MyStep:
    name = "my_step"

    def should_run(self, context: dict) -> bool:
        """Return True if this step should execute."""
        ...

    def execute(self, context: dict) -> dict:
        """Execute the step and return updated context."""
        ...
```

Steps should be **idempotent** where possible.

## Built-in Pipelines

### 1. News Briefing (`news_briefing`)

**Trigger:** Cron schedule (see `spec/CRON.md`) or ad-hoc
**Steps:** `fetch_feeds` -> `score_importance` -> `format_briefing` -> `librarian_handoff`

```
[RSS Feeds] -> [Concurrent Fetch] -> [Keyword Scoring] -> [Markdown Briefing] -> [Log + Librarian]
```

### 2. Article Extraction (`article_extraction`)

**Trigger:** Ad-hoc (user request or high-importance story)
**Steps:** `fetch_url` -> `extract_content` -> `librarian_handoff` (optional)

```
[URL] -> [HTTP GET (Tier 1)] -> [HTML Parse] -> [Clean Text] -> [Log]
```

If Tier 1 fails, the agent should escalate to Tier 2/3 using `read_article` or `browse_url` skills.

### 3. Weather Briefing (`weather_briefing`)

**Trigger:** Cron schedule (see `spec/CRON.md`)
**Steps:** `fetch_weather` -> `format_weather` -> `librarian_handoff`

```
[wttr.in API] -> [JSON Parse] -> [Markdown Table] -> [Log + Librarian]
```

## Step Reference

| Step | Module | Input Context | Output Context |
|------|--------|--------------|----------------|
| `fetch_feeds` | `steps/fetch.py` | `settings`, `feeds_config` | `entries` |
| `fetch_url` | `steps/fetch.py` | `url`, `settings` | `raw_html`, `fetch_tier` |
| `extract_content` | `steps/extract.py` | `raw_html` | `content`, `title` |
| `score_importance` | `steps/score.py` | `entries`, `feeds_config` | `scored_entries` |
| `format_briefing` | `steps/format.py` | `scored_entries` | `briefing` |
| `format_weather` | `steps/format.py` | `weather_data` | `weather_briefing` |
| `librarian_handoff` | `steps/handoff.py` | `briefing` or `weather_briefing` | `handoff_path` |

## Running Pipelines

### Via Docker (zero-install)

```bash
docker compose run --rm pipeline news
docker compose run --rm pipeline article https://example.com
docker compose run --rm pipeline weather 6am
docker compose run --rm pipeline validate
```

### Via Poetry (development)

```bash
cd tools
poetry install
poetry run pipeline news
poetry run pipeline article https://example.com
```

## Testing Pipelines

See `spec/TESTING.md` for the full test strategy.

```bash
# Run all tests (Docker)
docker compose run --rm pipeline-test

# Run specific test
cd tools && poetry run pytest tests/test_pipelines/test_news.py -v
```

## Extending

To add a new pipeline:

1. Create a new step in `pipeline_runner/steps/` (if needed)
2. Create a pipeline builder in `pipeline_runner/pipelines/`
3. Register the CLI command in `pipeline_runner/cli.py`
4. Add tests in `tools/tests/test_pipelines/`
5. Document in this file
6. If architecturally significant, create an ADR in `.archgate/adrs/`

## Related

- **Architecture:** `spec/ARCHITECTURE.md`
- **ADRs:** `.archgate/adrs/ARCH-003-pipeline-architecture.md`
- **Testing:** `spec/TESTING.md`
- **Cron schedule:** `spec/CRON.md`
