---
id: ARCH-006
title: Long-Running Scheduler Service
domain: architecture
rules: false
---

# ARCH-006: Long-Running Scheduler Service

## Context

The Journalist agent runs pipelines on a cron schedule (spec/CRON.md): news
briefings at 06:00/08:00/14:00/20:00, weather at 12:00/16:00, and combined
slots. Previously, each invocation required `docker compose run --rm pipeline`
which:

- Incurs ~1-2s container startup overhead per run
- Requires an external trigger (host cron, OpenClaw heartbeat, or agent skill)
- Has no centralized scheduling — everything depends on external orchestration

**Rejected alternatives:**
- Host-level crontab (not portable, not containerized, breaks zero-install)
- Keep run-once only (acceptable but slower and less autonomous)
- Kubernetes CronJobs (overkill for single-machine deployment)
- Celery/Dramatiq (heavy dependencies for simple time-based scheduling)

## Decision

Add a **long-running scheduler service** to docker-compose.yml:

```yaml
scheduler:
  command: ["scheduler"]
  restart: unless-stopped
```

The scheduler uses the lightweight `schedule` library to execute pipelines at
the times defined in spec/CRON.md. It runs as a persistent Docker service
alongside the existing one-shot `pipeline` service.

**Service topology:**

| Service | Lifecycle | Purpose |
|---------|-----------|---------|
| `scheduler` | Always running | Executes pipelines on cron schedule |
| `pipeline` | One-shot (cli profile) | Ad-hoc commands, CI |
| `pipeline-test` | One-shot (test profile) | Test suite |
| `journalist` | One-shot (legacy profile) | Legacy scripts |

**Ad-hoc commands via the running scheduler:**
```bash
docker compose exec scheduler pipeline news          # instant, no startup
docker compose exec scheduler pipeline article <url>  # reuses running container
```

**Agent skills** use `docker compose exec scheduler` instead of
`docker compose run --rm` for zero-startup-overhead execution.

## Do's and Don'ts

**Do:**
- Use `docker compose up -d scheduler` to start the scheduler
- Use `docker compose exec scheduler pipeline <cmd>` for ad-hoc work
- Handle SIGTERM gracefully (scheduler stops within 30s grace period)
- Log all scheduled executions for audit trail
- Catch exceptions in scheduled tasks (don't crash the scheduler)

**Don't:**
- Run the scheduler AND host crontab for the same tasks (double execution)
- Put business logic in the scheduler (it just invokes pipeline functions)
- Skip the `restart: unless-stopped` policy (scheduler must survive crashes)

## Consequences

**Benefits:**
- Zero startup overhead for ad-hoc commands (~0ms vs ~1-2s)
- Self-contained scheduling (no external cron dependency)
- Graceful shutdown on SIGTERM (Docker stop works cleanly)
- Single container for scheduled + ad-hoc work
- Agent skills execute instantly via `docker compose exec`

**Trade-offs:**
- One always-running container (~30MB memory)
- Schedule is defined in Python code (must match spec/CRON.md manually)
- One-shot `pipeline` service still available for CI and when scheduler is down

**Mitigation:**
- Memory footprint is minimal (Python idle + schedule library)
- Tests validate that register_schedule() creates exactly 7 tasks matching CRON.md

## References

- `spec/CRON.md` — Schedule definition
- `tools/pipeline_runner/scheduler.py` — Implementation
- `tools/tests/test_scheduler.py` — Tests
- `docker-compose.yml` — Service definition
- `ARCH-002` — Zero-install containerization
- `ARCH-003` — Pipeline architecture
