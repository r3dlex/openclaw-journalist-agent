# ARCHITECTURE.md - System Design

## Overview

The Journalist agent operates as a three-tier research pipeline with composable
pipeline execution. Architecture decisions are tracked as ADRs in `.archgate/adrs/`.

```
Sources → Pipeline Steps → Output → Librarian
```

## Architecture Decision Records (ADRs)

Architectural decisions follow the [archgate](https://github.com/archgate/cli) format.
Each ADR documents the context, decision, consequences, and (optionally) enforceable rules.

| ADR | Title | Domain |
|-----|-------|--------|
| `ARCH-001` | Three-Tier Research Pipeline | architecture |
| `ARCH-002` | Zero-Install Containerization | architecture |
| `ARCH-003` | Pipeline Architecture | architecture |
| `ARCH-004` | Inter-Agent Collaboration Protocol | architecture |
| `ARCH-005` | Cost Management Strategy | architecture |
| `ARCH-006` | Scheduler Service | architecture |

ADRs live in `.archgate/adrs/`. To create a new one, follow the naming convention:
`ARCH-NNN-short-slug.md` with YAML frontmatter (`id`, `title`, `domain`, `rules`).

## Research Tiers (ARCH-001)

The Journalist uses a tiered approach to minimize credit consumption:

### Tier 1: RSS Feeds / HTTP (lowest cost)
- Pipeline step: `fetch_feeds` or `fetch_url` (see `spec/PIPELINES.md`)
- Legacy script: `scripts/fetch_news.py`
- Feeds configured in `config/feeds.json`
- Importance scoring filters signal from noise
- Runs on schedule (see `spec/CRON.md`)

### Tier 2: Headless Browser Engine (medium cost)
- Elixir-based headless browser in `engine/`
- Used for: article extraction, JavaScript-rendered pages, paywalled content
- Containerized (zero-install via Docker)
- Legacy script: `scripts/read_url.py` wraps this for simple extraction

### Tier 3: OpenClaw Browser (fallback, highest cost)
- Full browser via `openclaw browser` relay
- Agent skill: `browse_url` (defined in `agent.yaml`)
- Command: `openclaw browser navigate <url> && openclaw browser snapshot --json`
- Used when: Tier 1 and Tier 2 fail or return no meaningful content
- This is the fallback of last resort (see `ARCH-005` for cost limits)

### Decision Logic

```
1. Try RSS feed / direct HTTP fetch (pipeline step: fetch_feeds/fetch_url)
2. If content is empty, JavaScript-rendered, or paywalled:
   → Use headless browser engine (Tier 2)
3. If headless engine fails or returns garbage:
   → Fall back to openclaw browser relay (Tier 3)
4. Log which tier was used for cost tracking
```

## Pipeline Architecture (ARCH-003)

All workflows are implemented as composable pipelines. See `spec/PIPELINES.md` for details.

```
Pipeline → [Step1 → Step2 → Step3] → PipelineResult
```

**Pre-built pipelines:**

| Pipeline | Steps | Trigger |
|----------|-------|---------|
| `news_briefing` | fetch_feeds → score → format → handoff → iamq_announce | Cron |
| `article_extraction` | fetch_url → extract → handoff → iamq_announce | Ad-hoc |
| `weather_briefing` | fetch_weather → format → handoff → iamq_announce | Cron |

**Execution (via scheduler):**
```bash
docker compose up -d scheduler                           # Start scheduler (auto-runs cron tasks)
docker compose exec scheduler pipeline news              # Ad-hoc execution (instant)
docker compose exec scheduler pipeline article https://example.com
docker compose exec scheduler pipeline weather 6am
```

**Execution (one-shot, cli profile):**
```bash
docker compose run --rm --profile cli pipeline news
```

## Data Flow

```
[RSS Feeds]  ──┐
[Web Crawl]  ──┤──→ [Pipeline Steps] ──→ [Briefing]
[Ad-hoc URLs]──┘         │                    │
                          │                    ├──→ IAMQ (inter-agent messaging)
                    [Importance Scoring]        ├──→ log/ (file logging)
                                                └──→ Librarian (archival)
```

## Component Map

| Component | Skill name | Location | Runtime |
|-----------|-----------|----------|---------|
| Scheduler service | - | `tools/pipeline_runner/scheduler.py` | Docker (long-running, ARCH-006) |
| Pipeline runner | - | `tools/pipeline_runner/` | Docker (Poetry) |
| News fetcher | `fetch_briefing` | `scripts/fetch_news.py` | Docker container |
| URL reader | `read_article` | `scripts/read_url.py` | Docker container |
| Weather | `weather_forecast` | `scripts/weather_forecast.py` | Docker container |
| Feed config | - | `config/feeds.json` | Static JSON |
| Browser engine | - | `engine/` | Docker (Elixir, planned) |
| OpenClaw browser | `browse_url` | `openclaw browser` | Host CLI (Tier 3 fallback) |
| Logs | - | `log/` + `$JOURNALIST_DATA_DIR/log/` | File logging with rotation |

## Inter-Agent Protocol (ARCH-004)

The Journalist hands off to the Librarian via file-based inbox protocol:
1. Write output to `$JOURNALIST_DATA_DIR/log/{timestamp}_{pipeline}.md`
2. Write metadata to `$JOURNALIST_DATA_DIR/log/{timestamp}_{pipeline}.meta.json`
3. Write handoff signal to `$LIBRARIAN_AGENT_WORKSPACE/inbox/journalist_{timestamp}.json`
4. Librarian picks up signals on next session startup

See `ARCH-004` for the full protocol specification.

## Cost Management (ARCH-005)

- Tier 1 (RSS) is free — use aggressively
- Tier 2 (headless) costs compute — use for important stories
- Tier 3 (openclaw browser) costs API credits — max ~10/day
- Importance threshold: only stories scoring >= 3 trigger detailed fetch
- Track tier usage in daily logs for cost analysis

## Containerization (ARCH-002)

All scripts and pipelines run inside Docker containers (zero-install):

| Image / Service | Purpose | Dockerfile | Profile |
|----------------|---------|-----------|---------|
| `scheduler` | Long-running scheduler (ARCH-006) | `tools/Dockerfile` | default |
| `pipeline` | One-shot pipeline runner | `tools/Dockerfile` | `cli` |
| `pipeline-test` | Test suite | `tools/Dockerfile` (test stage) | `test` |
| `journalist` | Legacy scripts | `./Dockerfile` | `legacy` |

The **scheduler** service is the primary runtime. It auto-executes all 7 cron-scheduled
tasks from `spec/CRON.md` plus an IAMQ heartbeat (8 total) using the `schedule` library and also accepts ad-hoc commands
via `docker compose exec scheduler pipeline <cmd>`.

## Testing

See `spec/TESTING.md` for the full test strategy, including:
- Unit tests for each pipeline step
- Integration tests with mocked HTTP
- Pipeline validation (`pipeline validate`)
- Smoke test checklist
