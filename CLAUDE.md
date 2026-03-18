# CLAUDE.md - Developer Guide for the Journalist Agent

This file is for **you** (Claude Code / developer agents) working on this repository.
It is NOT read by the Journalist openclaw agent itself.

## What Is This Repo?

An OpenClaw agent called **Journalist** that autonomously researches, crawls, summarizes,
and organizes intelligence briefings. It delivers structured outputs to the user and
hands off results to the **Librarian** agent for archival.

## Repo Layout

```
.
├── CLAUDE.md            # You are here (developer guide)
├── README.md            # Public-facing project documentation
├── AGENTS.md            # OpenClaw agent operational framework (read by Journalist)
├── IDENTITY.md          # Agent identity (read by Journalist)
├── SOUL.md              # Agent personality & protocols (read by Journalist)
├── USER.md              # User profile template (read by Journalist)
├── TOOLS.md             # Local environment notes (read by Journalist)
├── HEARTBEAT.md         # Periodic task definitions (read by Journalist)
├── agent.yaml           # OpenClaw agent configuration
├── .env.example         # Environment variable template
├── config/              # Runtime configuration (feeds, sources)
│   └── feeds.json       # RSS feed definitions
├── requirements.txt     # Python dependencies for legacy scripts
├── scripts/             # Legacy containerized scripts (see also tools/)
│   ├── fetch_news.py    # RSS aggregator with importance scoring
│   ├── read_url.py      # Article content extractor
│   └── weather_forecast.py  # Weather briefing generator
├── tools/               # Pipeline runner module (Poetry + zero-install)
│   ├── pyproject.toml   # Poetry project definition
│   ├── Dockerfile       # Multi-stage build (base/test/production)
│   ├── README.md        # Pipeline runner documentation
│   ├── pipeline_runner/  # Python package
│   │   ├── cli.py       # CLI entry point
│   │   ├── config.py    # Configuration management
│   │   ├── runner.py    # Core pipeline engine
│   │   ├── pipelines/   # Pre-built pipeline definitions
│   │   └── steps/       # Composable pipeline steps
│   └── tests/           # Test suite (pytest)
├── engine/              # Elixir headless browser engine (Tier 2, future)
│   └── README.md        # Engine architecture notes
├── .archgate/           # Architecture Decision Records
│   └── adrs/            # ADRs in archgate format
│       ├── ARCH-001-three-tier-research-pipeline.md
│       ├── ARCH-002-zero-install-containerization.md
│       ├── ARCH-003-pipeline-architecture.md
│       ├── ARCH-004-inter-agent-collaboration.md
│       └── ARCH-005-cost-management.md
├── spec/                # Detailed specifications (progressive disclosure)
│   ├── ARCHITECTURE.md  # System design and ADR index
│   ├── PIPELINES.md     # Pipeline architecture spec
│   ├── CRON.md          # Scheduled recurring tasks
│   ├── TASK.md          # One-shot task queue
│   ├── TESTING.md       # How to test the agent
│   ├── TROUBLESHOOTING.md  # Common issues and fixes
│   └── LEARNINGS.md     # Lessons learned over time
├── .github/
│   └── workflows/
│       └── ci.yml       # GitHub Actions CI pipeline
├── Dockerfile           # Zero-install container for legacy scripts
├── docker-compose.yml   # Full stack orchestration
└── LICENSE              # MIT
```

## Two Audiences, Two Sets of Files

| Audience | Files | Purpose |
|----------|-------|---------|
| **Developers / Claude Code** | `CLAUDE.md`, `spec/*`, `.archgate/adrs/*`, `tools/`, `Dockerfile`, `docker-compose.yml`, `README.md` | Build, test, improve the agent |
| **Journalist Agent (openclaw)** | `AGENTS.md`, `SOUL.md`, `IDENTITY.md`, `USER.md`, `TOOLS.md`, `HEARTBEAT.md`, `spec/CRON.md`, `spec/TASK.md` | Runtime behavior and memory |

## Environment Variables

All configuration lives in `.env` (never committed). See `.env.example` for the full list.

Key variables:
- `JOURNALIST_DATA_DIR` - Where logs and reports are written
- `LIBRARIAN_AGENT_WORKSPACE` - Path to the librarian agent for handoffs
- `USER_DISPLAY_NAME`, `USER_LOCATION`, etc. - User PII kept out of git
- `WEATHER_LOCATION`, `WEATHER_COUNTRY` - Weather config
- `NEWS_API_KEY` - Optional API key

## Scripts & Skills

**Legacy scripts** run inside Docker containers (zero-install):

```bash
docker compose run --rm journalist python scripts/fetch_news.py
docker compose run --rm journalist python scripts/read_url.py <url>
docker compose run --rm journalist python scripts/weather_forecast.py 6am
```

**Pipeline runner** (recommended) — composable, testable pipelines:

```bash
docker compose run --rm pipeline news
docker compose run --rm pipeline article https://example.com
docker compose run --rm pipeline weather 6am
docker compose run --rm pipeline validate
```

The agent also has a `browse_url` skill that uses the OpenClaw browser relay
as a Tier 3 fallback when containerized scripts can't extract content.
This runs on the host via `openclaw browser` (not containerized).

## Architecture Decision Records

ADRs follow the [archgate](https://github.com/archgate/cli) format in `.archgate/adrs/`.
See `spec/ARCHITECTURE.md` for the ADR index and how they map to the system design.

## Testing & CI

Run tests via Docker (zero-install):

```bash
# Pipeline runner tests (pytest + ruff)
docker compose run --rm pipeline-test

# Local development
cd tools && poetry install && poetry run pytest -v
```

**GitHub Actions** (`.github/workflows/ci.yml`) runs on every push and PR:
- Lint + type check (ruff, mypy)
- Unit tests on Python 3.12 and 3.13
- Per-pipeline integration tests (news, article, weather)
- Docker build validation
- Secrets scan (blocks if hardcoded secrets or local paths found)
- Config validation (feeds.json, .env.example)

See `spec/TESTING.md` for the full test strategy and CI matrix.

## Progressive Disclosure

For deeper topics, see `spec/`:
- **Architecture & ADRs**: `spec/ARCHITECTURE.md`
- **Pipelines**: `spec/PIPELINES.md`
- **Scheduled tasks**: `spec/CRON.md`
- **One-shot tasks**: `spec/TASK.md`
- **Testing**: `spec/TESTING.md`
- **Troubleshooting**: `spec/TROUBLESHOOTING.md`
- **Lessons learned**: `spec/LEARNINGS.md`

## Sensitive Data Policy

- **NEVER** commit `.env`, credentials, API keys, or PII
- User profile data is referenced via `$USER_DISPLAY_NAME` etc. in templates
- The `.gitignore` excludes: `.env`, `artifacts/`, `logs/`, `memory/`, `.openclaw/`
- Before committing, run: `git diff --cached` and check for secrets
- CI will block merges if secrets or hardcoded paths are detected

## Contributing

1. Read this file and `spec/ARCHITECTURE.md`
2. Copy `.env.example` to `.env` and configure
3. Use `docker compose` for all script and pipeline execution
4. Run tests before committing: `docker compose run --rm pipeline-test`
5. Keep the Journalist agent autonomous - it makes its own decisions
6. Document architectural decisions as ADRs in `.archgate/adrs/`
7. Document learnings in `spec/LEARNINGS.md`
