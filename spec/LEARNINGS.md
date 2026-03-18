# LEARNINGS.md - Lessons Learned

Document insights, mistakes, and improvements discovered over time.
Both the Journalist agent and developers should contribute here.

## Format

```markdown
### YYYY-MM-DD — Title
**Context:** What happened
**Learning:** What we learned
**Action:** What changed as a result
```

## Entries

### 2026-03-19 — Scheduler service replaces one-shot container pattern
**Context:** Cron-scheduled pipelines were running via `docker compose run --rm pipeline <cmd>`,
which incurred container startup overhead on every execution (7 times/day). Ad-hoc commands
also suffered from cold-start delays.
**Learning:** A long-running scheduler service using the `schedule` library eliminates per-run
container startup costs and enables instant ad-hoc execution via `docker compose exec`.
The one-shot pattern is still available via `docker compose run --rm --profile cli pipeline <cmd>`
for CI and debugging, but production use should prefer the scheduler.
**Action:** Implemented ARCH-006: `tools/pipeline_runner/scheduler.py` with 9 tests in
`tools/tests/test_scheduler.py`. Docker Compose profiles (`cli`, `test`, `legacy`) organize
one-shot services. Documentation updated across the repo.
