---
id: ARCH-001
title: Three-Tier Research Pipeline
domain: architecture
rules: false
---

# ARCH-001: Three-Tier Research Pipeline

## Context

The Journalist agent must gather content from diverse web sources: RSS feeds,
static pages, JavaScript-rendered SPAs, and occasionally paywalled content.
Each method has different cost implications:

- **RSS/HTTP** is free and fast, but misses JS-rendered content
- **Headless browsers** handle JS but consume compute resources
- **OpenClaw browser relay** handles everything but costs API credits

A single approach wastes resources. We need a tiered fallback chain.

**Rejected alternatives:**
- Always use headless browser (too expensive for RSS-available content)
- Always use OpenClaw relay (highest cost, defeats purpose of autonomy)
- Let the agent decide ad-hoc (inconsistent, no cost tracking)

## Decision

Implement a three-tier research pipeline with automatic fallback:

| Tier | Method | Cost | When to use |
|------|--------|------|-------------|
| 1 | RSS/HTTP direct | Free | Default for all feeds and simple pages |
| 2 | Headless browser (Elixir engine) | Compute | JS-rendered pages, empty Tier 1 results |
| 3 | OpenClaw browser relay | API credits | Last resort when Tier 1+2 fail |

**Escalation logic:**
1. Always start with Tier 1
2. If content is empty, truncated, or clearly JS-dependent, escalate to Tier 2
3. If Tier 2 fails or is unavailable, escalate to Tier 3
4. Log which tier was used for every fetch (cost tracking)

## Do's and Don'ts

**Do:**
- Always attempt Tier 1 first
- Log the tier used for each fetch
- Track cumulative tier usage in daily logs
- Respect timeouts at each tier

**Don't:**
- Skip directly to Tier 3 (even if you "know" the page needs JS)
- Retry the same tier more than once per URL
- Use Tier 3 for batch operations (RSS aggregation)

## Consequences

**Benefits:**
- Minimizes credit consumption by 80-90% vs always using Tier 3
- Provides graceful degradation when services are unavailable
- Enables cost tracking and optimization over time

**Trade-offs:**
- Slightly slower for JS-heavy pages (two failed attempts before success)
- Tier 2 engine is not yet built (falls through to Tier 3 until ready)

**Mitigation:**
- Cache known JS-heavy domains to skip Tier 1 on subsequent visits
- Track Tier 2 readiness in `engine/README.md`

## Compliance and Enforcement

- **Pipeline validation:** `pipeline validate` checks tier configuration
- **Log review:** Daily logs include tier usage statistics
- **Manual review:** Spot-check tier escalation patterns weekly

## References

- `spec/ARCHITECTURE.md` — Full system design
- `spec/PIPELINES.md` — Pipeline execution details
- `engine/README.md` — Tier 2 engine status
