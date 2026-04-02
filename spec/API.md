# API — openclaw-journalist-agent

## Overview

The Journalist agent does not expose an HTTP server. All cross-agent interaction
uses IAMQ. The agent also provides a CLI via the pipeline runner for operators
who want to trigger pipelines manually.

---

## IAMQ Message Interface

### Incoming messages accepted by `journalist_agent`

| Subject | Purpose | Body fields |
|---------|---------|-------------|
| `journalist.briefing` | Request an immediate news briefing | `type?: "morning"\|"evening"\|"custom"` |
| `journalist.article` | Fetch and summarise a specific article | `url: string` |
| `journalist.weather` | Fetch the weather forecast | `period?: "6am"\|"12pm"\|"4pm"\|"8pm"\|"sunday_9pm"` |
| `journalist.search` | Search for articles on a topic | `query: string`, `max_results?: number` |
| `journalist.digest` | Request the compiled daily digest | `date?: "YYYY-MM-DD"` |
| `status` | Return agent health and last pipeline run timestamp | — |

#### Example: request a news briefing

```json
{
  "from": "agent_claude",
  "to": "journalist_agent",
  "type": "request",
  "priority": "NORMAL",
  "subject": "journalist.briefing",
  "body": {"type": "morning"}
}
```

#### Example response

```json
{
  "from": "journalist_agent",
  "to": "agent_claude",
  "type": "response",
  "priority": "NORMAL",
  "subject": "journalist.briefing.result",
  "body": {
    "type": "morning",
    "headline_count": 12,
    "top_stories": ["Story A", "Story B", "Story C"],
    "report_path": "/data/journalist/log/2026-04-02-morning.md",
    "timestamp": "2026-04-02T06:01:00Z"
  }
}
```

---

## CLI Interface (Pipeline Runner)

All pipelines are run inside Docker for zero-install operation:

```bash
# Run the news pipeline (fetch + score + format + notify)
docker compose exec scheduler pipeline news

# Fetch and summarise a single article
docker compose exec scheduler pipeline article https://example.com/article

# Generate a weather forecast
docker compose exec scheduler pipeline weather 6am

# One-shot alternatives (without scheduler)
docker compose run --rm --profile cli pipeline news
docker compose run --rm --profile cli pipeline weather 6am
```

---

## Handoff to Librarian

After each briefing, the Journalist automatically calls the Librarian agent via
IAMQ to archive the report. This is implemented as the `librarian_handoff`
pipeline step and requires no manual intervention.

```json
{
  "from": "journalist_agent",
  "to": "librarian_agent",
  "type": "request",
  "subject": "librarian.file",
  "body": {
    "source_path": "/data/journalist/log/2026-04-02-morning.md",
    "category": "news_briefings",
    "date": "2026-04-02"
  }
}
```

---

## RSS Feed Configuration

Feeds are configured in `config/feeds.json`. Adding or removing feeds does not
require a restart — the pipeline reads the config fresh on each run.

---

**Related:** `spec/COMMUNICATION.md`, `spec/PIPELINES.md`, `spec/CRON.md`
