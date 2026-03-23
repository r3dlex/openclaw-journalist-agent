# Safety & Red Lines

> Non-negotiable rules for the Journalist Agent. These protect sources, respect rate limits, and keep secrets out of output.

## Content Attribution

- **Never publish raw scraped content without attribution.** Every briefing item must cite its source (feed name, URL, or API).
- Summarize and transform — do not copy-paste full articles into briefings.
- If attribution cannot be determined, mark the item as `[source unknown]` and flag for review.

## Web Crawling & RSS

- **Respect `robots.txt`.** Before crawling a domain, check its robots.txt. Honor `Disallow` and `Crawl-delay` directives.
- **Rate-limit RSS polling.** Never poll a single feed more than once per 15 minutes. The scheduler in `spec/CRON.md` enforces this.
- **No classified or restricted content.** Do not scrape paywalled, login-gated, or government-classified sources. If a URL returns 401/403, skip it.
- **Respect feed terms of service.** Some RSS feeds prohibit automated redistribution. When in doubt, summarize rather than quote.

## IAMQ Message Safety

- **Truncate content in messages.** IAMQ messages to `broadcast` must stay under 500 characters. Full content goes only to `librarian_agent`.
- **No secrets in messages.** Never include API keys, credentials, or internal paths in any IAMQ message body.
- **No PII in broadcasts.** User location, display name, and personal preferences stay out of broadcast messages.

## Credential Handling

- **`NEWS_API_KEY` from env only.** Read from `$NEWS_API_KEY` at runtime. Never hardcode, never log, never include in reports.
- **All secrets via environment variables.** Telegram tokens, API keys, and user PII are resolved from `.env` or `~/.openclaw/openclaw.json`. Never committed to git.
- **No secrets in logs.** The pipeline logger must redact any value matching known secret patterns (API keys, tokens, passwords).

## Failure Modes

When the agent encounters an error:

1. Log the error with context (feed URL, step name, timestamp)
2. Skip the failing item and continue the pipeline
3. Report failures in the pipeline summary (not silently swallowed)
4. Never crash the entire briefing because one feed or source fails

## Data Retention

| Data | Retention | Notes |
|------|-----------|-------|
| Pipeline logs | 7 days | In `$JOURNALIST_DATA_DIR/log/` |
| Briefing output | Permanent | Archived by Librarian |
| Feed cache | 24 hours | Prevents duplicate fetching |

## Related

- Communication rules: [COMMUNICATION.md](COMMUNICATION.md)
- Cron schedule: [CRON.md](CRON.md)
- Troubleshooting: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---
*Owner: journalist_agent*
