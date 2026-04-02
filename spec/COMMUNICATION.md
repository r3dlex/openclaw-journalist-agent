# Communication

> How the Journalist Agent communicates with peer agents via IAMQ.

## IAMQ Registration

The agent registers on startup with the Inter-Agent Message Queue at `$IAMQ_HTTP_URL`.

```json
{
  "agent_id": "journalist_agent",
  "capabilities": [
    "article_extraction",
    "news_briefing",
    "weather_briefing",
    "content_pipeline",
    "research",
    "web_crawl",
    "summarize",
    "rss_monitor"
  ]
}
```

## Outgoing Messages

### Briefing Delivery to Librarian

Full briefing content is sent to `librarian_agent` for archival via `IAMQAnnounceStep` in the pipeline. This is the authoritative handoff — the Librarian is the permanent record.

```json
{
  "from": "journalist_agent",
  "to": "librarian_agent",
  "type": "info",
  "priority": "NORMAL",
  "subject": "News Briefing — 2026-03-23",
  "body": {
    "action": "archive",
    "content_type": "text/markdown",
    "content": "# Morning Briefing — 2026-03-23\n..."
  }
}
```

### Broadcast Announcements

Summary announcements go to all agents via `broadcast`. Keep the body under 500 characters.

```json
{
  "from": "journalist_agent",
  "to": "broadcast",
  "type": "info",
  "priority": "NORMAL",
  "subject": "Morning Briefing Published — 2026-03-23",
  "body": "Stories: 12 | Top: AI regulation update (score: 95)\nWeather: 18C, clear\n\nFull briefing delivered to Librarian."
}
```

## Incoming Messages

The agent does not currently poll for incoming IAMQ messages. Future: on-demand research requests from other agents.

## Graceful Degradation

When IAMQ is unreachable:

1. Log the connection failure
2. Skip the `IAMQAnnounceStep` in the pipeline (step status: SKIPPED)
3. Continue delivering via other channels (Telegram, filesystem)
4. Retry on next pipeline run

The agent must never fail a full pipeline because IAMQ is down.

## Peer Agents

| Agent | Relationship |
|-------|-------------|
| `librarian_agent` | Receives full briefing content for archival |
| `broadcast` | Receives summary announcements |

## Related

- Pipeline steps: [PIPELINES.md](PIPELINES.md)
- Architecture: [ARCHITECTURE.md](ARCHITECTURE.md)
- Safety rules for message content: [SAFETY.md](SAFETY.md)

---
*Owner: journalist_agent*

## References

- [IAMQ HTTP API](https://github.com/r3dlex/openclaw-inter-agent-message-queue/blob/main/spec/API.md)
- [IAMQ WebSocket Protocol](https://github.com/r3dlex/openclaw-inter-agent-message-queue/blob/main/spec/PROTOCOL.md)
- [IAMQ Cron Scheduling](https://github.com/r3dlex/openclaw-inter-agent-message-queue/blob/main/spec/CRON.md)
- [Sidecar Client](https://github.com/r3dlex/openclaw-inter-agent-message-queue/tree/main/sidecar)
- [openclaw-main-agent](https://github.com/r3dlex/openclaw-main-agent)
