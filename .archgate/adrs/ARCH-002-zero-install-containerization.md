---
id: ARCH-002
title: Zero-Install Containerization
domain: architecture
rules: false
---

# ARCH-002: Zero-Install Containerization

## Context

The Journalist agent runs scripts for RSS fetching, article extraction, and weather.
These scripts have Python dependencies (`feedparser`, `requests`, `beautifulsoup4`,
`pydantic`). The agent may run on different machines with varying OS and Python versions.

We need reproducible execution with zero host-side installation.

**Rejected alternatives:**
- Require Python + pip on host (fragile, version conflicts)
- Use conda/pyenv (heavy, adds another tool to manage)
- Serverless functions (latency, cold starts, vendor lock-in)

## Decision

All scripts and pipelines run inside Docker containers. The host needs only
Docker and Docker Compose. No Python, Node, or other runtime required.

**Two container images:**

| Image | Purpose | Base | Location |
|-------|---------|------|----------|
| `journalist` | Legacy scripts (`scripts/`) | `python:3.12-slim` | `./Dockerfile` |
| `pipeline` | Pipeline runner (`tools/`) | `python:3.12-slim` | `tools/Dockerfile` |

The `pipeline` image uses Poetry for dependency management with a multi-stage build:
- **base stage:** Install production dependencies
- **test stage:** Add dev dependencies, run pytest + ruff
- **production stage:** Slim image with just the pipeline CLI

## Do's and Don'ts

**Do:**
- Use `docker compose run --rm` for all script execution
- Keep dependency files (`pyproject.toml`, `requirements.txt`) as the first COPY layer
- Use read-only mounts for scripts and config
- Pin dependency versions with ranges (e.g., `^6.0`, not `latest`)

**Don't:**
- Install packages on the host for script execution
- Use `docker compose up` (these are run-once tasks, not services)
- Copy `.env` into the image (use `env_file:` in compose)
- Run as root inside containers (add USER in production)

## Consequences

**Benefits:**
- True zero-install: clone, `cp .env.example .env`, `docker compose build`
- Reproducible builds across machines and CI
- No host-side Python version conflicts

**Trade-offs:**
- Docker Desktop required (not always available in restricted environments)
- Slightly slower startup vs native Python (~1-2s container overhead)

## References

- `./Dockerfile` — Legacy scripts container
- `tools/Dockerfile` — Pipeline runner container
- `docker-compose.yml` — Orchestration
- `ARCH-003` — Pipeline architecture
