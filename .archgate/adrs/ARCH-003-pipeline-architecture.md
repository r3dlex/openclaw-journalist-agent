---
id: ARCH-003
title: Pipeline Architecture
domain: architecture
rules: false
---

# ARCH-003: Pipeline Architecture

## Context

The Journalist agent executes multi-step workflows: fetch RSS, score articles,
format briefings, hand off to Librarian. These steps need to be:

- **Composable:** Mix and match steps for different workflows
- **Testable:** Each step independently testable with mock data
- **Observable:** Track timing, success/failure, and errors per step
- **Extensible:** Add new pipelines without modifying the engine

The legacy scripts (`scripts/`) are monolithic: `fetch_news.py` does everything
in a single file. This works but is hard to test and extend.

**Rejected alternatives:**
- Keep monolithic scripts (not testable, not composable)
- Use a workflow engine like Airflow/Prefect (overkill for this scale)
- Use shell scripts chaining Python scripts (fragile, poor error handling)

## Decision

Implement a lightweight pipeline engine in `tools/pipeline_runner/`:

```
Pipeline → [Step1 → Step2 → Step3] → PipelineResult
```

**Core abstractions:**

| Concept | Type | Description |
|---------|------|-------------|
| `Pipeline` | Class | Ordered sequence of steps |
| `PipelineStep` | Protocol | Interface for composable steps |
| `StepResult` | Dataclass | Outcome of one step (status, duration, error) |
| `PipelineResult` | Dataclass | Outcome of full pipeline (steps, context, summary) |

**Step Protocol:**
```python
class PipelineStep(Protocol):
    name: str
    def should_run(self, context: dict) -> bool: ...
    def execute(self, context: dict) -> dict: ...
```

Steps communicate via a shared **context dict**. Each step reads what it needs
and writes what it produces.

## Do's and Don'ts

**Do:**
- Keep steps small and focused (one responsibility)
- Make steps idempotent where possible
- Use `should_run()` to skip unnecessary steps
- Test each step in isolation with mock context
- Test full pipelines with mocked external calls

**Don't:**
- Put business logic in the `Pipeline` class (it's just orchestration)
- Have steps depend on each other's internal state (use context)
- Catch exceptions inside steps (let the pipeline engine handle it)
- Mix pipeline engine concerns with step implementation

## Consequences

**Benefits:**
- Each step is independently testable (50+ unit tests)
- New pipelines can be composed from existing steps in minutes
- Duration tracking enables cost optimization
- Fail-fast vs continue modes for different use cases

**Trade-offs:**
- More files than monolithic scripts
- Context dict is loosely typed (mitigated by docstrings and tests)

## References

- `spec/PIPELINES.md` — Pipeline specification
- `tools/pipeline_runner/` — Implementation
- `tools/tests/` — Test suite
- `ARCH-001` — Three-tier research pipeline
- `ARCH-002` — Zero-install containerization
