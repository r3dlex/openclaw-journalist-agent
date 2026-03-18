# Headless Browser Engine

Elixir-based headless browser for Tier 2 research (see `spec/ARCHITECTURE.md`).

## Purpose

Provides JavaScript-rendered page content for URLs that RSS and simple HTTP
fetching cannot handle. Runs as a containerized service alongside the
Python scripts.

## Status

**Planned.** The engine will be built using:
- Elixir/OTP for concurrency and fault tolerance
- A headless browser library (e.g., Wallaby + ChromeDriver)
- Docker container for zero-install deployment

## Intended API

```
GET /fetch?url=<url>&timeout=<ms>
  → { "content": "...", "title": "...", "status": 200 }
```

## Fallback

Until the engine is built, Tier 2 falls through to Tier 3
(OpenClaw browser relay via the `browse_url` skill in `agent.yaml`).
