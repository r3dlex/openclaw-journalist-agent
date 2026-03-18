# TESTING.md - How to Test the Journalist Agent

## Pipeline Tests (Recommended)

The pipeline runner has a comprehensive test suite. Run it via Docker (zero-install):

```bash
# Build and run all tests + lint
docker compose run --rm pipeline-test
```

### Test Coverage

| Test File | What it tests |
|-----------|---------------|
| `tests/test_runner.py` | Core pipeline engine (pass/fail/skip/chain/context) |
| `tests/test_config.py` | Configuration loading (FeedConfig, PipelineSettings) |
| `tests/test_steps/test_score.py` | Importance scoring (keywords, boosts, caps) |
| `tests/test_steps/test_extract.py` | HTML content extraction (tags, truncation) |
| `tests/test_steps/test_fetch.py` | URL fetching (mock HTTP, error handling) |
| `tests/test_pipelines/test_news.py` | End-to-end news pipeline (mock feeds) |
| `tests/test_pipelines/test_article.py` | End-to-end article extraction (mock HTTP) |
| `tests/test_pipelines/test_weather.py` | End-to-end weather pipeline (mock API) |

### Running Locally (Development)

```bash
cd tools
poetry install
poetry run pytest -v                    # All tests
poetry run pytest -v -m "not integration"  # Unit tests only
poetry run ruff check pipeline_runner/  # Lint
poetry run mypy pipeline_runner/        # Type check
```

## Legacy Script Testing

All legacy scripts run in Docker. No local Python install required.

```bash
# Build the container
docker compose build

# Test news fetcher
docker compose run --rm journalist python scripts/fetch_news.py

# Test URL reader
docker compose run --rm journalist python scripts/read_url.py "https://en.wikipedia.org/wiki/Main_Page"

# Test weather
docker compose run --rm journalist python scripts/weather_forecast.py 6am
```

## Pipeline Validation

Validate configuration and connectivity:

```bash
docker compose run --rm pipeline validate
```

This checks:
- `config/feeds.json` is valid and has feeds
- `$JOURNALIST_DATA_DIR` exists
- `$LIBRARIAN_AGENT_WORKSPACE` is reachable (warning if not)

## Feed Configuration

Validate `config/feeds.json` is well-formed:

```bash
docker compose run --rm journalist python -c "import json; json.load(open('config/feeds.json')); print('OK')"
```

## Browser Fallback Testing

Test the OpenClaw browser relay (Tier 3 fallback):

```bash
# Requires OpenClaw gateway to be running
openclaw browser navigate "https://en.wikipedia.org/wiki/Main_Page" && openclaw browser snapshot --json
```

## Integration Testing

1. **News pipeline**: `docker compose run --rm pipeline news` — verify briefing output
2. **Article pipeline**: `docker compose run --rm pipeline article <url>` — verify extraction
3. **Weather pipeline**: `docker compose run --rm pipeline weather 6am` — verify format
4. **Browser fallback**: Test `browse_url` on a JS-heavy page
5. **Librarian handoff**: Verify files appear in `$JOURNALIST_DATA_DIR/log/`
6. **Pipeline validation**: `docker compose run --rm pipeline validate`

## Smoke Test Checklist

- [ ] `docker compose build` succeeds (all services)
- [ ] `docker compose run --rm pipeline-test` passes (all pipeline tests)
- [ ] `docker compose run --rm pipeline news` returns a briefing
- [ ] `docker compose run --rm pipeline validate` reports OK
- [ ] `fetch_news.py` returns scored stories (legacy)
- [ ] `read_url.py` extracts article content (legacy)
- [ ] `weather_forecast.py` returns formatted weather (legacy)
- [ ] `browse_url` works when OpenClaw gateway is running
- [ ] No secrets in git: `git diff --cached | grep -iE '(api_key|password|token|secret)'` returns nothing
- [ ] `.env` is NOT tracked: `git ls-files .env` returns nothing

## Continuous Integration

All tests run automatically on every push and pull request via GitHub Actions.

**Workflow:** `.github/workflows/ci.yml`

| Job | What it does |
|-----|-------------|
| `pipeline-lint` | Ruff lint + format check + mypy type check |
| `pipeline-test` | Full pytest suite on Python 3.12 and 3.13 with coverage |
| `pipeline-news` | News pipeline integration test (isolated) |
| `pipeline-article` | Article pipeline integration test (isolated) |
| `pipeline-weather` | Weather pipeline integration test (isolated) |
| `docker-build` | Build all Docker images + run containerized tests |
| `secrets-scan` | Scan for hardcoded secrets and local paths |
| `validate-config` | Validate feeds.json and .env.example completeness |

CI will fail if:
- Any test fails
- Ruff finds lint issues
- Mypy finds type errors
- Hardcoded secrets or local paths are detected
- `.env` is accidentally committed
- `config/feeds.json` is malformed
- `.env.example` is missing required variables

## Related

- **Pipeline spec**: `spec/PIPELINES.md`
- **Architecture**: `spec/ARCHITECTURE.md`
- **Troubleshooting**: `spec/TROUBLESHOOTING.md`
- **ADR**: `.archgate/adrs/ARCH-003-pipeline-architecture.md`
- **CI workflow**: `.github/workflows/ci.yml`
