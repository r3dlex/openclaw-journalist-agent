---
id: ARCH-004
title: Inter-Agent Collaboration Protocol
domain: architecture
rules: false
---

# ARCH-004: Inter-Agent Collaboration Protocol

## Context

The Journalist agent produces research outputs (briefings, articles, weather reports)
that need to be archived and indexed by the Librarian agent. These agents run in
separate workspaces and sessions.

We need a reliable, file-based handoff protocol that works when agents are not
running simultaneously.

**Rejected alternatives:**
- Direct API calls between agents (agents don't have persistent servers)
- Shared database (overkill, adds infrastructure dependency)
- Message queue (same: infrastructure dependency)

## Decision

Use a **file-based inbox protocol**:

1. Journalist writes output to `$JOURNALIST_DATA_DIR/log/{timestamp}_{pipeline}.md`
2. Journalist writes metadata to `$JOURNALIST_DATA_DIR/log/{timestamp}_{pipeline}.meta.json`
3. If `$LIBRARIAN_AGENT_WORKSPACE` is configured and exists, Journalist writes a
   **handoff signal** to `$LIBRARIAN_AGENT_WORKSPACE/inbox/journalist_{timestamp}.json`
4. The Librarian picks up signals from its `inbox/` on next session startup

**Handoff signal format:**
```json
{
  "source_agent": "journalist",
  "target_agent": "librarian",
  "pipeline": "news_briefing",
  "timestamp": "2026-03-18T10:00:00+00:00",
  "output_file": "/path/to/log/20260318_100000_news_briefing.md",
  "output_size_bytes": 4096
}
```

## Do's and Don'ts

**Do:**
- Always write to local log directory first (Journalist owns its outputs)
- Use UTC timestamps in filenames and metadata
- Include `output_size_bytes` so Librarian can estimate processing time
- Gracefully handle missing Librarian workspace (log a warning, don't fail)

**Don't:**
- Write directly to Librarian's workspace outside of `inbox/`
- Assume the Librarian is running when the handoff signal is written
- Include sensitive data (API keys, PII) in handoff signals
- Delete local logs after handoff (Journalist keeps its own copy)

## Consequences

**Benefits:**
- Zero infrastructure: just filesystem operations
- Resilient: handoff signals persist until processed
- Auditable: both agents keep their own copy
- Works across sessions (no need for simultaneous execution)

**Trade-offs:**
- No real-time notification (Librarian discovers signals on next startup)
- Requires both agents to agree on the inbox path convention

## References

- `spec/ARCHITECTURE.md` — System design
- `AGENTS.md` — Collaboration section
- `tools/pipeline_runner/steps/handoff.py` — Implementation
