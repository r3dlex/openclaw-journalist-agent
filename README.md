<p align="center">
  <img src="assets/logo.svg" alt="Journalist Agent logo" width="96" height="96">
</p>

# OpenClaw Journalist Agent

An autonomous research and intelligence briefing agent built on [OpenClaw](https://docs.openclaw.ai/).

The Journalist gathers, crawls, scores, and synthesizes information from RSS feeds, web sources, and knowledge bases. It delivers structured briefings and hands off results to the [Librarian](https://github.com/your-org/openclaw-librarian-agent) agent for archival.

## Features

- **RSS aggregation** with importance scoring and deduplication
- **Three-tier research pipeline**: RSS (free) -> headless browser (medium) -> OpenClaw browser relay (fallback)
- **Composable pipelines** with testable steps (see `spec/PIPELINES.md`)
- **Scheduled briefings** with configurable cron (see `spec/CRON.md`)
- **Weather forecasting** with 5 daily time slots
- **Inter-agent collaboration** with the Librarian agent
- **Architecture Decision Records** via [archgate](https://github.com/archgate/cli)
- **Zero-install** via Docker containers
- **Telegram notifications** — sends generated content to Telegram
- **File-based logging** — all pipeline output to `log/` with rotation
- **No secrets in git** - all configuration via `.env`

## Quick Start

```bash
# 1. Clone and configure
git clone https://github.com/your-org/openclaw-journalist-agent.git
cd openclaw-journalist-agent
cp .env.example .env
# Edit .env with your values

# 2. Build and start the scheduler
docker compose build
docker compose up -d scheduler

# Run ad-hoc commands via the scheduler (instant, no startup delay)
docker compose exec scheduler pipeline news
docker compose exec scheduler pipeline weather 6am

# Or one-shot via cli profile
docker compose run --rm --profile cli pipeline news

# Or legacy scripts
docker compose run --rm --profile legacy journalist python scripts/fetch_news.py

# 3. Run tests
docker compose run --rm --profile test pipeline-test
```

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose
- [OpenClaw](https://docs.openclaw.ai/) (for browser relay fallback and agent hosting)

No Python, Node, or other runtime installation required on the host.

## Configuration

All configuration is via environment variables in `.env`. See `.env.example` for the full list.

| Variable | Description | Default |
|----------|-------------|---------|
| `JOURNALIST_DATA_DIR` | Where logs and reports are stored | `.` |
| `LIBRARIAN_AGENT_WORKSPACE` | Path to librarian agent | - |
| `WEATHER_LOCATION` | City for weather forecasts | `Stuttgart` |
| `NEWS_API_KEY` | Optional NewsAPI key | - |
| `FEEDS_FILE` | Path to RSS feed config | `config/feeds.json` |
| *(Telegram)* | Managed by OpenClaw gateway (`~/.openclaw/openclaw.json`) | - |
| `AGENT_MODEL` | Claude model for the agent | `claude-sonnet-4-20250514` |

## Skills

| Skill | Purpose | Cost Tier |
|-------|---------|-----------|
| `fetch_briefing` | RSS aggregation with importance scoring | Tier 1 (free) |
| `read_article` | Article content extraction from URLs | Tier 1/2 |
| `weather_forecast` | Weather briefings by time slot | Tier 1 (free) |
| `browse_url` | OpenClaw browser relay (full JS rendering) | Tier 3 (fallback) |

The agent follows a tiered research approach: RSS first (free), then direct HTTP extraction,
then OpenClaw browser relay only as a last resort (highest credit cost).

### Running via Scheduler (Recommended)

The scheduler service runs all cron-scheduled pipelines automatically and also
serves as the fastest way to run ad-hoc commands (no container startup overhead):

```bash
docker compose up -d scheduler                                  # Start scheduler
docker compose exec scheduler pipeline news                     # News briefing
docker compose exec scheduler pipeline article <url>            # Article extraction
docker compose exec scheduler pipeline weather <slot>           # Weather briefing
docker compose exec scheduler pipeline validate                 # Validate config
```

### Running One-Shot Pipelines

Use the `cli` profile for standalone one-shot runs (cold start each time):

```bash
docker compose run --rm --profile cli pipeline news
docker compose run --rm --profile cli pipeline article <url>
docker compose run --rm --profile cli pipeline weather <slot>
```

### Running Legacy Scripts

```bash
docker compose run --rm --profile legacy journalist python scripts/fetch_news.py
docker compose run --rm --profile legacy journalist python scripts/read_url.py <url>
docker compose run --rm --profile legacy journalist python scripts/weather_forecast.py <slot>
```

## Architecture

Architecture decisions are tracked as ADRs in `.archgate/adrs/` following the
[archgate](https://github.com/archgate/cli) format.

| ADR | Decision |
|-----|----------|
| `ARCH-001` | Three-Tier Research Pipeline |
| `ARCH-002` | Zero-Install Containerization |
| `ARCH-003` | Pipeline Architecture |
| `ARCH-004` | Inter-Agent Collaboration Protocol |
| `ARCH-005` | Cost Management Strategy |
| `ARCH-006` | Scheduler Service |

See `spec/ARCHITECTURE.md` for the full system design.

## Testing & CI

```bash
# Run all pipeline tests (Docker, zero-install)
docker compose run --rm --profile test pipeline-test

# Local development
cd tools && poetry install && poetry run pytest -v
```

**GitHub Actions** runs on every push and PR (`.github/workflows/ci.yml`):
- Lint, type check, and unit tests (Python 3.12 + 3.13)
- Per-pipeline integration tests (news, article, weather)
- Docker build validation
- Secrets scan and config validation

See `spec/TESTING.md` for the complete test strategy and CI matrix.

## Documentation

| File | Audience | Purpose |
|------|----------|---------|
| `CLAUDE.md` | Developers | How to work on this repo |
| `AGENTS.md` | Journalist agent | Operational framework |
| `SOUL.md` | Journalist agent | Identity and protocols |
| `spec/ARCHITECTURE.md` | Both | System design + ADR index |
| `spec/PIPELINES.md` | Both | Pipeline architecture |
| `spec/CRON.md` | Journalist agent | Scheduled tasks |
| `spec/TASK.md` | Journalist agent | One-shot task queue |
| `spec/TESTING.md` | Developers | How to test |
| `spec/TROUBLESHOOTING.md` | Both | Common issues |
| `spec/LEARNINGS.md` | Both | Lessons learned |

## License

MIT - see [LICENSE](LICENSE).
