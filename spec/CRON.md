# CRON.md - Recurring Scheduled Tasks

The Journalist maintains this schedule of recurring activities.
Update this file when tasks are added, changed, or retired.

## Active Schedule

| Time | Task | Pipeline / Script | Notes |
|------|------|-------------------|-------|
| 06:00 | Morning briefing | `pipeline news` + `pipeline weather 6am` | Full day ahead |
| 08:00 | News update | `pipeline news` | Catch early stories |
| 12:00 | Midday weather | `pipeline weather 12pm` | Rest of day |
| 14:00 | Afternoon briefing | `pipeline news` | Afternoon cycle |
| 16:00 | Afternoon weather | `pipeline weather 4pm` | Rest of day |
| 20:00 | Evening briefing | `pipeline news` + `pipeline weather 8pm` | Next day preview |
| Sun 21:00 | Weekly weather | `pipeline weather sunday_9pm` | 7-day lookahead |

All 7 scheduled tasks are auto-executed by the **scheduler service** (ARCH-006).
Start it with `docker compose up -d scheduler`. The scheduler uses the `schedule`
library and runs pipelines in-process — no container startup overhead per task.

For ad-hoc runs, use: `docker compose exec scheduler pipeline <command>`.
One-shot fallback: `docker compose run --rm --profile cli pipeline <command>`.

## Handoff Schedule

| Frequency | Action |
|-----------|--------|
| After each briefing | Pipeline auto-writes to `$JOURNALIST_DATA_DIR/log/` |
| After each briefing | Pipeline auto-sends handoff signal to Librarian |
| Daily (evening) | Summarize day's tier usage in handoff |
| Weekly (Sunday) | Summary handoff to Librarian |

Handoffs are automated by the `librarian_handoff` pipeline step (see `spec/PIPELINES.md`).

## Retired Tasks

_(Move tasks here when they're no longer active, with date retired.)_

---

**Owner:** Journalist agent. Keep this current.
**Related:** `spec/PIPELINES.md`, `spec/ARCHITECTURE.md`, `ARCH-005` (cost management)
