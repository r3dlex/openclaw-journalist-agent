---
id: ARCH-005
title: Cost Management Strategy
domain: architecture
rules: false
---

# ARCH-005: Cost Management Strategy

## Context

The Journalist agent consumes resources across three tiers (ARCH-001) and runs
scheduled tasks (spec/CRON.md). Without cost awareness, the agent could burn
through API credits rapidly via unnecessary Tier 3 browser relay calls.

## Decision

Implement cost management through:

1. **Tiered execution** (ARCH-001): Always prefer cheaper tiers
2. **Importance scoring**: Only fetch detailed content for high-scoring stories
3. **Batched scheduling**: Group tasks in heartbeat windows to reduce API calls
4. **Tier logging**: Every fetch logs which tier was used
5. **Daily summaries**: Include tier usage statistics in evening handoff

**Cost tiers:**

| Tier | Method | Approx. cost | Max per day |
|------|--------|-------------|-------------|
| 1 | RSS/HTTP | Free | Unlimited |
| 2 | Headless browser | Compute | 50 pages |
| 3 | OpenClaw relay | API credits | 10 pages |

**Importance threshold:** Only stories scoring >= `importance_threshold_for_detail`
(default: 3) trigger detailed article extraction.

## Do's and Don'ts

**Do:**
- Track tier usage in daily log files
- Use `pipeline validate` to verify configuration
- Review tier statistics in weekly Librarian handoffs
- Cache known JS-heavy domains to avoid failed Tier 1 attempts

**Don't:**
- Use Tier 3 for batch operations
- Fetch full articles for every RSS entry
- Run pipelines more frequently than the cron schedule

## Consequences

**Benefits:**
- 80-90% cost reduction vs naive approach
- Transparent: cost is visible in logs
- Configurable: thresholds in `config/feeds.json`

**Trade-offs:**
- Some stories may be under-researched (low score = no detail fetch)
- Tier tracking adds slight overhead to each fetch

## References

- `ARCH-001` — Three-tier research pipeline
- `spec/CRON.md` — Scheduling
- `config/feeds.json` — Importance threshold configuration
