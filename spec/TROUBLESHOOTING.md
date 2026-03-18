# TROUBLESHOOTING.md - Common Issues and Fixes

## Docker

### Container won't build
- Check Docker Desktop is running: `docker info`
- Ensure `requirements.txt` exists and is valid
- Try: `docker compose build --no-cache`

### Scripts timeout
- Check internet connectivity from inside container
- Some RSS feeds are slow or blocked — check `config/feeds.json`
- Increase timeout in script if needed

## RSS Feeds

### Feed returns empty
- The feed URL may have changed — check the source website
- Some feeds require specific User-Agent headers
- Rate limiting: wait and retry

### Importance scoring seems off
- Review `important_keywords` in `config/feeds.json`
- Scoring is additive — a story matching many keywords scores higher
- Adjust `importance_threshold_for_detail` in `config/feeds.json` `settings`

## Weather

### "Weather unavailable"
- `wttr.in` may be down — it's a free service
- Check: `curl -s "wttr.in/Stuttgart?format=j1" | head`
- Verify `$WEATHER_LOCATION` in `.env`

## OpenClaw Browser Fallback

### Browser relay not responding
- Ensure OpenClaw gateway is running: `openclaw status`
- Check: `openclaw browser status`
- The gateway must be running for Tier 3 fallback to work

## Scheduler Service

### Scheduler won't start
- Check Docker is running: `docker info`
- Verify the image builds: `docker compose build scheduler`
- Check logs: `docker compose logs scheduler`
- Ensure `.env` exists and has required variables

### Scheduled tasks not firing
- Verify the scheduler is running: `docker compose ps scheduler`
- Check scheduler logs for registration messages: `docker compose logs scheduler | grep schedule`
- Compare task times with `spec/CRON.md` — the scheduler runs 7 tasks matching that spec
- Time zone mismatch: the scheduler uses the container's TZ (set via `TZ` env var in `.env`)

### Ad-hoc `docker compose exec` fails
- The scheduler container must be running: `docker compose up -d scheduler`
- If container is stopped: `docker compose exec` will fail with "no such service" — start it first
- One-shot fallback: `docker compose run --rm --profile cli pipeline <cmd>`

### Scheduler crashes or restarts
- Check logs: `docker compose logs --tail=50 scheduler`
- The scheduler has error isolation per task — one failing pipeline should not crash the service
- If persistent crashes, check `tools/pipeline_runner/scheduler.py` for the error handler

## Environment

### Missing .env variables
- Copy `.env.example` to `.env`: `cp .env.example .env`
- Fill in all required values
- Restart containers after changing `.env`

## Librarian Handoff

### Files not appearing in librarian workspace
- Verify `$LIBRARIAN_AGENT_WORKSPACE` points to correct path
- Check `$JOURNALIST_DATA_DIR/log/` has output files
- Ensure the librarian agent workspace directory exists
