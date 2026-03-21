# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your_ specifics.

## Skills (from agent.yaml)

| Skill | Command | Cost Tier |
|-------|---------|-----------|
| `fetch_briefing` | `docker compose exec scheduler pipeline news` | Tier 1 (free) |
| `read_article` | `docker compose exec scheduler pipeline article <url>` | Tier 1/2 |
| `weather_forecast` | `docker compose exec scheduler pipeline weather <slot>` | Tier 1 (free) |
| `browse_url` | `openclaw browser navigate <url> && openclaw browser snapshot --json` | Tier 3 (fallback) |

The **scheduler service** (ARCH-006) must be running: `docker compose up -d scheduler`.
All skill commands execute instantly via `docker compose exec` (no container startup).
One-shot fallback: `docker compose run --rm --profile cli pipeline <cmd>`.

**Research order:** RSS first, then `read_article`, then `browse_url` only as last resort.

Pipelines are composable and testable. See `spec/PIPELINES.md` for how they work.

## Research Sources

- RSS feeds: configured in `config/feeds.json` (126 feeds across 23 categories in 7 domains)
- Knowledge: Grokipedia (`grokipedia.com`), Wikipedia, and other public sources
- Web: headless browser engine (see `engine/`), or OpenClaw browser relay (Tier 3 fallback)

## Inter-Agent Message Queue (IAMQ)

The IAMQ service at `$IAMQ_HTTP_URL` (default `http://127.0.0.1:18790`) connects
all OpenClaw agents. The scheduler auto-registers on startup and sends heartbeats
every 2 minutes. Every pipeline announces its completion to the queue.

```bash
# Check your inbox
curl http://127.0.0.1:18790/inbox/journalist_agent?status=unread

# List online agents
curl http://127.0.0.1:18790/agents

# Send a message to another agent
curl -X POST http://127.0.0.1:18790/send \
  -H "Content-Type: application/json" \
  -d '{"from":"journalist_agent","to":"librarian_agent","type":"request","priority":"NORMAL","subject":"...","body":"..."}'
```

## Environment-Specific Notes

_(Add local setup details here: custom feeds, SSH hosts, preferred voices, etc.)_

---

Keep shared skills and local setup separate. This is your cheat sheet.
For deeper details: `spec/PIPELINES.md`, `spec/ARCHITECTURE.md`, `spec/TROUBLESHOOTING.md`.
